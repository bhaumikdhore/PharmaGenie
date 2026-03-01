# 📚 API Reference - AI Medicine Safety Check

## Base URL
```
http://localhost:8000
```

---

## 🔍 AI Medicine Safety Check

### Endpoint
```
POST /ai/test/ai-safety-medicine
```

### Description
Check if a medicine is safe or restricted. Uses Ollama AI if available, otherwise falls back to rule-based checking against 15 restricted medicines list.

### Request Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `medicine_name` | string | ✅ Yes | Name of medicine to check | "Morphine" |
| `dosage` | string | ❌ No | Dosage amount (informational only) | "10mg" |

### Request Body (JSON)
```json
{
  "medicine_name": "Morphine",
  "dosage": "10mg"
}
```

### Response

#### Success Response (200 OK)
```json
{
  "agent": "ai_safety_medicine",
  "status": "success",
  "medicine_name": "Morphine",
  "is_restricted": true,
  "is_approved": false,
  "approval_status": "⏹️ RESTRICTED",
  "ai_analysis": "⏹️ Morphine is on the RESTRICTED/CONTROLLED medicines list. It requires prescription verification and special authorization for purchase.",
  "source": "rule_based"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `agent` | string | Always "ai_safety_medicine" |
| `status` | string | "success" or "error" |
| `medicine_name` | string | The medicine checked |
| `is_restricted` | boolean | Is medicine in restricted list? |
| `is_approved` | boolean | Can medicine be purchased? |
| `approval_status` | string | "✅ APPROVED" or "⏹️ RESTRICTED" |
| `ai_analysis` | string | Detailed reason from AI or rule engine |
| `source` | string | "ollama_ai" or "rule_based" |

---

## 📋 Response Examples

### Example 1: APPROVED Medicine (Paracetamol)

**Request:**
```bash
curl -X POST http://localhost:8000/ai/test/ai-safety-medicine \
  -H "Content-Type: application/json" \
  -d '{"medicine_name": "Paracetamol"}'
```

**Response:**
```json
{
  "agent": "ai_safety_medicine",
  "status": "success",
  "medicine_name": "Paracetamol",
  "is_restricted": false,
  "is_approved": true,
  "approval_status": "✅ APPROVED",
  "ai_analysis": "Paracetamol is not on the restricted list. Generally safe for over-the-counter purchase with standard dosing.",
  "source": "rule_based"
}
```

### Example 2: RESTRICTED Medicine (Morphine)

**Request:**
```bash
curl -X POST http://localhost:8000/ai/test/ai-safety-medicine \
  -H "Content-Type: application/json" \
  -d '{"medicine_name": "Morphine"}'
```

**Response:**
```json
{
  "agent": "ai_safety_medicine",
  "status": "success",
  "medicine_name": "Morphine",
  "is_restricted": true,
  "is_approved": false,
  "approval_status": "⏹️ RESTRICTED",
  "ai_analysis": "⏹️ Morphine is on the RESTRICTED/CONTROLLED medicines list. It requires prescription verification and special authorization.",
  "source": "rule_based"
}
```

### Example 3: With Ollama AI Available

**Request:**
```bash
curl -X POST http://localhost:8000/ai/test/ai-safety-medicine \
  -H "Content-Type: application/json" \
  -d '{
    "medicine_name": "Tramadol",
    "dosage": "50mg"
  }'
```

**Response:**
```json
{
  "agent": "ai_safety_medicine",
  "status": "success",
  "medicine_name": "Tramadol",
  "is_restricted": true,
  "is_approved": false,
  "approval_status": "⏹️ RESTRICTED",
  "ai_analysis": "Tramadol is a controlled opioid analgesic on the restricted medicines list. It poses addiction and dependency risks. Medical supervision and proper prescribing is required.",
  "source": "ollama_ai"
}
```

---

## 🎯 HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Medicine checked successfully |
| 400 | Bad Request | Missing required field |
| 500 | Server Error | Backend crash or Ollama error |

---

## 🔄 Request/Response Flow

```
Client Request
    ↓
POST /ai/test/ai-safety-medicine
    ↓
Backend Receives: {medicine_name, dosage}
    ↓
Check against 15 RESTRICTED_MEDICINES
    ↓
Is Ollama Available? 
  → YES: Use AI for detailed analysis
  → NO: Use rule-based decision
    ↓
