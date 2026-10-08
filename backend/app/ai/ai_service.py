import json
import hashlib
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Recommendation, Campaign, Product, Customer, DecisionMemory
from app.ai.providers import get_llm_provider
from app.decision_engine.engine import get_diagnostics
from app.services.analytics_service import (
    get_campaign_profitability, 
    get_product_profitability,
    get_customer_analytics,
    get_dashboard_overview
)

# Simple in-memory cache for explanations
EXPLANATION_CACHE = {}

PLANNER_SYSTEM_PROMPT = """You are DeciFlow's Query Planner.
Your job is to classify the user's business question into a structured JSON query plan.
Domains: PERFORMANCE, PROFITABILITY, RISK, OPPORTUNITY, CAMPAIGN, PRODUCT, CUSTOMER, TREND, COMPARISON, GENERAL_BUSINESS.
Extract specific entity names (e.g., campaign names, product names) if mentioned.
Return ONLY valid JSON:
{
  "domain": "PROFITABILITY",
  "entities": ["campaign name if any"],
  "intent": "identify_loss_making_campaigns",
  "comparison": null,
  "time_range": "available_data"
}
If the user asks a follow-up question (e.g., "Why?", "What about the other one?"), use the conversation history to infer the domain and entities.
"""

SYSTEM_PROMPT = """You are DeciFlow's business intelligence analyst.
Your role is to interpret the organization's verified business data and help the user understand performance, profitability, risk, and opportunities.
Financial metrics supplied in the context are authoritative.
Do not invent financial values, entities, campaigns, products, customers, orders, attribution, or projections.
Do not override deterministic DeciFlow decisions.
You may reason over the supplied data, compare entities, identify patterns, explain trade-offs, and synthesize multiple metrics.
When information is missing, state that it is unavailable.
Do not assume missing values are zero.
ROAS measures revenue efficiency, not profitability.
Contribution profit accounts for revenue, product cost, and marketing spend.
When campaign attribution is unavailable, do not claim campaign-level profitability.
Answer naturally and conversationally rather than using rigid templates.
Use exact values from the supplied business context when making quantitative claims.
Keep your answers concise, ideally 1-3 paragraphs. For complex questions, use bullets."""

EXPLAIN_SYSTEM_PROMPT = SYSTEM_PROMPT + """
You must output ONLY valid JSON matching this schema exactly:
{
  "summary": "Short explanation of what happened.",
  "why_it_matters": "Business significance.",
  "recommended_action": "What the existing decision recommends.",
  "risk": "Important caveat.",
  "evidence_points": ["point 1", "point 2"]
}"""

def _hash_evidence(evidence_dict: dict) -> str:
    s = json.dumps(evidence_dict, sort_keys=True)
    return hashlib.md5(s.encode('utf-8')).hexdigest()

def explain_recommendation(db: Session, organization_id: str, recommendation_id: str):
    rec = db.query(Recommendation).filter(
        Recommendation.id == recommendation_id,
        Recommendation.organization_id == organization_id
    ).first()
    
    if not rec:
        return {"available": False, "reason": "Recommendation not found"}
        
    fallback = {
        "available": False,
        "summary": "AI explanation is currently unavailable.",
        "deterministic_summary": f"{rec.title}. {rec.reason}"
    }

    provider = get_llm_provider()
    if not provider:
        return fallback

    context = {
        "campaign_id": rec.campaign_id,
        "title": rec.title,
        "action": rec.action_type,
        "score": rec.score,
        "confidence": rec.confidence,
        "reason": rec.reason,
        "projected_profit": rec.projected_profit,
        "evidence": json.loads(rec.evidence_json) if rec.evidence_json else {}
    }

    evidence_hash = _hash_evidence(context)
    cache_key = f"{rec.id}_{evidence_hash}"
    if cache_key in EXPLANATION_CACHE:
        return EXPLANATION_CACHE[cache_key]

    user_prompt = f"Explain the following recommendation evidence:\n{json.dumps(context, indent=2)}"

    try:
        response_json = provider.generate_json(EXPLAIN_SYSTEM_PROMPT, user_prompt)
        required_keys = ["summary", "why_it_matters", "recommended_action", "risk", "evidence_points"]
        for k in required_keys:
            if k not in response_json:
                response_json[k] = "N/A"
        response_json["available"] = True
        EXPLANATION_CACHE[cache_key] = response_json
        return response_json
    except Exception as e:
        return fallback

