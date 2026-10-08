import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Organization, Product, Customer, Order, OrderItem, Campaign, DailyCampaignMetric, User, DataSource, Inventory, InventoryMovement
from app.core import security
from datetime import datetime, timedelta
import random

def seed_demo_data():
    db = SessionLocal()
    try:
        # Create Demo Organization
        org = db.query(Organization).filter_by(name="DeciFlow Demo Org").first()
        if not org:
            org = Organization(name="DeciFlow Demo Org")
            db.add(org)
            db.commit()
            db.refresh(org)
            
        # Create Demo User
        user = db.query(User).filter_by(email="demo@deciflow.com").first()
        if not user:
            user = User(
                name="Demo User",
                email="demo@deciflow.com",
                hashed_password=security.get_password_hash("demo123"),
                organization_id=org.id,
                is_active=True
            )
            db.add(user)
            db.commit()
            
        # Data Sources
        meta_ds = db.query(DataSource).filter_by(name="Meta Ads", organization_id=org.id).first()
        if not meta_ds:
            meta_ds = DataSource(organization_id=org.id, name="Meta Ads", source_type="Meta", status="CONNECTED", last_sync_time=datetime.utcnow(), record_count=12482)
            db.add(meta_ds)
            
        google_ds = db.query(DataSource).filter_by(name="Google Ads", organization_id=org.id).first()
        if not google_ds:
            google_ds = DataSource(organization_id=org.id, name="Google Ads", source_type="Google", status="CONNECTED", last_sync_time=datetime.utcnow(), record_count=8452)
            db.add(google_ds)
            
        shopify_ds = db.query(DataSource).filter_by(name="Shopify", organization_id=org.id).first()
        if not shopify_ds:
            shopify_ds = DataSource(organization_id=org.id, name="Shopify", source_type="Shopify", status="CONNECTED", last_sync_time=datetime.utcnow(), record_count=5210)
            db.add(shopify_ds)
            
        db.commit()
        db.refresh(meta_ds)
        db.refresh(google_ds)
        db.refresh(shopify_ds)

        # Clean existing data for this org to ensure idempotency
        db.query(InventoryMovement).filter(InventoryMovement.inventory_id.in_(
            db.query(Inventory.id).filter(Inventory.organization_id == org.id)
        )).delete(synchronize_session=False)
        db.query(Inventory).filter(Inventory.organization_id == org.id).delete()
        db.query(OrderItem).filter(OrderItem.organization_id == org.id).delete()
        db.query(Order).filter(Order.organization_id == org.id).delete()
        db.query(Customer).filter(Customer.organization_id == org.id).delete()
        db.query(Product).filter(Product.organization_id == org.id).delete()
        db.query(DailyCampaignMetric).filter(DailyCampaignMetric.campaign.has(organization_id=org.id)).delete()
        db.query(Campaign).filter(Campaign.organization_id == org.id).delete()
        db.commit()

        # 1. Products
        p1 = Product(organization_id=org.id, data_source_id=shopify_ds.id, sku="SKU-HIGH", name="Premium SaaS Sub", price=500.0, cost=100.0)
        p2 = Product(organization_id=org.id, data_source_id=shopify_ds.id, sku="SKU-LOW", name="Physical Hardware Unit", price=1000.0, cost=800.0)
        p3 = Product(organization_id=org.id, data_source_id=shopify_ds.id, sku="SKU-MED1", name="Consulting Hour", price=200.0, cost=100.0)
        p4 = Product(organization_id=org.id, data_source_id=shopify_ds.id, sku="SKU-EBOOK", name="Digital E-Book", price=50.0, cost=5.0)
        p5 = Product(organization_id=org.id, data_source_id=shopify_ds.id, sku="SKU-LEAD", name="Welcome Kit", price=20.0, cost=20.0)
        
        products = [p1, p2, p3, p4, p5]
        for p in products:
            db.add(p)
        db.commit()
        
        # 1a. Inventory
        for p in products:
            inv = Inventory(organization_id=org.id, data_source_id=shopify_ds.id, product_id=p.id, quantity_on_hand=100, quantity_available=100)
            db.add(inv)
            db.flush()
            inv_mov = InventoryMovement(inventory_id=inv.id, movement_type="RECEIPT", quantity=100)
            db.add(inv_mov)
        db.commit()

        # 2. Customers
        customers = []
        for i in range(1, 12):
            c = Customer(organization_id=org.id, data_source_id=shopify_ds.id, external_id=f"CUST-{i}", email=f"customer{i}@example.com", name=f"Customer {i}")
            customers.append(c)
            db.add(c)
        db.commit()

        # 3. Campaigns
        c1 = Campaign(id=f"CAMP-PROF-{org.id}", data_source_id=google_ds.id, organization_id=org.id, name="Search - High Intent", platform="Google", daily_budget=200)
        c2 = Campaign(id=f"CAMP-TRAP-{org.id}", data_source_id=meta_ds.id, organization_id=org.id, name="Social - Broad Match", platform="Meta", daily_budget=300)
        c3 = Campaign(id=f"CAMP-LOW-{org.id}", data_source_id=google_ds.id, organization_id=org.id, name="Display - Cold Audience", platform="Google", daily_budget=100)
        c4 = Campaign(id=f"CAMP-IMP-{org.id}", data_source_id=meta_ds.id, organization_id=org.id, name="Retargeting - Cart", platform="Meta", daily_budget=50)
        c5 = Campaign(id=f"CAMP-DEC-{org.id}", data_source_id=meta_ds.id, organization_id=org.id, name="TikTok - Influencer", platform="TikTok", daily_budget=150)
        
        camps = [c1, c2, c3, c4, c5]
        for c in camps:
            db.add(c)
        db.commit()

        # 4. Daily Metrics (last 7 days)
        today = datetime.utcnow()
        for i in range(7):
            date_str = (today - timedelta(days=6-i)).strftime("%Y-%m-%d")
            
            # Helper to calculate metrics safely
            def create_metric(camp_id, spend, revenue, conversions, impressions, clicks):
                ctr = (clicks / impressions * 100) if impressions > 0 else 0
                cpc = spend / clicks if clicks > 0 else 0
                cpm = (spend / impressions * 1000) if impressions > 0 else 0
                cpa = spend / conversions if conversions > 0 else 0
                cvr = (conversions / clicks * 100) if clicks > 0 else 0
                roas = revenue / spend if spend > 0 else 0
                return DailyCampaignMetric(campaign_id=camp_id, date=date_str, spend=spend, revenue=revenue, conversions=conversions, impressions=impressions, clicks=clicks, ctr=ctr, cpc=cpc, cpm=cpm, cpa=cpa, cvr=cvr, roas=roas, creative_fatigue_score=random.uniform(0.1, 0.9))

            db.add(create_metric(c1.id, 100, 500, 1, 1000, 50))
            db.add(create_metric(c2.id, 200, 600, 1, 2000, 80))
            db.add(create_metric(c3.id, 100, 50, 1, 5000, 20))
            db.add(create_metric(c4.id, 50, 100 + (i * 20), 1, 800, 30))
            db.add(create_metric(c5.id, 150, 300 - (i * 30), 1, 3000, 100))
            
        db.commit()

        # 5. Orders & Order Items
        for i in range(7):
            o = Order(organization_id=org.id, data_source_id=shopify_ds.id, customer_id=customers[i].id, external_id=f"O-C1-{i}", order_date=today - timedelta(days=6-i), status="completed", total=500.0, attribution_campaign_id=c1.id)
            db.add(o)
            db.flush()
            db.add(OrderItem(organization_id=org.id, data_source_id=shopify_ds.id, order_id=o.id, product_id=p1.id, quantity=1, unit_price=500.0, product_cost=100.0, total=500.0))

        for i in range(7):
            o = Order(organization_id=org.id, data_source_id=shopify_ds.id, customer_id=customers[i%5].id, external_id=f"O-C2-{i}", order_date=today - timedelta(days=6-i), status="completed", total=600.0, attribution_campaign_id=c2.id)
            db.add(o)
            db.flush()
            db.add(OrderItem(organization_id=org.id, data_source_id=shopify_ds.id, order_id=o.id, product_id=p2.id, quantity=1, unit_price=600.0, product_cost=800.0, total=600.0))
            
        for i in range(5):
            o = Order(organization_id=org.id, data_source_id=shopify_ds.id, customer_id=customers[0].id, external_id=f"O-ORG-{i}", order_date=today - timedelta(days=i), status="completed", total=200.0, attribution_campaign_id=None)
            db.add(o)
            db.flush()
            db.add(OrderItem(organization_id=org.id, data_source_id=shopify_ds.id, order_id=o.id, product_id=p3.id, quantity=1, unit_price=200.0, product_cost=100.0, total=200.0))

        db.commit()
        print("Successfully seeded Step 2 Demo Data!")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
