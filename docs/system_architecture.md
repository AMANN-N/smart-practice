# 🏗️ System Architecture & Codebase Status

**Last Updated:** 2026-01-23
**Status:** Phase 1 Prototype (Mocked Agents)

This document serves as the "Source of Truth" for the current codebase structure, logic flow, and data schemas. It will be updated as we implement real AI agents.

---

## 1. Project Structure

```
/Users/amansingh/Personal/smart-practice/
├── config/                  # Configuration files (Empty)
├── data/
│   ├── db/                  # Generated Knowledge Bases (JSON/Vector)
│   │   └── python_basics.json  # Seed DB generated from ingestion
│   └── uploads/             # Raw input files
│       └── python_basics/      # Topic folder
│           └── intro_to_python.txt
├── docs/                    # Documentation
│   └── system_architecture.md  # THIS FILE
├── src/
│   ├── agents/
│   │   ├── ingestion_agent.py  # Builds the DB (Mocked LLM)
│   │   └── tutor_agent.py      # Manages the Practice Session (Adaptive Logic)
│   ├── core/
│   │   └── schema.py           # Shared Pydantic Data Models
│   └── main_cli.py          # Terminal Runner (User Interface)
└── venv/                    # Virtual Environment
```

---

## 2. Core Data Schemas (`src/core/schema.py`)

The system relies on a few key Pydantic models to ensure type safety.

*   **`KnowledgeBase`**: The container for a topic. Holds:
    *   `skills`: A Dict of `SkillNode` (The Graph).
    *   `questions`: A Dict of `Question` (The Content).
*   **`SkillNode`**: A single concept (e.g., "Variables").
    *   `prerequisites`: List of IDs that must be mastered first.
    *   `mastery_threshold`: Score needed to progress (Default: 0.8).
*   **`Question`**:
    *   `difficulty`: BEGINNER, INTERMEDIATE, ADVANCED.
    *   `type`: MULTIPLE_CHOICE, CODE_CORRECTION, etc.
    *   `content`: The question text.
*   **`SessionState`**:
    *   `skill_states`: Tracks mastery score per skill for the user.
    *   `coverage_map`: Tracks which skills have been attempted.

---

## 3. Workflow & Logic

### A. Ingestion Pipeline (`src/agents/ingestion_agent.py`)
*   **Input:** Reads text files from `data/uploads/{topic}/`.
*   **Extraction (Currently Mocked):**
    *   Hardcoded to return 3 skills: `variables`, `data_types`, `loops`.
    *   Hardcoded to generate 2 mock questions per skill (Beginner/Intermediate).
*   **Output:** Saves a `KnowledgeBase` JSON to `data/db/{topic}.json`.

### B. The Tutor Loop (`src/agents/tutor_agent.py`)
This is the "Brain" of the practice session.

1.  **Selection Logic (`get_next_question`):**
    *   **Graph Traversal:** Looks for the first skill where `mastery_score < 0.8` AND `prerequisites` are met.
    *   **Difficulty Scaling:**
        *   If `attempts == 0` -> Start **BEGINNER**.
        *   If `mastery > 0.7` -> Move to **INTERMEDIATE**.
        *   Otherwise (Struggling) -> Stay **BEGINNER**.
2.  **Grading Logic (`submit_answer`):**
    *   Checks exact string match (case-insensitive).
    *   **Correct:** +0.3 Mastery Score. Unlocks next difficulty/skill.
    *   **Incorrect:** -0.1 Mastery Score. Keeps user on current level.

---

## 4. Current Capabilities vs. Planned

| Feature | Current Status | Logic Source |
| :--- | :--- | :--- |
| **Ingestion** | ✅ Working | `src/agents/ingestion_agent.py` (Mocked) |
| **Data Storage** | ✅ Working | JSON Files in `data/db/` |
| **Adaptive Loop** | ✅ Working | `src/agents/tutor_agent.py` (Rule-based) |
| **Concept Extraction** | 🚧 Mocked | Hardcoded Dictionary |
| **Question Generation** | 🚧 Mocked | Hardcoded Strings |
| **Answer Evaluation** | 🚧 Basic | String Matching |
| **LLM Integration** | ❌ Pending | None (Pure Python Logic) |

## 5. Next Steps
1.  **Connect Gemini:** Replace the `_mock_extract_skills` and `_mock_generate_questions` methods in `IngestionAgent` with real API calls.
2.  **Enhance Evaluator:** Use LLM to grade "Code Correction" or "Explanation" questions instead of exact string matching.










##LONG TERM PLAN -> 



1. Ingestion agent - Reads all the input data -> Extracts concepts -> Generates or questions -> Stores in DB

DB contains -> 
- Concepts
- Questions
- Difficulty levels
- Prerequisites
- Mastery threshold
- Coverage map




2. Tutor agent - Manages the practice session -> Adaptive Logic -> Grading Logic
3. 