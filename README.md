# 4303 Final Project

Comparative security analysis of AI-generated backend code across three LLMs: **ChatGPT**, **Claude**, and **GitHub Copilot**.

Each LLM was given identical prompts to generate Python FastAPI backend components. The generated code was then analyzed for security vulnerabilities using static analysis tools and manual exploitation testing.

## Structure

| Directory | Purpose |
|-----------|---------|
| `prompts/` | Standardized prompts used for code generation and exploitation elicitation |
| `generated_code/` | Raw, unmodified LLM outputs organized by model and task |
| `apps/` | Runnable FastAPI apps assembled from generated code for exploitation testing |
| `analysis/` | Static analysis results (Bandit, Semgrep) |
| `exploitation/` | Exploit scripts and LLM responses to adversarial prompts |
| `results/` | Aggregated findings, vulnerability summary CSV, and report figures |
| `report/` | Written report sections |

## Generation Tasks

| Task | Prompt |
|------|--------|
| Login system | `prompts/generation/login_system.md` |
| Database search | `prompts/generation/database_search.md` |
| File upload | `prompts/generation/file_upload.md` |

## Running an App

```bash
pip install -r apps/<model>/requirements.txt
uvicorn apps.<model>.main:app --reload --port 8000
```

Replace `<model>` with `claude`, `chatgpt`, or `copilot`. Interactive API docs at `http://localhost:8000/docs`.

## Static Analysis

```bash
# You will need to install bandit and semgrep
# Bandit: pip install bandit
# Semgrep: pip install semgrep

# Run bandit
bandit -r generated_code/<model>/ -o analysis/bandit/<model>_report.txt

# Run semgrep
semgrep --config auto generated_code/<model>/ --output analysis/semgrep/<model>_report.txt
```

## Exploitation Testing

Adversarial prompts are in `prompts/exploitation/`. LLM responses (refusal vs. compliance) are logged in `exploitation/<category>/llm_responses.md`. Exploit scripts are in `exploitation/<category>/`. 

## Requirements

- Python 3.10+
- `bandit`, `semgrep` (install globally or in a venv)
- `fastapi`, `uvicorn` per app (see each `apps/<model>/requirements.txt`)
