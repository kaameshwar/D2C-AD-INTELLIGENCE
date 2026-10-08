from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Campaign, Product, DailyCampaignMetric, Creative, Order, Customer, OrderItem
import pandas as pd

def get_all_campaigns(db: Session, organization_id: str):
    campaigns = db.query(Campaign).filter(Campaign.organization_id == organization_id).all()
    result = []
    for c in campaigns:
        metrics = db.query(DailyCampaignMetric).filter(DailyCampaignMetric.campaign_id == c.id).all()
        total_spend = sum(m.spend for m in metrics)
        total_revenue = sum(m.revenue for m in metrics)
        total_conversions = sum(m.conversions for m in metrics)
        
        result.append({
            "campaign_id": c.id,
            "campaign_name": c.name,
            "platform": c.platform,
            "spend": total_spend,
            "revenue": total_revenue,
            "conversions": total_conversions,
            "target_product_sku": c.target_product_sku,
            "status": c.status
        })
    return result

def get_campaign_by_id(db: Session, organization_id: str, campaign_id: str):
    c = db.query(Campaign).filter(
        Campaign.organization_id == organization_id,
        Campaign.id == campaign_id
    ).first()
    if not c: return None
    
    metrics = db.query(DailyCampaignMetric).filter(DailyCampaignMetric.campaign_id == c.id).all()
    total_spend = sum(m.spend for m in metrics)
    total_revenue = sum(m.revenue for m in metrics)
    total_conversions = sum(m.conversions for m in metrics)
    
    return {
        "campaign_id": c.id,
        "campaign_name": c.name,
        "platform": c.platform,
        "spend": total_spend,
        "revenue": total_revenue,
        "conversions": total_conversions,
        "target_product_sku": c.target_product_sku,
        "status": c.status,
        "daily_budget": c.daily_budget
    }

def get_all_products(db: Session, organization_id: str):
    products = db.query(Product).filter(Product.organization_id == organization_id).all()
    res = []
    for p in products:
        # Calculate product stats from order items
        items = db.query(OrderItem).filter(OrderItem.product_id == p.id).all()
        units_sold = sum(i.quantity for i in items)
        revenue = sum(i.total for i in items)
        cost = sum((i.product_cost or 0) * i.quantity for i in items)
        profit = revenue - cost if p.cost is not None else None
        
        res.append({
            "id": p.id,
            "sku": p.sku, 
            "name": p.name, 
            "price": p.price, 
            "cost": p.cost, 
            "currency": p.currency,
            "status": p.status,
            "inventory": p.inventory_count,
            "units_sold": units_sold,
            "revenue": revenue,
            "profit": profit
        })
    return res

def get_all_creatives(db: Session, organization_id: str):
    creatives = db.query(Creative).filter(Creative.organization_id == organization_id).all()
    return [{
        "id": c.id,
        "campaign_id": c.campaign_id,
        "name": c.name,
        "platform": c.platform,
        "status": c.status
    } for c in creatives]

def get_all_customers(db: Session, organization_id: str):
    customers = db.query(Customer).filter(Customer.organization_id == organization_id).all()
    return [{"id": c.id, "external_id": c.external_id, "name": c.name} for c in customers]

def get_all_orders(db: Session, organization_id: str):
    orders = db.query(Order).filter(Order.organization_id == organization_id).all()
    return [{
        "id": o.id,
        "external_id": o.external_id,
        "order_date": o.order_date,
        "status": o.status,
        "total": o.total
    } for o in orders]
