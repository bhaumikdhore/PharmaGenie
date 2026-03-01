# N8N Workflow Configuration Guide

This file provides instructions for setting up n8n workflows to integrate with the Delivery and Notification agents.

## Prerequisites

1. N8N instance running (self-hosted or cloud)
2. Backend API running and accessible from n8n
3. Configuration of environment variables

## Environment Variables Setup

Add these to your `.env` file in the backend directory:

```env
# N8N Configuration
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/stock-refill-notifications
N8N_BASE_URL=https://your-n8n-instance.com
BACKEND_API_URL=http://your-backend-api:8000
```

## 1. Stock Refill Notification Workflow

### Workflow Name: Stock Refill Notification Trigger

**Trigger:** Webhook from backend `/notifications/check-stock` endpoint

**Flow:**
1. Receive stock level data
2. Check if stock is below threshold
3. If critical: Send SMS (priority 1)
4. If warning: Send Email (priority 2)
5. Log notification in database via webhook
6. Update notification status

### N8N Workflow JSON

```json
{
  "name": "Stock Refill Notification",
  "nodes": [
    {
      "parameters": {
        "protocol": "http",
        "authentication": "basicAuth",
        "method": "POST",
        "url": "={{ $env['BACKEND_API_URL'] }}/notifications/webhook/from-n8n",
        "authentication1": "basicAuth",
        "user": "webhook_user",
        "password": "webhook_password",
        "sendBody": true,
        "bodyType": "json",
        "bodyParameters": {
          "parameters": [
            {
              "name": "notification_id",
              "value": "={{ $node['Parse Notification'].json.notification_id }}"
            },
            {
              "name": "status",
              "value": "={{ $node['Send SMS or Email'].json.status }}"
            },
            {
              "name": "n8n_workflow_id",
              "value": "={{ $workflow.id }}"
            },
            {
              "name": "n8n_execution_id",
              "value": "={{ $execution.id }}"
            }
          ]
        }
      },
      "name": "Report to Backend",
      "type": "n8n-nodes-base.httpRequest"
    },
    {
      "parameters": {
        "jsCode": "// Parse incoming stock alert notification\nconst alert_level = data.alert_level;\nconst medicine_name = data.medicine_name;\nconst current_stock = data.current_stock;\nconst total_stock = data.total_stock;\n\nreturn {\n  notification_id: Math.random().toString(36).substr(2, 9),\n  medicine_name,\n  current_stock,\n  total_stock,\n  alert_level,\n  timestamp: new Date().toISOString()\n};"
      },
      "name": "Parse Notification",
      "type": "n8n-nodes-base.code"
    },
    {
      "parameters": {
        "conditions": {
          "options": {
            "caseSensitive": true,
            "leftValue": "={{ $node['Parse Notification'].json.alert_level }}",
            "operator": {
              "name": "filter.operator.equals",
              "type": "string",
              "operation": "equals"
            },
            "rightValue": "critical"
          }
        },
        "combineOperation": "any"
      },
      "name": "Is Critical Alert?",
      "type": "n8n-nodes-base.if"
    },
    {
      "parameters": {
        "phoneNumber": "={{ $node['Parse Notification'].json.customer_phone }}",
        "message": "URGENT: Your medicine {{ $node['Parse Notification'].json.medicine_name }} stock is critically low! Refill immediately to avoid missing your medication.",
        "twilioCredentials": "twilio_account"
      },
      "name": "Send Critical SMS",
      "type": "n8n-nodes-base.twilio"
    },
    {
      "parameters": {
        "email": "={{ $node['Parse Notification'].json.customer_email }}",
        "subject": "URGENT: Refill Your Medicine NOW",
        "text": "Your medicine stock is critically low"
      },
      "name": "Send Email",
      "type": "n8n-nodes-base.sendEmail"
    },
    {
      "parameters": {
        "httpMethod": "POST",
        "url": "={{ $env['BACKEND_API_URL'] }}/notifications/webhook/from-n8n",
        "sendBody": true,
        "bodyType": "json",
        "bodyParameters": {
          "parameters": [
            {
              "name": "notification_id",
              "value": "={{ $node['Parse Notification'].json.notification_id }}"
            },
            {
              "name": "status",
              "value": "success"
            }
          ]
        }
      },
      "name": "Update Backend",
      "type": "n8n-nodes-base.httpRequest"
    }
  ],
  "connections": {
    "Parse Notification": {
      "main": [
        [
          {
            "node": "Is Critical Alert?",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Is Critical Alert?": {
      "main": [
        [
          {
            "node": "Send Critical SMS",
            "type": "main",
            "index": 0
          }
        ],
        [
          {
            "node": "Send Email",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Send Critical SMS": {
      "main": [
        [
          {
            "node": "Update Backend",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Send Email": {
      "main": [
        [
          {
            "node": "Update Backend",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

## 2. Delivery Status Update Workflow

### Workflow Name: Delivery Status Update

**Trigger:** Webhook when order status changes

**Flow:**
1. Receive delivery status update
2. Update delivery record in database
3. Determine notification type (SMS/Email)
4. Send notification to customer
5. Confirm update in backend

### Setup Instructions

### Step 1: Get Webhook URL from N8N

1. Open n8n instance
2. Create new workflow
3. Add "Webhook" node as first node
4. Copy the webhook URL (format: `https://your-n8n.com/webhook/...`)

