from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, TokenResponse
from app.services.user_service import user_service
from app.core.security import token_handler
from app.core.logger import setup_logger
from app.core.exceptions import InvalidCredentialsError, InvalidTokenError

logger = setup_logger(__name__)


class AuthService:
    def __init__(self):
        self.user_service = user_service
    
    def signup(self, db: Session, user_create: UserCreate) -> TokenResponse:
        logger.info(f"Signup attempt for email: {user_create.email}")
        
        user = self.user_service.create_user(db, user_create)
        
        access_token = token_handler.create_access_token(data={"sub": str(user.id)})
        refresh_token = token_handler.create_refresh_token(data={"sub": str(user.id)})
        
        logger.info(f"Signup successful for user: {user.id}")
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    
    def login(self, db: Session, user_login: UserLogin) -> TokenResponse:
        logger.info(f"Login attempt for email: {user_login.email}")
        
        user = self.user_service.get_user_by_email(db, user_login.email)
        
        if not user:
            logger.warning(f"Login failed: user not found for email {user_login.email}")
            raise InvalidCredentialsError()
        
        if not self.user_service.verify_password(user_login.password, user.password_hash):
            logger.warning(f"Login failed: invalid password for email {user_login.email}")
            raise InvalidCredentialsError()
        
        access_token = token_handler.create_access_token(data={"sub": str(user.id)})
        refresh_token = token_handler.create_refresh_token(data={"sub": str(user.id)})
        
        logger.info(f"Login successful for user: {user.id}")
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    
    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        logger.info("Refreshing access token")
        
        payload = token_handler.decode_token(refresh_token)
        
        if not token_handler.verify_token_type(payload, "refresh"):
            logger.warning("Token refresh failed: invalid token type")
            raise InvalidTokenError(detail="Invalid refresh token")
        
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Token refresh failed: missing user id in token")
            raise InvalidTokenError(detail="Invalid token payload")
        
        access_token = token_handler.create_access_token(data={"sub": user_id})
        new_refresh_token = token_handler.create_refresh_token(data={"sub": user_id})
        
        logger.info(f"Access token refreshed for user: {user_id}")
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token
        )
    
    def get_current_user(self, db: Session, token: str) -> User:
        logger.debug("Validating current user from token")
        
        payload = token_handler.decode_token(token)
        
        if not token_handler.verify_token_type(payload, "access"):
            logger.warning("Token validation failed: invalid token type")
            raise InvalidTokenError(detail="Invalid access token")
        
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Token validation failed: missing user id")
            raise InvalidTokenError(detail="Invalid token payload")
        
        user = self.user_service.get_user_by_id(db, user_id)
        logger.debug(f"Current user validated: {user.id}")
        return user


auth_service = AuthService()