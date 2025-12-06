from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, TokenResponse, TokenRefresh, UserResponse
from app.services.auth_service import auth_service
from app.dependencies import get_current_user
from app.models.user import User
from app.core.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    user_create: UserCreate,
    db: Session = Depends(get_db)
):
    logger.info(f"Signup request received for email: {user_create.email}")
    tokens = auth_service.signup(db, user_create)
    logger.info("Signup completed successfully")
    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(
    user_login: UserLogin,
    db: Session = Depends(get_db)
):
    logger.info(f"Login request received for email: {user_login.email}")
    tokens = auth_service.login(db, user_login)
    logger.info("Login completed successfully")
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_refresh: TokenRefresh
):
    logger.info("Token refresh request received")
    tokens = auth_service.refresh_access_token(token_refresh.refresh_token)
    logger.info("Token refresh completed successfully")
    return tokens


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User info request for user: {current_user.id}")
    return current_user