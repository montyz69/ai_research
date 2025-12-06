from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.services.auth_service import auth_service
from app.core.logger import setup_logger
from app.core.exceptions import AuthenticationError

logger = setup_logger(__name__)

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    try:
        token = credentials.credentials
        user = auth_service.get_current_user(db, token)
        return user
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise AuthenticationError(detail="Could not validate credentials")


async def get_optional_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if not authorization:
        return None
    
    try:
        token = authorization.replace("Bearer ", "")
        user = auth_service.get_current_user(db, token)
        return user
    except Exception as e:
        logger.warning(f"Optional auth failed: {str(e)}")
        return None