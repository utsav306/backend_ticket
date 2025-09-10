"""
Script to clear all data from the database tables.
This will remove all users, events, bookings, and waitlists.
"""

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import User, Event, Booking, Waitlist
import sys

def clear_all_tables():
    """Clear all data from all tables."""
    print("🗑️  Clearing all database tables...")
    
    db = SessionLocal()
    try:
        # Delete in order to respect foreign key constraints
        print("Deleting waitlists...")
        waitlist_count = db.query(Waitlist).count()
        db.query(Waitlist).delete()
        print(f"✅ Deleted {waitlist_count} waitlist entries")
        
        print("Deleting bookings...")
        booking_count = db.query(Booking).count()
        db.query(Booking).delete()
        print(f"✅ Deleted {booking_count} bookings")
        
        print("Deleting events...")
        event_count = db.query(Event).count()
        db.query(Event).delete()
        print(f"✅ Deleted {event_count} events")
        
        print("Deleting users...")
        user_count = db.query(User).count()
        db.query(User).delete()
        print(f"✅ Deleted {user_count} users")
        
        # Commit all changes
        db.commit()
        print("\n🎉 All tables cleared successfully!")
        
        # Verify tables are empty
        print("\n📊 Verification:")
        print(f"Users: {db.query(User).count()}")
        print(f"Events: {db.query(Event).count()}")
        print(f"Bookings: {db.query(Booking).count()}")
        print(f"Waitlists: {db.query(Waitlist).count()}")
        
    except Exception as e:
        print(f"❌ Error clearing tables: {str(e)}")
        db.rollback()
    finally:
        db.close()

def reset_sequences():
    """Reset auto-increment sequences (PostgreSQL specific)."""
    print("\n🔄 Resetting ID sequences...")
    
    try:
        with engine.connect() as connection:
            # Reset sequences for PostgreSQL
            tables = ['users', 'events', 'bookings', 'waitlists']
            for table in tables:
                try:
                    connection.execute(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1")
                    print(f"✅ Reset {table} ID sequence")
                except Exception as e:
                    print(f"⚠️  Could not reset {table} sequence: {str(e)}")
            
            connection.commit()
            
    except Exception as e:
        print(f"⚠️  Could not reset sequences: {str(e)}")
        print("This is normal if you're not using PostgreSQL")

if __name__ == "__main__":
    print("🚨 DATABASE CLEANUP SCRIPT")
    print("=" * 40)
    print("This will DELETE ALL DATA from:")
    print("- Users")
    print("- Events") 
    print("- Bookings")
    print("- Waitlists")
    print("\n⚠️  THIS ACTION CANNOT BE UNDONE!")
    
    confirm = input("\nType 'YES' to proceed: ")
    
    if confirm == "YES":
        clear_all_tables()
        reset_sequences()
        print("\n✨ Database is now clean and ready for fresh testing!")
    else:
        print("❌ Operation cancelled")
        sys.exit(1)
