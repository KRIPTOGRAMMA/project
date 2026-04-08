# from passlib.context import CryptContext
# from typing import Optional

# pwd_content = CryptContext(
#     schemes=['bcrypt'],
#     deprecated='auto',
#     bcrypt__rounds=12
# )

# def hash_password(password: str) -> str:
#     return pwd_content.hash(password)

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_content.verify(plain_password, hashed_password)
import bcrypt

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    
    salt = bcrypt.gensalt()
    
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)

    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )