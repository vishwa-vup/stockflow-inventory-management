import pytest

def get_token(client, email, password):
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]

def test_login_success(client):
    resp = client.post("/api/auth/login", json={"email": "admintest@stockflow.com", "password": "Admin@123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "admintest@stockflow.com"
    assert data["user"]["role"] == "ADMIN"

def test_login_invalid_password(client):
    resp = client.post("/api/auth/login", json={"email": "admintest@stockflow.com", "password": "WrongPassword"})
    assert resp.status_code == 401
    assert "Invalid email or password" in resp.json()["detail"]

def test_rbac_admin_only_users_endpoint(client):
    admin_token = get_token(client, "admintest@stockflow.com", "Admin@123")
    staff_token = get_token(client, "stafftest@stockflow.com", "Staff@123")

    # Admin access should succeed
    admin_resp = client.get("/api/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_resp.status_code == 200
    assert len(admin_resp.json()) >= 2

    # Staff access should be forbidden (403)
    staff_resp = client.get("/api/users", headers={"Authorization": f"Bearer {staff_token}"})
    assert staff_resp.status_code == 403
    assert "Admin privilege required" in staff_resp.json()["detail"]

def test_product_crud_and_validation(client):
    admin_token = get_token(client, "admintest@stockflow.com", "Admin@123")
    staff_token = get_token(client, "stafftest@stockflow.com", "Staff@123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Product creation with invalid stock bounds (max <= min)
    invalid_payload = {
        "product_code": "TEST-INV-01",
        "name": "Invalid Item",
        "category_id": 1,
        "supplier_id": 1,
        "purchase_price": 50.0,
        "selling_price": 75.0,
        "initial_stock": 5,
        "minimum_stock": 20,
        "maximum_stock": 10,  # Max < Min!
    }
    resp = client.post("/api/products", json=invalid_payload, headers=headers)
    assert resp.status_code == 422

    # 2. Valid creation
    valid_payload = {
        "product_code": "TEST-KBD-99",
        "name": "Pro Gaming Keyboard",
        "description": "RGB Backlit",
        "category_id": 1,
        "supplier_id": 1,
        "purchase_price": 40.0,
        "selling_price": 89.99,
        "initial_stock": 15,
        "minimum_stock": 5,
        "maximum_stock": 50,
        "location": "Shelf A2"
    }
    resp = client.post("/api/products", json=valid_payload, headers=headers)
    assert resp.status_code == 201
    prod_data = resp.json()
    assert prod_data["product_code"] == "TEST-KBD-99"
    assert prod_data["current_stock"] == 15
    prod_id = prod_data["id"]

    # 3. Staff trying to delete product should receive 403 Forbidden
    del_staff = client.delete(f"/api/products/{prod_id}", headers={"Authorization": f"Bearer {staff_token}"})
    assert del_staff.status_code == 403

    # 4. Admin update product
    update_resp = client.put(f"/api/products/{prod_id}", json={"name": "Pro Gaming Keyboard V2", "selling_price": 99.99}, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Pro Gaming Keyboard V2"
    assert update_resp.json()["selling_price"] == 99.99

    # 5. Admin delete product
    del_resp = client.delete(f"/api/products/{prod_id}", headers=headers)
    assert del_resp.status_code == 200

def test_stock_in_and_stock_out_flow(client):
    token = get_token(client, "stafftest@stockflow.com", "Staff@123")
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch product 1
    p_resp = client.get("/api/products/1", headers=headers)
    assert p_resp.status_code == 200
    start_stock = p_resp.json()["current_stock"]

    # Perform Stock In of 15 units
    in_payload = {
        "product_id": 1,
        "quantity": 15,
        "reference_number": "PO-TEST-001",
        "notes": "Incoming test shipment"
    }
    in_resp = client.post("/api/inventory/stock-in", json=in_payload, headers=headers)
    assert in_resp.status_code == 201
    tx_in = in_resp.json()
    assert tx_in["transaction_type"] == "STOCK_IN"
    assert tx_in["quantity"] == 15
    assert tx_in["new_stock"] == start_stock + 15

    # Perform Stock Out of 5 units
    out_payload = {
        "product_id": 1,
        "quantity": 5,
        "customer_department": "Sales Dept",
        "reference_number": "SO-TEST-001",
        "notes": "Delivered to sales"
    }
    out_resp = client.post("/api/inventory/stock-out", json=out_payload, headers=headers)
    assert out_resp.status_code == 201
    tx_out = out_resp.json()
    assert tx_out["transaction_type"] == "STOCK_OUT"
    assert tx_out["quantity"] == 5
    assert tx_out["new_stock"] == start_stock + 10

def test_insufficient_stock_rejection(client):
    token = get_token(client, "stafftest@stockflow.com", "Staff@123")
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to stock out an impossibly large amount
    out_payload = {
        "product_id": 1,
        "quantity": 99999,
        "notes": "Excessive request"
    }
    resp = client.post("/api/inventory/stock-out", json=out_payload, headers=headers)
    assert resp.status_code == 400
    assert "Insufficient stock" in resp.json()["detail"]

def test_low_stock_and_reorder_calculation(client):
    admin_token = get_token(client, "admintest@stockflow.com", "Admin@123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create a product with current stock 2 and min stock 10
    low_prod = {
        "product_code": "TEST-LOW-01",
        "name": "Low Stock Widget",
        "category_id": 1,
        "supplier_id": 1,
        "purchase_price": 10.0,
        "selling_price": 20.0,
        "initial_stock": 2,
        "minimum_stock": 10,
        "maximum_stock": 50,
        "location": "Aisle 9"
    }
    p_resp = client.post("/api/products", json=low_prod, headers=headers)
    assert p_resp.status_code == 201
    assert p_resp.json()["status"] == "LOW_STOCK"

    # Verify dashboard alerts endpoint lists it
    alert_resp = client.get("/api/dashboard/low-stock-alerts", headers=headers)
    assert alert_resp.status_code == 200
    codes = [item["product_code"] for item in alert_resp.json()]
    assert "TEST-LOW-01" in codes

    # Verify reorder recommendation: 50 - 2 = 48
    reorder_resp = client.get("/api/dashboard/reorder-recommendations", headers=headers)
    assert reorder_resp.status_code == 200
    matching = [r for r in reorder_resp.json() if r["product_code"] == "TEST-LOW-01"]
    assert len(matching) > 0
    assert matching[0]["suggested_order_quantity"] == 48

def test_dashboard_stats(client):
    token = get_token(client, "stafftest@stockflow.com", "Staff@123")
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/dashboard/stats", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_products" in data
    assert "total_stock" in data
    assert "low_stock_count" in data
    assert "out_of_stock_count" in data
    assert "total_inventory_value" in data
    assert "total_suppliers" in data
    assert data["total_products"] >= 1
    assert data["total_stock"] >= 0
