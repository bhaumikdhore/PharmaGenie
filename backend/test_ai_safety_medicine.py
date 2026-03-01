#!/usr/bin/env python3
"""
Test AI Safety Medicine Check Agent
Tests the new AI-powered medicine safety checking system
"""
import asyncio
import httpx
import json
from datetime import datetime

BACKEND_URL = "http://localhost:8000"


async def test_ai_safety_medicine():
    """Test AI safety medicine check"""
    print("\n" + "="*80)
    print("🤖 AI MEDICINE SAFETY CHECK - TESTS")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        
        # Restricted medicines to test
        restricted_medicines = [
            ("Morphine 10mg", "Restricted opioid"),
            ("Codeine 30mg", "Restricted opioid"),
            ("Alprazolam 0.5mg", "Restricted benzodiazepine"),
            ("Fentanyl patch", "Restricted opioid"),
            ("Lithium 300mg", "Restricted mood stabilizer"),
        ]
        
        # Non-restricted medicines to test
        safe_medicines = [
            ("Paracetamol 500mg", "Common pain reliever"),
            ("Aspirin 75mg", "Common anticoagulant"),
            ("Amoxicillin 500mg", "Common antibiotic"),
            ("Vitamin D3 1000IU", "Common supplement"),
            ("Ibuprofen 400mg", "Common pain reliever"),
        ]
        
        print("\n📋 RESTRICTED MEDICINES (Should show ⏹️ RESTRICTED)")
        print("-" * 80)
        
        for medicine, desc in restricted_medicines:
            print(f"\n  Testing: {medicine} ({desc})")
            
            try:
                response = await client.post(
                    f"{BACKEND_URL}/ai/test/ai-safety-medicine",
                    json={"medicine_name": medicine},
                    headers={"Content-Type": "application/json"}
                )
                
                result = response.json()
                
                if result.get("status") == "success":
                    approval = result.get("approval_status")
                    analysis = result.get("ai_analysis", "")[:100]
                    source = result.get("source", "unknown")
                    
                    print(f"    {approval}")
                    print(f"    Analysis: {analysis}...")
                    print(f"    Source: {source}")
                    
                    # Verify it's marked as restricted
                    if "RESTRICTED" in approval:
                        print(f"    ✅ Correctly marked as RESTRICTED")
                    else:
                        print(f"    ❌ ERROR: Should be RESTRICTED!")
                        
                else:
                    print(f"    ❌ Error: {result.get('message')}")
                    
            except Exception as e:
                print(f"    ❌ Request failed: {str(e)}")
        
        print("\n\n✅ SAFE MEDICINES (Should show ✅ APPROVED)")
        print("-" * 80)
        
        for medicine, desc in safe_medicines:
            print(f"\n  Testing: {medicine} ({desc})")
            
            try:
                response = await client.post(
                    f"{BACKEND_URL}/ai/test/ai-safety-medicine",
                    json={"medicine_name": medicine},
                    headers={"Content-Type": "application/json"}
                )
                
                result = response.json()
                
                if result.get("status") == "success":
                    approval = result.get("approval_status")
                    analysis = result.get("ai_analysis", "")[:100]
                    source = result.get("source", "unknown")
                    
                    print(f"    {approval}")
                    print(f"    Analysis: {analysis}...")
                    print(f"    Source: {source}")
                    
                    # Verify it's marked as approved
                    if "APPROVED" in approval:
                        print(f"    ✅ Correctly marked as APPROVED")
                    else:
                        print(f"    ❌ ERROR: Should be APPROVED!")
                        
                else:
                    print(f"    ❌ Error: {result.get('message')}")
                    
            except Exception as e:
                print(f"    ❌ Request failed: {str(e)}")
        
        # Test prescription validation
        print("\n\n📋 PRESCRIPTION VALIDATION TEST")
        print("-" * 80)
        print("\n  Testing prescription with mixed medicines...")
        
        try:
            response = await client.post(
                f"{BACKEND_URL}/ai/test/ai-safety-medicine",
                json={
                    "action": "validate",
                    "medicines": [
                        {"name": "Paracetamol", "dosage": "500mg"},
                        {"name": "Amoxicillin", "dosage": "500mg"},
                        {"name": "Vitamin D3", "dosage": "1000IU"},
                    ]
                },
                headers={"Content-Type": "application/json"}
            )
            
            result = response.json()
            
            if result.get("status") == "success":
                print(f"    Overall: {result.get('overall_status')}")
                print(f"    Total medicines: {result.get('total_medicines')}")
                print(f"    Approved count: {result.get('approved_count')}")
                print(f"    Restricted count: {result.get('restricted_count')}")
                print(f"    ✅ Prescription result: {'APPROVED' if result.get('prescription_approved') else 'CONTAINS RESTRICTED'}")
            else:
                print(f"    ❌ Error: {result.get('message')}")
                
        except Exception as e:
            print(f"    ❌ Request failed: {str(e)}")


async def test_ollama_status():
    """Check if Ollama is available"""
    print("\n\n🔧 OLLAMA STATUS CHECK")
    print("-" * 80)
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            
            if response.status_code == 200:
                print("  ✅ Ollama is RUNNING")
                print("  Available models will use AI analysis")
                models = response.json().get("models", [])
                if models:
                    print(f"  Found {len(models)} model(s)")
                else:
                    print("  ⚠️ No models installed (fallback to rule-based)")
            else:
                print("  ⚠️ Ollama returned error status")
    except:
        print("  ⏹️ Ollama is NOT RUNNING")
        print("  Will use rule-based safety check (15 restricted medicines list)")


async def main():
    """Run all tests"""
    try:
        print("🧪 AI Medicine Safety Check - Test Suite")
        print("Started at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Check Ollama status first
        await test_ollama_status()
        
        # Run safety tests
        await test_ai_safety_medicine()
        
        # Summary
        print("\n\n" + "="*80)
        print("✨ RESTRICTED MEDICINES LIST (15 items)")
        print("="*80)
        print("""
        1.  Morphine
        2.  Codeine
        3.  Tramadol
        4.  Fentanyl
        5.  Oxycodone
        6.  Alprazolam
        7.  Diazepam
        8.  Lorazepam
        9.  Methadone
        10. Barbiturates
        11. Benzodiazepines
        12. Amphetamine
        13. Methylphenidate
        14. Steroids
        15. Lithium
        
        All other medicines are considered SAFE/APPROVED.
        """)
        
        print("="*80)
        print("✨ TEST COMPLETE")
        print("="*80)
        print("""
✅ What was tested:
   1. AI Safety Medicine Check Agent
   2. 5 Restricted medicines (should show ⏹️ RESTRICTED)
   3. 5 Safe medicines (should show ✅ APPROVED)
   4. Prescription validation with multiple medicines
   5. Ollama availability check

📝 Next Steps:
   1. Start Ollama (optional): ollama serve
   2. Start backend: python -m uvicorn app.main:app --reload
   3. Visit http://localhost:3000/dashboard/customer/prescriptions
   4. Test "AI Medicine Safety Check" section
   5. Enter restricted medicine name (e.g., "Morphine")
   6. Should show ⏹️ RESTRICTED status

🔗 API Endpoint:
   POST /ai/test/ai-safety-medicine
   - Input: medicine_name, dosage (optional)
   - Output: is_approved, approval_status, ai_analysis
        """)
        
    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Tests failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
