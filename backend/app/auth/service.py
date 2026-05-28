from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.security import create_access_token, hash_password, verify_password


def register_user(db: Session, email: str, password: str) -> tuple[User, str]:
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='EMAIL_ALREADY_REGISTERED')
    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, create_access_token(str(user.id))


def authenticate_user(db: Session, email: str, password: str) -> tuple[User, str]:
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='INVALID_CREDENTIALS')
    return user, create_access_token(str(user.id))


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)
