# AI usage declaration

## 1. Models and APIs the product calls
| Provider | Model | Where in code | What it is used for |
|---|---|---|---|
| Groq API (OpenAI-compatible endpoint, `LLM_BASE_URL`) | Set by `LLM_MODEL` (default `llama-3.3-70b-versatile`) | `backend/app/services/llm.py` | The only AI call in the product |

The same model is used for three jobs, all through `call_llm()`:
1. **Venue request parser** (`backend/app/services/booking_parser.py`): turns English or Hinglish text into a draft booking form.
2. **Faculty assistant** (`backend/app/services/assistant.py`): picks out what a faculty member wants (unavailable, move a session, extra session, show timetable) from a chat message.
3. **Explanation wording** (`backend/app/services/explain.py`): rewords facts that our code already computed into plain sentences.

No other AI model or AI API is used. Scheduling is classical constraint optimisation, not AI.

## 2. What the LLM is NOT allowed to decide
- Whether a timetable, exam schedule, booking or change is valid
- Whether a booking is approved, rejected or given an alternative
- Which request has priority (fixed order in the dataset, and each role's category cap)
- Where a session, exam or booking is placed
- Who may do what (roles are checked from the login, never from message text)
- Whether anything is saved: nothing the LLM returns is stored directly

## 3. How every LLM output is controlled
- **Parser:** the LLM only fills a form. Code converts times to periods, drops unknown room types, features, rooms and groups, and re-validates the draft. The user checks and edits it, then `POST /api/bookings/preview` and `/request` run the booking engine (pure code).
- **Assistant:** the LLM only returns an intent. Code builds the change, the repair code finds the fix, and the validator must show zero hard violations. The Admin approves, and approval runs the validator again.
- **Explanations:** facts come from code. If the LLM wording contains a number that is not in the facts, the wording is discarded and the plain facts are shown.
- **Untrusted text:** messages are treated as data. Attempts to change rules, priority or roles are detected, ignored and flagged to the user.
- **No API, no problem:** if the key is missing, wrong or out of credit, a built-in rules parser takes over and the manual booking form and all decisions keep working. `GET /api/ai/status` shows whether the LLM is available.

## 4. AI tools used to build the project
| Tool | Used by | Parts it helped with |
|---|---|---|
| Claude (Anthropic, claude.ai) | Tisha | Backend: FastAPI app, auth and roles, database and dataset loader, validator, timetable and exam storage, booking priority engine, rescheduling and approval flow, LLM parser, faculty assistant, explanations, dashboard data, admin and export scripts, and these documents. All of it was run and tested by the team. |

> TEAM: Dipan and the frontend owner must add every AI tool they used (assistant, UI generator, etc.) and which files it helped with. Undeclared AI use costs marks.

## 5. Where prompts are kept
**Prompts used inside the product** (in the repo):
- `backend/app/services/booking_parser.py`, variable `SYSTEM`
- `backend/app/services/assistant.py`, variable `SYSTEM`
- `backend/app/services/explain.py`, variable `REWORD`

**Prompts used while building:** written as chat messages to Claude in the claude.ai project "WEB HACKATHON". A summary of what was asked is in `docs/BUILD_PROMPTS.md`.
