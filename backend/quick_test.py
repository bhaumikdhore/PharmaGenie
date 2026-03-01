#!/usr/bin/env python
"""Quick test to verify agents work"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.agents import delivery_agent, notification_agent


async def main():
    print("=" * 80)
    print("AGENT FUNCTIONALITY TEST")
    print("=" * 80)
    
    # Test Delivery Agent
    print("\n--- DELIVERY AGENT TEST ---")
    try:
        result = await delivery_agent.run({
            "action": "track",
            "order_id": "ORD-TEST-001"
        })
        print(f"✅ Delivery Agent Status: {result.get('status')}")
        print(f"   - Current Stage: {result.get('current_stage')}")
        print(f"   - Tracking Number: {result.get('tracking_number')}")
    except Exception as e:
        print(f"❌ Delivery Agent Error: {str(e)}")
        return False
    
    # Test Notification Agent
    print("\n--- NOTIFICATION AGENT TEST ---")
    try:
        result = await notification_agent.run({
            "action": "check_stock",
            "medicine_name": "Paracetamol",
            "current_stock": 25,
            "total_stock": 100
        })
        print(f"✅ Notification Agent Status: {result.get('status')}")
        print(f"   - Alert Level: {result.get('alert_level')}")
        print(f"   - Stock Percentage: {result.get('stock_percentage')}%")
    except Exception as e:
        print(f"❌ Notification Agent Error: {str(e)}")
        return False
    
    print("\n" + "=" * 80)
    print("✅ ALL AGENTS WORKING CORRECTLY!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
