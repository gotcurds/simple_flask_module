from jose import jwt 
import jose
from datetime import datetime,timedelta,timezone
from functools import wraps
from flask import request, jsonify



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

def token_required(f):
    @wraps(f)
    def decoration(*args, **kwargs):

        token = None

        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split()[1]
        
        if not token:
            return jsonify({"error": "toekn missing from authorization headers"}), 401

        try:

            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            print(data)

        except jose.exceptions.ExpiredSignatureError:
            return jsonify({"message": "token is expired"}), 403
        except jose.exceptions.JWTError:
            return jsonify({"message": "invalid token"}), 403

        return f(*args, **kwargs)

    return decoration 