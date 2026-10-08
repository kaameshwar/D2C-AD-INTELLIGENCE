import pytest
from app.models import Organization, Product, Customer, Order, OrderItem, Campaign, DailyCampaignMetric, Recommendation
from app.services import import_service, analytics_service
from app.decision_engine.engine import get_opportunities, get_recommendations
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
    org2 = Organization(id="ORG-2", name="Test Org 2")
    db.add(org1)
    db.add(org2)
    db.commit()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_tenant_isolation(db_session):
    # Org 1 data
    import_service.import_products(db_session, "ORG-1", b"sku,name,price,cost,currency\nSKU-1,Prod1,100,40,USD")
    # Org 2 data
    import_service.import_products(db_session, "ORG-2", b"sku,name,price,cost,currency\nSKU-2,Prod2,100,40,USD")
    
    # Query Org 1
    prods1 = analytics_service.get_product_profitability(db_session, "ORG-1")
    assert len(prods1) == 1
    assert prods1[0]["sku"] == "SKU-1"

    # Query Org 2
    prods2 = analytics_service.get_product_profitability(db_session, "ORG-2")
    assert len(prods2) == 1
    assert prods2[0]["sku"] == "SKU-2"

def test_financial_fixture(db_session):
    # Product A: price = 1500, cost = 700
    # Product B: price = 1000, cost = 900
    prod_csv = b"sku,name,price,cost,currency,status\nPROD-A,Product A,1500,700,USD,active\nPROD-B,Product B,1000,900,USD,active"
    import_service.import_products(db_session, "ORG-1", prod_csv)
    
    # Campaign A: spend = 20000, attributed revenue = 50000, product cost = 35000
    camp_a = Campaign(id="CAMP-A", organization_id="ORG-1", name="Campaign A", platform="Google", daily_budget=100.0)
    # Campaign B: spend = 20000, attributed revenue = 60000, product cost = 20000
    camp_b = Campaign(id="CAMP-B", organization_id="ORG-1", name="Campaign B", platform="Meta", daily_budget=100.0)
    
    db_session.add(camp_a)
    db_session.add(camp_b)
    
    # To get spend=20000, revenue=50000 over 4 days, let's just add 4 rows.
    for i in range(1, 5):
        db_session.add(DailyCampaignMetric(campaign_id="CAMP-A", date=f"2023-01-0{i}", spend=5000.0, revenue=12500.0, conversions=2))
        db_session.add(DailyCampaignMetric(campaign_id="CAMP-B", date=f"2023-01-0{i}", spend=5000.0, revenue=15000.0, conversions=2))
    
    # To get 35000 product cost from PROD-A (cost 700), we need 50 units.
    # 50 units * 1500 price = 75000 revenue. Wait, the prompt says attributed revenue = 50000.
    # So if 50 units are sold, price should be 1000 to get 50000 revenue. But Product A price is 1500.
    # Maybe we just use 10 orders of 5 units? Wait, 50 units * 1500 = 75000. 
    # Let's adjust order item unit_price to be 1000 (discounted) so revenue=50000, cost=35000.
    
    # To get 20000 product cost from PROD-A (cost 700) and PROD-B (cost 900), wait:
    # Campaign B: attributed rev = 60000, cost = 20000.
    # Let's just create OrderItems directly or via import. Import reads unit_price.
    
    order_csv = b"""order_id,customer_id,order_date,status,currency,product_sku,quantity,unit_price,attribution_campaign_id
O-A1,C-1,2023-01-01,completed,USD,PROD-A,50,1000,CAMP-A
O-B1,C-2,2023-01-01,completed,USD,PROD-B,22.222,900,CAMP-B
""" # Using direct DB adds instead to be precise.
    
    from datetime import datetime
    o1 = Order(organization_id="ORG-1", external_id="O-A1", status="completed", attribution_campaign_id="CAMP-A", total=50000.0, order_date=datetime(2023, 1, 1))
    o2 = Order(organization_id="ORG-1", external_id="O-B1", status="completed", attribution_campaign_id="CAMP-B", total=60000.0, order_date=datetime(2023, 1, 1))
    db_session.add(o1)
    db_session.add(o2)
    db_session.commit()
    
    pA = db_session.query(Product).filter_by(sku="PROD-A").first()
    pB = db_session.query(Product).filter_by(sku="PROD-B").first()
    
    # Camp A items
    db_session.add(OrderItem(organization_id="ORG-1", order_id=o1.id, product_id=pA.id, quantity=50, unit_price=1000, product_cost=700, total=50000))
    # Camp B items: cost needs to be 20000. Let's use PROD-B (cost 900) but unit_price=1000. Wait, 20000/900 = 22.22. Let's just set the product_cost directly on the item.
    db_session.add(OrderItem(organization_id="ORG-1", order_id=o2.id, product_id=pB.id, quantity=1, unit_price=60000, product_cost=20000, total=60000))
    db_session.commit()
    
    res = analytics_service.get_campaign_profitability(db_session, "ORG-1")
    camp_a_prof = next(c for c in res if c["campaign_id"] == "CAMP-A")
    camp_b_prof = next(c for c in res if c["campaign_id"] == "CAMP-B")
    
    assert camp_a_prof["roas"] == 2.5
    assert camp_a_prof["contribution_profit"] == -5000.0
    assert camp_a_prof["contribution_margin"] == -10.0
    
    assert camp_b_prof["roas"] == 3.0
    assert camp_b_prof["contribution_profit"] == 20000.0
    assert round(camp_b_prof["contribution_margin"], 2) == 33.33
    
    # Run decision engine
    opps = get_opportunities(db_session, "ORG-1")
    
    # Check decisions
    camp_a_opp = next((o for o in opps if o["campaign_id"] == "CAMP-A"), None)
    camp_b_opp = next((o for o in opps if o["campaign_id"] == "CAMP-B"), None)
    
    assert camp_a_opp is not None, "Missing PROFITABILITY_REVIEW"
    assert "PROFITABILITY_REVIEW" in str(camp_a_opp) or "Misleading ROAS" in camp_a_opp["title"]
    
    assert camp_b_opp is not None, "Missing SCALE_PROFITABLE"
    assert "SCALE" in camp_b_opp["recommended_action"] or "Scale Highly Profitable" in camp_b_opp["title"]

