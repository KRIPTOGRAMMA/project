from passlib.context import CryptContext
from typing import Optional

pwd_content = CryptContext(
    schemes=['bcrypt'],
    deprecated='auto',
    bcrypt__round=12
)

def hash_password(password: str) -> str:
    return pwd_content.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_content.verify(plain_password, hashed_password)