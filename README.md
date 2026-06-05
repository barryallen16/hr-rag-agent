# Agentic Enterprise RAG Assistant

An edge-inference AI assistant designed to automate backend workflows. It routes natural language queries to local databases using a Retrieval-Augmented Generation (RAG) pipeline and structured JSON-schema tool calling. Built for fully offline execution to ensure 100% data privacy.
<img width="1854" height="1048" alt="Screenshot from 2026-06-05 17-47-41" src="https://github.com/user-attachments/assets/e3eafb4d-04cc-49e5-bc11-4bf7a817398b" />
<img width="1854" height="1048" alt="Screenshot from 2026-06-05 17-47-47" src="https://github.com/user-attachments/assets/7deb69ec-af61-48e2-afeb-016352b9ff00" />

## Architecture

- **Inference Engine:** LM Studio (Local Edge Execution)
- **Vector Database:** ChromaDB (Semantic Document Search)
- **Relational Database:** SQLite (Transactional Data Handling)
- **Routing:** JSON-schema tool-calling mapped to Python functions

## Project Structure

```text
├── main.py                  # Application entry point
├── config.py                # Inference and environment variables
├── requirements.txt         # Project dependencies
├── data/                    # CSV datasets (Relational & Vector data)
├── database/                # SQLite and ChromaDB access layer
└── agent/                   # LLM orchestration loop and tool schemas

```

## Quick Start

**1. Install dependencies**

```bash
pip install -r requirements.txt

```

**2. Start Local Inference**
Open LM Studio, load a model optimized for function calling (e.g., Qwen 2.5), and start the Local Server on `http://localhost:1234/v1`.

**3. Run the Agent**

```bash
python main.py

```

## Execution Flow

1. **Semantic Routing:** User queries regarding policies map to `vector_search_hr_policy` and execute against ChromaDB.
2. **Action Routing:** Actionable requests (e.g., booking time off) trigger LLM payload extraction, passing arguments to `submit_leave_request` for SQLite database updates.
3. **Validation:** Agent dynamically handles missing arguments by halting execution and prompting the user for required parameters (e.g., specific dates).

