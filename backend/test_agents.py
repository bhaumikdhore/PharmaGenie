"""
Test script for delivery and notification agents with n8n integration
Run this after starting the backend server: python test_agents.py
"""

import asyncio
import httpx
import json
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}


async def test_delivery_agent():
    """Test delivery tracking agent"""
    print("\n" + "="*60)
    print("TESTING DELIVERY AGENT")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        # Test 1: Track delivery
        print("\n1. Testing delivery tracking...")
        payload = {
            "action": "track",
            "order_id": "ORD-12345"
        }
        
        response = await client.post(
            f"{BACKEND_URL}/ai/test/delivery",
            json=payload,
            headers=HEADERS
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Test 2: Update delivery status
        print("\n2. Testing delivery status update...")
        payload = {
            "action": "update_status",
            "order_id": "ORD-12345",
            "new_stage": "dispatched",
            "customer_phone": "+919876543210"
        }
        
        response = await client.post(
            f"{BACKEND_URL}/ai/test/delivery",
            json=payload,
            headers=HEADERS
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Test 3: Get delivery history
        print("\n3. Testing delivery history...")
        payload = {
            "action": "get_history",
            "order_id": "ORD-12345"
        }
        
        response = await client.post(
            f"{BACKEND_URL}/ai/test/delivery",
            json=payload,
            headers=HEADERS
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")


async def test_notification_agent():
    """Test notification agent"""
    print("\n" + "="*60)
    print("TESTING NOTIFICATION AGENT")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        # Test 1: Check stock levels
        print("\n1. Testing stock level check...")
        payload = {
            "action": "check_stock",
            "medicine_id": 1,
            "medicine_name": "Paracetamol",
            "current_stock": 25,
            "total_stock": 100
        }
        
        response = await client.post(
            f"{BACKEND_URL}/ai/test/notification",
            json=payload,
            headers=HEADERS
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Test 2: Send notification
        print("\n2. Testing send notification...")
        payload = {
            "action": "send_notification",
            "medicine_name": "Paracetamol",
            "customer_phone": "+919876543210",
            "customer_email": "user@example.com",
            "customer_id": "CUST-001",
            "alert_type": "both"
        }
        
        response = await client.post(
            f"{BACKEND_URL}/ai/test/notification",
            json=payload,
            headers=HEADERS
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Test 3: Subscribe to alerts
        print("\n3. Testing subscription...")
        payload = {
            "action": "subscribe",
            "customer_id": "CUST-001",
            "customer_phone": "+919876543210",
            "customer_email": "user@example.com",
            "medicines": ["Paracetamol", "Amoxicillin"]
        }
        
        response = await client.post(
            f"{BACKEND_URL}/ai/test/notification",
            json=payload,
            headers=HEADERS
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Test 4: Get active alerts
        print("\n4. Testing get alerts...")
        payload = {
            "action": "get_alerts",
            "customer_id": "CUST-001"
        }
        
        response = await client.post(
            f"{BACKEND_URL}/ai/test/notification",
            json=payload,
            headers=HEADERS
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")


async def test_delivery_routes():
    """Test delivery routes"""
    print("\n" + "="*60)
    print("TESTING DELIVERY ROUTES")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        # Test 1: Track via route
        print("\n1. Testing /delivery/track route...")
        payload = {
            "order_id": "ORD-99999"
        }
        
        response = await client.post(
            f"{BACKEND_URL}/delivery/track",
            json=payload,
            headers=HEADERS
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Error: {response.text}")
        
        # Test 2: Get stages
        print("\n2. Testing /delivery/stages route...")
        response = await client.get(f"{BACKEND_URL}/delivery/stages")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Test 3: Health check
        print("\n3. Testing /delivery/health route...")
        response = await client.get(f"{BACKEND_URL}/delivery/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")


async def test_notification_routes():
    """Test notification routes"""
    print("\n" + "="*60)
    print("TESTING NOTIFICATION ROUTES")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        # Test 1: Check stock via route
        print("\n1. Testing /notifications/check-stock route...")
        payload = {
            "medicine_name": "Amoxicillin",
            "current_stock": 8,
            "total_stock": 100
        }
        
        response = await client.post(
            f"{BACKEND_URL}/notifications/check-stock",
            json=payload,
            headers=HEADERS
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Error: {response.text}")
        
        # Test 2: Get templates
        print("\n2. Testing /notifications/templates route...")
        response = await client.get(f"{BACKEND_URL}/notifications/templates")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Test 3: Get statistics
        print("\n3. Testing /notifications/statistics route...")
        response = await client.get(f"{BACKEND_URL}/notifications/statistics")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Test 4: Health check
        print("\n4. Testing /notifications/health route...")
        response = await client.get(f"{BACKEND_URL}/notifications/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")


async def test_webhook_simulation():
    """Simulate n8n webhook calls"""
    print("\n" + "="*60)
    print("TESTING WEBHOOK SIMULATION (N8N)")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        # Test 1: Delivery webhook
        print("\n1. Simulating delivery webhook from n8n...")
        payload = {
            "order_id": "ORD-12345",
            "new_stage": "out_for_delivery",
            "location": {
                "latitude": 19.0760,
                "longitude": 72.8777,
                "address": "Out for delivery - Mumbai"
            },
            "notes": "Driver on the way",
            "customer_id": "CUST-001"
        }
        
        response = await client.post(
            f"{BACKEND_URL}/delivery/webhook/from-n8n",
            json=payload,
            headers=HEADERS
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Test 2: Notification webhook
        print("\n2. Simulating notification webhook from n8n...")
        payload = {
            "notification_id": 1,
            "status": "success",
            "n8n_workflow_id": "n8n_workflow_123",
            "n8n_execution_id": "n8n_exec_456"
        }
        
        response = await client.post(
            f"{BACKEND_URL}/notifications/webhook/from-n8n",
            json=payload,
            headers=HEADERS
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("DELIVERY AND NOTIFICATION AGENTS - COMPREHENSIVE TEST SUITE")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Backend URL: {BACKEND_URL}")
    
    try:
        # Test agents
        await test_delivery_agent()
        await test_notification_agent()
        
        # Test routes
        await test_delivery_routes()
        await test_notification_routes()
        
        # Test webhook simulation
        await test_webhook_simulation()
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
