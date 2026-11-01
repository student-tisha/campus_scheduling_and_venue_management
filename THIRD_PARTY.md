# Third-party software

All libraries are open source. Versions are the ones installed from `requirements.txt` (backend) and `package.json` (frontend).

## Backend (Python)
| Library | Used for | Licence |
|---|---|---|
| FastAPI | Web API framework | MIT |
| Uvicorn | Server that runs the API | BSD-3-Clause |
| Pydantic and pydantic-settings | Request validation and settings from `.env` | MIT |
| SQLAlchemy | Database access (SQLite locally, PostgreSQL when deployed) | MIT |
| PyJWT | Login tokens | MIT |
| httpx | Calls to the LLM API | BSD-3-Clause |
| psycopg2-binary (deployment only) | PostgreSQL driver | LGPL-3.0 with exceptions |

## Solver
| Library | Used for | Licence |
|---|---|---|
| Google OR-Tools (CP-SAT) | Timetable generation | Apache-2.0 |

## Frontend
| Library | Used for | Licence |
|---|---|---|
| React | UI | MIT |
| Vite | Build tool | MIT |
| Tailwind CSS | Styling | MIT |

> TEAM: Dipan and the frontend owner, please check the Solver and Frontend tables match what you actually installed, and add anything else (for example a router or chart library).

## Data and checker
The dataset (`cit_public.json`) and the official `validator.py` come from the hackathon organisers and are used unmodified.

## Not third-party
The timetable repair, exam scheduler, booking priority engine, validators and parsers are written by the team. No existing timetable project or template was used.
