# Jewellery Marketplace - Retail Inventory System API Reference

## System Overview
A production-ready retail inventory management system where:
- **Suppliers** submit products for approval
- **Admin** approves products, sets selling prices, and manages purchases from suppliers
- **Customers** browse and purchase approved products
- **No direct supplier-to-customer sales** - all inventory is owned by admin

---

## Authentication
All endpoints except product listing require JWT authentication.

**Token Endpoints** (from accounts app):
- `POST /api/accounts/register/` - User registration
- `POST /api/accounts/login/` - Get JWT tokens
- `POST /api/accounts/refresh/` - Refresh access token

**Headers for authenticated requests:**
```
Authorization: Bearer <access_token>
```

---

## Product Management APIs

### 1. Product Listing & Discovery

#### Get All Approved Products (Public)
```
GET /api/products/products/
```
- **Who can access:** Everyone (unauthenticated)
- **Query params:** 
  - `is_approved=true` - Only approved products (default)
  - `category__slug=<slug>` - Filter by category
  - `purity=22K` - Filter by purity
  - `search=<keyword>` - Search by name/description
  - `ordering=selling_price` - Sort by price

**Response Example:**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "name": "Gold Ring 22K",
      "slug": "gold-ring-22k",
      "description": "Premium gold ring",
      "selling_price": "25000.00",
      "stock_quantity": 5,
      "sku": "PROD-0001",
      "is_approved": true,
      "purity": "22K",
      "images": [
        {"id": 1, "image": "https://...", "is_primary": true}
      ]
    }
  ]
}
```

#### Get Product Details
```
GET /api/products/products/{id}/
```
- **Who can access:** Everyone
- **Returns:** Full product details including cost_price (if admin/supplier)

---

### 2. Supplier Product Management

#### Submit Product (Supplier Only)
```
POST /api/products/products/
```
- **Who can access:** Suppliers (role=SUPPLIER)
- **Required fields:**
  - `name` (string) - Product name
  - `description` (text) - Product description
  - `cost_price` (decimal) - Supplier's cost price
  - `category` (int) - Category ID
  - `purity` (choice) - '18K', '22K', or '24K'
  - `stock_quantity` (int) - Initial stock
  - `gold_weight` (decimal) - Weight in grams (optional)
  - `diamond_clarity` (string) - Clarity grade (optional)

**Note:** Supplier cannot set `selling_price` - only admin can

**Request Example:**
```json
{
  "name": "Diamond Bracelet",
  "description": "22K Gold with diamonds",
  "cost_price": "50000.00",
  "category": 1,
  "purity": "22K",
  "stock_quantity": 10,
  "gold_weight": 10.5
}
```

#### View My Products (Supplier Only)
```
GET /api/products/products/my_products/
```
- **Who can access:** Suppliers
- **Returns:** All products submitted by this supplier (approved and unapproved)

#### Update My Product (Supplier Only)
```
PATCH /api/products/products/{id}/
PUT /api/products/products/{id}/
```
- **Who can access:** Supplier who owns the product
- **Can update:** All fields except `selling_price` (admin-only)

#### Delete My Product (Supplier Only)
```
DELETE /api/products/products/{id}/
```
- **Who can access:** Supplier who owns the product

---

### 3. Admin Product Control

#### Approve Product
```
POST /api/products/products/{id}/approve_product/
```
- **Who can access:** Admin only
- **Effect:** Sets `is_approved=true`, makes product visible to customers
- **Response:** `{"status": "Product approved"}`

#### Set Selling Price
```
POST /api/products/products/{id}/set_selling_price/
Content-Type: application/json

{
  "selling_price": "75000.00"
}
```
- **Who can access:** Admin only
- **Required:** `selling_price` in request body
- **Effect:** Sets the customer-facing price
- **Response:** `{"status": "Selling price updated", "selling_price": 75000.0}`

#### View All Products
```
GET /api/products/products/?admin=true
```
- **Who can access:** Admin
- **Returns:** All products (approved and unapproved), with cost_price visible

---

## Purchase Order APIs (Admin Buys from Supplier)

### Create Purchase Order (Admin Only)
```
POST /api/products/purchase-orders/
Content-Type: application/json

