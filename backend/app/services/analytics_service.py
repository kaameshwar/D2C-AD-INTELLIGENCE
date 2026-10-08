from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Campaign, DailyCampaignMetric, Order, OrderItem, Customer
from datetime import datetime, timedelta

def get_dashboard_overview(db: Session, organization_id: str, days: int = 7):
    campaigns = db.query(Campaign.id).filter(Campaign.organization_id == organization_id).subquery()
    
    # Find the latest date for this organization's data to anchor "last X days"
    latest_date_str = db.query(func.max(DailyCampaignMetric.date)).filter(DailyCampaignMetric.campaign_id.in_(campaigns)).scalar()
    
    metrics_query = db.query(
        func.sum(DailyCampaignMetric.spend).label("total_spend"),
        func.sum(DailyCampaignMetric.revenue).label("total_revenue"),
        func.sum(DailyCampaignMetric.conversions).label("total_conversions"),
        func.sum(DailyCampaignMetric.impressions).label("total_impressions"),
        func.sum(DailyCampaignMetric.clicks).label("total_clicks")
    ).filter(DailyCampaignMetric.campaign_id.in_(campaigns))
    
    ts_query = db.query(
        DailyCampaignMetric.date,
        func.sum(DailyCampaignMetric.spend).label("spend"),
        func.sum(DailyCampaignMetric.revenue).label("revenue"),
        func.sum(DailyCampaignMetric.conversions).label("conversions")
    ).filter(DailyCampaignMetric.campaign_id.in_(campaigns))

    if latest_date_str:
        try:
            latest_date = datetime.strptime(latest_date_str, "%Y-%m-%d")
            start_date = (latest_date - timedelta(days=days - 1)).strftime("%Y-%m-%d")
            metrics_query = metrics_query.filter(DailyCampaignMetric.date >= start_date)
            ts_query = ts_query.filter(DailyCampaignMetric.date >= start_date)
        except ValueError:
            pass # fallback to all time if parsing fails
            
    metrics = metrics_query.first()
    
    total_spend = float(metrics.total_spend or 0)
    total_revenue = float(metrics.total_revenue or 0)
    total_conversions = int(metrics.total_conversions or 0)
    total_impressions = int(metrics.total_impressions or 0)
    total_clicks = int(metrics.total_clicks or 0)
    total_profit = total_revenue - total_spend
    
    roas = total_revenue / total_spend if total_spend > 0 else 0.0
    tracked_profit_roas = total_profit / total_spend if total_spend > 0 else 0.0
    ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0.0
    cpc = (total_spend / total_clicks) if total_clicks > 0 else 0.0
    cpa = (total_spend / total_conversions) if total_conversions > 0 else 0.0
    cvr = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0.0
    
    # Calculate Order-based metrics for Contribution Profit
    order_query = db.query(
        func.sum(Order.total).label("order_revenue")
    ).filter(Order.organization_id == organization_id, Order.status != 'cancelled')
    
    item_query = db.query(
        func.sum(OrderItem.product_cost * OrderItem.quantity).label("total_product_cost"),
        func.sum(OrderItem.quantity).label("total_items_sold")
    ).join(Order, OrderItem.order_id == Order.id).filter(
        OrderItem.organization_id == organization_id,
        Order.status != 'cancelled'
    )
    
    if latest_date_str:
        try:
            start_datetime = datetime.strptime(latest_date_str, "%Y-%m-%d") - timedelta(days=days - 1)
            order_query = order_query.filter(Order.order_date >= start_datetime)
            item_query = item_query.filter(Order.order_date >= start_datetime)
        except ValueError:
            pass

    order_stats = order_query.first()
    item_stats = item_query.first()
    
    order_revenue = float(order_stats.order_revenue or 0)
    total_product_cost = float(item_stats.total_product_cost or 0)
    
    data_completeness = {
        "orders_exist": order_revenue > 0,
        "product_cost_available": total_product_cost > 0
    }
    
    if data_completeness["orders_exist"] and data_completeness["product_cost_available"]:
        contribution_profit = order_revenue - total_product_cost - total_spend
        profit_roas = contribution_profit / total_spend if total_spend > 0 else 0.0
    else:
        contribution_profit = None
        profit_roas = None
        
    # Additional customer stats
    total_customers = db.query(func.count(Customer.id)).filter(Customer.organization_id == organization_id).scalar()
    total_orders = db.query(func.count(Order.id)).filter(Order.organization_id == organization_id).scalar()
    
    ts_results = ts_query.group_by(DailyCampaignMetric.date).order_by(DailyCampaignMetric.date).all()
    timeseries = []
    for r in ts_results:
        s = float(r.spend or 0)
        rev = float(r.revenue or 0)
        timeseries.append({
            "name": r.date,
            "date": r.date,
            "spend": s,
            "revenue": rev,
            "profit": rev - s,
            "conversions": int(r.conversions or 0)
        })
    
    contribution_margin = None
    if contribution_profit is not None and order_revenue > 0:
        contribution_margin = (contribution_profit / order_revenue) * 100.0

    return {
        "summary": {
            "spend": total_spend,
            "revenue": total_revenue, # Note: this is tracked_revenue from marketing metrics
            "profit": total_profit,
            "roas": roas,
            "tracked_profit_roas": tracked_profit_roas,
            "profit_roas": profit_roas,
            "ctr": ctr,
            "cpc": cpc,
            "cpa": cpa,
            "cvr": cvr,
            "conversions": total_conversions,
            "contribution_profit": contribution_profit,
            "contribution_margin": contribution_margin,
            "order_revenue": order_revenue,
            "product_cost": total_product_cost,
            "total_customers": total_customers,
            "total_orders": total_orders,
            "data_completeness": data_completeness
        },
        "timeseries": timeseries
    }

