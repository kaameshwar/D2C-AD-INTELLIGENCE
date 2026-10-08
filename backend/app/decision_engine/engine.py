import json
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.models import Recommendation, Action, Campaign, DailyCampaignMetric, DecisionMemory
from app.services.analytics_service import get_campaign_profitability

DECISION_THRESHOLDS = {
    "low_roas": 1.5,
    "strong_roas": 2.0,
    "minimum_spend": 100.0,
    "minimum_conversions": 1,
    "minimum_days": 3,
    "decline_threshold": 0.20,
    "improvement_threshold": 0.20,
    "healthy_margin": 20.0,
    "low_margin": 10.0,
}

def calculate_confidence_score(spend: float, conversions: int, days: int) -> dict:
    """Deterministic confidence calculation based on data volume."""
    c_days = min(30, (days / 14.0) * 30)
    c_spend = min(40, (spend / 1000.0) * 40)
    c_conv = min(30, (conversions / 50.0) * 30)
    
    score = int(c_days + c_spend + c_conv)
    score = max(1, min(100, score))
    
    if score >= 80:
        label = "High"
    elif score >= 50:
        label = "Medium"
    else:
        label = "Low"
        
    return {"score": score, "label": label}

def generate_recommendations(db: Session, organization_id: str):
    campaigns = db.query(Campaign).filter(Campaign.organization_id == organization_id).all()
    if not campaigns:
        return
        
    camp_dict = {c.id: c for c in campaigns}
    camp_ids = list(camp_dict.keys())
    
    # To track which recommendations are active this cycle
    active_recommendation_keys = set()
    
    from app.services.financial_context import get_campaign_financial_context
    
    for camp_id in camp_ids:
        camp = camp_dict[camp_id]
        
        ctx = get_campaign_financial_context(db, organization_id, camp_id, days=7)
        if not ctx:
            continue
            
        spend = ctx["spend"]
        revenue = ctx["revenue"]
        conversions = ctx["conversions"]
        days_count = ctx["analysis_days"]
        
        profit = revenue - spend
        roas = ctx["roas"]
        
        # Insufficient Data Check
        if (spend * days_count) < DECISION_THRESHOLDS["minimum_spend"] or days_count < DECISION_THRESHOLDS["minimum_days"]:
            continue
            
        conf_data = calculate_confidence_score(spend * days_count, int(conversions * days_count), days_count)
        # If signal is too weak, don't automate a recommendation
        if conf_data["score"] < 30:
            continue
            
        recommendation_data = None
        
        # Retrieve profitability metrics from context
        attribution_available = ctx["attribution_available"]
        contribution_profit = ctx["contribution_profit"]
        contribution_margin = ctx["contribution_margin"]
        product_cost = ctx["product_cost"]
        attributed_revenue = revenue if attribution_available else 0
        
        # Check historical context
        history = db.query(DecisionMemory).join(
            Recommendation, DecisionMemory.recommendation_id == Recommendation.id
        ).filter(
            Recommendation.campaign_id == camp.id,
            Recommendation.organization_id == organization_id,
            DecisionMemory.outcome_classification.isnot(None)
        ).order_by(DecisionMemory.evaluated_at.desc()).first()
        
        historical_reason = ""
        if history and history.actual_profit is not None and history.expected_profit is not None:
            hist_rec = db.query(Recommendation).filter(Recommendation.id == history.recommendation_id).first()
            if hist_rec and hist_rec.budget_change:
                action_desc = "Previous budget " + ("increase" if hist_rec.budget_change > 0 else "reduction")
                variance = history.actual_profit - history.expected_profit
                if history.expected_profit != 0:
                    pct = int(abs(variance / history.expected_profit) * 100)
                    if pct > 0:
                        direction = "improved" if variance > 0 else "reduced"
                        historical_reason = f" {action_desc} {direction} contribution profitability by {pct}%."
        # Rule Precedence (Phase 5 + Phase 3):
        # 1. Negative contribution profit (PROFITABILITY_REVIEW) - if attributed
        # 2. Negative gross profit (Phase 3 legacy) - if not attributed
        # 3. Low margin (MARGIN_REVIEW)
        # 4. Underperformance (ROAS < 1.5)
        # 5. Strong profitable campaign (SCALE_PROFITABLE)
        # 6. Profitable but under-scaled (SCALE_OPPORTUNITY)
        # 7. Strong ROAS (Phase 3 legacy)
        
        if attribution_available and contribution_profit < 0:
            if roas >= DECISION_THRESHOLDS["strong_roas"]:
                # B. ROAS MISLEADING
                recommendation_data = {
                    "title": f"Misleading ROAS: {camp.name}",
                    "action_type": "PROFITABILITY_REVIEW",
                    "budget_change": - (spend * 0.5) if spend else -50.0,
                    "projected_profit": abs(contribution_profit),
                    "score": min(100, 80 + int((abs(contribution_profit) / 1000) * 10)),
                    "confidence": conf_data["label"],
                    "reason": "ROAS is healthy, but the campaign is contribution-negative after product costs.",
                    "evidence_json": {
                        "campaign": {"id": camp.id, "name": camp.name},
                        "metrics": {"spend": spend, "attributed_revenue": attributed_revenue, "product_cost": product_cost, "contribution_profit": contribution_profit, "roas": roas, "contribution_margin": contribution_margin},
                        "data_quality": {"attribution_available": attribution_available, "product_cost_available": product_cost is not None},
                        "decision": {"type": "PROFITABILITY_REVIEW", "reason": "Strong ROAS but negative contribution profit"}
                    }
                }
            else:
                # Regular negative profit
                recommendation_data = {
                    "title": f"Negative Contribution Alert: {camp.name}",
                    "action_type": "PAUSE_OR_REDUCE",
                    "budget_change": - (spend * 0.5) if spend else -50.0,
                    "projected_profit": abs(contribution_profit),
                    "score": min(100, 75 + int((abs(contribution_profit) / 1000) * 10)),
                    "confidence": conf_data["label"],
                    "reason": "Campaign is generating negative contribution profit.",
                    "evidence_json": {
                        "campaign": {"id": camp.id, "name": camp.name},
                        "metrics": {"spend": spend, "attributed_revenue": attributed_revenue, "product_cost": product_cost, "contribution_profit": contribution_profit, "roas": roas, "contribution_margin": contribution_margin},
                        "data_quality": {"attribution_available": attribution_available, "product_cost_available": product_cost is not None},
                        "decision": {"type": "PAUSE_OR_REDUCE", "reason": "Negative contribution profit"}
                    }
                }
                
        elif not attribution_available and profit < 0:
            # Action: Reduce budget. Projected profit savings = reduced spend * (1 - ROAS)
            budget_change = - (spend * 0.5) if spend else -50.0
            proj_profit = abs(budget_change) * (1.0 - roas)
            
            recommendation_data = {
                "title": f"Negative Profit Alert: {camp.name}",
                "action_type": "PAUSE_OR_REDUCE",
                "budget_change": budget_change,
                "projected_profit": proj_profit,
                "score": min(100, 70 + int((abs(profit) / 1000) * 30)),
                "confidence": conf_data["label"],
                "reason": "Campaign is generating negative contribution.",
                "evidence_json": {
                    "campaign_id": camp.id,
                    "metrics": {"spend": spend, "revenue": revenue, "profit": profit, "roas": roas, "conversions": conversions},
                    "thresholds": {},
                    "decision": {"type": "PAUSE_OR_REDUCE", "reason": "Profit < 0"}
                }
            }
            
        elif attribution_available and contribution_profit > 0 and contribution_margin < DECISION_THRESHOLDS["low_margin"]:
            # C. LOW-MARGIN CAMPAIGN
            recommendation_data = {
                "title": f"Low Margin Review: {camp.name}",
                "action_type": "MARGIN_REVIEW",
                "budget_change": 0.0,
                "projected_profit": None,
                "score": 65,
                "confidence": conf_data["label"],
                "reason": f"Contribution profit is positive, but margin ({contribution_margin:.1f}%) is below target.",
                "evidence_json": {
                    "campaign": {"id": camp.id, "name": camp.name},
                    "metrics": {"spend": spend, "attributed_revenue": attributed_revenue, "product_cost": product_cost, "contribution_profit": contribution_profit, "roas": roas, "contribution_margin": contribution_margin},
                    "data_quality": {"attribution_available": attribution_available, "product_cost_available": product_cost is not None},
                    "decision": {"type": "MARGIN_REVIEW", "reason": "Low contribution margin"}
                }
            }
            
        elif roas < DECISION_THRESHOLDS["low_roas"]:
            # If profit > 0 but ROAS is low, cutting spend doesn't mathematically increase gross profit, it only improves margin.
            # So projected_profit is None (null) because we can't guarantee gross profit increases.
            budget_change = - (spend * 0.2) if spend else -20.0
            
            recommendation_data = {
                "title": f"Review Low-Performing Campaign: {camp.name}",
                "action_type": "REDUCE",
                "budget_change": budget_change,
                "projected_profit": None, 
                "score": min(100, 50 + int((1.5 - roas) * 30)),
                "confidence": conf_data["label"],
                "reason": f"Campaign ROAS ({roas:.2f}) is below target.",
                "evidence_json": {
                    "campaign_id": camp.id,
                    "metrics": {"spend": spend, "revenue": revenue, "profit": profit, "roas": roas, "conversions": conversions},
                    "thresholds": {"low_roas": DECISION_THRESHOLDS["low_roas"]},
                    "decision": {"type": "REDUCE", "reason": "ROAS below acceptable threshold"}
                }
            }
            
        elif attribution_available and contribution_profit > 0 and contribution_margin >= DECISION_THRESHOLDS["healthy_margin"]:
            # A. SCALE PROFITABLE CAMPAIGN / D. PROFITABLE BUT UNDER-SCALED
            if (spend * days_count) < 500:
                action_type = "SCALE_OPPORTUNITY"
                title = f"Scale Opportunity: {camp.name}"
            else:
                action_type = "SCALE_PROFITABLE"
                title = f"Scale Highly Profitable Campaign: {camp.name}"
                
            budget_change = (spend * 0.2) if spend else 20.0
            
            recommendation_data = {
                "title": title,
                "action_type": action_type,
                "budget_change": budget_change,
                "projected_profit": budget_change * (roas - 1.0) * (contribution_margin / 100.0),
                "score": min(100, 70 + int(contribution_margin)),
                "confidence": conf_data["label"],
                "reason": f"Campaign maintains a healthy {contribution_margin:.1f}% contribution margin.",
                "evidence_json": {
                    "campaign": {"id": camp.id, "name": camp.name},
                    "metrics": {"spend": spend, "attributed_revenue": attributed_revenue, "product_cost": product_cost, "contribution_profit": contribution_profit, "roas": roas, "contribution_margin": contribution_margin},
                    "data_quality": {"attribution_available": attribution_available, "product_cost_available": product_cost is not None},
                    "decision": {"type": action_type, "reason": "Healthy contribution margin and positive profit"}
                }
            }

        elif roas >= DECISION_THRESHOLDS["strong_roas"] and conversions >= DECISION_THRESHOLDS["minimum_conversions"]:
            # Action: Scale budget. Projected profit = scaled spend * (ROAS - 1)
            budget_change = (spend * 0.2) if spend else 20.0
            proj_profit = budget_change * (roas - 1.0)
            
            recommendation_data = {
                "title": f"Scale Strong Campaign: {camp.name}",
                "action_type": "SCALE",
                "budget_change": budget_change,
                "projected_profit": proj_profit,
                "score": min(100, 60 + int((roas - 2.0) * 20) + int((spend / 1000) * 20)),
                "confidence": conf_data["label"],
                "reason": f"Campaign is highly profitable (ROAS {roas:.2f}).",
                "evidence_json": {
                    "campaign_id": camp.id,
                    "metrics": {"spend": spend, "revenue": revenue, "profit": profit, "roas": roas, "conversions": conversions},
                    "thresholds": {"strong_roas": DECISION_THRESHOLDS["strong_roas"]},
                    "decision": {"type": "SCALE", "reason": "ROAS exceeds strong threshold"}
                }
            }

        # Append historical context if present
        if recommendation_data and historical_reason:
            recommendation_data["reason"] += historical_reason

        # Handle persistence
        if recommendation_data:
            rec_key = f"{camp.id}_{recommendation_data['action_type']}"
            active_recommendation_keys.add(rec_key)
            
            existing_rec = db.query(Recommendation).filter(
                Recommendation.organization_id == organization_id,
                Recommendation.campaign_id == camp.id,
                Recommendation.action_type == recommendation_data["action_type"],
                Recommendation.status == "Pending"
            ).first()

            evidence_str = json.dumps(recommendation_data["evidence_json"])
            
            if existing_rec:
                existing_rec.title = recommendation_data["title"]
                existing_rec.budget_change = recommendation_data["budget_change"]
                existing_rec.projected_profit = recommendation_data["projected_profit"]
                existing_rec.score = recommendation_data["score"]
                existing_rec.confidence = recommendation_data["confidence"]
                existing_rec.reason = recommendation_data["reason"]
                existing_rec.evidence_json = evidence_str
            else:
                new_rec = Recommendation(
                    organization_id=organization_id,
                    campaign_id=camp.id,
                    title=recommendation_data["title"],
                    action_type=recommendation_data["action_type"],
                    budget_change=recommendation_data["budget_change"],
                    projected_profit=recommendation_data["projected_profit"],
                    score=recommendation_data["score"],
                    confidence=recommendation_data["confidence"],
                    reason=recommendation_data["reason"],
                    evidence_json=evidence_str,
                    status="Pending"
                )
                db.add(new_rec)
                
    # Handle Stale Recommendations (ones that were pending but no longer apply)
    all_pending = db.query(Recommendation).filter(
        Recommendation.organization_id == organization_id,
        Recommendation.status == "Pending"
    ).all()
    
    for p_rec in all_pending:
        key = f"{p_rec.campaign_id}_{p_rec.action_type}"
        if key not in active_recommendation_keys:
            # Condition no longer holds, mark as resolved
            p_rec.status = "Resolved"
            
    db.commit()


