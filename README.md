# Adaptive Mastery Platform

An adaptive learning system that builds mastery through micro-adaptive loops and LLM-generated content.

## Project Structure

*   **`src/`**: Source code
    *   **`src/agents/`**: The AI agents (Curriculum Architect, Tutor, Generator, Evaluator).
    *   **`src/core/`**: Core data structures, schemas, and shared utilities.
*   **`data/`**: Data storage
    *   **`data/uploads/`**: Drop your PDFs/Text files here, organized by topic folder (e.g., `data/uploads/binary_search/`).
    *   **`data/db/`**: Local JSON/Vector database files.
*   **`config/`**: Configuration files (prompts, settings).

## Getting Started

1.  **Place Data:** Create a folder in `data/uploads/` (e.g., `data/uploads/python_basics/`) and add your study materials.
2.  **Run Ingestion:** (Coming soon) Run the ingestion script to build the Skill Graph.
3.  **Start Session:** (Coming soon) Run the main practice loop.
