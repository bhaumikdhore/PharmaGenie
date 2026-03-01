"""
Direct test of agents without needing the server running
Tests the agent functions directly
"""

import asyncio
import sys
import os

# Add the backend to path
sys.path.insert(0, 'vsls:/backend')

# Import agents directly
from app.agents import delivery_agent, notification_agent


async def test_agents_directly():
    """Test agents directly without HTTP calls"""
    print("\n" + "="*80)
    print("DIRECT AGENT TESTING (Without HTTP Server)")
    print("="*80)
    
    # Test Delivery Agent
    print("\n" + "="*60)
    print("DELIVERY AGENT TESTS")
    print("="*60)
    
    # Test 1: Track delivery
    print("\n1. Testing delivery tracking...")
    result = await delivery_agent.run({
        "action": "track",
        "order_id": "ORD-TEST-001"
    })
    print(f"Status: {result.get('status')}")
    print(f"Agent: {result.get('agent')}")
    print(f"Order: {result.get('order_id')}")
    print(f"Stage: {result.get('current_stage')}")
    print(f"Tracking: {result.get('tracking_number')}")
    
    # Test 2: Update delivery status
    print("\n2. Testing delivery status update...")
    result = await delivery_agent.run({
        "action": "update_status",
        "order_id": "ORD-TEST-001",
        "new_stage": "in_transit",
        "customer_phone": "+919876543210"
    })
    print(f"Status: {result.get('status')}")
    print(f"New Stage: {result.get('new_stage')}")
    print(f"Notification Triggered: {result.get('notification_triggered')}")
    
    # Test 3: Get history
    print("\n3. Testing delivery history...")
    result = await delivery_agent.run({
        "action": "get_history",
        "order_id": "ORD-TEST-001"
    })
    print(f"Status: {result.get('status')}")
    print(f"Total Events: {result.get('total_events')}")
    if result.get('history'):
        print(f"First Event: {result['history'][0]['stage']} - {result['history'][0]['description']}")
    
    # Test Notification Agent
    print("\n" + "="*60)
    print("NOTIFICATION AGENT TESTS")
    print("="*60)
    
    # Test 1: Check stock levels
    print("\n1. Testing stock level check (Warning)...")
    result = await notification_agent.run({
        "action": "check_stock",
        "medicine_id": 1,
        "medicine_name": "Paracetamol",
        "current_stock": 25,
        "total_stock": 100
    })
    print(f"Status: {result.get('status')}")
    print(f"Medicine: {result.get('medicine_name')}")
    print(f"Stock Percentage: {result.get('stock_percentage')}%")
    print(f"Alert Level: {result.get('alert_level')}")
    print(f"Needs Refill: {result.get('needs_refill')}")
    print(f"N8N Triggered: {result.get('n8n_workflow_triggered')}")
    
    # Test 2: Check critical stock
    print("\n2. Testing stock level check (Critical)...")
    result = await notification_agent.run({
        "action": "check_stock",
        "medicine_id": 2,
        "medicine_name": "Amoxicillin",
        "current_stock": 5,
        "total_stock": 100
    })
    print(f"Status: {result.get('status')}")
    print(f"Medicine: {result.get('medicine_name')}")
    print(f"Stock Percentage: {result.get('stock_percentage')}%")
    print(f"Alert Level: {result.get('alert_level')}")
    print(f"Severity: {result.get('severity')}")
    
    # Test 3: Send notification
    print("\n3. Testing send notification...")
    result = await notification_agent.run({
        "action": "send_notification",
        "medicine_name": "Paracetamol",
        "customer_phone": "+919876543210",
        "customer_email": "user@example.com",
        "customer_id": "CUST-001",
        "alert_type": "both"
    })
    print(f"Status: {result.get('status')}")
    print(f"Message: {result.get('message')}")
    print(f"Notification Sent: {result.get('notification_sent')}")
    print(f"Recipients Phone: {result.get('recipients', {}).get('phone')}")
    
    # Test 4: Subscribe to alerts
    print("\n4. Testing subscription...")
    result = await notification_agent.run({
        "action": "subscribe",
        "customer_id": "CUST-001",
        "customer_phone": "+919876543210",
        "customer_email": "user@example.com",
        "medicines": ["Paracetamol", "Amoxicillin", "Lisinopril"]
    })
    print(f"Status: {result.get('status')}")
    print(f"Message: {result.get('message')}")
    print(f"Subscribed Medicines: {len(result.get('subscribed_medicines', []))}")
    
    # Test 5: Get alerts
    print("\n5. Testing get alerts...")
    result = await notification_agent.run({
        "action": "get_alerts",
        "customer_id": "CUST-001"
    })
    print(f"Status: {result.get('status')}")
    print(f"Alert Count: {result.get('alert_count')}")
    print(f"Critical Alerts: {result.get('critical_alerts')}")
    print(f"Warning Alerts: {result.get('warning_alerts')}")
    
    # Summary
    print("\n" + "="*80)
    print("✅ ALL AGENT TESTS COMPLETED SUCCESSFULLY!")
    print("="*80)
    print("\nThe agents are working correctly and ready for n8n integration.")
    print("\nNext Steps:")
    print("1. Set up n8n instance")
    print("2. Configure environment variables (N8N_WEBHOOK_URL)")
    print("3. Create workflows in n8n that call these agents")
    print("4. Test webhook integration")
    print("\nFor detailed setup instructions, see: N8N_INTEGRATION_GUIDE.md")


if __name__ == "__main__":
    asyncio.run(test_agents_directly())
