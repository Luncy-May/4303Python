# 4303 Final Projet

Comparative security analysis of AI-generated backend code across multiple LLMs (ChatGPT, Claude, GitHub Copilot).

## Structure

- `prompts/` — Standardized prompts used to generate code and elicit exploits
- `generated_code/` — Raw, unmodified LLM outputs for each task
- `apps/` — Runnable FastAPI apps assembled from generated code for exploitation testing
- `analysis/` — Static analysis results (Bandit, Semgrep)
- `exploitation/` — Exploit scripts and LLM responses to exploitation prompts
- `results/` — Aggregated findings, summary CSVs, and report figures
- `report/` — Written report sections

## Tasks

| Task | File |
|------|------|
| Login system | `prompts/generation/login_system.md` |
| User registration | `prompts/generation/user_registration.md` |
| Database search | `prompts/generation/database_search.md` |
| File upload | `prompts/generation/file_upload.md` |

## Running Static Analysis

```bash
bash analysis/run_analysis.sh
```

## Requirements

- Python 3.10+
- `bandit`, `semgrep` (install globally or in a venv)
- `fastapi`, `uvicorn` per app (see each `apps/<model>/requirements.txt`)
