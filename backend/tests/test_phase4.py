import pytest
from app.models import Organization, Product, Customer, Order, OrderItem
from app.services import import_service, analytics_service
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

def test_database_creation(db_session):
    p = Product(organization_id="ORG-1", sku="SKU-1", name="Product 1", price=100.0, cost=40.0)
    c = Customer(organization_id="ORG-1", external_id="CUST-1", name="John Doe")
    db_session.add(p)
    db_session.add(c)
    db_session.commit()
    
    o = Order(organization_id="ORG-1", customer_id=c.id, external_id="ORD-1", total=200.0)
    db_session.add(o)
    db_session.commit()
    
    i = OrderItem(organization_id="ORG-1", order_id=o.id, product_id=p.id, quantity=2, unit_price=100.0, product_cost=40.0, total=200.0)
    db_session.add(i)
    db_session.commit()
    
    assert db_session.query(Product).count() == 1
    assert db_session.query(Customer).count() == 1
    assert db_session.query(Order).count() == 1
    assert db_session.query(OrderItem).count() == 1

def test_tenant_isolation(db_session):
    p1 = Product(organization_id="ORG-1", sku="SKU-1", name="Product 1")
    p2 = Product(organization_id="ORG-2", sku="SKU-2", name="Product 2")
    db_session.add(p1)
    db_session.add(p2)
    db_session.commit()
    
    org1_prods = db_session.query(Product).filter(Product.organization_id == "ORG-1").all()
    assert len(org1_prods) == 1
    assert org1_prods[0].sku == "SKU-1"

def test_product_import_valid(db_session):
    csv_data = b"sku,name,price,cost,currency,status\nSKU-1,Prod1,100,40,USD,active\nSKU-2,Prod2,200,80,USD,active"
    res = import_service.import_products(db_session, "ORG-1", csv_data)
    assert res["success"]
    assert res["created"] == 2
    assert db_session.query(Product).count() == 2

def test_product_import_duplicate_updates(db_session):
    csv_data = b"sku,name,price,cost,currency,status\nSKU-1,Prod1,100,40,USD,active"
    import_service.import_products(db_session, "ORG-1", csv_data)
    
    # Update
    csv_data2 = b"sku,name,price,cost,currency,status\nSKU-1,Prod1_New,150,50,USD,active"
    res = import_service.import_products(db_session, "ORG-1", csv_data2)
    
    assert res["success"]
    assert res["updated"] == 1
    
    p = db_session.query(Product).first()
    assert p.name == "Prod1_New"
    assert p.price == 150

def test_order_import_valid(db_session):
    prod_csv = b"sku,name,price,cost,currency,status\nSKU-1,Prod1,100,40,USD,active"
    import_service.import_products(db_session, "ORG-1", prod_csv)
    
    order_csv = b"order_id,customer_id,order_date,status,currency,product_sku,quantity,unit_price,total\nO-1,C-1,2023-01-01,completed,USD,SKU-1,2,100,200"
    res = import_service.import_orders(db_session, "ORG-1", order_csv)
    
    assert res["success"]
    assert res["created_orders"] == 1
    assert res["created_items"] == 1
    
    o = db_session.query(Order).first()
    assert o.total == 200.0
    
def test_analytics_contribution_profit(db_session):
    # Create products and orders
    prod_csv = b"sku,name,price,cost,currency,status\nSKU-1,Prod1,100,40,USD,active"
    import_service.import_products(db_session, "ORG-1", prod_csv)
    
    order_csv = b"order_id,customer_id,order_date,status,currency,product_sku,quantity,unit_price,total\nO-1,C-1,2023-01-01,completed,USD,SKU-1,2,100,200"
    import_service.import_orders(db_session, "ORG-1", order_csv)
    
    # Check overview analytics
    stats = analytics_service.get_dashboard_overview(db_session, "ORG-1", days=30)
    summary = stats["summary"]
    
    # Total revenue = 200, Total product cost = 80 (since qty=2, cost=40), Spend = 0
    # Contribution profit = 200 - 80 - 0 = 120
    assert summary["order_revenue"] == 200.0
    assert summary["product_cost"] == 80.0
    assert summary["contribution_profit"] == 120.0
