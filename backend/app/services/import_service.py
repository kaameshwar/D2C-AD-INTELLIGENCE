import pandas as pd
import io
from sqlalchemy.orm import Session
from app.models import DataSource, ImportJob, Campaign, DailyCampaignMetric, Product, Customer, Order, OrderItem
import datetime

def import_campaigns(db: Session, org_id: str, file_contents: bytes, data_source_name: str = "CSV Upload"):
    data_source = db.query(DataSource).filter_by(organization_id=org_id, name=data_source_name).first()
    if not data_source:
        data_source = DataSource(organization_id=org_id, name=data_source_name, source_type="CSV", status="CONNECTED")
        db.add(data_source)
        db.commit()
        db.refresh(data_source)
        
    job = ImportJob(organization_id=org_id, data_source_id=data_source.id, status="PROCESSING", file_name="campaigns_import.csv")
    db.add(job)
    db.commit()
    db.refresh(job)
    ds_id = data_source.id
    try:
        df = pd.read_csv(io.BytesIO(file_contents))
        df.columns = [str(c).replace('\ufeff', '').strip().lower() for c in df.columns]
    except Exception as e:
        return {"success": False, "error": "Invalid CSV file format."}
        
    required_cols = {'campaign_id', 'spend', 'revenue', 'clicks', 'conversions'}
    detected_cols = set(df.columns)
    missing_cols = required_cols - detected_cols
    if missing_cols:
        return {"success": False, "error": f"Missing required columns: {', '.join(missing_cols)}. Detected columns: {', '.join(detected_cols)}"}
        
    created = 0
    updated = 0
    skipped = 0
    failed = 0
    errors = []
    
    unique_campaigns = df.drop_duplicates(subset=['campaign_id'])
    for idx, row in unique_campaigns.iterrows():
        try:
            campaign = db.query(Campaign).filter(Campaign.id == str(row['campaign_id'])).first()
            if campaign:
                if campaign.organization_id != org_id:
                    failed += 1
                    errors.append({"row": idx, "reason": f"Campaign {row['campaign_id']} owned by another org."})
                    continue
                else:
                    campaign.name = str(row.get('campaign_name', campaign.name))
                    campaign.platform = str(row.get('platform', campaign.platform))
                    campaign.daily_budget = float(row.get('spend', campaign.daily_budget))
                    updated += 1
            else:
                campaign = Campaign(
                    id=str(row['campaign_id']),
                    organization_id=org_id,
                    name=str(row.get('campaign_name', 'Unknown')),
                    platform=str(row.get('platform', 'Unknown')),
                    target_product_sku=str(row.get('sku_id', '')),
                    data_source_id=ds_id,
                    daily_budget=float(row.get('spend', 0)),
                    status="Active"
                )
                db.add(campaign)
                created += 1
        except Exception as e:
            failed += 1
            errors.append({"row": idx, "reason": str(e)})

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        return {"success": False, "error": f"Database commit failed: {str(e)}"}
        
    # Process metrics
    metric_count = 0
    for idx, row in df.iterrows():
        try:
            # Simple deduplication could go here. For now we append.
            metric = DailyCampaignMetric(
                campaign_id=str(row['campaign_id']),
                date=str(row.get('date', '2023-01-01')),
                spend=float(row.get('spend', 0)),
                revenue=float(row.get('revenue', 0)),
                impressions=int(row.get('impressions', 0)),
                clicks=int(row.get('clicks', 0)),
                conversions=int(row.get('conversions', 0)),
                creative_fatigue_score=0.5
            )
            db.add(metric)
            metric_count += 1
        except Exception as e:
            failed += 1
            

    db.commit()
    
    job.status = "SUCCESS" if failed == 0 else ("PARTIAL_SUCCESS" if created > 0 else "FAILED")
    job.row_count = len(df)
    job.errors = str(errors) if errors else None
    data_source.last_sync_time = datetime.datetime.utcnow()
    data_source.record_count += created
    db.commit()
    
    return {
        "success": True,
        "created": created,
        "updated": updated,
        "metrics_added": metric_count,
        "failed": failed,
        "errors": errors
    }

