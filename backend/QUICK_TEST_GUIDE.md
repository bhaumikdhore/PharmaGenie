# Quick Testing Guide

## Run These Commands to Test the Agents

### 1. Test Delivery Agent - Track Order
```bash
curl -X POST http://localhost:8000/ai/test/delivery \
  -H "Content-Type: application/json" \
  -d '{
    "action": "track",
    "order_id": "ORD-PIZZA-123"
  }'
```

**Expected Response:**
```json
{
  "agent": "delivery",
  "status": "success",
  "order_id": "ORD-PIZZA-123",
  "tracking_number": "TRK-ORD-PIZZA-123-1234567890",
  "current_stage": "in_transit",
  "stage_info": {
    "label": "In Transit",
    "description": "Order on the way to delivery location"
  },
  "location": {
    "lat": 19.0760,
    "lng": 72.8777,
    "address": "In Transit - Mumbai"
  },
  "estimated_delivery": "2026-03-01T18:00:00"
}
```

---

### 2. Test Delivery Agent - Update Status
```bash
curl -X POST http://localhost:8000/ai/test/delivery \
  -H "Content-Type: application/json" \
  -d '{
    "action": "update_status",
    "order_id": "ORD-PIZZA-123",
    "new_stage": "out_for_delivery",
    "customer_phone": "+919876543210"
  }'
```

**Expected Response:**
```json
{
  "agent": "delivery",
  "status": "success",
  "order_id": "ORD-PIZZA-123",
  "new_stage": "out_for_delivery",
  "stage_info": {
    "label": "Out for Delivery",
    "description": "Order out for delivery today"
  },
  "notification_triggered": true,
  "notification_payload": {
    "order_id": "ORD-PIZZA-123",
    "new_stage": "out_for_delivery",
    "customer_phone": "+919876543210"
  }
}
```

---

### 3. Test Delivery Agent - Get History
```bash
curl -X POST http://localhost:8000/ai/test/delivery \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get_history",
    "order_id": "ORD-PIZZA-123"
  }'
```

**Expected Response:**
```json
{
  "agent": "delivery",
  "status": "success",
  "order_id": "ORD-PIZZA-123",
  "total_events": 5,
  "history": [
    {
      "stage": "pending",
      "timestamp": "2026-02-28T10:00:00",
      "description": "Order placed"
    },
    {
      "stage": "confirmed",
      "timestamp": "2026-02-28T10:30:00",
      "description": "Order confirmed by pharmacy"
    },
    {
      "stage": "packed",
      "timestamp": "2026-02-28T14:00:00",
      "description": "Order packed and ready"
    },
    {
      "stage": "dispatched",
      "timestamp": "2026-02-28T16:00:00",
      "description": "Order dispatched"
    },
    {
      "stage": "in_transit",
      "timestamp": "2026-03-01T08:00:00",
      "description": "Order in transit"
    }
  ]
}
```

---

### 4. Test Notification Agent - Check Stock (Warning Level)
```bash
curl -X POST http://localhost:8000/ai/test/notification \
  -H "Content-Type: application/json" \
  -d '{
    "action": "check_stock",
    "medicine_id": 1,
    "medicine_name": "Paracetamol",
    "current_stock": 25,
    "total_stock": 100
  }'
```

**Expected Response:**
```json
{
  "agent": "notification",
  "status": "success",
  "medicine_id": 1,
  "medicine_name": "Paracetamol",
  "current_stock": 25,
  "total_stock": 100,
  "stock_percentage": 25.0,
  "alert_level": "warning",
  "needs_refill": true,
  "refill_quantity": 50,
  "severity": "warning",
  "n8n_workflow_triggered": true,
  "n8n_payload": {
    "medicine_id": 1,
    "medicine_name": "Paracetamol",
    "current_stock": 25,
    "refill_quantity": 50,
    "alert_level": "warning"
  }
}
```

---

### 5. Test Notification Agent - Check Stock (Critical Level)
```bash
curl -X POST http://localhost:8000/ai/test/notification \
  -H "Content-Type: application/json" \
  -d '{
    "action": "check_stock",
    "medicine_id": 2,
    "medicine_name": "Amoxicillin",
    "current_stock": 5,
    "total_stock": 100
  }'
```

