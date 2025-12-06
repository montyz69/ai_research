from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.domain import (
    DomainResponse,
    DomainUpdate,
    DomainOnboardingStart,
    DomainOnboardingMessage,
    DomainOnboardingResponse,
    DomainOnboardingComplete
)
from app.services.domain_service import domain_service
from app.core.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/domains", tags=["Domains"])


@router.post("/onboard/start", response_model=DomainOnboardingResponse)
async def start_domain_onboarding(
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Domain onboarding start request from user: {current_user.id}")
    
    session_id, question = domain_service.start_onboarding()
    
    return DomainOnboardingResponse(
        session_id=session_id,
        question=question,
        is_complete=False
    )


@router.post("/onboard/message", response_model=DomainOnboardingResponse)
async def send_onboarding_message(
    request: DomainOnboardingMessage,
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Onboarding message from user: {current_user.id}, session: {request.session_id}")
    
    question, is_complete, collected_info = domain_service.process_onboarding_message(
        request.session_id,
        request.message
    )
    
    response = DomainOnboardingResponse(
        session_id=request.session_id,
        question=question,
        is_complete=is_complete
    )
    
    if is_complete:
        response.collected_info = collected_info.dict()
    
    return response


@router.post("/onboard/complete", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
async def complete_domain_onboarding(
    request: DomainOnboardingComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Completing domain onboarding for user: {current_user.id}, session: {request.session_id}")
    
    domain = domain_service.complete_onboarding(db, request.session_id, current_user.id)
    
    return domain


@router.get("", response_model=List[DomainResponse])
async def list_domains(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"List domains request from user: {current_user.id}")
    
    domains = domain_service.get_user_domains(db, current_user.id, skip, limit)
    
    return domains


@router.get("/{domain_id}", response_model=DomainResponse)
async def get_domain(
    domain_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Get domain request: {domain_id} from user: {current_user.id}")
    
    domain = domain_service.get_domain(db, domain_id, current_user.id)
    
    return domain


@router.put("/{domain_id}", response_model=DomainResponse)
async def update_domain(
    domain_id: UUID,
    domain_update: DomainUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Update domain request: {domain_id} from user: {current_user.id}")
    
    domain = domain_service.update_domain(db, domain_id, current_user.id, domain_update)
    
    return domain


@router.delete("/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_domain(
    domain_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Delete domain request: {domain_id} from user: {current_user.id}")
    
    domain_service.delete_domain(db, domain_id, current_user.id)
    
    return None