def get_channel_performance(db: Session, organization_id: str, days: int = 7):
    campaigns = db.query(Campaign.id).filter(Campaign.organization_id == organization_id).subquery()
    latest_date_str = db.query(func.max(DailyCampaignMetric.date)).filter(DailyCampaignMetric.campaign_id.in_(campaigns)).scalar()
    
    query = db.query(
        Campaign.platform,
        func.sum(DailyCampaignMetric.spend).label("spend"),
        func.sum(DailyCampaignMetric.revenue).label("revenue"),
        func.sum(DailyCampaignMetric.conversions).label("conversions")
    ).join(DailyCampaignMetric, Campaign.id == DailyCampaignMetric.campaign_id)\
     .filter(Campaign.organization_id == organization_id)
     
    if latest_date_str:
        try:
            latest_date = datetime.strptime(latest_date_str, "%Y-%m-%d")
            start_date = (latest_date - timedelta(days=days - 1)).strftime("%Y-%m-%d")
            query = query.filter(DailyCampaignMetric.date >= start_date)
        except ValueError:
            pass

    results = query.group_by(Campaign.platform).all()
     
    data = []
    for r in results:
        spend = float(r.spend or 0)
        revenue = float(r.revenue or 0)
        profit = revenue - spend
        data.append({
            "platform": r.platform,
            "spend": spend,
            "revenue": revenue,
            "conversions": int(r.conversions or 0),
            "roas": revenue / spend if spend > 0 else 0,
            "profit": profit
        })
    return data

def get_campaign_profitability(db: Session, organization_id: str, campaign_id: str = None):
    # Returns profitability metrics for campaigns, including attribution.
    query = db.query(Campaign).filter(Campaign.organization_id == organization_id)
    if campaign_id:
        query = query.filter(Campaign.id == campaign_id)
        
    campaigns = query.all()
    results = []
    
    for camp in campaigns:
        # Get marketing spend and tracked revenue
        metrics = db.query(
            func.sum(DailyCampaignMetric.spend).label("spend"),
            func.sum(DailyCampaignMetric.revenue).label("tracked_revenue")
        ).filter(DailyCampaignMetric.campaign_id == camp.id).first()
        
        spend = float(metrics.spend or 0)
        tracked_revenue = float(metrics.tracked_revenue or 0)
        
        # Get attributed revenue from orders
        # Only count orders explicitly attributed to this campaign
        order_metrics = db.query(
            func.sum(Order.total).label("attributed_revenue"),
            func.count(Order.id).label("attributed_orders")
        ).filter(Order.organization_id == organization_id, Order.attribution_campaign_id == camp.id, Order.status != 'cancelled').first()
        
        attributed_revenue = float(order_metrics.attributed_revenue or 0)
        attributed_orders = int(order_metrics.attributed_orders or 0)
        
        # Product Cost for attributed orders
        item_metrics = db.query(
            func.sum(OrderItem.product_cost * OrderItem.quantity).label("product_cost")
        ).join(Order, OrderItem.order_id == Order.id).filter(
            Order.organization_id == organization_id,
            Order.attribution_campaign_id == camp.id,
            Order.status != 'cancelled'
        ).first()
        
        product_cost = float(item_metrics.product_cost or 0)
        
        attribution_available = attributed_orders > 0
        
        if attribution_available:
            contribution_profit = attributed_revenue - product_cost - spend
            contribution_margin = (contribution_profit / attributed_revenue * 100.0) if attributed_revenue > 0 else 0.0
        else:
            contribution_profit = None
            contribution_margin = None
            attributed_revenue = None
            product_cost = None
            
        results.append({
            "campaign_id": camp.id,
            "campaign_name": camp.name,
            "platform": camp.platform,
            "spend": spend,
            "tracked_revenue": tracked_revenue,
            "attributed_revenue": attributed_revenue,
            "product_cost": product_cost,
            "contribution_profit": contribution_profit,
            "contribution_margin": contribution_margin,
            "roas": tracked_revenue / spend if spend > 0 else 0.0,
            "attribution_available": attribution_available
        })
        
    return results