**Expected Response:**
```json
{
  "agent": "notification",
  "status": "success",
  "medicine_id": 2,
  "medicine_name": "Amoxicillin",
  "current_stock": 5,
  "total_stock": 100,
  "stock_percentage": 5.0,
  "alert_level": "critical",
  "needs_refill": true,
  "refill_quantity": 50,
  "severity": "critical",
  "n8n_workflow_triggered": true,
  "n8n_payload": {
    "medicine_id": 2,
    "medicine_name": "Amoxicillin",
    "current_stock": 5,
    "refill_quantity": 50,
    "alert_level": "critical"
  }
}
```

---

### 6. Test N otification Agent - Send Notification
```bash
curl -X POST http://localhost:8000/ai/test/notification \
  -H "Content-Type: application/json" \
  -d '{
    "action": "send_notification",
    "medicine_name": "Paracetamol",
    "customer_phone": "+919876543210",
    "customer_email": "patient@example.com",
    "customer_id": "CUST-001",
    "alert_type": "both"
  }'
```

**Expected Response:**
```json
{
  "agent": "notification",
  "status": "success",
  "message": "Notification sent for Paracetamol",
  "medicine_name": "Paracetamol",
  "notification_sent": true,
  "recipients": {
    "phone": "+919876543210",
    "email": "patient@example.com",
    "customer_id": "CUST-001"
  },
  "n8n_webhook_status": "pending"
}
```

---

### 7. Test Notification Agent - Subscribe to Alerts
```bash
curl -X POST http://localhost:8000/ai/test/notification \
  -H "Content-Type: application/json" \
  -d '{
    "action": "subscribe",
    "customer_id": "CUST-001",
    "customer_phone": "+919876543210",
    "customer_email": "patient@example.com",
    "medicines": ["Paracetamol", "Amoxicillin", "Lisinopril"]
  }'
```

**Expected Response:**
```json
{
  "agent": "notification",
  "status": "success",
  "message": "Successfully subscribed to stock refill alerts",
  "customer_id": "CUST-001",
  "customer_phone": "+919876543210",
  "customer_email": "patient@example.com",
  "subscribed_medicines": ["Paracetamol", "Amoxicillin", "Lisinopril"],
  "subscription_count": 3
}
```

---

### 8. Test Notification Agent - Get Alerts
```bash
curl -X POST http://localhost:8000/ai/test/notification \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get_alerts",
    "customer_id": "CUST-001"
  }'
```

**Expected Response:**
```json
{
  "agent": "notification",
  "status": "success",
  "customer_id": "CUST-001",
  "active_alerts": [
    {
      "id": "ALERT-001",
      "medicine_name": "Paracetamol 500mg",
      "level": "warning",
      "current_stock": 25,
      "threshold": 30,
      "refill_quantity": 100
    },
    {
      "id": "ALERT-002",
      "medicine_name": "Amoxicillin 250mg",
      "level": "critical",
      "current_stock": 5,
      "threshold": 10,
      "refill_quantity": 200
    }
  ],
  "alert_count": 2,
  "critical_alerts": 1,
  "warning_alerts": 1
}
```

---

## API Documentation

Access the interactive Swagger UI at:
```
http://localhost:8000/docs
```

This will show all available endpoints with request/response examples.

---

## What This Tests

✅ **Delivery Agent:**
- Track order delivery status in real-time
- Update delivery stages with automatic notifications
- Get complete delivery history

✅ **Notification Agent:**
- Monitor medicine stock levels
- Detect warning and critical stock situations
- Send notifications to customers
- Manage customer alert subscriptions
- Retrieve active alerts by user

✅ **N8N Integration:**
- Webhook readiness for SMS/Email delivery
- Payload formats for n8n workflows
- Status tracking for notifications

---

## Next Steps

1. ✅ Test all endpoints above
2. Set up n8n instance
3. Configure Twilio/SMTP credentials
4. Import workflow templates from `N8N_INTEGRATION_GUIDE.md`
5. Test SMS/Email delivery
6. Deploy to production

---

## Troubleshooting

If you get errors:
1. Ensure backend is running on port 8000
2. Check all JSON syntax in requests
3. Review backend logs for errors
4. Verify database connection
5. Check n8n workflow logs if SMS/Email not sending

See `INTEGRATION_COMPLETE.md` for detailed troubleshooting guide.