def test_double_counting_joins(db_session):
    # Ensure one order with 3 items doesn't triple the attributed revenue
    camp_c = Campaign(id="CAMP-C", organization_id="ORG-1", name="Campaign C", platform="Google")
    db_session.add(camp_c)
    
    db_session.add(DailyCampaignMetric(campaign_id="CAMP-C", date="2023-01-01", spend=100.0, revenue=300.0))
    db_session.commit()
    
    # Order with 3 items
    o = Order(organization_id="ORG-1", external_id="O-MULTI", status="completed", attribution_campaign_id="CAMP-C", total=300.0)
    db_session.add(o)
    db_session.commit()
    
    p = Product(organization_id="ORG-1", sku="SKU-MULTI", price=100, cost=50)
    db_session.add(p)
    db_session.commit()
    
    db_session.add(OrderItem(organization_id="ORG-1", order_id=o.id, product_id=p.id, quantity=1, unit_price=100, product_cost=50, total=100))
    db_session.add(OrderItem(organization_id="ORG-1", order_id=o.id, product_id=p.id, quantity=1, unit_price=100, product_cost=50, total=100))
    db_session.add(OrderItem(organization_id="ORG-1", order_id=o.id, product_id=p.id, quantity=1, unit_price=100, product_cost=50, total=100))
    db_session.commit()
    
    res = analytics_service.get_campaign_profitability(db_session, "ORG-1")
    camp_c_prof = next(c for c in res if c["campaign_id"] == "CAMP-C")
    
    assert camp_c_prof["attributed_revenue"] == 300.0 # NOT 900
    assert camp_c_prof["product_cost"] == 150.0

def test_cancelled_refunded_orders(db_session):
    # Ensure cancelled orders don't count towards attributed revenue
    camp_d = Campaign(id="CAMP-D", organization_id="ORG-1", name="Campaign D", platform="Google")
    db_session.add(camp_d)
    
    db_session.add(DailyCampaignMetric(campaign_id="CAMP-D", date="2023-01-01", spend=100.0, revenue=300.0))
    db_session.commit()
    
    o = Order(organization_id="ORG-1", external_id="O-CANCELLED", status="cancelled", attribution_campaign_id="CAMP-D", total=300.0)
    db_session.add(o)
    db_session.commit()
    
    db_session.add(OrderItem(organization_id="ORG-1", order_id=o.id, quantity=1, unit_price=300, product_cost=50, total=300))
    db_session.commit()
    
    res = analytics_service.get_campaign_profitability(db_session, "ORG-1")
    camp_d_prof = next(c for c in res if c["campaign_id"] == "CAMP-D")
    
    assert camp_d_prof["attributed_revenue"] == 0.0 or camp_d_prof["attribution_available"] is False

def test_missing_data(db_session):
    camp = Campaign(id="CAMP-NO-DATA", organization_id="ORG-1", name="No Data")
    db_session.add(camp)
    db_session.commit()
    
    res = analytics_service.get_campaign_profitability(db_session, "ORG-1")
    prof = next(c for c in res if c["campaign_id"] == "CAMP-NO-DATA")
    
    assert prof["attribution_available"] is False
    assert prof["contribution_profit"] is None
    assert prof["contribution_margin"] is None

