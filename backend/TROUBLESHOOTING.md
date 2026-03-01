# 🐛 Troubleshooting Guide - AI Medicine Safety Check

## Common Issues & Solutions

---

## ❌ "Failed to fetch" Error

### Symptom
- Browser shows: "Failed to fetch"
- No response from medicine safety check
- Console shows: `TypeError: Failed to fetch`

### Root Cause
Backend server is not running.

### Solution

**Step 1: Check if backend is running**
```bash
curl http://localhost:8000/health
```

If you see error like `Connection refused`, proceed to Step 2.

**Step 2: Start the backend server**
```bash
cd backend
python -m uvicorn app.main:app --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

**Step 3: Test again**
- Refresh browser page
- Try checking a medicine again

---

## ❌ Everything Shows as "APPROVED"

### Symptom
- Even restricted medicines show: **✅ APPROVED**
- Even "Morphine" shows: **✅ APPROVED**
- This shouldn't happen

### Root Cause
Usually means the API call isn't reaching the AI Safety Medicine agent.

### Solution

**Step 1: Verify endpoint is correct**
```bash
# Should return 200 status
curl -X POST http://localhost:8000/ai/test/ai-safety-medicine \
  -H "Content-Type: application/json" \
  -d '{"medicine_name": "Morphine"}'
```

**Step 2: Check backend logs**
Look at terminal where you ran `uvicorn`:
```
POST /ai/test/ai-safety-medicine
```

If you don't see this, the frontend is calling wrong endpoint.

**Step 3: Verify frontend is calling correct endpoint**
Open Browser DevTools → Network tab → Click "Check Safety"

Should show:
```
POST /ai/test/ai-safety-medicine
Status: 200
```

If showing different endpoint, frontend code wasn't updated correctly.

**Step 4: Hard refresh browser**
```
Windows: Ctrl + Shift + R
Mac: Cmd + Shift + R
```

---

## ❌ "Ollama not available" / Very Slow Response

### Symptom
- Responses taking 5+ seconds
- Or messages about Ollama not connecting
- Source shows: `"source": "rule_based"` (not AI)

### Root Cause
Either:
1. Ollama is not installed (OK - fallback is working)
2. Ollama is installed but not running

### Solution

**Option A: If you don't want AI analysis (OK!)**
- Keep using rule-based (it works perfectly!)
- No action needed
- System will always use restricted medicines list

**Option B: If you want AI analysis**

**Step 1: Install Ollama**
```bash
# macOS/Linux
curl https://ollama.ai/install.sh | sh

# Windows
Download from https://ollama.ai and run installer
```

**Step 2: Start Ollama**
```bash
ollama serve
```

**Expected Output:**
```
Listening on 127.0.0.1:11434
```

**Step 3: Pull Mistral model (first time only)**
```bash
ollama pull mistral
```

**Takes 15-30 minutes first time** (4GB download)

**Step 4: Test Ollama is working**
```bash
curl http://localhost:11434/api/tags
```

**Should return:**
```json
{
  "models": [
    {
      "name": "mistral:latest",
      ...
    }
  ]
}
```

**Step 5: Restart backend + test**
```bash
# In backend terminal: Ctrl+C
# Then restart:
python -m uvicorn app.main:app --reload

# In browser: Test again
# Should now show: "source": "ollama_ai"
```

---

## ❌ Medicine Not Recognized / Wrong Result

### Symptom
- Medicine name you entered shows as APPROVED but should be RESTRICTED
- Or vice versa
- Result doesn't seem right

### Root Cause
- Medicine name spelling might not match exactly
- Medicine might have different name in database

### Solution

**Step 1: Check restricted medicines list**
Only these 15 medicines are RESTRICTED:
1. Morphine
2. Codeine
3. Tramadol
4. Fentanyl
5. Oxycodone
6. Alprazolam
7. Diazepam
8. Lorazepam
9. Methadone
10. Barbiturates
11. Benzodiazepines
12. Amphetamine
13. Methylphenidate
14. Steroids
15. Lithium

**Step 2: Check spelling**
```bash
# Try exact name:
curl -X POST http://localhost:8000/ai/test/ai-safety-medicine \
  -H "Content-Type: application/json" \
  -d '{"medicine_name": "Morphine"}'

