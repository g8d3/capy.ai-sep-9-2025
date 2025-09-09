from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    get_current_user,
)
from app.models.user import User
from app.schemas.user import UserCreate, UserRead
from app.schemas.auth import TokenPair, LoginRequest
from app.core.config import settings

router = APIRouter()


@router.post("/register", response_model=UserRead)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, password_hash=get_password_hash(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=refresh,
        httponly=True,
        samesite="Lax",
        secure=False,
        max_age=settings.JWT_REFRESH_EXPIRE_DAYS * 24 * 3600,
        path="/auth",
    )
    return TokenPair(access_token=access)


@router.post("/refresh", response_model=TokenPair)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    from app.core.security import decode_token
    token = request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_id = int(payload.get("sub"))
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    access = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        samesite="Lax",
        secure=False,
        max_age=settings.JWT_REFRESH_EXPIRE_DAYS * 24 * 3600,
        path="/auth",
    )
    return TokenPair(access_token=access)


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    return user
