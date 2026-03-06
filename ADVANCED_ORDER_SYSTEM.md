# Advanced Order Management System - Complete Reference

## Overview
A production-grade order management system with real-time tracking, status management, order actions, and comprehensive timeline events.

---

## ✨ Key Features

### 1. **Advanced Order Statuses**
Orders flow through multiple states:
- **PENDING_PAYMENT** → Awaiting payment
- **PAYMENT_CONFIRMED** → Payment received
- **ORDER_CONFIRMED** → Order confirmed by admin
- **PROCESSING** → Being processed in warehouse
- **PACKED** → Items packed and ready
- **SHIPPED** → In transit with carrier
- **OUT_FOR_DELIVERY** → Local delivery stage
- **DELIVERED** → Successfully delivered
- **CANCELLED** → Order cancelled
- **REFUND_INITIATED** → Return/refund started
- **REFUNDED** → Refund completed
- **RETURNED** → Item returned

### 2. **Real-Time Tracking**
Each order has a dedicated `OrderTracking` record:
- Unique tracking number (auto-generated)
- Carrier information and URL
- Current location updates
- Pickup, delivery estimates, and actual dates
- Tracking status synchronized with order status

### 3. **Order Timeline Events**
Comprehensive audit trail with `OrderTimelineEvent`:
- **STATUS_CHANGE** - Status updates
- **PAYMENT_UPDATE** - Payment confirmations
- **LOCATION_UPDATE** - Tracking location changes
- **DELIVERY_ATTEMPT** - Delivery attempts
- **CUSTOMER_NOTE** - Customer communications
- **ADMIN_NOTE** - Admin communications
- **RETURN_REQUEST** - Return requests
- **REFUND_INITIATED** - Refund processing

### 4. **Order Actions System**
Request-based actions with approval workflow:
- **CONFIRM_ORDER** - Customer confirms order
- **CANCEL_ORDER** - Request order cancellation
- **RETURN_REQUEST** - Request return/refund
- **REFUND_REQUEST** - Request refund
- **EDIT_SHIPPING** - Update shipping address
- **UPDATE_TRACKING** - Admin updates tracking
- **ADD_NOTE** - Add internal notes

Action Statuses: PENDING → APPROVED/REJECTED → COMPLETED

### 5. **Status History Logging**
`OrderStatusLog` tracks every status change:
- Previous and new status
- Who changed it (changed_by user)
- Timestamp
- Optional notes

---

## 📊 Database Models

### Order Model
```python
Fields:
- id (PK)
- order_number (Unique, auto-generated: ORD-XXXXXXXX)
- user (FK → User)
- status (Choice field with 12+ statuses)
- payment_status (PENDING, PROCESSING, PAID, FAILED, REFUND_PENDING, REFUNDED)
- tracking_number (Unique, auto-generated)
- current_location, carrier_name
- full_name, phone, address (shipping details)
- total_amount, tax_amount, discount_amount, net_amount
- estimated_delivery_date, actual_delivery_date
- created_at, updated_at
```

### OrderTracking Model (1-to-1 with Order)
```python
Fields:
- order (OneToOneField)
- tracking_number (Unique)
- carrier, carrier_url
- status (PENDING, PICKED_UP, IN_TRANSIT, OUT_FOR_DELIVERY, DELIVERED, etc.)
- current_location
- picked_up_date, estimated_delivery, actual_delivery_date
- last_updated, created_at
```

### OrderTimelineEvent Model
```python
Fields:
- order (FK)
- event_type (Choice: STATUS_CHANGE, PAYMENT_UPDATE, LOCATION_UPDATE, etc.)
- title (string)
- description (text)
- user (FK → who triggered it)
- location (for tracking updates)
- created_at
```

### OrderAction Model
```python
Fields:
- order (FK)
- action_type (Choice: CONFIRM_ORDER, CANCEL_ORDER, RETURN_REQUEST, etc.)
- status (PENDING, APPROVED, REJECTED, COMPLETED)
- requested_by (FK → User)
- approved_by (FK → User, nullable)
- description, rejection_reason
- requested_at, updated_at, completed_at
```

---

## 🔌 API Endpoints

### List All Orders
```
GET /api/orders/
Query Params:
  - search=<order_number|tracking_number|email>
  - ordering=created_at|status|net_amount
Filters:
  - status
  - payment_status
Returns: Paginated list
```

### Get Order Details
```
GET /api/orders/{id}/
Returns: Full order detail with items, tracking, timeline, actions
```

