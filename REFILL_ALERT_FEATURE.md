# Refill Alert Button - Hackathon Demo Feature

## Overview
Added a **"Refill Alert"** button in the prescription table on the user dashboard to trigger refill notifications via N8N, demonstrating the integration between the frontend, backend, and N8N notification automation system.

## Changes Made

### Frontend Changes
**File:** `vsls:/frontend/frontend/app/dashboard/customer/prescriptions/page.tsx`

#### 1. **New Imports**
- Added `Bell` icon from lucide-react for the refill notification button

#### 2. **New State Variables**
```typescript
const [refillNotificationLoading, setRefillNotificationLoading] = useState<Record<string, boolean>>({})
const [refillNotificationMsg, setRefillNotificationMsg] = useState<{ rxId: string; type: "success" | "error"; text: string } | null>(null)
```

#### 3. **New Function: `triggerRefillNotification`**
```typescript
const triggerRefillNotification = async (rx: Prescription) => {
  // Step 1: Create a refill notification record in backend
  // Step 2: Trigger N8N workflow via backend endpoint
  // Step 3: Display success/error message to user
}
```

This function:
- Creates a refill notification record via `/api/refill-notifications/create`
- Triggers the N8N workflow via `/api/refill-notifications/{notification_id}/trigger-n8n`
- Shows user-friendly feedback messages

#### 4. **Button UI in Prescription Table**
- Appears only for prescriptions with `status === "refill-needed"`
- Shows bell icon and "Refill Alert" text
- Changes to "Sending..." with spinner while processing
- Positioned before "View Details" and "Add to Cart" buttons in the Actions column

#### 5. **Notification Message Display**
- Card that appears after the table showing success/error messages
- Displays: ✅ for success, ❌ for errors
- Can be dismissed by clicking the X button
- Shows message about N8N workflow being triggered

### Backend Integration

**Backend Endpoints Used:**
1. **`POST /api/refill-notifications/create`**
   - Creates a refill notification record in the database
   - Returns `notification_id` needed for triggering N8N

2. **`POST /api/refill-notifications/{notification_id}/trigger-n8n`**
   - Sends webhook payload to N8N workflow
   - Payload includes:
     - `notification_id`
     - `medicine_name`
     - `dosage`
     - `quantity`
     - `refill_date`
     - `customer_id`
     - `triggered_at` (timestamp)
     - `event`: "refill_reminder_test"

### N8N Integration

**Webhook Configuration:**
- Environment Variable: `N8N_ORDER_WEBHOOK` (already set in `.env`)
- Value: `https://shiftry.app.n8n.cloud/webhook/order-created`

**Workflow Triggers:**
When a refill alert is triggered from the frontend:
1. Backend creates a notification record
2. Backend POSTs to N8N webhook with refill details
3. N8N receives the webhook and can:
   - Send SMS notifications to customer
   - Send Email notifications to customer
   - Log the notification event
   - Update notification status
   - Trigger other automation workflows

## How It Works for Hackathon Demo

### User Flow:
1. User goes to Dashboard → My Prescriptions
2. Finds a prescription with status "Refill Needed"
3. Clicks the blue "Refill Alert" button
4. Button shows "Sending..." with spinner
5. Backend creates refill notification and triggers N8N webhook
6. N8N receives the webhook and sends notifications (SMS/Email)
7. User sees success message: ✅ "Refill alert triggered for [Medicine]! N8N workflow initiated. Customer will receive notification via SMS/Email."

### What It Demonstrates:
✅ **AI-driven Notification System** - Shows how N8N can automate customer notifications
✅ **Full Stack Integration** - Frontend → Backend → N8N → Customer
✅ **Real-time Feedback** - User gets immediate feedback on action
✅ **Pharmacy Management Automation** - Demonstrates automated refill reminders

## Testing

### Manual Testing Steps:
1. Navigate to Dashboard → My Prescriptions (Customer view)
2. Scroll to the prescription table
3. Look for prescriptions with "Refill Needed" status (e.g., RX-4518: Lisinopril)
4. Click the "Refill Alert" button
5. Observe:
   - Button changes to loading state
   - Backend processes the request
   - Success/error message appears
   - Message should indicate N8N workflow was triggered

### Sample Test Data:
- **RX-4518** (Lisinopril) has status "refill-needed" by default
- Clicking "Refill Alert" will trigger the workflow

## Sample Success Message
```
✅ Refill alert triggered for Lisinopril! 
N8N workflow initiated. 
Customer will receive notification via SMS/Email.
```

## Sample Error Message
```
❌ Error: [Error details from backend/N8N]
```

## Files Modified
1. ✅ `vsls:/frontend/frontend/app/dashboard/customer/prescriptions/page.tsx`
   - Added Bell icon import
   - Added state variables for refill notification
   - Added `triggerRefillNotification()` function
   - Added button in prescription table Actions column
   - Added success/error message display card

## Backend Files (Already Exist & Configured)
1. ✅ `vsls:/backend/app/routes/refill_notifications.py` - Refill notification endpoints
2. ✅ `vsls:/backend/app/main.py` - Router registration
3. ✅ `vsls:/backend/.env` - N8N webhook URL configured

## Key Features
- 🔔 **One-Click Refill Alerts** - Trigger notifications instantly
- 📲 **N8N Integration** - Leverages N8N for SMS/Email automation
- 💾 **Database Persistence** - Notification records stored in DB
- ⚡ **Real-time Feedback** - Immediate UI feedback
- 🎯 **Smart Filtering** - Button only shows for refill-needed prescriptions
- 🔐 **Secure** - Uses authenticated API endpoints
- 📊 **Hackathon Ready** - Perfect for demonstrating automation

## Environment Variables Required
```env
N8N_ORDER_WEBHOOK=https://shiftry.app.n8n.cloud/webhook/order-created
```
✅ Already configured in `.env`

---

**Feature Status:** ✅ Complete and Ready for Demo
**Last Updated:** March 1, 2026
