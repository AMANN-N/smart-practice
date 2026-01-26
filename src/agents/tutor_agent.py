import os
import json
import uuid
from typing import Optional, Dict, List
import google.generativeai as genai

from src.core.schema import (
    KnowledgeBase, KnowledgeNode, Question, Difficulty, 
    SessionState, UserSkillState, AssessmentResult, QuestionType
)
from src.core.config import Config

class TutorAgent:
    """
    Manages the practice session, serving questions adaptively based on user performance.
    """
    def __init__(self, session_path: str = "data/sessions/current_session.json"):
        self.session_path = session_path
        self.kb: Optional[KnowledgeBase] = None
        self.session: Optional[SessionState] = None
        self.model = genai.GenerativeModel(Config.LLM_MODEL_NAME) if Config.get_api_key() else None

    def start_session(self, user_id: str, topic_name: str) -> str:
        """Starts a new session (or loads existing) for a topic."""
        # 1. Load Knowledge Base
        kb_path = f"data/db/{topic_name}.json"
        if not os.path.exists(kb_path):
            raise FileNotFoundError(f"Knowledge Base for '{topic_name}' not found. Run ingestion first.")
        
        with open(kb_path, "r") as f:
            data = json.load(f)
            # Reconstruct Pydantic models? For now, dict access might be easier 
            # or we parse back to schema. Let's parse strictly for type safety.
            self.kb = KnowledgeBase(**data)

        # 2. Init Session
        self.session = SessionState(
            user_id=user_id,
            current_topic=topic_name,
            node_states={},
            coverage_map={},
            active_node_id=None
        )
        self._save_session()
        return f"Session started for {topic_name}"

    def get_next_question(self) -> Optional[Question]:
        """
        Core Logic: Determines the next question to ask.
        Returns None if topic is fully mastered.
        """
        if not self.session or not self.kb:
            raise ValueError("Session not initialized.")

        # 1. Scope Selection (Graph Traversal)
        active_node = self._get_or_select_active_node()
        if not active_node:
            return None # Implementation: All done!

        # 2. Difficulty Selection (Adaptive Probe)
        node_state = self.session.node_states.get(active_node.id)
        # Default state if new node
        if not node_state:
            node_state = UserSkillState(node_id=active_node.id)
            # Start at configured difficulty
            try:
                # We store current_difficulty in UserSkillState? 
                # Schema didn't have it explicitly, only 'mastery_score'.
                # Let's add specific logic here or rely on score.
                # ACTUALLY: The Algo says "Start Intermediate".
                # I'll modify UserSkillState on the fly or just use a helper dict?
                # Better: Let's assume 'mastery_score' maps to difficulty roughly, 
                # or simpler: Add a transient field. 
                # For this implementation, I will just pick based on history.
                pass 
            except: pass
            self.session.node_states[active_node.id] = node_state
        
        # Determine current difficulty based on recent history
        target_diff = self._determine_difficulty(node_state)
        
        # 3. Fetch Question
        question = self._fetch_available_question(active_node, target_diff, node_state.history)
        
        if not question:
            # Bucket empty? Trigger Dynamic Gen
            # We generate dynamic questions for ANY difficulty if we run out, 
            # ensuring the user must hit the streak to proceed.
            print(f"      ⚠️ Running low on {target_diff.value} questions. Generating dynamic...")
            question = self._generate_dynamic_question(active_node, target_diff)

        return question

    def submit_answer(self, question_id: str, user_answer: str) -> AssessmentResult:
        """
        Evaluates answer, updates state (promote/demote), saves session.
        """
        # Find question in KB (slow linear search or map? schema has node_map, but not global q map)
        # Let's search efficient path: Active Node
        q_obj = None
        active_node = self.kb.node_map[self.session.active_node_id]
        
        # Search buckets
        for diff in active_node.questions:
            for q in active_node.questions[diff]:
                if q.id == question_id:
                    q_obj = q
                    break
            if q_obj: break
        
        if not q_obj:
            raise ValueError("Question not found in active node.")

        # Check correctness
        user_ans = user_answer.strip()
        correct_ans = q_obj.correct_answer.strip().upper()
        
        is_correct = False
        
        # 1. Direct Match (Letter vs Letter OR Text vs Text)
        if user_ans.upper() == correct_ans:
            is_correct = True
        # 2. Text vs Letter (User sent text, Correct is 'C')
        elif user_ans in q_obj.options:
             # Find which letter this text corresponds to
             idx = q_obj.options.index(user_ans)
             # Map index 0->A, 1->B, etc.
             expected_letter = chr(ord('A') + idx) 
             if expected_letter == correct_ans:
                 is_correct = True

        # Update State
        node_state = self.session.node_states[active_node.id]
        node_state.attempts += 1
        node_state.history.append(question_id)
        
        feedback = ""
        
        if is_correct:
            node_state.correct_streak += 1
            feedback = f"✅ Correct! {q_obj.explanation}"
            
            # Promotion Logic
            if q_obj.difficulty == Difficulty.INTERMEDIATE:
                if node_state.correct_streak >= Config.TUTOR_MASTERY_STREAK:
                     feedback += "\n🚀 FAST-TRACK: Moving to Advanced!"
            elif q_obj.difficulty == Difficulty.ADVANCED:
                if node_state.correct_streak >= Config.TUTOR_MASTERY_STREAK:
                     feedback += "\n🏆 CONCEPT MASTERED!"
                     # Mark as done? We just clear active_node_id so loop picks next
                     self.session.active_node_id = None
                     self.session.coverage_map[active_node.id] = True
        else:
            node_state.correct_streak = 0
            feedback = f"❌ Incorrect. Correct answer: {q_obj.correct_answer}.\n{q_obj.explanation}"
            # Demotion handled implicitly by _determine_difficulty next turn
        
        self._save_session()
        
        return AssessmentResult(
            question_id=question_id,
            user_answer=user_answer,
            is_correct=is_correct,
            feedback=feedback,
            timestamp=0
        )

    # --- Helpers ---

    def _get_or_select_active_node(self) -> Optional[KnowledgeNode]:
        """DFS (Document Order) to find next unmastered leaf."""
        if self.session.active_node_id:
            return self.kb.node_map[self.session.active_node_id]
        
        # Traversal: Find first LEAF that is NOT in coverage_map
        # Use a stack for DFS (Last-In, First-Out)
        # We start with Root
        stack = [self.kb.root]
        
        while stack:
            node = stack.pop() # Take from top
            
            if node.is_leaf:
                if not self.session.coverage_map.get(node.id):
                    # Found one!
                    self.session.active_node_id = node.id
                    return node
            
            # DFS: Push children in REVERSE order so the first child is popped first
            # e.g. Children [A, B]. Push B, then A. Stack: [B, A]. Pop A.
            for child in reversed(node.children):
                stack.append(child)
            
        return None

    def _determine_difficulty(self, state: UserSkillState) -> Difficulty:
        """
        State Machine for Difficulty:
        - No history -> Intermediate (Probe)
        - Streak > X on Int -> Adv
        - Fail on Int -> Beg
        - Fail on Adv -> Int
        """
        if not state.history:
            return Difficulty(Config.TUTOR_STARTING_DIFFICULTY)
        
        # Look at last attempt?
        # A simple heuristic:
        # If Streak > X -> Promote
        # If Streak == 0 -> Demote
        
        # We need to know the difficulty of the LAST question asked.
        # But we don't store that in UserSkillState directly (only QID).
        # Optimization: Just use a transient counter or simple logic:
        
        # Logic:
        # If High Streak -> Advanced
        if state.correct_streak >= Config.TUTOR_MASTERY_STREAK:
            return Difficulty.ADVANCED
        
        # If 0 Streak (Last was fail)
        if state.correct_streak == 0:
             return Difficulty.BEGINNER
             
        # Normal
        return Difficulty.INTERMEDIATE

    def _fetch_available_question(self, node: KnowledgeNode, difficulty: Difficulty, history: List[str]) -> Optional[Question]:
        available = node.questions.get(difficulty, [])
        for q in available:
            if q.id not in history:
                return q
        return None

    def _generate_dynamic_question(self, node: KnowledgeNode, difficulty: Difficulty) -> Question:
        """Call LLM to generate a fresh question similar to existing ones."""
        if not self.model:
            raise Exception("No LLM available for dynamic generation.")
            
        prompt = f"""
        Generate a NEW 1-shot practice question for concept: "{node.name}".
        Difficulty: {difficulty.value}
        Description: {node.description}
        
        The user has exhausted static questions. Create a variation.
        
        Output JSON:
        {{
            "content": "...",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "...",
             "explanation": "..."
        }}
        """
        try:
            resp = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            data = json.loads(resp.text)
            
            # Handle edge case where LLM returns a list instead of single object
            if isinstance(data, list):
                if not data: raise ValueError("Empty response list")
                data = data[0]
                
            q = Question(
                id=str(uuid.uuid4()),
                difficulty=difficulty,
                type=QuestionType.MULTIPLE_CHOICE,
                content=data["content"],
                options=data.get("options", []),
                correct_answer=data["correct_answer"],
                explanation=data.get("explanation", ""),
                metadata={"generated": True}
            )
            
            # CRITICAL FIX: Save to node so submit_answer can find it!
            if difficulty not in node.questions:
                node.questions[difficulty] = []
            node.questions[difficulty].append(q)
            
            return q
        except Exception as e:
            print(f"Dynamic Gen Failed: {e}")
            return None

    def _save_session(self):
        os.makedirs(os.path.dirname(self.session_path), exist_ok=True)
        with open(self.session_path, "w") as f:
            f.write(self.session.model_dump_json(indent=2))

if __name__ == "__main__":
    # CLI Demo
    agent = TutorAgent()
    try:
        print(agent.start_session("user_123", "python_basics"))
        
        # Simulate 3 turns
        for i in range(3):
            print(f"\n--- Turn {i+1} ---")
            q = agent.get_next_question()
            if not q:
                print("🎉 Session Complete!")
                break
                
            print(f"[{q.difficulty.name}] {q.content}")
            print(f"Options: {q.options}")
            
            # Simulate generic answer "A" - In our Ingestion demo, correct answers were mostly "A" or similar.
            # Let's try to actually answer correctly if possible, or just fail and see remediation.
            # Using 'A' is a safe bet for a blind test.
            ans = "A" 
            print(f"> User Answer: {ans}")
            
            result = agent.submit_answer(q.id, ans)
            print(f"Result: {result.is_correct}")
            print(f"Feedback: {result.feedback}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