# Try lowercase:
-d '{"medicine_name": "morphine"}'

# Try with spaces:
-d '{"medicine_name": "Morphine Sulfate"}'
```

**Step 3: Try with Ollama**
If you have Ollama running, AI might recognize variants:
```
"morphine 10mg" → Recognized as Morphine (RESTRICTED)
"Tramadol XR" → Recognized as Tramadol (RESTRICTED)
```

---

## ❌ API Returns 500 Error

### Symptom
- Browser shows: `500 Internal Server Error`
- API call fails
- Backend terminal shows: `ValueError` or exception

### Root Cause
- Syntax error in agent code
- Missing import
- Database connection issue

### Solution

**Step 1: Check backend logs**
Look at terminal where `uvicorn` is running:
```
ERROR: Exception in ASGI application
Traceback (most recent call last):
  File "app/agents/ai_safety_medicine.py", line X
    ...
```

**Step 2: Common fixes**

If error mentions `ai_safety_medicine`:
```bash
# Verify file exists:
ls -la backend/app/agents/ai_safety_medicine.py

# Check syntax:
python -m py_compile backend/app/agents/ai_safety_medicine.py
```

If error mentions import:
```bash
# Verify it's imported in app/routes/ai.py:
grep "ai_safety_medicine" backend/app/routes/ai.py

# Should show:
# from app.agents import ai_safety_medicine
```

**Step 3: Restart backend**
```bash
# Press Ctrl+C in backend terminal
# Then restart:
python -m uvicorn app.main:app --reload
```

---

## ❌ "Failed to load configuration" or Import Errors

### Symptom
- Backend won't start
- Error: `ModuleNotFoundError`
- Error: `ImportError`

### Root Cause
- Python dependencies not installed
- File not in correct location
- Python version mismatch

### Solution

**Step 1: Verify Python version**
```bash
python --version
# Should be: Python 3.9+
```

**Step 2: Install dependencies**
```bash
cd backend
pip install -r requirements.txt
```

**Step 3: Verify file exists**
```bash
# Windows
dir app\agents\ai_safety_medicine.py

# Mac/Linux
ls -la app/agents/ai_safety_medicine.py
```

**Step 4: Try importing directly**
```bash
python -c "from app.agents import ai_safety_medicine; print('OK')"
```

Should output: `OK`

---

## ❌ Frontend Page Doesn't Show Medicine Check Section

### Symptom
- Prescriptions page loads but no "AI Medicine Safety Check" section
- Can't find where to input medicine name

### Root Cause
- Frontend file wasn't updated correctly
- Browser cache issue
- Component isn't rendering

### Solution

**Step 1: Hard refresh browser**
```
Windows: Ctrl + Shift + R
Mac: Cmd + Shift + R
```

**Step 2: Check DevTools console for errors**
Open: DevTools → Console tab

Should NOT show red errors.

If shows errors about:
- `runSafetyCheck is not defined` → Frontend file not updated
- `fetch is not defined` → JavaScript environment issue

**Step 3: Verify frontend file was updated**
```bash
cd frontend
grep "ai-safety-medicine" frontend/app/dashboard/customer/prescriptions/page.tsx
```

Should return multiple lines with endpoint.

**Step 4: Clear frontend cache**
```bash
# Kill frontend server (Ctrl+C)
# Delete cache:
rm -rf .next

