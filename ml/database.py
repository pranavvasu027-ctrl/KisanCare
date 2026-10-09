import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# By default, use service role key for backend operations so we don't need user tokens for internal tasks,
# though endpoints might optionally accept a user token.
supabase: Client = create_client(url, key) if url and key else None

def get_db():
    return supabase
