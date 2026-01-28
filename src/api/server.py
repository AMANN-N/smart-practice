from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.api.models import (
    IngestRequest, IngestResponse,
    StartSessionRequest, StartSessionResponse,
    QuestionResponse, SubmitAnswerRequest, SubmitAnswerResponse
)
from src.agents.ingestion_agent import IngestionAgent
from src.agents.tutor_agent import TutorAgent
import os

app = FastAPI(title="Smart Practice API")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Agent Instances (For MVP - ideally per-session or DB backed)
# We will reload TutorAgent per request based on session file persistence, 
# ensuring statelessness across restarts.
tutor_agent = TutorAgent()
ingestion_agent = IngestionAgent()

@app.get("/api/health")
def health_check():
    return {"status": "running"}

@app.post("/api/ingest", response_model=IngestResponse)
def ingest_topic(req: IngestRequest):
    try:
        # Check if dummy data exists for specific known demos
        topic_path = os.path.join("data/uploads", req.topic_name)
        if not os.path.exists(topic_path):
             # Auto-create dummy for convenience if it doesn't exist
             os.makedirs(topic_path, exist_ok=True)
             with open(os.path.join(topic_path, "intro.txt"), "w") as f:
                 f.write(f"Introduction to {req.topic_name}.")

        kb = ingestion_agent.load_topic(req.topic_name)
        
        # Save happens inside agent, but let's confirm
        kb_path = f"data/db/{kb.topic_name}.json"
        
        return IngestResponse(
            message=f"Successfully ingested {req.topic_name}",
            kb_path=kb_path
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/session/start", response_model=StartSessionResponse)
def start_session(req: StartSessionRequest):
    try:
        msg = tutor_agent.start_session(req.user_id, req.topic_name)
        return StartSessionResponse(
            message=msg,
            session_id=tutor_agent.session_path
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session/next", response_model=QuestionResponse)
def get_next_question():
    try:
        # Assuming single active session for MVP
        # In prod, we'd need session_id lookup
        q = tutor_agent.get_next_question()
        
        if not q:
            # Signal completion? 
            # Return a special "Done" question or 204?
            # Let's return a dummy "Session Complete" question object for frontend simplicity
            return QuestionResponse(
                id="DONE",
                content="🎉 Topic Mastered! You have completed all available concepts.",
                options=[],
                difficulty="completed"
            )
            
        return QuestionResponse(
            id=q.id,
            content=q.content,
            options=q.options,
            difficulty=q.difficulty.value
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/session/submit", response_model=SubmitAnswerResponse)
def submit_answer(req: SubmitAnswerRequest):
    try:
        result = tutor_agent.submit_answer(req.question_id, req.user_answer)
        return SubmitAnswerResponse(
            is_correct=result.is_correct,
            feedback=result.feedback,
            correct_answer=None # Hidden unless we want to expilcitly show it separate from feedback
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.staticfiles import StaticFiles
import os

# ... existing endpoints ...

@app.get("/api/kb/graph")
def get_graph():
    """Returns the Knowledge Graph structure for Cytoscape.js"""
    if not tutor_agent.kb:
        return {"elements": []}
    
    elements = []
    
    # BFS Traversal
    stack = [tutor_agent.kb.root]
    while stack:
        node = stack.pop(0)
        
        # Determine Status
        status = "pending"
        if node.id == tutor_agent.session.active_node_id:
            status = "active"
        elif tutor_agent.session.coverage_map.get(node.id):
            status = "mastered"
            
        # Add Node
        elements.append({
            "data": {
                "id": node.id,
                "label": node.name,
                "status": status,
                "type": "leaf" if node.is_leaf else "topic"
            }
        })
        
        # Add Edge
        if node.parent_id:
            elements.append({
                "data": {
                    "source": node.parent_id,
                    "target": node.id
                }
            })
            
        stack.extend(node.children)
        
    return {"elements": elements}

@app.get("/api/session/status")
def get_session_status():
    if not tutor_agent.session:
        return {"active": False}
        
    active_id = tutor_agent.session.active_node_id
    if not active_id:
        return {"active": True, "mastered_all": True}
        
    node = tutor_agent.kb.node_map.get(active_id)
    breadcrumb = node.path.replace(" > ", " / ") if node else ""
    
    state = tutor_agent.session.node_states.get(active_id)
    streak = state.correct_streak if state else 0
    
    return {
        "active": True,
        "breadcrumb": breadcrumb,
        "streak": streak,
        "target_streak": Config.TUTOR_MASTERY_STREAK
    }

# Create web dir if not exists
os.makedirs("src/web", exist_ok=True)
# Mount Static Files (Must be last to avoid catching API routes)
app.mount("/", StaticFiles(directory="src/web", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
