from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Ingestion
class IngestRequest(BaseModel):
    topic_name: str
    
class IngestResponse(BaseModel):
    message: str
    kb_path: str
    cost_summary: Optional[str] = None

# Session Management
class StartSessionRequest(BaseModel):
    user_id: str
    topic_name: str

class StartSessionResponse(BaseModel):
    message: str
    session_id: str # Path or UUID

# Question Serving
class QuestionResponse(BaseModel):
    id: str
    content: str
    options: List[str]
    difficulty: str
    
class QuestionRequest(BaseModel):
    # GET request usually implies fetching for current active session
    # But for statelessness, maybe pass user_id?
    # We'll use the singleton TutorAgent for this MVP or simple instantiation
    user_id: str
    topic_name: str

# Answer Submission
class SubmitAnswerRequest(BaseModel):
    question_id: str
    user_answer: str

class SubmitAnswerResponse(BaseModel):
    is_correct: bool
    feedback: str
    correct_answer: Optional[str] = None # Only show if wrong? Algo says show always.
