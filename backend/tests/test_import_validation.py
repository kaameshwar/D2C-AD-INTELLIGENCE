import pytest
from app.services.import_service import import_campaigns, import_products, import_orders
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base
from app.models import Organization

# Setup test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    org1 = Organization(id="org_test", name="Test Org")
    db.add(org1)
    db.commit()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_campaign_import_validation(test_db):
    valid_csv = b"campaign_id,spend,revenue,clicks,conversions\n1,100,200,10,2\n"
    res = import_campaigns(test_db, "org_test", valid_csv)
    assert res["success"] == True

    invalid_csv = b"sku,name,price,cost\nSKU1,Test,10,5\n"
    res = import_campaigns(test_db, "org_test", invalid_csv)
    assert res["success"] == False
    assert "Missing required columns" in res["error"]
    assert "campaign_id" in res["error"]

def test_product_import_validation(test_db):
    valid_csv = b"sku,name,price,cost\nSKU1,Test,10,5\n"
    res = import_products(test_db, "org_test", valid_csv)
    assert res["success"] == True

    invalid_csv = b"campaign_id,spend,revenue,clicks,conversions\n1,100,200,10,2\n"
    res = import_products(test_db, "org_test", invalid_csv)
    assert res["success"] == False
    assert "Missing required columns" in res["error"]
    assert "sku" in res["error"]

def test_order_import_validation(test_db):
    valid_csv = b"order_id,product_sku,customer_id,quantity,total\n1,SKU1,CUST1,1,10\n"
    res = import_orders(test_db, "org_test", valid_csv)
    assert res["success"] == True

    invalid_csv = b"campaign_id,spend,revenue,clicks,conversions\n1,100,200,10,2\n"
    res = import_orders(test_db, "org_test", invalid_csv)
    assert res["success"] == False
    assert "Missing required columns" in res["error"]
    assert "order_id" in res["error"]

def test_case_insensitivity(test_db):
    # Test that headers are processed correctly even with mixed cases and spaces
    valid_csv = b" Campaign_ID , SPEND, Revenue , cLicKs,  CoNvErSiOnS \n1,100,200,10,2\n"
    res = import_campaigns(test_db, "org_test", valid_csv)
    assert res["success"] == True
