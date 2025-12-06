from typing import TypedDict, List, Dict, Any, Annotated
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langsmith import traceable
from app.config import settings
from app.core.logger import setup_logger
from app.services.domain_models import DomainInfo, NextQuestion
import uuid
import os

logger = setup_logger(__name__)

if settings.LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = str(settings.LANGCHAIN_TRACING_V2).lower()
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT


class OnboardingState(TypedDict):
    session_id: str
    messages: List[Any]
    collected_info: DomainInfo
    is_complete: bool
    next_question: str


class DomainOnboardingAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.3
        )
        self.sessions: Dict[str, OnboardingState] = {}
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(OnboardingState)
        
        workflow.add_node("extract_info", self._extract_information)
        workflow.add_node("generate_question", self._generate_next_question)
        
        workflow.set_entry_point("extract_info")
        
        workflow.add_edge("extract_info", "generate_question")
        workflow.add_conditional_edges(
            "generate_question",
            self._should_continue,
            {
                "continue": END,
                "end": END
            }
        )
        
        return workflow.compile()
    
    def _extract_information(self, state: OnboardingState) -> OnboardingState:
        try:
            if not state["messages"]:
                return state
            
            last_message = state["messages"][-1]
            if not isinstance(last_message, HumanMessage):
                return state
            
            system_prompt = f"""You are an information extraction assistant. Extract domain information from the user's message.

Current collected information:
- Name: {state["collected_info"].name or "Not provided"}
- Description: {state["collected_info"].description or "Not provided"}
- Use Case: {state["collected_info"].use_case or "Not provided"}
- Target User: {state["collected_info"].target_user or "Not provided"}
- MCP Server URLs: {", ".join(state["collected_info"].mcp_server_urls) if state["collected_info"].mcp_server_urls else "Not provided"}

Extract any new information from the user's latest message and update the fields accordingly. If the user hasn't provided new information for a field, keep the existing value."""

            structured_llm = self.llm.with_structured_output(DomainInfo)
            
            extracted_info = structured_llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=last_message.content)
            ])
            
            current_info = state["collected_info"]
            updated_info = DomainInfo(
                name=extracted_info.name or current_info.name,
                description=extracted_info.description or current_info.description,
                use_case=extracted_info.use_case or current_info.use_case,
                target_user=extracted_info.target_user or current_info.target_user,
                mcp_server_urls=extracted_info.mcp_server_urls or current_info.mcp_server_urls
            )
            
            state["collected_info"] = updated_info
            logger.info(f"Extracted info for session {state['session_id']}: {updated_info.dict()}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error extracting information: {str(e)}")
            return state
    
    def _generate_next_question(self, state: OnboardingState) -> OnboardingState:
        try:
            info = state["collected_info"]
            
            required_fields = {
                "name": info.name,
                "description": info.description,
                "use_case": info.use_case,
                "target_user": info.target_user
            }
            
            missing_fields = [field for field, value in required_fields.items() if not value]
            
            system_prompt = f"""You are a domain onboarding assistant. Your goal is to collect information about a domain the user wants to create.

Required fields (mandatory):
- name: Domain name
- description: Brief description of the domain
- use_case: Primary use case or problem it solves
- target_user: Who will use this domain

Optional fields:
- mcp_server_urls: MCP server URLs (can be empty)

Current collected information:
- Name: {info.name or "Not provided"}
- Description: {info.description or "Not provided"}
- Use Case: {info.use_case or "Not provided"}
- Target User: {info.target_user or "Not provided"}
- MCP Server URLs: {", ".join(info.mcp_server_urls) if info.mcp_server_urls else "Not provided"}

Missing required fields: {", ".join(missing_fields) if missing_fields else "None"}

Generate the next question to ask the user. If all required fields are collected, mark as complete. Be conversational and friendly."""

            structured_llm = self.llm.with_structured_output(NextQuestion)
            
            result = structured_llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content="What should I ask next?")
            ])
            
            state["next_question"] = result.question
            state["is_complete"] = result.is_complete and len(missing_fields) == 0
            
            state["messages"].append(AIMessage(content=result.question))
            
            logger.info(f"Generated question for session {state['session_id']}: {result.question}, Complete: {state['is_complete']}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error generating question: {str(e)}")
            state["next_question"] = "Could you tell me more about your domain?"
            return state
    
    def _should_continue(self, state: OnboardingState) -> str:
        return "end" if state["is_complete"] else "continue"
    
    @traceable(name="start_onboarding_session")
    def start_session(self) -> tuple[str, str]:
        session_id = str(uuid.uuid4())
        
        initial_state: OnboardingState = {
            "session_id": session_id,
            "messages": [],
            "collected_info": DomainInfo(),
            "is_complete": False,
            "next_question": ""
        }
        
        initial_question = "Hi! I'll help you onboard a new domain. Let's start with the basics - what would you like to name this domain?"
        initial_state["messages"].append(AIMessage(content=initial_question))
        initial_state["next_question"] = initial_question
        
        self.sessions[session_id] = initial_state
        
        logger.info(f"Started onboarding session: {session_id}")
        
        return session_id, initial_question
    
    @traceable(name="process_onboarding_message")
    def process_message(self, session_id: str, user_message: str) -> tuple[str, bool, DomainInfo]:
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        state = self.sessions[session_id]
        
        state["messages"].append(HumanMessage(content=user_message))
        
        updated_state = self.graph.invoke(state)
        
        self.sessions[session_id] = updated_state
        
        logger.info(f"Processed message for session {session_id}, Complete: {updated_state['is_complete']}")
        
        return (
            updated_state["next_question"],
            updated_state["is_complete"],
            updated_state["collected_info"]
        )
    
    def get_session(self, session_id: str) -> OnboardingState:
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        return self.sessions[session_id]
    
    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared session: {session_id}")


domain_onboarding_agent = DomainOnboardingAgent()