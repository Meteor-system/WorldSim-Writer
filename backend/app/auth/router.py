from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_user
from app.auth.models import User
from app.auth.schemas import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from app.auth.service import authenticate_user, register_user
from app.core.database import get_db

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/register', response_model=AuthResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user, token = register_user(db, payload.email, payload.password)
    return AuthResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post('/login', response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user, token = authenticate_user(db, payload.email, payload.password)
    return AuthResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post('/logout')
def logout() -> dict[str, bool]:
    return {'success': True}


@router.get('/me', response_model=UserResponse)
def me(current_user: User = Depends(require_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
