from typing import List, Optional, Dict, Any, ForwardRef
from enum import Enum
from pydantic import BaseModel, Field

class Difficulty(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    CODE_CORRECTION = "code_correction"
    CONCEPT_EXPLANATION = "concept_explanation"
    CODING_IMPLEMENTATION = "coding_implementation"

class Question(BaseModel):
    """A single practice question."""
    id: str
    difficulty: Difficulty
    type: QuestionType
    content: str = Field(..., description="The main text or code of the question")
    options: Optional[List[str]] = Field(None, description="For multiple choice questions")
    correct_answer: str = Field(..., description="The definitive correct answer or key")
    explanation: str = Field(..., description="Explanation of why the answer is correct")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Source file, generation timestamp, etc.")

# Forward reference for recursive definition
KnowledgeNodeRef = ForwardRef('KnowledgeNode')

class KnowledgeNode(BaseModel):
    """
    A generic node in the knowledge hierarchy.
    Can be a generic container (Topic/Sub-topic) or a Leaf (Concept/Variation).
    """
    id: str
    name: str
    description: str
    path: str = Field(..., description="Breadcrumb path e.g. 'Python > Loops > For Loops'")
    
    # Hierarchy
    parent_id: Optional[str] = None
    children: List[KnowledgeNodeRef] = Field(default_factory=list)
    is_leaf: bool = False
    
    # Leaf Content (Only populated if is_leaf=True)
    questions: Dict[Difficulty, List[Question]] = Field(default_factory=dict)
    
    # Progression
    prerequisites: List[str] = Field(default_factory=list, description="IDs of other nodes")

    class Config:
        arbitrary_types_allowed = True

class KnowledgeBase(BaseModel):
    """The entire structure starting from the root."""
    topic_name: str
    root: KnowledgeNode
    # Flat map for O(1) lookups during specific operations
    node_map: Dict[str, KnowledgeNode] = Field(default_factory=dict, description="ID -> Node reference")

class AssessmentResult(BaseModel):
    """The result of a user answering a question."""
    question_id: str
    user_answer: str
    is_correct: bool
    error_type: Optional[str] = None
    feedback: str
    timestamp: float

class UserSkillState(BaseModel):
    """Tracks the user's progress on a specific node."""
    node_id: str
    mastery_score: float = 0.0
    attempts: int = 0
    correct_streak: int = 0
    history: List[str] = Field(default_factory=list)

class SessionState(BaseModel):
    """The live state of a practice session."""
    user_id: str
    current_topic: str
    node_states: Dict[str, UserSkillState] = Field(default_factory=dict)
    active_node_id: Optional[str] = None
    coverage_map: Dict[str, bool] = Field(default_factory=dict)

# Resolve forward refs
KnowledgeNode.update_forward_refs()