Return Response: {is_approved, approval_status, ai_analysis, source}
    ↓
Frontend Displays:
  ✅ APPROVED (green badge)
  ⏹️ RESTRICTED (red badge)
```

---

## 📊 Restricted Medicines List

The following 15 medicines always show `is_approved: false`:

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

**All other medicines** show `is_approved: true`

---

## 🧪 Testing

### Using cURL

**Test Approved Medicine:**
```bash
curl -X POST http://localhost:8000/ai/test/ai-safety-medicine \
  -H "Content-Type: application/json" \
  -d '{"medicine_name": "Ibuprofen"}'
```

**Test Restricted Medicine:**
```bash
curl -X POST http://localhost:8000/ai/test/ai-safety-medicine \
  -H "Content-Type: application/json" \
  -d '{"medicine_name": "Codeine"}'
```

**Test with Dosage:**
```bash
curl -X POST http://localhost:8000/ai/test/ai-safety-medicine \
  -H "Content-Type: application/json" \
  -d '{
    "medicine_name": "Aspirin",
    "dosage": "500mg"
  }'
```

### Using Python
```python
import requests

response = requests.post(
    "http://localhost:8000/ai/test/ai-safety-medicine",
    json={
        "medicine_name": "Paracetamol",
        "dosage": "500mg"
    }
)

print(response.json())
# Output:
# {
#   "agent": "ai_safety_medicine",
#   "status": "success",
#   "is_approved": true,
#   "approval_status": "✅ APPROVED",
#   ...
# }
```

### Using JavaScript/Fetch
```javascript
fetch('http://localhost:8000/ai/test/ai-safety-medicine', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    medicine_name: 'Morphine'
  })
})
.then(res => res.json())
.then(data => {
  console.log(data.approval_status); // ⏹️ RESTRICTED
  console.log(data.is_approved);     // false
});
```

---

## ⚡ Performance

| Mode | Response Time | Needs Setup |
|------|---------------|-------------|
| Rule-based | <100ms | No |
| Ollama AI | 2-5 seconds | Yes (install Ollama) |

---

## 🔐 Data Validation

**Input Validation:**
- `medicine_name`: Required, non-empty string
- `dosage`: Optional, string (not validated)

**Example Invalid Request:**
```json
{
  "medicine_name": ""
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "medicine_name is required"
}
```

---

## 🚀 Integration Guide

### Frontend Integration
```typescript
// Call API
const response = await fetch('/ai/test/ai-safety-medicine', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ medicine_name })
});

const data = await response.json();

// Display result
if (data.is_approved) {
  show_green_badge("✅ APPROVED");
} else {
  show_red_badge("⏹️ RESTRICTED");
}
```

### Mobile App Integration
```javascript
const checkMedicineSafety = async (medicineName) => {
  try {
    const response = await fetch(
      `${API_BASE}/ai/test/ai-safety-medicine`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ medicine_name: medicineName })
      }
    );
    
    const result = await response.json();
    return {
      approved: result.is_approved,
      status: result.approval_status,
      reason: result.ai_analysis
    };
  } catch (error) {
    console.error('Failed to check medicine:', error);
  }
};
```

---

## 📞 Support & Debugging

### Check Backend Status
```bash
curl http://localhost:8000/health
# Returns: {"status": "ok"}
```

### Check API Documentation
```
http://localhost:8000/docs
```

### View Recent Logs
```bash
# Look at backend terminal for request logs
# POST /ai/test/ai-safety-medicine - 200 OK
```

---

## 🔗 Related Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/ai/test/prescription-requirement` | CSV-based prescription checking (legacy) |
| `/ai/test/ai-safety-medicine` | AI-powered safety check (new) |
| `/prescription-storage/...` | Prescription photo storage |

---

## ✨ Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-03-01 | Initial release with 15 restricted medicines + Ollama integration |

---

## 📝 Notes

- Restricted medicines list is hardcoded (not from database)
- Dosage parameter is accepted but doesn't affect approval status
- Medicine name matching is case-insensitive and partial-match tolerant
- Ollama integration is automatic and has fallback
- No user authentication required for this endpoint

---

**Questions?** See [AI_MEDICINE_SAFETY_GUIDE.md](./AI_MEDICINE_SAFETY_GUIDE.md) for complete documentation.
