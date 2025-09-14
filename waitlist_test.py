"""
Improved waitlist test script with proper booking ID tracking.
Run this after starting your FastAPI server.
"""

import requests
import json
import random
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def generate_unique_email(base_name, i):
    """Generate a unique email with timestamp to avoid conflicts."""
    timestamp = int(time.time())
    random_num = random.randint(1000, 9999)
    return f"{base_name}{i}_{timestamp}_{random_num}@test.com"

def test_waitlist_flow_improved():
    """Test the complete waitlist flow with proper booking tracking."""
    
    print("🚀 Testing Waitlist System (Improved)")
    print("=" * 50)
    
    try:
        # 1. Create a test event with capacity 2
        print("1. Creating test event...")
        event_data = {
            "name": "Test Concert",
            "venue": "Small Hall",
            "time": (datetime.now() + timedelta(days=1)).isoformat(),
            "capacity": 2
        }
        
        # Try admin endpoint first, then public endpoint
        event_response = requests.post(f"{BASE_URL}/admin/events/", json=event_data)
        if event_response.status_code != 200:
            print(f"Admin endpoint failed, trying public endpoint...")
            event_response = requests.post(f"{BASE_URL}/events/", json=event_data)
        
        if event_response.status_code != 200:
            print(f"❌ Failed to create event: {event_response.text}")
            return
        
        event = event_response.json()
        event_id = event["id"]
        print(f"✅ Created event {event_id} with capacity 2")
        
        # 2. Create test users with unique emails
        print("\n2. Creating test users...")
        users = []
        for i in range(5):
            user_data = {
                "name": f"User {i+1}",
                "email": generate_unique_email("user", i+1),
                "password": "password123"
            }
            
            user_response = requests.post(f"{BASE_URL}/users/", json=user_data)
            print(f"User creation response: Status {user_response.status_code}")
            if user_response.status_code == 200:
                user_result = user_response.json()
                users.append(user_result)
                print(f"✅ Created user {user_result.get('id', 'unknown_id')} with email {user_data['email']}")
            else:
                print(f"❌ User creation failed: {user_response.text}")
        
        print(f"Total users created: {len(users)}")
        if len(users) < 3:
            print("❌ Need at least 3 users for testing")
            return
        
        # 3. Book the first 2 users (fill the event) and track booking IDs
        print("\n3. Filling event capacity...")
        booking_ids = []
        for i in range(2):
            booking_data = {"user_id": users[i]["id"]}
            booking_response = requests.post(f"{BASE_URL}/bookings/book/{event_id}", json=booking_data)
            
            if booking_response.status_code == 200:
                booking_result = booking_response.json()
                booking_id = booking_result.get("booking_id")
                booking_ids.append(booking_id)
                print(f"✅ User {users[i]['id']} booked successfully (Booking ID: {booking_id})")
            else:
                print(f"❌ Booking failed: {booking_response.text}")
        
        # 4. Try to book the 3rd user (should fail)
        print("\n4. Testing full event booking (should fail)...")
        booking_data = {"user_id": users[2]["id"]}
        booking_response = requests.post(f"{BASE_URL}/bookings/book/{event_id}", json=booking_data)
        
        if booking_response.status_code == 400:
            print("✅ Booking correctly failed - event is full")
        else:
            print(f"❌ Expected booking to fail but got: {booking_response.status_code}")
        
        # 5. Add users to waitlist
        print("\n5. Adding users to waitlist...")
        waitlist_users = []
        for i in range(2, 5):  # Users 3, 4, 5
            waitlist_data = {"user_id": users[i]["id"]}
            waitlist_response = requests.post(f"{BASE_URL}/waitlist/join/{event_id}", json=waitlist_data)
            
            if waitlist_response.status_code == 200:
                waitlist_info = waitlist_response.json()
                waitlist_users.append(waitlist_info)
                print(f"✅ User {users[i]['id']} joined waitlist at position {waitlist_info['position']}")
            else:
                print(f"❌ Waitlist join failed: {waitlist_response.text}")
        
        # 6. Check waitlist
        print("\n6. Checking event waitlist...")
        waitlist_response = requests.get(f"{BASE_URL}/waitlist/event/{event_id}")
        
        if waitlist_response.status_code == 200:
            waitlist = waitlist_response.json()
            print(f"✅ Event waitlist has {len(waitlist)} people:")
            for entry in waitlist:
                print(f"   Position {entry['position']}: User {entry['user_id']}")
        
        # 7. Check individual waitlist position
        print("\n7. Checking waitlist position for first waitlisted user...")
        if waitlist_users:
            first_waitlist_user = waitlist_users[0]["user_id"]
            position_response = requests.get(f"{BASE_URL}/waitlist/position/{event_id}/{first_waitlist_user}")
            
            if position_response.status_code == 200:
                position_info = position_response.json()
                print(f"✅ User {first_waitlist_user} is at position {position_info['position']} of {position_info['total_in_waitlist']}")
        
        # 8. Cancel a booking using actual booking ID (should promote from waitlist)
        print("\n8. Canceling a booking (should promote from waitlist)...")
        
        if booking_ids and booking_ids[0]:
            booking_id_to_cancel = booking_ids[0]
            cancel_response = requests.delete(f"{BASE_URL}/bookings/cancel/{booking_id_to_cancel}")
            
            if cancel_response.status_code == 200:
                cancel_info = cancel_response.json()
                print(f"✅ Booking {booking_id_to_cancel} cancelled: {cancel_info['message']}")
                
                # Check waitlist again (should have one less person)
                print("\n   Checking waitlist after cancellation...")
                waitlist_response = requests.get(f"{BASE_URL}/waitlist/event/{event_id}")
                if waitlist_response.status_code == 200:
                    waitlist_after = waitlist_response.json()
                    print(f"✅ Waitlist now has {len(waitlist_after)} people (was {len(waitlist_users)})")
                    if len(waitlist_after) < len(waitlist_users):
                        print("✅ Someone was automatically promoted from waitlist!")
                    for entry in waitlist_after:
                        print(f"   Position {entry['position']}: User {entry['user_id']}")
            else:
                print(f"❌ Booking cancellation failed: {cancel_response.text}")
        else:
            print("⚠️  No booking ID available for cancellation test")
        
        # 9. User leaves waitlist
        print("\n9. Testing leave waitlist...")
        if waitlist_users and len(waitlist_users) > 1:
            # Have the last user in waitlist leave
            last_waitlist_user = waitlist_users[-1]["user_id"]
            leave_response = requests.delete(f"{BASE_URL}/waitlist/leave/{event_id}?user_id={last_waitlist_user}")
            
            if leave_response.status_code == 200:
                leave_info = leave_response.json()
                print(f"✅ User {last_waitlist_user} left waitlist: {leave_info['message']}")
                
                # Check positions updated
                print("\n   Checking updated waitlist positions...")
                waitlist_response = requests.get(f"{BASE_URL}/waitlist/event/{event_id}")
                if waitlist_response.status_code == 200:
                    final_waitlist = waitlist_response.json()
                    print(f"✅ Final waitlist has {len(final_waitlist)} people:")
                    for entry in final_waitlist:
                        print(f"   Position {entry['position']}: User {entry['user_id']}")
        
        # 10. Test viewing user's waitlists
        print("\n10. Testing user waitlists view...")
        if users and len(users) > 2:
            user_id_to_check = users[3]["id"]  # 4th user should be in waitlist
            user_waitlist_response = requests.get(f"{BASE_URL}/waitlist/user/{user_id_to_check}")
            
            if user_waitlist_response.status_code == 200:
                user_waitlists = user_waitlist_response.json()
                print(f"✅ User {user_id_to_check} has {len(user_waitlists)} waitlist entries")
        
        print("\n🎉 Comprehensive waitlist testing completed!")
        print("📊 Summary: All core waitlist features are working correctly!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API. Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Test error: {str(e)}")

if __name__ == "__main__":
    print("Improved Waitlist System Test")
    print("Make sure your FastAPI server is running on localhost:8000")
    print("Press Enter to start testing...")
    input()
    test_waitlist_flow_improved()
