import os
import sys
import json
from src.core.schema import KnowledgeBase
from src.agents.tutor_agent import TutorAgent

def main():
    print("🚀 Welcome to Adaptive Mastery CLI")
    
    # 1. Load Knowledge Base
    topic = "python_basics"
    db_path = f"data/db/{topic}.json"
    
    if not os.path.exists(db_path):
        print(f"❌ Error: Database not found at {db_path}. Run ingestion first.")
        return

    with open(db_path, "r") as f:
        data = json.load(f)
        # Parse back into Pydantic model
        kb = KnowledgeBase(**data)

    # 2. Init Tutor
    tutor = TutorAgent(kb)
    msg = tutor.start_session(user_id="user_123")
    print(msg)
    print("--------------------------------------------------")

    # 3. Practice Loop
    while True:
        question = tutor.get_next_question()
        
        if not question:
            print("\n🎉 CONGRATULATIONS! You have mastered all skills in this topic.")
            break

        skill_name = kb.skills[question.skill_id].name
        print(f"\n📝 Topic: {skill_name} | Difficulty: {question.difficulty}")
        print(f"Q: {question.content}")
        
        if question.options:
            for idx, opt in enumerate(question.options):
                print(f"   [{idx + 1}] {opt}")
        
        user_input = input("\nYour Answer (type 'exit' to quit): ").strip()
        
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break

        # If multiple choice and user typed number, map to option string
        if question.options and user_input.isdigit():
             idx = int(user_input) - 1
             if 0 <= idx < len(question.options):
                 user_input = question.options[idx]

        result = tutor.submit_answer(question.id, user_input)
        print(f"\n{result.feedback}")
        
        # Show stats
        current_skill_state = tutor.session.skill_states[question.skill_id]
        print(f"📊 Skill Mastery: {current_skill_state.mastery_score * 100:.0f}%")
        print("--------------------------------------------------")

if __name__ == "__main__":
    main()
