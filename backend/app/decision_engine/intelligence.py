from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Campaign, DailyCampaignMetric, Order, OrderItem, Product, Inventory
from datetime import datetime, timedelta

def get_comparison_metrics(db: Session, organization_id: str, days: int = 7):
    # Calculates current period vs previous period
    campaigns = db.query(Campaign.id).filter(Campaign.organization_id == organization_id).subquery()
    latest_date_str = db.query(func.max(DailyCampaignMetric.date)).filter(DailyCampaignMetric.campaign_id.in_(campaigns)).scalar()
    
    if not latest_date_str:
        return None
        
    latest_date = datetime.strptime(latest_date_str, "%Y-%m-%d")
    current_start = (latest_date - timedelta(days=days - 1)).strftime("%Y-%m-%d")
    prev_start = (latest_date - timedelta(days=(days * 2) - 1)).strftime("%Y-%m-%d")
    prev_end = (latest_date - timedelta(days=days)).strftime("%Y-%m-%d")
    
    def fetch_period(start, end):
        return db.query(
            func.sum(DailyCampaignMetric.spend).label("spend"),
            func.sum(DailyCampaignMetric.revenue).label("revenue"),
            func.sum(DailyCampaignMetric.conversions).label("conversions"),
            func.sum(DailyCampaignMetric.clicks).label("clicks"),
            func.sum(DailyCampaignMetric.impressions).label("impressions")
        ).filter(
            DailyCampaignMetric.campaign_id.in_(campaigns),
            DailyCampaignMetric.date >= start,
            DailyCampaignMetric.date <= end
        ).first()
        
    curr = fetch_period(current_start, latest_date_str)
    prev = fetch_period(prev_start, prev_end)
    
    def safe_float(val): return float(val or 0)
    def calc_metrics(data):
        spend = safe_float(data.spend)
        rev = safe_float(data.revenue)
        clicks = safe_float(data.clicks)
        impressions = safe_float(data.impressions)
        convs = safe_float(data.conversions)
        return {
            "spend": spend,
            "revenue": rev,
            "profit": rev - spend,
            "roas": rev / spend if spend > 0 else 0,
            "cpc": spend / clicks if clicks > 0 else 0,
            "cpa": spend / convs if convs > 0 else 0,
            "cvr": convs / clicks if clicks > 0 else 0
        }
        
    curr_stats = calc_metrics(curr)
    prev_stats = calc_metrics(prev)
    
    comparisons = {}
    for k in curr_stats:
        cv = curr_stats[k]
        pv = prev_stats[k]
        diff = cv - pv
        pct = (diff / pv * 100) if pv != 0 else (100 if cv > 0 else 0)
        comparisons[k] = {
            "current_value": cv,
            "previous_value": pv,
            "absolute_change": diff,
            "percentage_change": pct,
            "direction": "up" if diff > 0 else ("down" if diff < 0 else "flat")
        }
    return comparisons

def detect_anomalies(db: Session, organization_id: str):
    anomalies = []
    comp = get_comparison_metrics(db, organization_id, 7)
    if not comp: return anomalies
    
    # 1. Spend increasing while revenue falls
    if comp["spend"]["direction"] == "up" and comp["revenue"]["direction"] == "down":
        anomalies.append({
            "type": "INEFFICIENCY",
            "severity": "HIGH",
            "entity": "Organization",
            "metric": "Revenue/Spend Divergence",
            "evidence": "Spend increased while revenue fell",
            "change": f"Spend {comp['spend']['percentage_change']:.1f}%, Rev {comp['revenue']['percentage_change']:.1f}%"
        })
        
    # 2. CPA increasing significantly
    if comp["cpa"]["percentage_change"] > 20:
        anomalies.append({
            "type": "COST_SPIKE",
            "severity": "MEDIUM",
            "entity": "Organization",
            "metric": "CPA",
            "evidence": "Customer acquisition cost is rising rapidly",
            "change": f"+{comp['cpa']['percentage_change']:.1f}%"
        })
        
    # 3. ROAS dropping
    if comp["roas"]["percentage_change"] < -15:
        anomalies.append({
            "type": "PERFORMANCE_DROP",
            "severity": "HIGH",
            "entity": "Organization",
            "metric": "ROAS",
            "evidence": "Return on ad spend is declining significantly",
            "change": f"{comp['roas']['percentage_change']:.1f}%"
        })
        
    return anomalies

def simulate_scenario(current_spend, current_roas, current_margin_pct, proposed_budget_change_pct):
    # What-If Foundation
    # Assumes marginal ROAS degradation of 10% for every 20% increase in spend
    new_spend = current_spend * (1 + (proposed_budget_change_pct / 100.0))
    degradation = (proposed_budget_change_pct / 20.0) * 0.10 if proposed_budget_change_pct > 0 else 0
    expected_roas = current_roas * (1 - degradation)
    
    expected_rev = new_spend * expected_roas
    expected_gross_profit = expected_rev * (current_margin_pct / 100.0)
    expected_net_profit = expected_gross_profit - new_spend
    
    return {
        "status": "SIMULATED",
        "proposed_spend": new_spend,
        "expected_roas": expected_roas,
        "expected_revenue": expected_rev,
        "expected_profit": expected_net_profit,
        "confidence": "Medium" if proposed_budget_change_pct <= 20 else "Low"
    }

def get_inventory_risks(db: Session, organization_id: str):
    invs = db.query(Inventory, Product).join(Product).filter(Inventory.organization_id == organization_id).all()
    risks = []
    for inv, prod in invs:
        if inv.quantity_available < 10:
            risks.append({
                "type": "STOCKOUT_RISK",
                "severity": "HIGH",
                "entity": f"Product: {prod.sku}",
                "metric": "Inventory",
                "current_value": inv.quantity_available,
                "evidence": f"Only {inv.quantity_available} units remaining for {prod.name}"
            })
    return risks
