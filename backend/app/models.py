from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="organization")
    data_sources = relationship("DataSource", back_populates="organization")
    campaigns = relationship("Campaign", back_populates="organization")
    products = relationship("Product", back_populates="organization")
    customers = relationship("Customer", back_populates="organization")
    orders = relationship("Order", back_populates="organization")
    creatives = relationship("Creative", back_populates="organization")
    integrations = relationship("Integration", back_populates="organization")
    recommendations = relationship("Recommendation", back_populates="organization")
    actions = relationship("Action", back_populates="organization")



class DataSource(Base):
    __tablename__ = "data_sources"
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"))
    data_source_id = Column(String, ForeignKey("data_sources.id"), nullable=True)
    name = Column(String)
    source_type = Column(String) # CSV, Meta, Google, Shopify, Demo
    status = Column(String, default="CONNECTED") # CONNECTED, SYNCING, SUCCESS, FAILED
    last_sync_time = Column(DateTime, nullable=True)
    record_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="data_sources")

class ImportJob(Base):
    __tablename__ = "import_jobs"
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"))
    data_source_id = Column(String, ForeignKey("data_sources.id"), nullable=True)
    status = Column(String, default="PROCESSING") # PROCESSING, SUCCESS, FAILED
    file_name = Column(String, nullable=True)
    row_count = Column(Integer, default=0)
    errors = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"))
    data_source_id = Column(String, ForeignKey("data_sources.id"), nullable=True)
    product_id = Column(String, ForeignKey("products.id"))
    quantity_on_hand = Column(Integer, default=0)
    quantity_allocated = Column(Integer, default=0)
    quantity_available = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    id = Column(String, primary_key=True, default=generate_uuid)
    inventory_id = Column(String, ForeignKey("inventory.id"))
    movement_type = Column(String) # RECEIPT, SALE, ADJUSTMENT, RETURN
    quantity = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"))
    data_source_id = Column(String, ForeignKey("data_sources.id"), nullable=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    
    organization = relationship("Organization", back_populates="users")

class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"))
    data_source_id = Column(String, ForeignKey("data_sources.id"), nullable=True)
    sku = Column(String, index=True)
    name = Column(String)
    description = Column(Text, nullable=True)
    price = Column(Float)
    cost = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    status = Column(String, default="active")
    inventory_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")

class Customer(Base):
    __tablename__ = "customers"
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"))
    data_source_id = Column(String, ForeignKey("data_sources.id"), nullable=True)
    external_id = Column(String, index=True, nullable=True)
    email = Column(String, index=True, nullable=True)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="customers")
    orders = relationship("Order", back_populates="customer")

