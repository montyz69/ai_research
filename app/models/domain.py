from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Domain(Base):
    __tablename__ = "domains"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    use_case = Column(Text, nullable=True)
    target_user = Column(String, nullable=True)
    mcp_server_urls = Column(JSONB, nullable=True, default=list)
    onboarding_conversation = Column(JSONB, nullable=True, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    user = relationship("User", back_populates="domains")
    notebook_domains = relationship("NotebookDomain", back_populates="domain", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Domain(id={self.id}, name={self.name}, user_id={self.user_id})>"