def get_diagnostics(db: Session, organization_id: str):
    campaigns = db.query(Campaign.id).filter(Campaign.organization_id == organization_id).subquery()
    campaign_count = db.query(Campaign).filter(Campaign.organization_id == organization_id).count()
    
    metrics = db.query(
        func.sum(DailyCampaignMetric.spend).label("spend"),
        func.sum(DailyCampaignMetric.revenue).label("revenue")
    ).filter(DailyCampaignMetric.campaign_id.in_(campaigns)).first()
    
    total_spend = float(metrics.spend or 0.0)
    total_revenue = float(metrics.revenue or 0.0)
    total_profit = total_revenue - total_spend
    average_roas = (total_revenue / total_spend) if total_spend > 0 else 0.0

    active_recommendations = db.query(Recommendation).filter(
        Recommendation.organization_id == organization_id,
        Recommendation.status == "Pending"
    ).count()

    camp_metrics = db.query(
        DailyCampaignMetric.campaign_id,
        func.sum(DailyCampaignMetric.spend).label("spend"),
        func.sum(DailyCampaignMetric.revenue).label("revenue")
    ).filter(DailyCampaignMetric.campaign_id.in_(campaigns)).group_by(DailyCampaignMetric.campaign_id).all()

    negative_profit_campaigns = 0
    low_roas_campaigns = 0
    strong_campaigns = 0

    for cm in camp_metrics:
        s = float(cm.spend or 0.0)
        r = float(cm.revenue or 0.0)
        p = r - s
        if p < 0:
            negative_profit_campaigns += 1
        
        roas = (r / s) if s > 0 else 0.0
        if s >= DECISION_THRESHOLDS["minimum_spend"]:
            if roas < DECISION_THRESHOLDS["low_roas"]:
                low_roas_campaigns += 1
            elif roas >= DECISION_THRESHOLDS["strong_roas"]:
                strong_campaigns += 1

    return {
        "campaign_count": campaign_count,
        "total_spend": total_spend,
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "average_roas": average_roas,
        "negative_profit_campaigns": negative_profit_campaigns,
        "low_roas_campaigns": low_roas_campaigns,
        "strong_campaigns": strong_campaigns,
        "active_recommendations": active_recommendations
    }