def import_products(db: Session, org_id: str, file_contents: bytes, data_source_name: str = "CSV Upload"):
    data_source = db.query(DataSource).filter_by(organization_id=org_id, name=data_source_name).first()
    if not data_source:
        data_source = DataSource(organization_id=org_id, name=data_source_name, source_type="CSV", status="CONNECTED")
        db.add(data_source)
        db.commit()
        db.refresh(data_source)
        
    job = ImportJob(organization_id=org_id, data_source_id=data_source.id, status="PROCESSING", file_name="products_import.csv")
    db.add(job)
    db.commit()
    db.refresh(job)
    ds_id = data_source.id
    try:
        df = pd.read_csv(io.BytesIO(file_contents))
        df.columns = [str(c).replace('\ufeff', '').strip().lower() for c in df.columns]
    except Exception as e:
        return {"success": False, "error": "Invalid CSV file format."}
        
    required_cols = {'sku', 'name', 'price', 'cost'}
    detected_cols = set(df.columns)
    missing_cols = required_cols - detected_cols
    if missing_cols:
        return {"success": False, "error": f"Missing required columns: {', '.join(missing_cols)}. Detected columns: {', '.join(detected_cols)}"}
        
    created = 0
    updated = 0
    failed = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            sku = str(row['sku']).strip()
            if not sku:
                failed += 1
                errors.append({"row": idx, "reason": "SKU cannot be empty"})
                continue
                
            price = float(row.get('price', 0))
            if pd.isna(price) or price < 0:
                failed += 1
                errors.append({"row": idx, "reason": "Invalid price"})
                continue
                
            cost = row.get('cost')
            if pd.isna(cost):
                cost = None
            else:
                cost = float(cost)
                
            product = db.query(Product).filter(
                Product.sku == sku, 
                Product.organization_id == org_id
            ).first()
            
            if product:
                product.name = str(row.get('name', product.name))
                product.price = price
                product.cost = cost
                product.currency = str(row.get('currency', product.currency))
                product.status = str(row.get('status', product.status))
                updated += 1
            else:
                product = Product(
                    organization_id=org_id,
                    sku=sku,
                    data_source_id=ds_id,
                    name=str(row.get('name', 'Unknown Product')),
                    price=price,
                    cost=cost,
                    currency=str(row.get('currency', 'USD')),
                    status=str(row.get('status', 'active'))
                )
                db.add(product)
                created += 1
                
        except Exception as e:
            failed += 1
            errors.append({"row": idx, "reason": str(e)})
            
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        return {"success": False, "error": f"Database error: {str(e)}"}
        
    return {
        "success": True,
        "created": created,
        "updated": updated,
        "failed": failed,
        "errors": errors
    }

