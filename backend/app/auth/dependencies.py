from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.auth.jwt import decode_access_token
from app.auth.security import hash_password

security_scheme = HTTPBearer(auto_error=False)

DEMO_ADMIN_EMAIL = "admin@stockflow.com"
DEMO_ADMIN_PASSWORD = "Admin@123"

def get_demo_user(db: Session) -> User:
    """Return the account used when no token is supplied (login-free demo mode)."""
    admin = (
        db.query(User)
        .filter(User.role == "ADMIN", User.is_active.is_(True))
        .order_by(User.id.asc())
        .first()
    )
    if admin:
        return admin

    demo = db.query(User).filter(User.email == DEMO_ADMIN_EMAIL).first()
    if demo:
        demo.role = "ADMIN"
        demo.is_active = True
        db.commit()
        db.refresh(demo)
        return demo

    demo = User(
        name="StockFlow Admin",
        email=DEMO_ADMIN_EMAIL,
        password_hash=hash_password(DEMO_ADMIN_PASSWORD),
        role="ADMIN",
        is_active=True,
    )
    db.add(demo)
    db.commit()
    db.refresh(demo)
    return demo

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    # Login is optional: without a bearer token the app runs as the demo admin.
    if not credentials:
        return get_demo_user(db)
    
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or token is invalid. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier in token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User associated with this token was not found.",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact an administrator.",
        )
    
    return user

def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role.upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Admin privilege required for this operation.",
        )
    return current_user
