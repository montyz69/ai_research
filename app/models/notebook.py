from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Notebook(Base):
    __tablename__ = "notebooks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    pinecone_namespace = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    user = relationship("User", back_populates="notebooks")
    notebook_domains = relationship("NotebookDomain", back_populates="notebook", cascade="all, delete-orphan")
    sources = relationship("Source", back_populates="notebook", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="notebook", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Notebook(id={self.id}, name={self.name}, user_id={self.user_id})>"


class NotebookDomain(Base):
    __tablename__ = "notebook_domains"
    
    notebook_id = Column(UUID(as_uuid=True), ForeignKey("notebooks.id", ondelete="CASCADE"), primary_key=True)
    domain_id = Column(UUID(as_uuid=True), ForeignKey("domains.id", ondelete="CASCADE"), primary_key=True)
    
    notebook = relationship("Notebook", back_populates="notebook_domains")
    domain = relationship("Domain", back_populates="notebook_domains")
    
    def __repr__(self):
        return f"<NotebookDomain(notebook_id={self.notebook_id}, domain_id={self.domain_id})>"