{
  "supplier": <supplier_user_id>,
  "product": <product_id>,
  "quantity": 5,
  "total_cost": "250000.00"
}
```
- **Who can access:** Admin only
- **Effect:** Creates order for admin to purchase inventory from supplier
- **Status:** Starts as 'PENDING'

**Response:**
```json
{
  "id": 1,
  "supplier": 5,
  "supplier_email": "supplier@example.com",
  "product": 1,
  "product_name": "Gold Ring",
  "product_sku": "PROD-0001",
  "quantity": 5,
  "total_cost": "250000.00",
  "status": "PENDING",
  "created_at": "2025-02-21T15:00:00Z"
}
```

### View Purchase Orders
```
GET /api/products/purchase-orders/
```
- **Admin:** See all purchase orders
- **Supplier:** See only orders from their products

**Query params:**
- `status=PENDING` - Filter by status
- `ordering=-created_at` - Sort by date (newest first)

### Mark Purchase Order as Received
```
POST /api/products/purchase-orders/{id}/mark_received/
```
- **Who can access:** Admin only
- **Effect:** 
  - Sets status to 'RECEIVED'
  - **Automatically increases product stock** by the ordered quantity
  - Triggers inventory update signal
- **Response:** `{"status": "Purchase order marked as received"}`

### Supplier View Their Orders
```
GET /api/products/purchase-orders/supplier_orders/
```
- **Who can access:** Suppliers
- **Returns:** All purchase orders created for this supplier's products

---

## Customer Order APIs

### Place Order (Customer Only)
```
POST /api/products/customer-orders/
Content-Type: application/json

