# ⚡ Quick Start Guide - AI Medicine Safety Check

## 🎯 What Was Just Built?

An intelligent medicine safety checking system that:
- ✅ Checks medicines against **15 restricted medicines list**
- ✅ Shows **✅ APPROVED** or **⏹️ RESTRICTED** status
- ✅ Uses AI (Ollama) for detailed analysis (optional)
- ✅ Falls back to rule-based checking automatically
- ✅ Works immediately without configuration

---

## 🚀 Get Started in 3 Steps

### Step 1: Start the Backend Server
```bash
cd backend
python -m uvicorn app.main:app --reload
```

✅ Backend running at: `http://localhost:8000`
✅ API docs at: `http://localhost:8000/docs`

### Step 2: Start the Frontend
```bash
cd frontend
npm run dev
```

✅ Frontend running at: `http://localhost:3000`

### Step 3: Test It
1. Open: `http://localhost:3000/dashboard/customer/prescriptions`
2. Look for: **"AI Medicine Safety Check"** section
3. Enter medicine name: `Morphine`
4. Click: **"Check Safety"**
5. Result: **⏹️ RESTRICTED** (red warning)

---

## 🧪 Test These Examples

### ✅ APPROVED Medicines (Should be Green)
- Paracetamol
- Ibuprofen
- Aspirin
- Cetirizine
- Hyaluronic Acid

### ⏹️ RESTRICTED Medicines (Should be Red)
- Morphine
- Codeine
- Fentanyl
- Alprazolam
- Diazepam

---

## 🤖 Optional: Setup Ollama for AI Analysis

### Install Ollama (First Time Only)

**macOS/Linux:**
```bash
curl https://ollama.ai/install.sh | sh
```

**Windows:**
1. Download from: https://ollama.ai
2. Run installer
3. Restart terminal

### Start Ollama

```bash
ollama serve
```

✅ Ollama running at: `http://localhost:11434`

### Pull AI Model

```bash
ollama pull mistral
```

⏳ First time: ~4GB download (15-30 minutes)
⏳ Subsequent uses: <1 second (cached)

### Verify It Works

```bash
curl http://localhost:11434/api/tags
```

---

## 📊 How to Know It's Working

### Without Ollama (Rule-Based):
```
Source: 📋 Rule-based Check
(Fast: <1 second)
```

### With Ollama (AI-Powered):
```
Source: 🤖 Ollama AI
(Slower: 2-5 seconds, but more detailed)
```

Both are correct! System chooses automatically.

---

## 🔍 Check Status

### In Browser Console (DevTools)
```javascript
// Check what endpoint is being called
// Network tab shows: POST /ai/test/ai-safety-medicine
// Response shows: is_approved (true/false)
```

### In Backend Terminal
```
POST /ai/test/ai-safety-medicine
{"medicine_name": "Morphine"}
```

---

## 📋 Files That Were Created

**Backend (3 files):**
1. `app/agents/ai_safety_medicine.py` - Main AI agent
2. `test_ai_safety_medicine.py` - Verification tests
3. `AI_MEDICINE_SAFETY_GUIDE.md` - Full documentation

**Frontend (1 file):**
1. `app/dashboard/customer/prescriptions/page.tsx` - Updated UI

**Modified:**
1. `app/routes/ai.py` - Added endpoint
2. `app/main.py` - Already updated
3. `app/db/init_db.py` - Already updated

---

## ⚡ API Endpoint

### Check Single Medicine
```bash
curl -X POST http://localhost:8000/ai/test/ai-safety-medicine \
  -H "Content-Type: application/json" \
  -d '{"medicine_name": "Morphine"}'
```

### Response Example
```json
{
  "agent": "ai_safety_medicine",
  "status": "success",
  "medicine_name": "Morphine",
  "is_restricted": true,
  "is_approved": false,
  "approval_status": "⏹️ RESTRICTED",
  "ai_analysis": "Morphine is on the RESTRICTED list...",
  "source": "rule_based"
}
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Failed to fetch" | Start backend: `python -m uvicorn app.main:app --reload` |
| No results | Reload browser page |
| Slow response (5+ sec) | This is Ollama AI analyzing (normal: 2-5 sec) |
| Says everything is APPROVED | Only 15 medicines are restricted (working as intended!) |
| Ollama connection error | That's fine! Falls back to rule-based (still works) |

---

## 🎯 Restricted Medicine List

The 15 medicines that show ⏹️ RESTRICTED:

1. **Morphine** - Opioid
2. **Codeine** - Opioid
3. **Tramadol** - Opioid
4. **Fentanyl** - Opioid
5. **Oxycodone** - Opioid
6. **Alprazolam** - Benzodiazepine
7. **Diazepam** - Benzodiazepine
8. **Lorazepam** - Benzodiazepine
9. **Methadone** - Synthetic Opioid
10. **Barbiturates** - Sedative
11. **Benzodiazepines** - Anti-anxiety
12. **Amphetamine** - Stimulant
13. **Methylphenidate** - Stimulant (ADHD)
14. **Steroids** - Corticosteroid
15. **Lithium** - Mood stabilizer

All other medicines = ✅ APPROVED

---

## 📈 What Happens Next

### Immediate:
✅ Test the system in browser
✅ Check a few medicines
✅ See ✅ APPROVED vs ⏹️ RESTRICTED status

### Optional:
⏳ Install Ollama for AI analysis
⏳ Test with Ollama running
⏳ Run test suite: `python test_ai_safety_medicine.py`

### Later:
📋 Integrate with actual prescription system
📋 Add pharmacy verification
📋 Deploy to production

---

## ✅ Success Checklist

- [ ] Backend started (`http://localhost:8000`)
- [ ] Frontend started (`http://localhost:3000`)
- [ ] Navigated to Prescriptions page
- [ ] Tested "Morphine" → Shows ⏹️ RESTRICTED
- [ ] Tested "Paracetamol" → Shows ✅ APPROVED
- [ ] (Optional) Installed Ollama
- [ ] (Optional) Ran test suite

---

## 🎉 You're All Set!

The AI Medicine Safety Check system is:
✅ Fully implemented
✅ Ready to test
✅ Working without Ollama (fallback)
✅ Enhanced with AI when Ollama available

**Next**: Go test it in browser! 🚀

---

## 💡 Pro Tips

1. **Dosage doesn't affect approval** - All dosages of a medicine get same status
2. **Name matching is flexible** - "morphine", "MORPHINE", "Morphine" all work
3. **Try combinations** - Test Paracetamol + Morphine together
4. **Watch the source** - See if using Rule-based or Ollama AI

---

**Questions?** Check [AI_MEDICINE_SAFETY_GUIDE.md](./AI_MEDICINE_SAFETY_GUIDE.md) for full details!
