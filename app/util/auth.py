from jose import jwt 
import jose
from datetime import datetime,timedelta,timezone

SECRET_KEY = "super secret secrets"

def encode_token(user_id, role="user"):
    payload = {
        "exp": datetime.now(timezone.utc) + timedelta(days=0, hours=1),
        "iat": datetime.now(timezone.utc),
        "sub": str(user_id),
        "role": role
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token