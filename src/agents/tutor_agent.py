import random
import uuid
import time
from typing import Optional, List
from src.core.schema import (
    KnowledgeBase, SessionState, UserSkillState, 
    Question, AssessmentResult, Difficulty
)

class TutorAgent:
    """
    The Orchestrator of the learning session.
    It manages the user's state, selects questions, and handles the adaptive loop.
    """

    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base
        self.session: Optional[SessionState] = None

    def start_session(self, user_id: str) -> str:
        """Initializes a new session."""
        self.session = SessionState(
            user_id=user_id,
            current_topic=self.kb.topic_name,
            skill_states={
                s_id: UserSkillState(skill_id=s_id) 
                for s_id in self.kb.skills
            },
            coverage_map={s_id: False for s_id in self.kb.skills}
        )
        return f"🎓 Session started for {self.kb.topic_name}!"

    def get_next_question(self) -> Optional[Question]:
        """
        The core Adaptive Logic.
        Decides what to show next based on the Micro-Adaptive Loop.
        """
        if not self.session:
            raise ValueError("Session not started.")

        # 1. Identify the Target Skill
        # Strategy: Find first unmastered skill that has prerequisites met
        target_skill_id = self._select_next_skill()
        
        if not target_skill_id:
            return None # Course Complete!

        self.session.active_skill_id = target_skill_id
        skill_state = self.session.skill_states[target_skill_id]
        
        # 2. Select Difficulty
        # If new skill (attempts=0), start Beginner (Warm-up)
        # If struggling (score low), stay Beginner
        # If progressing, move to Intermediate
        if skill_state.attempts == 0:
            target_difficulty = Difficulty.BEGINNER
        elif skill_state.mastery_score > 0.7:
            target_difficulty = Difficulty.INTERMEDIATE # Scale up
        else:
            target_difficulty = Difficulty.BEGINNER # Reinforce

        # 3. Fetch Question from Bank (or Generate)
        # For now, we fetch. In the future, this calls GeneratorAgent.
        candidates = [
            q for q in self.kb.questions.values()
            if q.skill_id == target_skill_id 
            and q.difficulty == target_difficulty
        ]
        
        if not candidates:
            # Fallback: Just return any question for that skill
            candidates = [q for q in self.kb.questions.values() if q.skill_id == target_skill_id]
        
        if not candidates:
            print(f"⚠️ No questions found for skill {target_skill_id}")
            return None

        # Return a random choice from candidates (Simulating variety)
        return random.choice(candidates)

    def submit_answer(self, question_id: str, user_answer: str) -> AssessmentResult:
        """
        Handles the user's response.
        Updates the internal state model.
        """
        question = self.kb.questions[question_id]
        is_correct = (user_answer.strip().lower() == question.correct_answer.strip().lower())
        
        # Grading Logic (Simplistic for now)
        feedback = "Correct! " + question.explanation if is_correct else f"Incorrect. {question.explanation}"
        
        # Update State (The 'Update Engine')
        skill_id = question.skill_id
        skill_state = self.session.skill_states[skill_id]
        
        skill_state.attempts += 1
        skill_state.history.append(question_id)
        
        if is_correct:
            skill_state.correct_streak += 1
            # Simple mastery boost
            skill_state.mastery_score = min(1.0, skill_state.mastery_score + 0.3)
            # Mark coverage
            self.session.coverage_map[skill_id] = True
        else:
            skill_state.correct_streak = 0
            # Penalty
            skill_state.mastery_score = max(0.0, skill_state.mastery_score - 0.1)

        return AssessmentResult(
            question_id=question_id,
            user_answer=user_answer,
            is_correct=is_correct,
            feedback=feedback,
            timestamp=time.time()
        )

    def _select_next_skill(self) -> Optional[str]:
        """Traverses the DAG to find the next learnable skill."""
        
        # 1. Priority: Active skill if not mastered
        if self.session.active_skill_id:
            active_state = self.session.skill_states[self.session.active_skill_id]
            if active_state.mastery_score < 0.8: # Threshold from Schema
                return self.session.active_skill_id
        
        # 2. Find next unlockable skill
        # (A skill is unlockable if all its prerequisites are mastered)
        for skill_id, node in self.kb.skills.items():
            state = self.session.skill_states[skill_id]
            if state.mastery_score >= 0.8:
                continue # Already done
            
            # Check prereqs
            prereqs_met = all(
                self.session.skill_states[p_id].mastery_score >= 0.8 
                for p_id in node.prerequisites
            )
            
            if prereqs_met:
                return skill_id
                
        return None # No skills left (or blocked)
