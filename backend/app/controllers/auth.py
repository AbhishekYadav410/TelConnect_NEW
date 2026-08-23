"""Layer 0 — authentication & role-based access.

Passwords: stdlib hashlib.scrypt (salted). Tokens: HMAC-SHA256 signed, JWT-shaped
payload (sub/role/exp) without the dependency.
ponytail: stdlib crypto instead of bcrypt+python-jose — same properties, zero deps.
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import time

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .. import db

SECRET_PATH = os.path.join(os.path.dirname(db.DB_PATH), "secret.key")
TOKEN_TTL = 60 * 60 * 12  # 12h sessions


def _secret() -> bytes:
    if os.path.exists(SECRET_PATH):
        with open(SECRET_PATH, "rb") as f:
            return f.read()
    os.makedirs(os.path.dirname(SECRET_PATH), exist_ok=True)
    key = secrets.token_bytes(32)
    with open(SECRET_PATH, "wb") as f:
        f.write(key)
    return key


def _kdf(password: str, salt: bytes) -> bytes:
    if hasattr(hashlib, "scrypt"):  # absent on LibreSSL-linked Python builds
        return hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    return base64.b64encode(salt).decode() + "$" + base64.b64encode(_kdf(password, salt)).decode()


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_b64, dk_b64 = stored.split("$")
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(dk_b64)
        return hmac.compare_digest(_kdf(password, salt), expected)
    except (ValueError, TypeError):
        return False


def make_token(user_id: str, role: str) -> str:
    payload = json.dumps({"sub": user_id, "role": role, "exp": int(time.time()) + TOKEN_TTL})
    body = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    sig = hmac.new(_secret(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def parse_token(token: str) -> dict:
    try:
        body, sig = token.split(".")
        expected = hmac.new(_secret(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise ValueError("bad signature")
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        if payload["exp"] < time.time():
            raise ValueError("expired")
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


_bearer = HTTPBearer(auto_error=False)


def current_user(cred: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    if cred is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = parse_token(cred.credentials)
    row = db.connect().execute("SELECT * FROM users WHERE user_id=?", (payload["sub"],)).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="Unknown user")
    return dict(row)


def require_admin(user: dict = Depends(current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def require_customer(user: dict = Depends(current_user)) -> dict:
    if user["role"] != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")
    return user


def create_user(role: str, name: str, email: str, password: str,
                region: str | None = None, service_type: str | None = None) -> dict:
    conn = db.connect()
    if conn.execute("SELECT 1 FROM users WHERE email=?", (email.lower(),)).fetchone():
        raise HTTPException(status_code=409, detail="Email already registered")
    user_id = db.new_id("USR")
    conn.execute(
        "INSERT INTO users(user_id,role,name,email,password_hash,region,service_type,created_at) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (user_id, role, name, email.lower(), hash_password(password), region, service_type, db.now_iso()),
    )
    conn.commit()
    return {"user_id": user_id, "role": role, "name": name, "email": email.lower(),
            "region": region, "service_type": service_type}


def login(email: str, password: str) -> dict:
    row = db.connect().execute("SELECT * FROM users WHERE email=?", (email.lower(),)).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="User is not registered. Please sign up first.")
    if not verify_password(password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect password. Please try again.")
    return {"token": make_token(row["user_id"], row["role"]),
            "user": {"user_id": row["user_id"], "role": row["role"], "name": row["name"],
                     "email": row["email"], "region": row["region"],
                     "service_type": row["service_type"]}}
