"""
Script to add a user to the database
Run with: python add_user.py
"""
import asyncio
import os
import sys
import uuid

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def create_tables():
    """Ensure all tables exist"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created/verified")


async def add_user_to_db():
    """Add user bhaumik.dhore@gmail.com to the database"""
    db = SessionLocal()
    
    try:
        # Check if user already exists
        stmt = select(User).where(User.email == "bhaumik.dhore@gmail.com")
        result = await db.execute(stmt)
        existing_user = result.scalars().first()
        
        if existing_user:
            print(f"⚠️ User already exists with ID: {existing_user.id}")
            return
        
        # Create new user
        user_id = str(uuid.uuid4())
        new_user = User(
            id=user_id,
            email="bhaumik.dhore@gmail.com",
            password="123456789",
            role="customer"
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        print("✅ User added successfully!")
        print(f"   ID: {user_id}")
        print(f"   Email: bhaumik.dhore@gmail.com")
        print(f"   Password: 123456789")
        print(f"   Role: customer")
        print("\n✨ You can now login with these credentials!")
        
    except Exception as e:
        print(f"❌ Error adding user: {str(e)}")
        await db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        await db.close()


async def main():
    """Main function"""
    print("User Registration Script")
    print("=" * 50)
    
    # Create tables
    await create_tables()
    
    # Add user
    await add_user_to_db()


if __name__ == "__main__":
    asyncio.run(main())
