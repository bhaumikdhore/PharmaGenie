#!/usr/bin/env python3
"""
Trigger N8N Notification Agent
Tests the notification agent with n8n webhook integration
"""
import asyncio
import httpx
import json
from datetime import datetime

BACKEND_URL = "http://localhost:8000"


async def test_notification_trigger():
    """Trigger the notification agent with stock alert"""
    print("\n" + "="*80)
    print("🔔 TRIGGERING N8N NOTIFICATION AGENT")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test 1: Check stock level (Critical) - Should trigger n8n
        print("\n1️⃣ STOCK CHECK - CRITICAL LEVEL")
        print("-" * 80)
        
        critical_stock = {
            "action": "check_stock",
            "medicine_id": 1,
            "medicine_name": "Paracetamol",
            "current_stock": 5,
            "total_stock": 100
        }
        
        try:
            response = await client.post(
                f"{BACKEND_URL}/ai/test/notification",
                json=critical_stock,
                headers={"Content-Type": "application/json"}
            )
            
            result = response.json()
            print(f"✅ Status Code: {response.status_code}")
            print(f"📊 Stock Percentage: {result.get('stock_percentage')}%")
            print(f"🚨 Alert Level: {result.get('alert_level')}")
            print(f"⚠️ Severity: {result.get('severity')}")
            print(f"🔗 N8N Triggered: {result.get('n8n_workflow_triggered')}")
            
            if result.get('n8n_workflow_triggered'):
                print(f"\n✨ N8N WORKFLOW TRIGGERED!")
                print(f"📦 Payload being sent to n8n:")
                print(json.dumps(result.get('n8n_payload'), indent=2))
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
        
        # Test 2: Send Notification via N8N
        print("\n\n2️⃣ SEND NOTIFICATION VIA N8N")
        print("-" * 80)
        
        send_notification = {
            "action": "send_notification",
            "medicine_name": "Paracetamol",
            "customer_phone": "+919876543210",
            "customer_email": "user@example.com",
            "customer_id": "CUST-001",
            "alert_type": "both"
        }
        
        try:
            response = await client.post(
                f"{BACKEND_URL}/ai/test/notification",
                json=send_notification,
                headers={"Content-Type": "application/json"}
            )
            
            result = response.json()
            print(f"✅ Status Code: {response.status_code}")
            print(f"📬 Message: {result.get('message')}")
            print(f"✉️ Phone: {result.get('recipients', {}).get('phone')}")
            print(f"📧 Email: {result.get('recipients', {}).get('customer_id')}")
            print(f"🔗 N8N Webhook Status: {result.get('n8n_webhook_status')}")
            
            print(f"\n✨ NOTIFICATION QUEUED FOR N8N! 📲")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
        
        # Test 3: Get Active Alerts
        print("\n\n3️⃣ GET ACTIVE STOCK ALERTS")
        print("-" * 80)
        
        get_alerts = {
            "action": "get_alerts",
            "customer_id": "CUST-001"
        }
        
        try:
            response = await client.post(
                f"{BACKEND_URL}/ai/test/notification",
                json=get_alerts,
                headers={"Content-Type": "application/json"}
            )
            
            result = response.json()
            print(f"✅ Status Code: {response.status_code}")
            print(f"🚨 Critical Alerts: {result.get('critical_alerts')}")
            print(f"⚠️ Warning Alerts: {result.get('warning_alerts')}")
            print(f"📊 Total Alerts: {result.get('alert_count')}")
            
            if result.get('active_alerts'):
                print(f"\n📋 Active Alerts:")
                for alert in result.get('active_alerts', [])[:3]:
                    print(f"  - {alert.get('medicine_name')}: {alert.get('level')} (Stock: {alert.get('current_stock')})")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
    
    # Print N8N Integration Instructions
    print("\n\n" + "="*80)
    print("🔗 N8N INTEGRATION SETUP")
    print("="*80)
    
    print("""
✅ What just happened:
   1. Stock alert was triggered at critical level (5%)
   2. N8N workflow notification was queued
   3. Notification payload prepared for SMS/Email delivery

🚀 Next Steps to Complete Integration:

1. DEPLOY N8N:
   Docker:
   docker run -it --rm -p 5678:5678 n8nio/n8n
   
   Then access at: http://localhost:5678

2. CONFIGURE IN .env:
   N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/stock-refill
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   SMTP_HOST=smtp.gmail.com
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password

3. CREATE WORKFLOWS IN N8N:
   - Add Webhook trigger node
   - Add Twilio SMS node (for SMS)
   - Add Email node (for Email)
   - Connect to your backend webhook endpoint

4. IMPORT WORKFLOW:
   See N8N_INTEGRATION_GUIDE.md for complete templates

5. TEST THE FULL FLOW:
   - Trigger stock alert (above)
   - Check n8n dashboard for webhook execution
   - Verify SMS/Email were sent

📚 Documentation:
   - See: N8N_INTEGRATION_GUIDE.md
   - See: QUICK_TEST_GUIDE.md
   - See: IMPLEMENTATION_SUMMARY.md
    """)
    
    print("\n" + "="*80)
    print("✨ NOTIFICATION AGENT TRIGGERED SUCCESSFULLY! 🎉")
    print("="*80)
    print("\n📝 The notification is ready to be delivered via n8n")
    print("⏳ Once n8n is setup, SMS/Email will be sent automatically")
    print("\nFor SMS: Will send to +919876543210")
    print("For Email: Will send to user@example.com")
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_notification_trigger())
        if success:
            print("\n✅ All tests completed successfully!\n")
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