### Step 2: Configure Backend Webhook URL

Set the environment variable in `.env`:
```env
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/your-path
```

### Step 3: Configure Credentials in N8N

#### For SMS (Twilio):
1. Go to Credentials → New
2. Select "Twilio"
3. Enter your Twilio Account SID and Auth Token
4. Save with name "twilio_account"

#### For Email:
1. Go to Credentials → New
2. Select "Gmail" or "SMTP"
3. Enter your email credentials
4. Save

### Step 4: Import Workflows

You can import the workflow JSON files provided in this directory into n8n.

### Step 5: Test the Webhook

```bash
# Test delivery tracking webhook
curl -X POST http://localhost:8000/delivery/webhook/from-n8n \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORD-001",
    "new_stage": "in_transit",
    "location": {
      "latitude": 19.0760,
      "longitude": 72.8777,
      "address": "In Transit to Mumbai"
    },
    "notes": "Package on way"
  }'

# Test notification webhook
curl -X POST http://localhost:8000/notifications/webhook/from-n8n \
  -H "Content-Type: application/json" \
  -d '{
    "notification_id": 1,
    "status": "success",
    "n8n_workflow_id": "workflow123",
    "n8n_execution_id": "exec456"
  }'
```

## API Endpoints for N8N Integration

### Notification Endpoints

**Check Stock Level:**
```bash
POST /notifications/check-stock
{
  "medicine_id": 1,
  "medicine_name": "Paracetamol",
  "current_stock": 25,
  "total_stock": 100
}
```

**Send Notification:**
```bash
POST /notifications/send
{
  "medicine_name": "Paracetamol",
  "customer_phone": "+919876543210",
  "customer_email": "user@example.com",
  "alert_type": "both"
}
```

**Subscribe to Alerts:**
```bash
POST /notifications/subscribe
{
  "customer_id": "CUST-001",
  "customer_phone": "+919876543210",
  "customer_email": "user@example.com",
  "medicines": ["Paracetamol", "Amoxicillin"]
}
```

### Delivery Endpoints

**Track Delivery:**
```bash
POST /delivery/track
{
  "order_id": "ORD-001"
}
```

**Update Delivery Status:**
```bash
POST /delivery/update-status
{
  "order_id": "ORD-001",
  "new_stage": "in_transit",
  "customer_phone": "+919876543210"
}
```

**Get Delivery History:**
```bash
POST /delivery/history
{
  "order_id": "ORD-001"
}
```

## N8N Webhook Receiver Endpoints

### Delivery Webhook
```
POST /delivery/webhook/from-n8n
```

Expected payload:
```json
{
  "order_id": "ORD-001",
  "new_stage": "delivered",
  "location": {
    "latitude": 19.0760,
    "longitude": 72.8777,
    "address": "Customer location"
  },
  "notes": "Delivered successfully"
}
```

### Notification Webhook
```
POST /notifications/webhook/from-n8n
```

Expected payload:
```json
{
  "notification_id": 1,
  "status": "success",
  "n8n_workflow_id": "workflow_id",
  "n8n_execution_id": "execution_id"
}
```

## Troubleshooting

### Webhook Not Being Called
1. Check if N8N URL is accessible from backend
2. Verify firewall rules
3. Check n8n workflow logs
4. Ensure webhook authentication is correct

### Notification Not Sending
1. Verify Twilio/Email credentials in n8n
2. Check customer phone/email in database
3. Review n8n execution logs
4. Check backend notification logs

### Database Updates Not Reflected
1. Ensure database migrations are run
2. Check database connection in backend
3. Verify webhook payload format

## Production Deployment

1. Use environment variables for all credentials
2. Enable webhook authentication in n8n
3. Set up proper logging and monitoring
4. Configure rate limiting
5. Use HTTPS for all webhooks
6. Set up backup webhook handler
7. Monitor webhook delivery status

## References

- [N8N Documentation](https://docs.n8n.io/)
- [Twilio SMS Integration](https://docs.n8n.io/nodes/n8n-nodes-base.twilio/)
- [SMTP Email](https://docs.n8n.io/nodes/n8n-nodes-base.sendEmail/)
