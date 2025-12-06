from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.domain import Domain
from app.repositories.base import BaseRepository
from app.core.logger import setup_logger
from app.core.exceptions import DatabaseError

logger = setup_logger(__name__)


class DomainRepository(BaseRepository[Domain]):
    def __init__(self):
        super().__init__(Domain)
    
    def get_by_user(self, db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[Domain]:
        try:
            return db.query(Domain).filter(Domain.user_id == user_id).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error fetching domains by user: {str(e)}")
            raise DatabaseError(detail="Failed to fetch user domains")
    
    def get_by_user_and_id(self, db: Session, user_id: str, domain_id: str) -> Optional[Domain]:
        try:
            return db.query(Domain).filter(
                Domain.user_id == user_id,
                Domain.id == domain_id
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error fetching domain: {str(e)}")
            raise DatabaseError(detail="Failed to fetch domain")


domain_repository = DomainRepository()