def get_opportunities(db: Session, organization_id: str):
    generate_recommendations(db, organization_id)

    recs = db.query(Recommendation).filter(
        Recommendation.organization_id == organization_id,
        Recommendation.status == "Pending"
    ).order_by(Recommendation.score.desc()).all()
    
    opps = []
    for r in recs:
        ev_data = []
        if r.evidence_json:
            try:
                parsed = json.loads(r.evidence_json)
                metrics = parsed.get("metrics", {})
                
                ev_data = []
                if "spend" in metrics:
                    ev_data.append(f"Marketing Spend: ₹{metrics['spend']:,.0f}")
                if "attributed_revenue" in metrics:
                    ev_data.append(f"Attributed Revenue: ₹{metrics['attributed_revenue']:,.0f}")
                elif "revenue" in metrics:
                    ev_data.append(f"Revenue: ₹{metrics['revenue']:,.0f}")
                if "product_cost" in metrics and metrics["product_cost"] is not None:
                    ev_data.append(f"Product Cost: ₹{metrics['product_cost']:,.0f}")
                if "contribution_profit" in metrics and metrics["contribution_profit"] is not None:
                    ev_data.append(f"Contribution Profit: ₹{metrics['contribution_profit']:,.0f}")
                elif "profit" in metrics:
                    ev_data.append(f"Profit: ₹{metrics['profit']:,.0f}")
                if "contribution_margin" in metrics and metrics["contribution_margin"] is not None:
                    ev_data.append(f"Contribution Margin: {metrics['contribution_margin']:.1f}%")
                if "roas" in metrics:
                    ev_data.append(f"ROAS: {metrics['roas']:.2f}x")
                    
                if "decision" in parsed and "reason" in parsed["decision"]:
                    ev_data.append(f"Reasoning: {parsed['decision']['reason']}")
            except:
                pass

        opps.append({
            "id": r.id,
            "title": r.title,
            "score": r.score,
            "projected_profit": r.projected_profit,
            "confidence": r.confidence,
            "evidence": ev_data,
            "campaign_id": r.campaign_id,
            "recommended_action": f"{'Increase' if r.budget_change > 0 else 'Decrease'} budget by ₹{abs(r.budget_change)}"
        })
    return opps

