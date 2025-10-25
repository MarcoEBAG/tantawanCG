from datetime import datetime,timedelta,timezone
from typing import Optional
from jose import jwt,JWTError
from passlib.context import CryptContext
import os
pwd_ctx=CryptContext(schemes=['bcrypt'],deprecated='auto')
JWT_SECRET=os.getenv('JWT_SECRET','change_me')
JWT_ALG=os.getenv('JWT_ALG','HS256')
JWT_EXPIRES_MIN=int(os.getenv('JWT_EXPIRES_MIN','43200'))
def hash_password(pw:str)->str: return pwd_ctx.hash(pw)
def verify_password(pw:str,hashed:str)->bool: return pwd_ctx.verify(pw,hashed)
def create_token(sub:str,extra:Optional[dict]=None)->str:
  now=datetime.now(timezone.utc)
  payload={'sub':sub,'iat':int(now.timestamp()),'exp':int((now+timedelta(minutes=JWT_EXPIRES_MIN)).timestamp())}
  if extra: payload.update(extra)
  return jwt.encode(payload,JWT_SECRET,algorithm=JWT_ALG)
def decode_token(token:str)->dict:
  try: return jwt.decode(token,JWT_SECRET,algorithms=[JWT_ALG])
  except JWTError as e: raise ValueError('invalid token') from e
