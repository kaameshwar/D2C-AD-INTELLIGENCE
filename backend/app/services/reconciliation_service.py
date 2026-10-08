from sqlalchemy.orm import Session
from app.models import Product, Customer, Campaign, Organization

def reconcile_products(db: Session, org_id: str, sku: str):
    """
    Find an existing product in the organization across any data source by SKU.
    """
    return db.query(Product).filter(Product.sku == sku, Product.organization_id == org_id).first()

def reconcile_customers(db: Session, org_id: str, external_id: str = None, email: str = None):
    """
    Find an existing customer by external_id or email across data sources.
    """
    if external_id:
        cust = db.query(Customer).filter(Customer.external_id == external_id, Customer.organization_id == org_id).first()
        if cust:
            return cust
    if email:
        return db.query(Customer).filter(Customer.email == email, Customer.organization_id == org_id).first()
    return None

def reconcile_campaigns(db: Session, org_id: str, campaign_id: str = None, name: str = None):
    """
    Find an existing campaign by ID or fuzzy name match.
    """
    if campaign_id:
        camp = db.query(Campaign).filter(Campaign.id == campaign_id, Campaign.organization_id == org_id).first()
        if camp:
            return camp
    if name:
        return db.query(Campaign).filter(Campaign.name == name, Campaign.organization_id == org_id).first()
    return None
