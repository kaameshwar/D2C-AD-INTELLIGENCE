import pytest
from sqlalchemy.orm import Session
from app.decision_engine.intelligence import get_comparison_metrics, detect_anomalies, simulate_scenario, get_inventory_risks
from app.models import Organization, Product, Inventory
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base

# Setup test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


def test_simulate_scenario():
    # Scenario: Spend = 1000, ROAS = 2.0, Margin = 50%, proposed increase = 20%
    # Expected:
    # new_spend = 1200
    # roas degrades slightly: degradation = (20 / 20) * 0.10 = 0.10
    # expected_roas = 2.0 * 0.90 = 1.80
    # expected_revenue = 1200 * 1.80 = 2160
    # expected_gross_profit = 2160 * 0.50 = 1080
    # expected_net_profit = 1080 - 1200 = -120 (Negative profit!)
    
    res = simulate_scenario(1000, 2.0, 50, 20)
    assert res["status"] == "SIMULATED"
    assert res["proposed_spend"] == 1200.0
    assert abs(res["expected_roas"] - 1.8) < 0.01
    assert abs(res["expected_revenue"] - 2160.0) < 0.01
    assert abs(res["expected_profit"] - (-120.0)) < 0.01

def test_inventory_risks(db_session: Session):
    org = Organization(id="ORG-INV-TEST", name="Inv Test")
    db_session.add(org)
    
    prod = Product(organization_id=org.id, sku="SKU-INV", name="Risk Product", price=100)
    db_session.add(prod)
    db_session.commit()
    
    inv = Inventory(organization_id=org.id, product_id=prod.id, quantity_available=5)
    db_session.add(inv)
    db_session.commit()
    
    risks = get_inventory_risks(db_session, org.id)
    assert len(risks) == 1
    assert risks[0]["type"] == "STOCKOUT_RISK"
    assert risks[0]["severity"] == "HIGH"