{
  "product": <product_id>,
  "quantity": 2,
  "total_price": "50000.00"
}
```
- **Who can access:** Customers (role=CUSTOMER)
- **Validation:**
  - Product must be `is_approved=true`
  - Stock must be available (>= quantity)
- **Effect:**
  - Creates order with status='PLACED'
  - **Automatically decreases product stock** by ordered quantity
  - Triggers inventory update signal
- **Error responses:**
  - `"Product is not approved for sale"` (403)
  - `"Insufficient stock available"` (400)

**Response:**
```json
{
  "id": 1,
  "customer": 10,
  "customer_email": "customer@example.com",
  "product": 1,
  "product_name": "Gold Ring",
  "product_image": "https://...",
  "quantity": 2,
  "total_price": "50000.00",
  "status": "PLACED",
  "created_at": "2025-02-21T15:05:00Z"
}
```

### View My Orders (Customer Only)
```
GET /api/products/customer-orders/my_orders/
```
- **Who can access:** Customers
- **Returns:** All orders placed by this customer

### Cancel Order (Customer Can Cancel Own Orders)
```
POST /api/products/customer-orders/{id}/cancel_order/
```
- **Who can access:** Customer who placed the order, or Admin
- **Constraint:** Can only cancel 'PLACED' status orders
- **Effect:**
  - Changes status to 'CANCELLED'
  - **Refunds stock** - increases product stock by cancelled quantity
- **Response:** `{"status": "Order cancelled"}`

### View All Orders (Admin Only)
```
GET /api/products/customer-orders/
```
- **Who can access:** Admin
- **Returns:** All customer orders

---

## Inventory Management

### Automatic Stock Updates (Handled by Signals)

**When Purchase Order Status → RECEIVED:**
- `Product.stock_quantity += PurchaseOrder.quantity`
- Example: Admin receives PO for 10 units → stock increases by 10

**When Customer Order Created (Status = PLACED):**
- `Product.stock_quantity -= CustomerOrder.quantity`
- Example: Customer orders 2 units → stock decreases by 2

**When Customer Order Cancelled:**
- `Product.stock_quantity += CustomerOrder.quantity`
- Example: Customer cancels order of 2 units → stock increases by 2

### Stock Validation
- Customers cannot place orders if `stock_quantity < order_quantity`
- Returns: `{"error": "Insufficient stock available"}`

---

## Permission Matrix

| Endpoint | Admin | Supplier | Customer | Public |
|----------|-------|----------|----------|--------|
| View approved products | ✓ | ✓ | ✓ | ✓ |
| View all products | ✓ | - | - | - |
| Submit product | - | ✓ | - | - |
| Approve product | ✓ | - | - | - |
| Set selling price | ✓ | - | - | - |
| Create purchase order | ✓ | - | - | - |
| Mark PO received | ✓ | - | - | - |
| View supplier's orders | ✓ | ✓* | - | - |
| Place customer order | - | - | ✓ | - |
| View own orders | - | - | ✓ | - |
| Cancel own order | - | - | ✓ | - |
| View all orders | ✓ | - | - | - |

*Suppliers see only their own orders

---

## Data Models

### Product
```
- id (int, auto)
- name (string, max 255)
- slug (string, unique, auto-generated)
- description (text)
- supplier_user (FK → User, role=SUPPLIER)
- cost_price (decimal) - Hidden from customers
- selling_price (decimal) - Visible to customers
- margin (calculated) - selling_price - cost_price
- margin_percentage (calculated) - (margin / cost_price) × 100
- stock_quantity (int)
- sku (string, unique, auto-generated)
- category (FK → Category)
- purity (choice: 18K, 22K, 24K)
- gold_weight (decimal, optional)
- diamond_clarity (choice, optional)
- is_approved (boolean, default=False)
- is_featured (boolean)
- is_enabled (boolean)
- created_at (datetime, auto)
- updated_at (datetime, auto)
```

### PurchaseOrder
```
- id (int, auto)
- supplier (FK → User, role=SUPPLIER)
- product (FK → Product)
- quantity (int)
- total_cost (decimal)
- status (choice: PENDING, APPROVED, RECEIVED, CANCELLED)
- created_at (datetime, auto)
- updated_at (datetime, auto)
```

### CustomerOrder
```
- id (int, auto)
- customer (FK → User, role=CUSTOMER)
- product (FK → Product)
- quantity (int)
- total_price (decimal)
- status (choice: PLACED, SHIPPED, DELIVERED, CANCELLED, RETURNED)
- created_at (datetime, auto)
- updated_at (datetime, auto)
```

---

## Business Logic Summary

### Supplier Workflow
1. Supplier registers with role='SUPPLIER'
2. Supplier submits product with `cost_price`
3. Supplier views own products (approved and unapproved)
4. Supplier views purchase orders admin creates for their products
5. Admin approves product and sets selling price

### Admin Workflow
1. Admin views all submitted products
2. Admin approves product → `is_approved=true` → visible to customers
3. Admin sets `selling_price` (customer-facing price)
4. Admin creates purchase order → orders inventory from supplier
5. When inventory arrives, admin marks PO as 'RECEIVED' → **stock automatically increases**
6. Admin can view all customer orders

### Customer Workflow
1. Customer registers with role='CUSTOMER'
2. Customer browses **only approved products**
3. Customer places order → **stock automatically decreases**
4. Customer can view their orders
5. Customer can cancel 'PLACED' orders → **stock automatically refunded**

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Insufficient stock available"
}
```

### 403 Forbidden
```json
{
  "detail": "You can only edit your own products"
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

---

## Rate Limiting & Pagination

Default pagination: 20 items per page
Customize with `?page_size=50`

---

## Admin Panel
Django admin available at `/admin/`
- Manage products, purchase orders, customer orders
- Bulk actions (approve products, mark orders as received/shipped/delivered)

---

## Security Notes
1. **cost_price** is hidden from customers (only visible to admin/supplier)
2. **Suppliers cannot:**
   - See customer information
   - See customer orders
   - Set selling prices
   - Modify other supplier's products
3. **Customers cannot:**
   - See supplier information
   - See cost prices
   - See other customer's orders
4. **All role validation** happens in backend (not frontend)
5. **Stock validation** prevents negative inventory
