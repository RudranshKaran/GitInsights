# GitInsight Backend

## Phase 0: Project Scaffolding & Contracts (Foundation)

This is the foundational structure for the GitInsight backend API.

## Structure

```
backend/
├── app/
│   ├── api/              # API endpoints and route handlers
│   │   ├── __init__.py
│   │   └── health.py     # Health check endpoint
│   ├── services/         # Business logic services (future)
│   │   └── __init__.py
│   ├── pipelines/        # Evaluation pipeline orchestration (future)
│   │   └── __init__.py
│   ├── schemas/          # Pydantic data models
│   │   ├── __init__.py
│   │   └── models.py     # All data contracts
│   ├── prompts/          # LLM prompt templates (future)
│   │   └── __init__.py
│   ├── utils/            # Utility functions (future)
│   │   └── __init__.py
│   ├── __init__.py
│   └── main.py           # FastAPI application entry point
└── requirements.txt      # Python dependencies
```

## Installation

1. Create a virtual environment (recommended):
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

Start the development server:
```bash
cd app
python main.py
```

Or using uvicorn directly:
```bash
uvicorn app.main:app --reload
```

The API will be available at: `http://localhost:8000`

## API Documentation

Once running, access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Available Endpoints

### Health Check
- **GET** `/health`
- Returns: `{"status": "ok"}`

## Data Contracts

The following Pydantic models are defined in `app/schemas/models.py`:

- **RepositoryData**: Parsed repository information
- **RuleEvaluationResult**: Rule-based evaluation output
- **AIInsightResult**: AI-generated insights
- **FinalReport**: Complete evaluation report

## Development Status

✅ Phase 0 Complete:
- Directory structure created
- FastAPI application skeleton
- Health check endpoint
- Data contracts defined

🔜 Next Phases:
- GitHub data fetching
- Rule-based evaluation
- AI integration
- Report generation
