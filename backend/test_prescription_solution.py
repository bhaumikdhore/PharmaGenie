#!/usr/bin/env python3
"""
Test Script for Prescription Requirement & Photo Storage System
Tests the new prescription_requirement_agent and prescription_storage API
"""
import asyncio
import httpx
import json
from datetime import datetime

BACKEND_URL = "http://localhost:8000"


async def test_prescription_requirement():
    """Test prescription requirement check"""
    print("\n" + "="*80)
    print("🔬 TESTING PRESCRIPTION REQUIREMENT AGENT")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        test_medicines = [
            "Paracetamol",
            "Azithromycin 250mg",
            "Aspirin 75mg",
            "Losartan 50mg",
            "NonExistentMedicine123"
        ]
        
        for medicine in test_medicines:
            print(f"\n📋 Testing: {medicine}")
            print("-" * 80)
            
            try:
                response = await client.post(
                    f"{BACKEND_URL}/ai/test/prescription-requirement",
                    json={"medicine_name": medicine},
                    headers={"Content-Type": "application/json"}
                )
                
                result = response.json()
                
                if result.get("status") == "success":
                    print(f"  Medicine: {result.get('medicine_name')}")
                    print(f"  Category: {result.get('category')}")
                    print(f"  Requires Prescription: {result.get('requires_prescription')}")
                    print(f"  Can Buy OTC: {result.get('can_buy_without_prescription')}")
                    print(f"  Stock Status: {result.get('stock_status')}")
                    print(f"  Stock Quantity: {result.get('stock_quantity')}")
                    print(f"  ✅ Message: {result.get('message')}")
                elif result.get("status") == "not_found":
                    print(f"  ⚠️ Not Found: {result.get('message')}")
                else:
                    print(f"  ❌ Error: {result.get('message')}")
                
                print(f"  Status Code: {response.status_code}")
                
            except Exception as e:
                print(f"  ❌ Request failed: {str(e)}")


async def test_prescription_storage():
    """Test prescription storage endpoints"""
    print("\n\n" + "="*80)
    print("📸 TESTING PRESCRIPTION STORAGE API")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        
        # Test 1: Get stored prescriptions (no prescriptions yet)
        print("\n1️⃣ GET STORED PRESCRIPTIONS")
        print("-" * 80)
        try:
            response = await client.get(
                f"{BACKEND_URL}/prescriptions/storage/list/CUST-TEST-001"
            )
            result = response.json()
            print(f"  Status: {response.status_code}")
            print(f"  Count: {result.get('count')}")
            print(f"  Response: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
        
        # Test 2: Get prescription for specific medicine
        print("\n2️⃣ GET PRESCRIPTION FOR SPECIFIC MEDICINE")
        print("-" * 80)
        try:
            response = await client.get(
                f"{BACKEND_URL}/prescriptions/storage/medicine/CUST-TEST-001/Paracetamol"
            )
            result = response.json()
            print(f"  Status: {response.status_code}")
            print(f"  Message: {result.get('message')}")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
        
        # Test 3: Get statistics
        print("\n3️⃣ GET PRESCRIPTION STATISTICS")
        print("-" * 80)
        try:
            response = await client.get(
                f"{BACKEND_URL}/prescriptions/storage/stats/CUST-TEST-001"
            )
            result = response.json()
            print(f"  Status: {response.status_code}")
            print(f"  Stats: {json.dumps(result.get('stats'), indent=2)}")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
        
        # Test 4: Cleanup expired
        print("\n4️⃣ CLEANUP EXPIRED PRESCRIPTIONS")
        print("-" * 80)
        try:
            response = await client.post(
                f"{BACKEND_URL}/prescriptions/storage/cleanup"
            )
            result = response.json()
            print(f"  Status: {response.status_code}")
            print(f"  Cleaned: {result.get('count')} prescriptions")
            print(f"  Message: {result.get('message')}")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")


async def test_updated_frontend_flow():
    """Test the complete flow as it would be used in frontend"""
    print("\n\n" + "="*80)
    print("🔄 COMPLETE FRONTEND FLOW TEST")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Simulate user checking if medicine needs prescription
        print("\n1️⃣ USER CHECKS IF MEDICINE NEEDS PRESCRIPTION")
        print("-" * 80)
        
        medicines_to_check = [
            ("Paracetamol", "No prescription needed - can buy directly"),
            ("Azithromycin 250mg", "Prescription required - needs doctor approval"),
        ]
        
        for medicine, expected_result in medicines_to_check:
            print(f"\n  Checking: {medicine}")
            
            try:
                response = await client.post(
                    f"{BACKEND_URL}/ai/test/prescription-requirement",
                    json={"medicine_name": medicine}
                )
                
                result = response.json()
                
                if result.get("status") == "success":
                    if result.get("can_buy_without_prescription"):
                        print(f"    ✅ {medicine} can be purchased without prescription")
                        print(f"       → User can add to cart directly")
                    else:
                        print(f"    📋 {medicine} requires a prescription")
                        print(f"       → System prompts to upload prescription")
                
            except Exception as e:
                print(f"    ❌ Error: {str(e)}")


async def main():
    """Run all tests"""
    try:
        # Test 1: Prescription Requirement Agent
        await test_prescription_requirement()
        
        # Test 2: Prescription Storage API
        await test_prescription_storage()
        
        # Test 3: Complete Flow
        await test_updated_frontend_flow()
        
        # Summary
        print("\n\n" + "="*80)
        print("✨ TEST COMPLETE")
        print("="*80)
        print("""
✅ What was tested:
   1. Prescription Requirement Agent (FIXED safety check issue)
   2. Prescription Storage API endpoints
   3. Complete user flow simulation

📝 Next Steps:
   1. Start backend: python -m uvicorn app.main:app --reload
   2. Run tests from frontend at /dashboard/customer/prescriptions
   3. Verify prescription requirement check works
   4. Test prescription photo upload feature

🔗 API Documentation:
   - Visit http://localhost:8000/docs (Swagger UI)
   - See PRESCRIPTION_SOLUTION_COMPLETE.md for details
        """)
        
    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Tests failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🧪 Prescription Solution Test Suite")
    print("Started at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    asyncio.run(main())
