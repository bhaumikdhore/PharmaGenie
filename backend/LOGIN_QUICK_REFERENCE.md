# 🔐 Quick Login Reference Card

## New User Account Added

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📧 EMAIL : bhaumik.dhore@gmail.com
  🔑 PASSWORD : 123456789
  👤 ROLE : Customer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Login Steps

1. Go to `http://localhost:3000`
2. Role: Select **Customer** 
3. Email: `bhaumik.dhore@gmail.com`
4. Password: `123456789`
5. Click **Sign In**

## All Available Demo Accounts

```
ROLE: Customer
├─ Email: bhaumik.dhore@gmail.com
│  Password: 123456789 ⭐ NEW
└─ Email: customer@pharmagenie.ai
   Password: Customer@123

ROLE: Pharmacist
└─ Email: pharmacist@pharmagenie.ai
   Password: Pharma@123

ROLE: Admin
└─ Email: admin@pharmagenie.ai
   Password: Admin@123

ROLE: Warehouse
└─ Email: warehouse@pharmagenie.ai
   Password: Warehouse@123
```

## Files Changed

| File | Change |
|------|--------|
| `frontend/frontend/app/page.tsx` | ✅ Added user to VALID_USERS |
| `backend/app/models/user.py` | ✅ Added password field |
| `backend/add_user.py` | ✅ Created new (optional) |

## Next: Add to Database (Optional)

```bash
cd backend
python add_user.py
```

## Status

✅ **Ready to Login!**  
✅ Works immediately in frontend  
✅ Database integration available  

---
**Login now and start using!** 🚀