### My Orders (User)
```
GET /api/orders/my_orders/
Returns: Orders for logged-in user
```

### Update Order Status (Admin Only)
```
POST /api/orders/{id}/update_status/
Body:
{
  "status": "SHIPPED",
  "notes": "Handed to carrier XYZ"
}
Returns: Updated order with new status_history entry
Auto-creates: OrderStatusLog, OrderTimelineEvent
```

### Update Tracking (Admin Only)
```
POST /api/orders/{id}/update_tracking/
Body:
{
  "status": "IN_TRANSIT",
  "current_location": "Delhi Hub",
  "carrier": "FedEx",
  "carrier_url": "https://tracking.fedex.com/...",
  "estimated_delivery": "2026-02-25T10:00:00Z",
  "picked_up_date": "2026-02-21T08:00:00Z"
}
Auto-creates: OrderTimelineEvent (location update)
```

### Create Order Action
```
POST /api/orders/{id}/create_action/
Body:
{
  "action_type": "RETURN_REQUEST",
  "description": "Product is damaged, requesting return"
}
Returns: Action created with PENDING status
Auto-creates: OrderTimelineEvent (RETURN_REQUEST)
```

### Approve/Reject Action (Admin Only)
```
POST /api/orders/{id}/approve_action/
Body:
{
  "action_id": 5,
  "action": "approve" | "reject",
  "rejection_reason": "Optional rejection reason"
}
Returns: Action updated
```

### Get Order Timeline
```
GET /api/orders/timeline/?order_id={id}
Returns: Chronological timeline events
```

---

## 📈 Business Logic

### Order Status Flow
```
Creation: PENDING_PAYMENT
         ↓
User Pays: PAYMENT_CONFIRMED
         ↓
Confirmation: ORDER_CONFIRMED
         ↓
Warehouse: PROCESSING → PACKED → SHIPPED
         ↓
Delivery: OUT_FOR_DELIVERY → DELIVERED
```

### Automatic Behavior
- **Order Creation**: Auto-generates order_number and tracking_number
- **Tracking Creation**: Auto-creates OrderTracking when order created
- **Timeline Event**: Auto-creates timeline entry for order creation
- **Status Update**: Auto-logs previous/new status, creates timeline event
- **Delivery**: Auto-sets actual_delivery_date when status → DELIVERED
- **Location Update**: Auto-creates timeline event with location

### Signals
```python
@receiver(post_save, sender=Order)
def create_order_tracking():
    # Auto-creates tracking on order creation

@receiver(post_save, sender=Order)
def log_order_status_change():
    # Auto-logs status changes
```

---

## 🔐 Permissions

| Endpoint | Admin | Customer | Supplier |
|----------|-------|----------|----------|
| List orders | See all | See own | No |
| Get order | See all | See own | No |
| Update status | ✓ | - | - |
| Update tracking | ✓ | - | - |
| Create action | ✓ | ✓ (own) | - |
| Approve action | ✓ | - | - |
| View timeline | ✓ | ✓ (own) | - |

---

## 📱 Real-Time Updates

### Timeline Events
Every significant action creates a timeline event:
- Status changes
- Tracking updates
- Location changes
- Delivery attempts
- Customer/Admin notes
- Return/Refund requests

### Tracking Updates
Real-time carrier integration possible:
- Updates current_location
- Updates estimated_delivery
- Creates timeline event
- Syncs with order status

---

## 💰 Payment Statuses

| Status | Meaning | Next |
|--------|---------|------|
| PENDING | Awaiting payment | PROCESSING, FAILED |
| PROCESSING | Payment being processed | PAID, FAILED |
| PAID | Payment received | (stays until refund) |
| FAILED | Payment failed | PENDING |
| REFUND_PENDING | Refund in progress | REFUNDED |
| REFUNDED | Refund completed | - |

---

## 🔄 Order Actions Workflow

### Customer Initiates Action
```
POST /api/orders/{id}/create_action/
{
  "action_type": "RETURN_REQUEST",
  "description": "Damaged item"
}
↓
Action created with status=PENDING
↓
OrderTimelineEvent created (RETURN_REQUEST)
↓
Admin notified (via timeline/events)
```

### Admin Approves/Rejects
```
POST /api/orders/{id}/approve_action/
{
  "action_id": 5,
  "action": "approve"
}
↓
Action status → APPROVED
↓
approved_by = admin user
↓
completed_at = now
```

---

## 📊 Admin Panel Features