def plan_query(provider, query: str, history: List[Dict[str, str]]) -> dict:
    if type(provider).__name__ == "MockProvider":
        # Mock planner behavior for missing api key
        q = query.lower()
        domain = "GENERAL_BUSINESS"
        if any(w in q for w in ["product", "item", "sku"]): domain = "PRODUCT"
        elif any(w in q for w in ["customer", "client", "buyer"]): domain = "CUSTOMER"
        elif any(w in q for w in ["campaign", "budget"]): domain = "CAMPAIGN"
        
        return {
            "domain": domain,
            "entities": [],
            "intent": "general_inquiry",
            "comparison": None,
            "time_range": "available_data"
        }
        
    history_text = ""
    if history:
        history_text = "Conversation History:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in history[-3:]]) + "\n\n"
        
    user_prompt = f"{history_text}User Query: {query}"
    
    try:
        plan = provider.generate_json(PLANNER_SYSTEM_PROMPT, user_prompt)
        return plan
    except Exception as e:
        # Fallback plan but we still log the error
        print(f"Planner error: {str(e)}")
        return {
            "domain": "GENERAL_BUSINESS",
            "entities": [],
            "intent": "fallback",
            "comparison": None,
            "time_range": "available_data"
        }

def answer_query(db: Session, organization_id: str, query: str, history: List[Dict[str, str]] = None):
    provider = get_llm_provider()
    if history is None:
        history = []
        
    if not provider:
        return {
            "answer": "OpenAI API Key is missing or not configured. Please configure LLM_API_KEY in the .env file.",
            "evidence": [],
            "impact": "N/A",
            "recommendation": "N/A",
            "confidence": "N/A"
        }

    plan = plan_query(provider, query, history)
    domain = plan.get("domain", "GENERAL_BUSINESS")
    entities = plan.get("entities", [])
    
    context = {}
    
    if domain == "PRODUCT":
        prods = get_product_profitability(db, organization_id)
        # Sort by profit
        prods.sort(key=lambda x: x.get("gross_profit") or 0, reverse=True)
        if entities:
            matched = [p for p in prods if any(e.lower() in p["name"].lower() for e in entities)]
            if matched:
                context["product_analytics"] = matched
            else:
                context["product_analytics"] = prods[:5]
                context["note"] = f"Could not find exact products matching {entities}. Showing top products instead."
        else:
            context["product_analytics"] = prods[:10]
            
    elif domain == "CUSTOMER":
        cust = get_customer_analytics(db, organization_id)
        context["customer_analytics"] = cust
        
    else:
        # Campaigns, Profitability, Risk, Opportunity, General
        camp_prof = get_campaign_profitability(db, organization_id)
        if entities:
            matched = [c for c in camp_prof if any(e.lower() in c.get("campaign_name", "").lower() for e in entities)]
            if matched:
                context["campaign_profitability"] = matched
            else:
                context["campaign_profitability"] = camp_prof
                context["note"] = f"Could not find exact campaigns matching {entities}. Showing all campaigns."
        else:
            context["campaign_profitability"] = camp_prof
            
        active_recs = db.query(Recommendation).filter(
            Recommendation.organization_id == organization_id,
            Recommendation.status == "Pending"
        ).order_by(Recommendation.score.desc()).all()
        
        context["top_recommendations"] = [
            {"title": r.title, "reason": r.reason, "action": r.action_type, "campaign_id": r.campaign_id} for r in active_recs
        ]
        
    # Include dashboard summary always as baseline
    diagnostics = get_diagnostics(db, organization_id)
    context["organization_summary"] = {
        "total_spend": diagnostics.get("total_spend", 0),
        "total_revenue": diagnostics.get("total_revenue", 0),
        "total_profit": diagnostics.get("total_profit", 0)
    }

    # Include decision memory / outcomes to answer questions like "What happened after I increased Campaign A?"
    decision_memories = db.query(DecisionMemory).filter(
        DecisionMemory.organization_id == organization_id
    ).order_by(DecisionMemory.evaluated_at.desc()).limit(10).all()
    
    if decision_memories:
        context["recent_outcomes"] = [
            {
                "id": m.id,
                "expected_profit": m.expected_profit,
                "actual_profit": m.actual_profit,
                "variance": m.variance,
                "outcome": m.outcome_classification,
                "learning": m.learning_signal
            } for m in decision_memories
        ]

    history_text = ""
    if history:
        history_text = "Conversation History:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in history[-3:]]) + "\n\n"
        
    user_prompt = f"Query Plan:\n{json.dumps(plan, indent=2)}\n\nOrganization Context:\n{json.dumps(context, indent=2)}\n\n{history_text}User Query: {query}"

    try:
        answer = provider.generate_text(SYSTEM_PROMPT, user_prompt)
        return {
            "answer": answer,
            "evidence": [],
            "impact": "",
            "recommendation": "",
            "confidence": "Calculated by AI based on context"
        }
    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "401" in error_msg:
            friendly_err = "OpenAI API Key is invalid or missing. Please configure a valid key."
        elif "timeout" in error_msg.lower():
            friendly_err = "The AI provider timed out. Please try again."
        elif "rate limit" in error_msg.lower() or "429" in error_msg:
            friendly_err = "The AI provider is rate limited. Please try again later."
        else:
            friendly_err = f"DeciFlow AI Provider Error: {error_msg}"
            
        return {
            "answer": friendly_err,
            "evidence": [],
            "impact": "Error",
            "recommendation": "Error",
            "confidence": "N/A"
        }
