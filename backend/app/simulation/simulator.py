from sqlalchemy.orm import Session
from app.models import Campaign, DailyCampaignMetric, Product

from app.services.financial_context import get_campaign_financial_context

def simulate_budget_change(db: Session, organization_id: str, campaign_id: str, proposed_spend: float):
    
    ctx = get_campaign_financial_context(db, organization_id, campaign_id, days=7)
    if not ctx:
        return {"error": "Campaign not found"}
        
    avg_daily_spend = ctx["spend"]
    roas = ctx["roas"]
    cpa = ctx["cpa"]
    margin_pct = ctx["margin_pct"]
    current_daily_profit = ctx["contribution_profit"]
    
    # Simple simulation logic based on historical data
    # Assuming diminishing returns at higher budget
    diminishing_factor = 0.9 if proposed_spend > avg_daily_spend else 1.05
    
    projected_revenue = proposed_spend * roas * diminishing_factor
    projected_conversions = int(proposed_spend / cpa * diminishing_factor) if cpa > 0 else 0
    
    projected_profit = (projected_revenue * margin_pct) - proposed_spend
    
    incremental_profit = projected_profit - current_daily_profit
    
    constraint_status = "Valid"
    inventory = ctx.get("inventory_count")
    if inventory is not None and inventory < (projected_conversions * 14): # Assuming 2 week supply needed
        constraint_status = f"Warning: Inventory risk for {ctx.get('product_sku')}"
    
    projected_roas = projected_revenue / proposed_spend if proposed_spend > 0 else 0
    
    return {
        "campaign_id": campaign_id,
        "current_spend": avg_daily_spend,
        "proposed_spend": proposed_spend,
        "current_revenue": ctx["revenue"],
        "projected_revenue": projected_revenue,
        "current_contribution_profit": current_daily_profit,
        "projected_contribution_profit": projected_profit,
        "current_roas": roas,
        "projected_roas": projected_roas,
        "incremental_contribution_profit": incremental_profit,
        "projected_conversions": projected_conversions,
        "constraint_status": constraint_status,
        "confidence": "High" if diminishing_factor > 0.8 else "Medium",
        "product_cost_available": ctx["product_cost"] is not None
    }
