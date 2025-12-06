from typing import List
from sqlalchemy.orm import Session
from uuid import UUID
from app.models.domain import Domain
from app.schemas.domain import DomainCreate, DomainUpdate
from app.repositories.domain_repository import domain_repository
from app.agent.domain_onboarding_agent import domain_onboarding_agent
from app.services.domain_models import DomainInfo
from app.core.logger import setup_logger
from app.core.exceptions import ResourceNotFoundError, AuthorizationError

logger = setup_logger(__name__)


class DomainService:
    def __init__(self):
        self.repository = domain_repository
        self.onboarding_agent = domain_onboarding_agent
    
    def start_onboarding(self) -> tuple[str, str]:
        logger.info("Starting domain onboarding session")
        session_id, initial_question = self.onboarding_agent.start_session()
        return session_id, initial_question
    
    def process_onboarding_message(self, session_id: str, user_message: str) -> tuple[str, bool, DomainInfo]:
        logger.info(f"Processing onboarding message for session: {session_id}")
        return self.onboarding_agent.process_message(session_id, user_message)
    
    def complete_onboarding(self, db: Session, session_id: str, user_id: UUID) -> Domain:
        logger.info(f"Completing onboarding for session: {session_id}")
        
        session_state = self.onboarding_agent.get_session(session_id)
        
        if not session_state["is_complete"]:
            raise ValueError("Onboarding is not complete yet")
        
        collected_info = session_state["collected_info"]
        
        conversation_history = [
            {"role": "assistant" if isinstance(msg, type(msg)) and hasattr(msg, 'content') else "user", 
             "content": msg.content}
            for msg in session_state["messages"]
        ]
        
        domain_data = {
            "user_id": user_id,
            "name": collected_info.name,
            "description": collected_info.description,
            "use_case": collected_info.use_case,
            "target_user": collected_info.target_user,
            "mcp_server_urls": collected_info.mcp_server_urls or [],
            "onboarding_conversation": conversation_history
        }
        
        domain = self.repository.create(db, domain_data)
        
        self.onboarding_agent.clear_session(session_id)
        
        logger.info(f"Domain created: {domain.id}")
        return domain
    
    def get_user_domains(self, db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Domain]:
        logger.debug(f"Fetching domains for user: {user_id}")
        return self.repository.get_by_user(db, str(user_id), skip, limit)
    
    def get_domain(self, db: Session, domain_id: UUID, user_id: UUID) -> Domain:
        logger.debug(f"Fetching domain: {domain_id} for user: {user_id}")
        domain = self.repository.get_by_user_and_id(db, str(user_id), str(domain_id))
        
        if not domain:
            raise ResourceNotFoundError(resource="Domain", identifier=str(domain_id))
        
        return domain
    
    def update_domain(self, db: Session, domain_id: UUID, user_id: UUID, domain_update: DomainUpdate) -> Domain:
        logger.info(f"Updating domain: {domain_id}")
        
        domain = self.get_domain(db, domain_id, user_id)
        
        update_data = domain_update.model_dump(exclude_unset=True)
        
        if not update_data:
            return domain
        
        updated_domain = self.repository.update(db, domain, update_data)
        logger.info(f"Domain updated: {domain_id}")
        
        return updated_domain
    
    def delete_domain(self, db: Session, domain_id: UUID, user_id: UUID) -> bool:
        logger.info(f"Deleting domain: {domain_id}")
        
        domain = self.get_domain(db, domain_id, user_id)
        
        result = self.repository.delete(db, str(domain_id))
        logger.info(f"Domain deleted: {domain_id}")
        
        return result


domain_service = DomainService()