# Restart:
npm run dev
```

---

## ❌ Slow Response (5+ Seconds)

### Symptom
- Every check takes 5-10 seconds
- Page feels sluggish
- Loading spinner spins for long time

### Is This a Problem?
**No!** If you see:
```
"source": "ollama_ai"
```

This is **expected behavior**. AI analysis takes 2-5 seconds.

### To Make It Faster

**Option 1: Use rule-based (instant)**
- Uninstall Ollama or don't start it
- System uses rule-based (<100ms response)

**Option 2: Upgrade Ollama model**
```bash
ollama pull neural-chat  # Faster than mistral
```

**Option 3: Use faster hardware**
- AI analysis = CPU-intensive
- Faster CPU = faster responses

---

## ❌ Testing Fails / Test Script Errors

### Symptom
Running this fails:
```bash
python test_ai_safety_medicine.py
```

With errors like:
- `AssertionError: is_approved is False`
- `asyncio.TimeoutError`
- `ConnectionRefusedError`

### Solution

**Step 1: Verify backend is running**
```bash
curl http://localhost:8000/health
```

**Step 2: Run individual medicine checks**
```bash
python -c "
from app.agents.ai_safety_medicine import check_medicine_safety_with_ollama
import asyncio

result = asyncio.run(check_medicine_safety_with_ollama('Morphine'))
print(result['is_approved'])  # Should be False
"
```

**Step 3: Check Ollama (if using AI)**
```bash
curl http://localhost:11434/api/tags
```

**Step 4: Run test with more info**
```bash
python -u test_ai_safety_medicine.py 2>&1 | head -50
```

---

## ✅ Verification Checklist

Is everything working? Verify these:

- [ ] Backend starts without errors
  ```bash
  python -m uvicorn app.main:app --reload
  ```

- [ ] Frontend loads
  ```bash
  http://localhost:3000/dashboard/customer/prescriptions
  ```

- [ ] API responds
  ```bash
  curl -X POST http://localhost:8000/ai/test/ai-safety-medicine \
    -H "Content-Type: application/json" \
    -d '{"medicine_name": "Morphine"}'
  ```

- [ ] "Morphine" shows ⏹️ RESTRICTED
  - Result: `is_approved: false`

- [ ] "Paracetamol" shows ✅ APPROVED
  - Result: `is_approved: true`

---

## 🆘 Still Not Working?

### Gather Information

**Step 1: Get backend status**
```bash
curl -v http://localhost:8000/ai/test/ai-safety-medicine \
  -H "Content-Type: application/json" \
  -d '{"medicine_name": "test"}'
```

**Step 2: Copy-paste entire response**
(Include headers + body)

**Step 3: Check backend logs**
Paste last 20 lines from backend terminal

**Step 4: Check frontend console**
Open DevTools → Console → Copy any errors

### For Support
Provide:
1. Full API response (from Step 1 above)
2. Backend logs (from Step 3 above)
3. Browser console errors (from Step 4 above)
4. Your OS and Python version
   ```bash
   python --version
   # macOS: system_profiler SPSoftwareDataType
   # Windows: ver
   ```

---

## 🔧 Emergency Restart

If everything is broken:

**Step 1: Kill all processes**
```bash
# Python backend
# Press Ctrl+C in backend terminal

# Node frontend
# Press Ctrl+C in frontend terminal

# Ollama (optional)
# Press Ctrl+C in ollama terminal
```

**Step 2: Clean rebuild**
```bash
# Backend
cd backend
rm -rf __pycache__ .pytest_cache
pip install -r requirements.txt --force-reinstall

# Frontend
cd frontend
rm -rf node_modules .next package-lock.json
npm install
```

**Step 3: Start fresh**
```bash
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Ollama (optional)
ollama serve
```

---

## 📞 Getting Help

**Check these files:**
1. [QUICK_START.md](./QUICK_START.md) - Fast intro
2. [AI_MEDICINE_SAFETY_GUIDE.md](./AI_MEDICINE_SAFETY_GUIDE.md) - Complete guide
3. [API_REFERENCE.md](./API_REFERENCE.md) - API details

**Run these commands:**
```bash
# View API docs
open http://localhost:8000/docs

# Run tests
python test_ai_safety_medicine.py

# Check imports
python -c "from app.agents import ai_safety_medicine; print('OK')"
```

---

**Version**: 1.0
**Last Updated**: March 1, 2024