### Order Management
- Bulk actions: Mark PAID, PROCESSING, PACKED, SHIPPED, DELIVERED
- Filter by status, payment status, date range
- Search by order number, tracking number, customer email
- View all order details, items, tracking, timeline

### Tracking Management
- Update carrier info
- Change location
- Set estimated delivery
- Record pickup date

### Timeline Management
- View-only audit trail
- See all status changes
- Track location updates
- Monitor return/refund requests

### Action Management
- Approve/reject pending actions
- View action history
- Manage return requests
- Process refund requests

---

## 🎯 Use Cases

### Case 1: Standard Order Flow
```
1. Customer places order → PENDING_PAYMENT
2. Payment confirmed → PAYMENT_CONFIRMED
3. Admin confirms → ORDER_CONFIRMED
4. Warehouse processes → PROCESSING → PACKED
5. Carrier picks up → SHIPPED
6. In local delivery → OUT_FOR_DELIVERY
7. Delivered → DELIVERED
8. All tracked in timeline
```

### Case 2: Return Request
```
1. Customer creates action: RETURN_REQUEST
2. Order timeline shows return request
3. Admin approves action
4. Order status → REFUND_INITIATED
5. Admin processes refund → status REFUNDED
6. Payment status → REFUNDED
7. Timeline documents all steps
```

### Case 3: Shipping Address Update
```
1. Customer creates action: EDIT_SHIPPING (while PENDING)
2. Admin approves → updates address
3. Order processing continues
4. All changes logged in timeline
```

### Case 4: Real-Time Tracking
```
1. Carrier scans package
2. Admin updates: current_location="Hyderabad Hub"
3. Timeline auto-creates location event
4. Customer sees live location
5. Estimated delivery auto-calculated
```

---

## 📝 Response Examples

### Order List Response
```json
{
  "count": 150,
  "next": "...",
  "results": [
    {
      "id": 1,
      "order_number": "ORD-ABC123DE",
      "tracking_number": "TRK-ORD-ABC123DE-XYZ789",
      "user_email": "customer@example.com",
      "status": "SHIPPED",
      "status_display": "Shipped",
      "payment_status": "PAID",
      "payment_status_display": "Paid",
      "net_amount": "45000.00",
      "item_count": 2,
      "estimated_delivery_date": "2026-02-25",
      "created_at": "2026-02-21T10:00:00Z",
      "updated_at": "2026-02-22T15:30:00Z"
    }
  ]
}
```

### Order Detail Response
```json
{
  "id": 1,
  "order_number": "ORD-ABC123DE",
  "status": "SHIPPED",
  "status_display": "Shipped",
  "tracking": {
    "tracking_number": "TRK-ORD-ABC123DE-XYZ789",
    "status": "IN_TRANSIT",
    "current_location": "Delhi Hub",
    "carrier": "FedEx",
    "estimated_delivery": "2026-02-25T10:00:00Z"
  },
  "timeline_events": [
    {
      "event_type": "STATUS_CHANGE",
      "title": "Order Status Updated",
      "description": "Status changed to SHIPPED",
      "created_at": "2026-02-22T15:30:00Z"
    },
    {
      "event_type": "LOCATION_UPDATE",
      "title": "Location Updated",
      "location": "Delhi Hub",
      "created_at": "2026-02-22T16:00:00Z"
    }
  ],
  "status_history": [
    {
      "previous_status": "PACKED",
      "new_status": "SHIPPED",
      "changed_by_email": "admin@jewellery.com",
      "created_at": "2026-02-22T15:30:00Z"
    }
  ],
  "actions": [
    {
      "action_type": "RETURN_REQUEST",
      "status": "PENDING",
      "requested_by_email": "customer@example.com",
      "requested_at": "2026-02-23T10:00:00Z"
    }
  ]
}
```

---

## 🚀 Production Considerations

1. **Carrier Integration**: Integrate with FedEx, USPS, DHL APIs
2. **Notifications**: Send email/SMS on status changes
3. **Webhooks**: Support carrier webhooks for auto-updates
4. **Caching**: Cache tracking data for performance
5. **Indexing**: Add DB indexes on order_number, tracking_number
6. **Backup**: Regular backups of order history
7. **Compliance**: Maintain audit trail for legal requirements
8. **Analytics**: Track order metrics and trends

---

## 🎯 System Status

✅ **All Features Implemented**
✅ **Migrations Applied**
✅ **Admin Panel Configured**
✅ **API Endpoints Ready**
✅ **Real-Time Updates Ready**
✅ **Production Deployable**

