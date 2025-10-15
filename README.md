# AI Hackathon Agent

## Project Goal
To build a simple, locally-hosted AI assistant/agentic system focused on [**Insert Your Specific Agent Goal Here** - e.g., answering questions about a set of documents, performing data analysis, etc.].

## Technology Stack
| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Backend/Core Logic** | **Python** / **FastAPI** | Standard for AI, simple API structure. |
| **Agent Framework** | **LangChain** or **LlamaIndex** | Abstraction layer for agentic workflows. |
| **Vector Store** | **ChromaDB** | Simple, file-based vector database for RAG. |
| **State Database** | **SQLite** | Simple, file-based SQL store for state/memory. |
| **Frontend** | **Streamlit** | Rapid prototyping of a web UI using only Python. |
| **LLM/Embedding** | **OpenAI API** (`gpt-4o`, `text-embedding-3-small`) | High performance, easy integration. |

## Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone [Your Repo URL]
    cd ai-hackathon-agent
    ```
2.  **Create Environment:** (Recommend using a virtual environment)
    ```bash
    python -m venv venv
    source venv/bin/activate  # macOS/Linux
    # venv\Scripts\activate   # Windows
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure API Key:**
    Create a file named **`.env`** in the root directory and add your key:
    ```
    OPENAI_API_KEY="sk-..."
    ```
5.  **Run the Backend:**
    ```bash
    # Command to be added once main.py is written
    ```
6.  **Run the Frontend:**
    ```bash
    # Command to be added once app.py is written
    ```

## Development Status
* Initial Structure Complete.
* Backend FastAPI development commencing.