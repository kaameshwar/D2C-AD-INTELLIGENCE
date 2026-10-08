from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.models import Campaign, DailyCampaignMetric, Order, OrderItem, Product

def get_campaign_financial_context(db: Session, organization_id: str, campaign_id: str, days: int = 7):
    # 1. Fetch Campaign
    camp = db.query(Campaign).filter(Campaign.id == campaign_id, Campaign.organization_id == organization_id).first()
    if not camp:
        return None
        
    # 2. Determine Analysis Period
    latest_date_str = db.query(func.max(DailyCampaignMetric.date)).filter(DailyCampaignMetric.campaign_id == campaign_id).scalar()
    
    start_date_str = None
    if latest_date_str:
        try:
            latest_date = datetime.strptime(latest_date_str, "%Y-%m-%d")
            start_date_str = (latest_date - timedelta(days=days - 1)).strftime("%Y-%m-%d")
        except ValueError:
            pass
            
    # 3. Fetch Tracked Metrics (Spend, Tracked Revenue)
    metrics_query = db.query(
        func.sum(DailyCampaignMetric.spend).label("spend"),
        func.sum(DailyCampaignMetric.revenue).label("tracked_revenue"),
        func.sum(DailyCampaignMetric.conversions).label("conversions"),
        func.count(DailyCampaignMetric.id).label("days_count")
    ).filter(DailyCampaignMetric.campaign_id == campaign_id)
    
    if start_date_str:
        metrics_query = metrics_query.filter(DailyCampaignMetric.date >= start_date_str)
        
    metrics = metrics_query.first()
    
    total_spend = float(metrics.spend or 0)
    tracked_revenue = float(metrics.tracked_revenue or 0)
    total_conversions = int(metrics.conversions or 0)
    days_count = int(metrics.days_count or 1)
    if days_count == 0:
        days_count = 1
        
    avg_daily_spend = total_spend / days_count
    avg_daily_conversions = total_conversions / days_count
    
    # 4. Fetch Attributed Revenue (from Orders)
    order_query = db.query(
        func.sum(Order.total).label("attributed_revenue")
    ).filter(
        Order.organization_id == organization_id, 
        Order.attribution_campaign_id == campaign_id, 
        Order.status != 'cancelled'
    )
    
    if start_date_str:
        # Assuming order_date is stored as string or can be compared
        order_query = order_query.filter(func.date(Order.order_date) >= start_date_str)
        
    order_metrics = order_query.first()
    attributed_revenue = float(order_metrics.attributed_revenue or 0)
    avg_daily_attributed_revenue = attributed_revenue / days_count
    
    # 5. Determine the best revenue to use (Attributed if available, otherwise Tracked)
    attribution_available = attributed_revenue > 0
    authoritative_revenue = attributed_revenue if attribution_available else tracked_revenue
    avg_daily_revenue = authoritative_revenue / days_count
    
    # 6. Fetch Product Cost
    product = None
    # 6. Fetch Product Cost (From Attributed Orders if possible)
    product_cost_total = None
    if attribution_available:
        item_query = db.query(
            func.sum(OrderItem.product_cost * OrderItem.quantity).label("product_cost")
        ).join(Order, OrderItem.order_id == Order.id).filter(
            Order.organization_id == organization_id,
            Order.attribution_campaign_id == campaign_id,
            Order.status != 'cancelled'
        )
        if start_date_str:
            item_query = item_query.filter(func.date(Order.order_date) >= start_date_str)
            
        item_metrics = item_query.first()
        product_cost_total = float(item_metrics.product_cost or 0)
        
    product = None
    if camp.target_product_sku:
        product = db.query(Product).filter(
            Product.sku == camp.target_product_sku,
            Product.organization_id == organization_id
        ).first()

    margin_pct = 0.4 # Default fallback
    if attribution_available and authoritative_revenue > 0:
        margin_pct = (authoritative_revenue - product_cost_total) / authoritative_revenue
    elif product and product.cost and product.price and product.price > 0:
        margin_pct = (float(product.price) - float(product.cost)) / float(product.price)
            
    # 7. Calculate Contribution Profit
    if attribution_available:
        daily_contribution_profit = (authoritative_revenue - product_cost_total - total_spend) / days_count
    else:
        daily_contribution_profit = (avg_daily_revenue * margin_pct) - avg_daily_spend
        
    contribution_margin = (daily_contribution_profit / avg_daily_revenue * 100) if avg_daily_revenue > 0 else 0.0
    roas = authoritative_revenue / total_spend if total_spend > 0 else 0.0
    cpa = total_spend / total_conversions if total_conversions > 0 else 0.0
    
    return {
        "campaign_id": campaign_id,
        "campaign_name": camp.name,
        "platform": camp.platform,
        "analysis_start": start_date_str,
        "analysis_end": latest_date_str,
        "analysis_days": days_count,
        "spend": avg_daily_spend,
        "revenue": avg_daily_revenue,
        "conversions": avg_daily_conversions,
        "product_cost": (product_cost_total / days_count) if product_cost_total is not None else None,
        "margin_pct": margin_pct,
        "contribution_profit": daily_contribution_profit,
        "contribution_margin": contribution_margin,
        "roas": roas,
        "cpa": cpa,
        "attribution_available": attribution_available,
        "inventory_count": product.inventory_count if product else None,
        "product_sku": product.sku if product else None,
        "daily_budget": camp.daily_budget
    }
