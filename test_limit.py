from slowapi import Limiter
from slowapi.util import get_remote_address
try:
    limiter = Limiter(key_func=get_remote_address, application_limits=["30/minute"])
    print("application_limits works")
except Exception as e:
    print(e)
