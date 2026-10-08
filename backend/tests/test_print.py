import pytest
from app.services.import_service import import_orders
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base
from app.models import Organization

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_order(test_db=None):
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    org1 = Organization(id="org_test", name="Test Org")
    db.add(org1)
    db.commit()
    valid_csv = b"order_id,product_sku,customer_id,quantity,total\n1,SKU1,CUST1,1,10\n"
    res = import_orders(db, "org_test", valid_csv)
    print(res)
    db.close()
    