class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"))
    data_source_id = Column(String, ForeignKey("data_sources.id"), nullable=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True)
    external_id = Column(String, index=True, nullable=True)
    order_date = Column(DateTime)
    status = Column(String, default="completed")
    currency = Column(String, default="USD")
    subtotal = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    shipping = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    refund_amount = Column(Float, default=0.0)
    attribution_campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    attributed_campaign = relationship("Campaign", foreign_keys=[attribution_campaign_id])

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"))
    data_source_id = Column(String, ForeignKey("data_sources.id"), nullable=True)
    order_id = Column(String, ForeignKey("orders.id"))
    product_id = Column(String, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    product_cost = Column(Float, nullable=True)
    total = Column(Float, default=0.0)
    
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(String, primary_key=True) # e.g. CAMP-001
    organization_id = Column(String, ForeignKey("organizations.id"))
    data_source_id = Column(String, ForeignKey("data_sources.id"), nullable=True)
    name = Column(String)
    platform = Column(String)
    target_product_sku = Column(String)
    daily_budget = Column(Float)
    status = Column(String, default="Active")
    
    organization = relationship("Organization", back_populates="campaigns")
    metrics = relationship("DailyCampaignMetric", back_populates="campaign")

class DailyCampaignMetric(Base):
    __tablename__ = "daily_campaign_metrics"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    campaign_id = Column(String, ForeignKey("campaigns.id"))
    date = Column(String) # YYYY-MM-DD
    spend = Column(Float)
    revenue = Column(Float)
    impressions = Column(Integer)
    clicks = Column(Integer)
    conversions = Column(Integer)
    ctr = Column(Float, nullable=True)
    cpc = Column(Float, nullable=True)
    cpm = Column(Float, nullable=True)
    cpa = Column(Float, nullable=True)
    cvr = Column(Float, nullable=True)
    roas = Column(Float, nullable=True)

    creative_fatigue_score = Column(Float)
    
    campaign = relationship("Campaign", back_populates="metrics")

class Creative(Base):
    __tablename__ = "creatives"
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"))
    data_source_id = Column(String, ForeignKey("data_sources.id"), nullable=True)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=True)
    name = Column(String)
    external_id = Column(String, index=True, nullable=True)
    platform = Column(String)
    status = Column(String, default="Active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="creatives")

class Integration(Base):
    __tablename__ = "integrations"
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"))
    data_source_id = Column(String, ForeignKey("data_sources.id"), nullable=True)
    provider = Column(String)
    status = Column(String, default="active")
    external_account_id = Column(String, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="integrations")

class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"))
    data_source_id = Column(String, ForeignKey("data_sources.id"), nullable=True)
    campaign_id = Column(String, ForeignKey("campaigns.id"))
    title = Column(String)
    action_type = Column(String)
    budget_change = Column(Float)
    projected_profit = Column(Float)
    score = Column(Integer)
    confidence = Column(String)
    reason = Column(Text)
    evidence_json = Column(Text) # JSON string array
    status = Column(String, default="NEW") # NEW, REVIEWED, APPROVED, REJECTED, EXECUTING, EXECUTED, MONITORING, AWAITING_OUTCOME, EVALUATED, FAILED
    
    # Expected vs Actual tracking
    actual_profit = Column(Float, nullable=True)
    variance = Column(Float, nullable=True)
    outcome_status = Column(String, nullable=True) # OUTPERFORMED_EXPECTATION, MET_EXPECTATION, UNDERPERFORMED_EXPECTATION, INSUFFICIENT_DATA
    evaluated_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="recommendations")

class Action(Base):
    __tablename__ = "actions"
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"))
    data_source_id = Column(String, ForeignKey("data_sources.id"), nullable=True)
    recommendation_id = Column(String, ForeignKey("recommendations.id"))
    user_id = Column(String, ForeignKey("users.id"))
    execution_mode = Column(String) # Simulated, Demo, Real
    execution_result = Column(String)
    execution_details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="actions")

class DecisionMemory(Base):
    __tablename__ = "decision_memory"
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"))
    recommendation_id = Column(String, ForeignKey("recommendations.id"))
    action_id = Column(String, ForeignKey("actions.id"))
    
    expected_impact_json = Column(Text, nullable=True)
    actual_impact_json = Column(Text, nullable=True)
    variance_json = Column(Text, nullable=True)
    
    expected_profit = Column(Float)
    actual_profit = Column(Float)
    variance = Column(Float)
    
    outcome_classification = Column(String) # OUTPERFORMED_EXPECTATION, MET_EXPECTATION, UNDERPERFORMED_EXPECTATION, INSUFFICIENT_DATA
    confidence = Column(String)
    learning_signal = Column(Text, nullable=True)
    
    evaluated_at = Column(DateTime, default=datetime.utcnow)

class LearningCalibration(Base):
    __tablename__ = "learning_calibrations"
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"))
    action_type = Column(String) # e.g. SCALE, REDUCE
    platform = Column(String, nullable=True)
    
    calibration_factor = Column(Float, default=1.0)
    bias = Column(Float, default=0.0)
    historical_prediction_error = Column(Float, default=0.0)
    number_of_observations = Column(Integer, default=0)
    confidence = Column(String, default="LOW")
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
