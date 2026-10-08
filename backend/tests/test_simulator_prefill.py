from fastapi.testclient import TestClient
from app.main import app
from app.db import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db import Base
from app.models import Organization, User, Recommendation, Campaign
from app.core.security import create_access_token
import pytest

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    org1 = Organization(id="org_1", name="Org 1")
    org2 = Organization(id="org_2", name="Org 2")
    user1 = User(id="user_1", email="test@test.com", hashed_password="pw", organization_id="org_1", is_active=True)
    
    camp1 = Campaign(id="camp_1", organization_id="org_1", name="Test Camp", daily_budget=100.0, target_product_sku="1")
    rec1 = Recommendation(
        id="rec_1", organization_id="org_1", campaign_id="camp_1",
        title="Increase", action_type="SCALE_PROFITABLE",
        budget_change=40.0,
        projected_profit=50.0
    )
    rec2 = Recommendation(
        id="rec_2", organization_id="org_2", campaign_id="camp_2",
        title="Decrease", action_type="MISLEADING_ROAS",
        budget_change=-150.0,
        projected_profit=10.0
    )
    
    db.add_all([org1, org2, user1, camp1, rec1, rec2])
    db.commit()
    db.close()
    
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

def test_get_recommendation_success():
    token = create_access_token(data={"sub": "user_1", "org_id": "org_1"})
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.get("/api/recommendations/rec_1", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "rec_1"
    assert data["campaign_name"] == "Test Camp"
    assert data["current_budget"] == 100.0
    assert data["recommended_action"] == "Increase spend by ₹40.0"
    assert data["budget_change"] == 40.0

def test_get_recommendation_cross_tenant():
    token = create_access_token(data={"sub": "user_1", "org_id": "org_1"})
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.get("/api/recommendations/rec_2", headers=headers)
    assert res.status_code == 404

def test_get_recommendation_not_found():
    token = create_access_token(data={"sub": "user_1", "org_id": "org_1"})
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.get("/api/recommendations/rec_99", headers=headers)
    assert res.status_code == 404