def get_recommendations(db: Session, organization_id: str):
    generate_recommendations(db, organization_id)

    recs = db.query(Recommendation).filter(
        Recommendation.organization_id == organization_id
    ).order_by(Recommendation.created_at.desc()).all()
    
    return [
        {
            "id": r.id,
            "campaign_id": r.campaign_id,
            "action": f"{'Increase' if r.budget_change > 0 else 'Decrease'} budget by ₹{abs(r.budget_change)}",
            "budget_change": r.budget_change,
            "expected_impact": (f"+₹{r.projected_profit:.2f} profit" if r.projected_profit >= 0 else f"Avoid ₹{abs(r.projected_profit):.2f} loss") if r.projected_profit is not None else "Margin Improvement",
            "confidence": r.confidence,
            "reason": r.reason,
            "status": r.status,
            "title": r.title,
            "score": r.score
        }
        for r in recs
    ]

def approve_recommendation(db: Session, id: str, organization_id: str):
    rec = db.query(Recommendation).filter(Recommendation.id == id, Recommendation.organization_id == organization_id).first()
    if rec:
        rec.status = "Approved"
        db.commit()
        return {"status": "success"}
    return {"status": "error", "message": "Not found"}

def execute_recommendation(db: Session, id: str, organization_id: str, user_id: str):
    rec = db.query(Recommendation).filter(Recommendation.id == id, Recommendation.organization_id == organization_id).first()
    if rec:
        rec.status = "Executed"
        
        action = Action(
            organization_id=rec.organization_id,
            recommendation_id=rec.id,
            user_id=user_id,
            execution_mode="Simulated",
            execution_result="Success"
        )
        db.add(action)
        db.commit()
        return {"status": "success"}
    return {"status": "error", "message": "Not found"}
