from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database import Base
from app.core.logger import setup_logger
from app.core.exceptions import DatabaseError, ResourceNotFoundError

logger = setup_logger(__name__)

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    def create(self, db: Session, obj_in: Dict[str, Any]) -> ModelType:
        try:
            db_obj = self.model(**obj_in)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Created {self.model.__name__} with id: {db_obj.id}")
            return db_obj
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating {self.model.__name__}: {str(e)}")
            raise DatabaseError(detail=f"Failed to create {self.model.__name__}")
    
    def get_by_id(self, db: Session, id: Any) -> Optional[ModelType]:
        try:
            obj = db.query(self.model).filter(self.model.id == id).first()
            if not obj:
                logger.warning(f"{self.model.__name__} not found with id: {id}")
            return obj
        except SQLAlchemyError as e:
            logger.error(f"Error fetching {self.model.__name__} by id: {str(e)}")
            raise DatabaseError(detail=f"Failed to fetch {self.model.__name__}")
    
    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        try:
            query = db.query(self.model)
            
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        query = query.filter(getattr(self.model, key) == value)
            
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error fetching multiple {self.model.__name__}: {str(e)}")
            raise DatabaseError(detail=f"Failed to fetch {self.model.__name__} list")
    
    def update(self, db: Session, db_obj: ModelType, obj_in: Dict[str, Any]) -> ModelType:
        try:
            for field, value in obj_in.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Updated {self.model.__name__} with id: {db_obj.id}")
            return db_obj
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating {self.model.__name__}: {str(e)}")
            raise DatabaseError(detail=f"Failed to update {self.model.__name__}")
    
    def delete(self, db: Session, id: Any) -> bool:
        try:
            obj = self.get_by_id(db, id)
            if not obj:
                raise ResourceNotFoundError(resource=self.model.__name__, identifier=str(id))
            
            db.delete(obj)
            db.commit()
            logger.info(f"Deleted {self.model.__name__} with id: {id}")
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting {self.model.__name__}: {str(e)}")
            raise DatabaseError(detail=f"Failed to delete {self.model.__name__}")