def get_product_profitability(db: Session, organization_id: str):
    # Reusable product-level analytics
    from app.models import Product
    products = db.query(Product).filter(Product.organization_id == organization_id).all()
    results = []
    
    for p in products:
        stats = db.query(
            func.sum(OrderItem.quantity).label("units_sold"),
            func.sum(OrderItem.total).label("revenue"),
            func.count(func.distinct(OrderItem.order_id)).label("order_count")
        ).join(Order, OrderItem.order_id == Order.id).filter(
            OrderItem.product_id == p.id,
            Order.status != 'cancelled'
        ).first()
        
        units_sold = int(stats.units_sold or 0)
        revenue = float(stats.revenue or 0)
        order_count = int(stats.order_count or 0)
        
        product_cost = float(p.cost or 0) * units_sold
        gross_profit = revenue - product_cost
        gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0
        
        results.append({
            "product_id": p.id,
            "sku": p.sku,
            "name": p.name,
            "price": p.price,
            "cost": p.cost,
            "units_sold": units_sold,
            "order_count": order_count,
            "revenue": revenue,
            "product_cost_total": product_cost,
            "gross_profit": gross_profit,
            "gross_margin": gross_margin
        })
    return results

def get_customer_analytics(db: Session, organization_id: str):
    customers = db.query(Customer).filter(Customer.organization_id == organization_id).all()
    
    total_customers = len(customers)
    new_customers = 0
    repeat_customers = 0
    
    results = []
    
    for c in customers:
        stats = db.query(
            func.count(Order.id).label("order_count"),
            func.sum(Order.total).label("total_revenue")
        ).filter(Order.customer_id == c.id, Order.status != 'cancelled').first()
        
        order_count = int(stats.order_count or 0)
        total_revenue = float(stats.total_revenue or 0)
        
        if order_count == 1:
            new_customers += 1
            segment = "NEW"
        elif order_count > 1:
            repeat_customers += 1
            segment = "RETURNING"
        else:
            segment = "LEAD"
            
        aov = total_revenue / order_count if order_count > 0 else 0
            
        results.append({
            "customer_id": c.id,
            "external_id": c.external_id,
            "name": c.name,
            "email": c.email,
            "order_count": order_count,
            "total_revenue": total_revenue,
            "average_order_value": aov,
            "segment": segment
        })
        
    return {
        "summary": {
            "total_customers": total_customers,
            "new_customers": new_customers,
            "repeat_customers": repeat_customers
        },
        "customers": results
    }

def get_customer_journey(db: Session, organization_id: str):
    from app.models import Order, Customer, OrderItem, Product
    orders = db.query(Order).join(Customer).filter(Order.organization_id == organization_id).order_by(Order.order_date.desc()).limit(100).all()
    journey = []
    for o in orders:
        items = db.query(OrderItem).filter(OrderItem.order_id == o.id).all()
        product_names = []
        for i in items:
            p = db.query(Product).filter(Product.id == i.product_id).first()
            if p:
                product_names.append(p.name)
        journey.append({
            "customer_id": o.customer.external_id or o.customer.id,
            "customer_email": o.customer.email,
            "order_date": o.order_date.isoformat() if o.order_date else None,
            "order_id": o.external_id or o.id,
            "order_value": o.total,
            "order_status": o.status,
            "products": product_names
        })
    return journey
