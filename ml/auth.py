import os
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client, ClientOptions

security = HTTPBearer()

def get_current_user_client(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Client:
    token = credentials.credentials
    url = os.environ.get("SUPABASE_URL", "")
    anon_key = os.environ.get("SUPABASE_ANON_KEY", "")
    
    if not url or not anon_key:
        raise HTTPException(status_code=500, detail="Supabase configuration missing")
    
    # 1. Verify token by fetching user
    auth_client = create_client(url, anon_key)
    try:
        user_response = auth_client.auth.get_user(token)
        if not user_response or not getattr(user_response, "user", None):
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")
        
    # 2. Return a client initialized with the user's token so RLS applies natively
    try:
        user_client = create_client(
            url, 
            anon_key,
            options=ClientOptions(headers={"Authorization": f"Bearer {token}"})
        )
        user_client.current_user_id = user_response.user.id
        return user_client
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize user context: {e}")