def import_orders(db: Session, org_id: str, file_contents: bytes, data_source_name: str = "CSV Upload"):
    data_source = db.query(DataSource).filter_by(organization_id=org_id, name=data_source_name).first()
    if not data_source:
        data_source = DataSource(organization_id=org_id, name=data_source_name, source_type="CSV", status="CONNECTED")
        db.add(data_source)
        db.commit()
        db.refresh(data_source)
        
    job = ImportJob(organization_id=org_id, data_source_id=data_source.id, status="PROCESSING", file_name="orders_import.csv")
    db.add(job)
    db.commit()
    db.refresh(job)
    ds_id = data_source.id
    try:
        df = pd.read_csv(io.BytesIO(file_contents))
        df.columns = [str(c).replace('\ufeff', '').strip().lower() for c in df.columns]
    except Exception as e:
        return {"success": False, "error": "Invalid CSV file format."}
        
    required_cols = {'order_id', 'customer_id', 'product_sku', 'quantity', 'total'}
    detected_cols = set(df.columns)
    missing_cols = required_cols - detected_cols
    if missing_cols:
        return {"success": False, "error": f"Missing required columns: {', '.join(missing_cols)}. Detected columns: {', '.join(detected_cols)}"}
        
    created_orders = 0
    updated_orders = 0
    created_items = 0
    failed = 0
    errors = []
    
    # Process customers first
    customers_df = df[['customer_id']].drop_duplicates()
    for _, row in customers_df.iterrows():
        ext_id = str(row['customer_id']).strip()
        if not ext_id or ext_id == 'nan':
            continue
        cust = db.query(Customer).filter(
            Customer.external_id == ext_id,
            Customer.organization_id == org_id
        ).first()
        if not cust:
            cust = Customer(organization_id=org_id, external_id=ext_id, data_source_id=ds_id)
            db.add(cust)
            
    db.commit()
    
    # Process orders
    cols_to_keep = ['order_id', 'customer_id', 'order_date', 'status', 'currency']
    if 'attribution_campaign_id' in df.columns:
        cols_to_keep.append('attribution_campaign_id')
    
    # Only keep columns that actually exist in the dataframe
    cols_to_keep = [c for c in cols_to_keep if c in df.columns]
    
    orders_df = df[cols_to_keep].drop_duplicates(subset=['order_id'])
    order_id_map = {}
    
    for idx, row in orders_df.iterrows():
        try:
            ext_order_id = str(row['order_id']).strip()
            if not ext_order_id:
                failed += 1
                continue
                
            cust_ext_id = str(row['customer_id']).strip()
            customer = db.query(Customer).filter(
                Customer.external_id == cust_ext_id,
                Customer.organization_id == org_id
            ).first()
            
            order_date_str = str(row.get('order_date', ''))
            try:
                if order_date_str == 'nan' or not order_date_str.strip():
                    order_date = datetime.datetime.utcnow()
                else:
                    order_date = pd.to_datetime(order_date_str).to_pydatetime()
            except:
                order_date = datetime.datetime.utcnow()
                
            order = db.query(Order).filter(
                Order.external_id == ext_order_id,
                Order.organization_id == org_id
            ).first()
            
            attribution_id = None
            if 'attribution_campaign_id' in row and not pd.isna(row['attribution_campaign_id']):
                attribution_id = str(row['attribution_campaign_id']).strip()
                if attribution_id == 'nan' or not attribution_id:
                    attribution_id = None
            
            if order:
                order.status = str(row.get('status', order.status))
                if attribution_id is not None:
                    order.attribution_campaign_id = attribution_id
                updated_orders += 1
            else:
                order = Order(
                    organization_id=org_id,
                    external_id=ext_order_id,
                    customer_id=customer.id if customer else None,
                    data_source_id=ds_id,
                    order_date=order_date,
                    status=str(row.get('status', 'completed')),
                    currency=str(row.get('currency', 'USD')),
                    attribution_campaign_id=attribution_id
                )
                db.add(order)
                created_orders += 1
            
            db.flush()
            order_id_map[ext_order_id] = order.id
            
        except Exception as e:
            failed += 1
            errors.append({"row": idx, "reason": str(e)})
            
    # Process order items
    for idx, row in df.iterrows():
        try:
            ext_order_id = str(row['order_id']).strip()
            if ext_order_id not in order_id_map:
                continue
                
            internal_order_id = order_id_map[ext_order_id]
            sku = str(row['product_sku']).strip()
            
            product = db.query(Product).filter(
                Product.sku == sku,
                Product.organization_id == org_id
            ).first()
            
            qty = int(row.get('quantity', 1))
            unit_price = float(row.get('unit_price', 0))
            if product and unit_price == 0:
                unit_price = product.price
                
            total = qty * unit_price
            
            # Check if this exact item exists to prevent duplicates (naive approach)
            existing_item = db.query(OrderItem).filter(
                OrderItem.order_id == internal_order_id,
                OrderItem.product_id == (product.id if product else None)
            ).first()
            
            if existing_item:
                continue
                
            item = OrderItem(
                organization_id=org_id,
                order_id=internal_order_id,
                data_source_id=ds_id,
                product_id=product.id if product else None,
                quantity=qty,
                unit_price=unit_price,
                product_cost=product.cost if product else None,
                total=total
            )
            db.add(item)
            
            # Update order totals
            order = db.query(Order).filter(Order.id == internal_order_id).first()
            if order:
                order.total += total
                order.subtotal += total
                
            created_items += 1
            
        except Exception as e:
            failed += 1
            
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        return {"success": False, "error": f"Database error: {str(e)}"}
        

    job.status = "SUCCESS" if failed == 0 else ("PARTIAL_SUCCESS" if created_orders > 0 else "FAILED")
    job.row_count = len(df)
    job.errors = str(errors) if errors else None
    data_source.last_sync_time = datetime.datetime.utcnow()
    data_source.record_count += created_orders
    db.commit()
    
    return {
        "success": True,
        "created_orders": created_orders,
        "updated_orders": updated_orders,
        "created_items": created_items,
        "failed": failed,
        "errors": errors
    }
