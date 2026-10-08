import pytest
from app.models import Organization, Product, Customer, Order, OrderItem, Campaign, DailyCampaignMetric
from app.services import import_service, analytics_service
from app.decision_engine.engine import get_opportunities
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base
import pandas as pd
import io

# Setup test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    org1 = Organization(id="ORG-1", name="Test Org 1")
    db.add(org1)
    db.commit()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_campaign_profitability(db_session):
    # Create products and orders
    prod_csv = b"sku,name,price,cost,currency,status\nSKU-1,Prod1,100,40,USD,active"
    import_service.import_products(db_session, "ORG-1", prod_csv)
    
    # Create a campaign
    camp = Campaign(id="CAMP-1", organization_id="ORG-1", name="Campaign 1", platform="Google")
    db_session.add(camp)
    
    # Add daily metrics
    metric = DailyCampaignMetric(campaign_id="CAMP-1", date="2023-01-01", spend=200.0, revenue=500.0)
    db_session.add(metric)
    db_session.commit()
    
    # Add attributed order
    order_csv = b"order_id,customer_id,order_date,status,currency,product_sku,quantity,unit_price,total,attribution_campaign_id\nO-1,C-1,2023-01-01,completed,USD,SKU-1,5,100,500,CAMP-1"
    import_service.import_orders(db_session, "ORG-1", order_csv)
    
    res = analytics_service.get_campaign_profitability(db_session, "ORG-1")
    
    assert len(res) == 1
    c = res[0]
    assert c["campaign_id"] == "CAMP-1"
    assert c["spend"] == 200.0
    assert c["tracked_revenue"] == 500.0
    assert c["attributed_revenue"] == 500.0  # 5 units * 100 price = 500
    assert c["product_cost"] == 200.0  # 5 units * 40 cost = 200
    assert c["contribution_profit"] == 100.0  # 500 rev - 200 cost - 200 spend = 100
    assert c["contribution_margin"] == 20.0  # 100 / 500 = 20%
    assert c["attribution_available"] is True

def test_scale_profitable_rule(db_session):
    prod_csv = b"sku,name,price,cost,currency,status\nSKU-2,Prod2,1000,200,USD,active"
    import_service.import_products(db_session, "ORG-1", prod_csv)
    
    camp = Campaign(id="CAMP-2", organization_id="ORG-1", name="Campaign 2", platform="Meta", daily_budget=100.0)
    db_session.add(camp)
    
    # Add daily metrics over a few days so confidence is high
    for i in range(1, 5):
        metric = DailyCampaignMetric(campaign_id="CAMP-2", date=f"2023-01-0{i}", spend=250.0, revenue=2000.0, conversions=5)
        db_session.add(metric)
    db_session.commit()
    
    # Add attributed order
    # Total spend = 1000.0. Tracked revenue = 8000.0.
    # Attributed orders: let's create enough to give good margin.
    # We create 1 order for 8 units = 8000. Cost = 8 * 200 = 1600.
    # Profit = 8000 - 1600 - 1000 = 5400. Margin = 5400 / 8000 = 67.5%
    order_csv = b"order_id,customer_id,order_date,status,currency,product_sku,quantity,unit_price,total,attribution_campaign_id\nO-2,C-2,2023-01-01,completed,USD,SKU-2,8,1000,8000,CAMP-2"
    import_service.import_orders(db_session, "ORG-1", order_csv)
    
    opps = get_opportunities(db_session, "ORG-1")
    # Rule should be SCALE_PROFITABLE
    assert len(opps) > 0
    
    # Find our specific recommendation
    rec = opps[0]
    assert "Scale Highly Profitable" in rec["title"]
    assert rec["campaign_id"] == "CAMP-2"
