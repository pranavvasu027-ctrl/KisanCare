import os
import sys
import uuid
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def seed_users():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        sys.exit(1)
        
    supabase: Client = create_client(url, key)
    
    # Define our 5 mock users with their roles
    mock_users = [
        {
            "email": "admin@kisancare.test",
            "password": "TestPassword123!",
            "role": "admin",
            "name": "System Admin",
            "phone": "+910000000001"
        },
        {
            "email": "farmer1@kisancare.test",
            "password": "TestPassword123!",
            "role": "farmer",
            "name": "Ramesh Patil",
            "phone": "+910000000002"
        },
        {
            "email": "farmer2@kisancare.test",
            "password": "TestPassword123!",
            "role": "farmer",
            "name": "Suresh Kumar",
            "phone": "+910000000003"
        },
        {
            "email": "agri_pro@kisancare.test",
            "password": "TestPassword123!",
            "role": "agri_professional",
            "name": "Dr. Sharma (Agronomist)",
            "phone": "+910000000004"
        },
        {
            "email": "restricted@kisancare.test",
            "password": "TestPassword123!",
            "role": "farmer",
            "name": "Restricted User",
            "phone": "+910000000005"
        }
    ]

    print("Seeding mock users...")
    
    for user_data in mock_users:
        # Check if user already exists (we can't easily query auth.users by email via the standard client without admin API,
        # but we can try to create and catch error, or check profiles)
        profiles = supabase.table("profiles").select("id").eq("phone", user_data["phone"]).execute()
        
        if len(profiles.data) > 0:
            print(f"User {user_data['email']} likely already exists (found profile with phone {user_data['phone']}). Skipping creation.")
            continue
            
        try:
            # Create user in auth schema
            res = supabase.auth.admin.create_user({
                "email": user_data["email"],
                "password": user_data["password"],
                "email_confirm": True
            })
            
            user_id = res.user.id
            print(f"Created auth user: {user_data['email']} ({user_id})")
            
            # Create profile (which also stores the custom role)
            profile = {
                "user_id": user_id,
                "name": user_data["name"],
                "phone": user_data["phone"],
                "role": user_data["role"]
            }
            supabase.table("profiles").insert(profile).execute()
            print(f"Created profile for {user_data['email']}")
            
        except Exception as e:
            print(f"Failed to create user {user_data['email']}: {e}")

if __name__ == "__main__":
    seed_users()
