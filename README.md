<div align="center">

# BusFactor

### Your grade is shared. Your understanding shouldn't be isolated.

An AI agent that finds the project decisions only one teammate can explain, organises peer teaching between teammates, and verifies the transfer with a new question.

[![Tests](https://github.com/Sajjad-Shahali/BusFactor_Reply_ai_on_campus/actions/workflows/tests.yml/badge.svg)](https://github.com/Sajjad-Shahali/BusFactor_Reply_ai_on_campus/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Pydantic](https://img.shields.io/badge/Models-Pydantic%202-E92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![SQLite](https://img.shields.io/badge/Storage-SQLite-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](#run-with-docker)
[![Lint: ruff](https://img.shields.io/badge/lint-ruff-261230?logo=ruff&logoColor=D7FF64)](pyproject.toml)
[![Types: mypy](https://img.shields.io/badge/types-mypy-2A6DB2)](pyproject.toml)
[![WCAG AA](https://img.shields.io/badge/contrast-WCAG%20AA-1f883d)](#accessibility)
[![Languages](https://img.shields.io/badge/UI-English%20%7C%20Italiano-1f883d)](#interface-language)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-prototype-orange)](#limitations)
[![Reply Student Tech Clash 2026](https://img.shields.io/badge/Reply%20Student%20Tech%20Clash-AI%20on%20Campus%202026-6f42c1)](https://studentclash.reply.com/challenges/AI_on_Campus_IT.html)

</div>

![BusFactor demo: coverage goes from 1/5 to 2/5 after a peer-teaching mission and an independent retest](docs/demo.gif)

---

## Table of contents

- [The problem](#the-problem)
- [How it works](#how-it-works)
- [Features](#features)
- [Screenshots](#screenshots)
- [Quick start](#quick-start)
- [Run with Docker](#run-with-docker)
- [Configuration](#configuration)
- [Using it for your own project](#using-it-for-your-own-project)
- [Access codes and human review](#access-codes-and-human-review)
- [Interface language](#interface-language)
- [Accessibility](#accessibility)
- [Architecture](#architecture)
- [Guarantees enforced in code](#guarantees-enforced-in-code)
- [Quality and evidence](#quality-and-evidence)
- [Example runs](#example-runs-demo-mode)
- [Testing](#testing)
- [Limitations](#limitations)
- [License](#license)

## The problem

In a group project, people usually split the work, and each person ends up understanding only their own part. The project gets one grade for everyone, but at the oral defense anyone can be asked about any part.

BusFactor looks at the key decisions of a project and checks which ones only one person in the team can explain. For each of those, it suggests that the person who understands it teaches a teammate who doesn't. After that, the teammate answers a new question on their own to show they really learned it.

It is a **learning and assessment** tool. It does not assign tasks, schedule work or track who did what.

> All data in `data/demo/` is made up for the demo (a fake project, fake members and fake answers). The app shows a **DEMO DATA, synthetic** label whenever this data is loaded.

## How it works

```mermaid
flowchart TD
    R["Project report<br/>PDF / MD / TXT"]

    subgraph S1["Step 1: Capture"]
        DC["Decision cards<br/>quote + page,<br/>human confirms"]
    end

    subgraph S2["Steps 2-3: Check and detect silos"]
        PC["Private checks<br/>Why? / What if?<br/>scored 0 / 1 / 2"]
        CM["Coverage map<br/>≥ 2 explainers<br/>per decision"]
        PC --> CM
    end

    Q{"How many members<br/>can explain it?"}

    subgraph S3["Steps 4-6: Teach and verify"]
        TM["Teaching mission<br/>mentor → learner<br/>(both consent)"]
        RT["Independent retest<br/>new question,<br/>no hints"]
        UP["Coverage goes up<br/>(if the learner scores 2)"]
        FU["Follow-up<br/>a few days later,<br/>another new question"]
        TM --> RT --> UP --> FU
    end

    R --> DC --> PC
    CM --> Q
    Q -- "2 or more" --> OK["Covered"]
    Q -- "nobody" --> TA["Course material<br/>or TA"]
    Q -- "only 1" --> TM
```

1. **Capture.** Read the project file and pull out 5 key decisions. Each one has a quote from the file, and the code checks that the quote is really on the page it cites. A person then confirms the cards.
2. **Private check.** Each member answers a "why" and a "what if" question about decisions they did not make. Answers get 0, 1 or 2 and only the member can see them.
3. **Detect silos.** Decision coverage is the number of decisions that at least 2 members can explain, divided by the number of decisions that have been assessed. A decision only one person can explain is a *single point of failure*.
4. **Peer-teaching mission.** For those decisions, BusFactor suggests a teaching session: someone who scored 2 teaches someone who didn't, only if both agree. If nobody in the team can explain it, it points to the course material or the TA instead of inventing a mentor. The pair ticks off a checklist (with conversation starters) and marks the session done; the retest opens after that. If the session does not happen, both people get a reminder.
5. **Independent retest.** The learner gets a new question, with no hints. If they score 2, coverage goes up.
6. **Follow-up.** A few days later the learner gets one more new question, because one correct answer on one day does not prove it stuck.

In the demo, coverage starts at **1/5**. Member B teaches Member D why the team used F1 instead of accuracy (D03), Member D passes the new question, and coverage goes to **2/5**.

**Plain words in the app.** The interface avoids jargon and keeps the technical term in a tooltip:

| In the app | Means |
|---|---|
| *Only 1 can explain it* | a single point of failure: one member has shown they can explain the decision |
| *2+ can explain it* | covered: at least two members have |
| *Nobody can explain it yet* | members were checked and nobody has shown it yet |
| *Solo question · no hints* | an independent check, answered alone |
| *Confirmed: can explain it* | the retest was passed on a new question |

## Features

| Feature | What it does |
|---|---|
| Source-checked decision cards | Every card quotes the document; the code verifies the quote is on the cited page. |
| Private, consent-based checks | Nobody is assessed without opting in. Answers are visible only to their author. |
| Coverage map | Shows which decisions only 1 person can explain (single points of failure). Counts only: never names or scores on the team page. |
| Consent-gated peer-teaching missions | A mentor is chosen only if they demonstrated the decision and agreed. No fake mentors. |
| Independent retest | A new, different question with no hints; asking for the answer is refused in code. |
| Spaced follow-up and reminders | A nudge when an accepted mission sits idle, and a second new question after a few days. |
| Access codes (live projects) | Each member unlocks their own answers with a personal code; hashed, shown once. |
| Human review queue | A reviewer scores answers the model could not, only for members who agreed, without names. |
| Team report export | PDF (with a coverage chart), Markdown and CSV of decision coverage: counts only. |
| Defense simulator | A mock oral: random new questions on any decision, no hints. Practice only: never counted in coverage. |
| Course-material pointers | When nobody can explain a decision, the app shows the page of your course files that talks about it. |
| Hardened guards | Answer-request and prompt-injection detection survives paraphrases, other languages and spelling tricks (see [Quality and evidence](#quality-and-evidence)). |
| Accessible by design | Measured contrast, keyboard focus, status icons, phone layout, larger-text switch (see [Accessibility](#accessibility)). |
| Your next step | Every page opens with the one thing this member should do now, with a button that goes there; Back/Next at the bottom. |
| Teaching-session checklist | The pair ticks off the four steps, gets conversation starters built from the confirmed card, and marks the session done to open the retest. |
| Drafts and sign-in | Typed answers survive moving to another page; an optional, expiring "keep me signed in" token; Sign out. |
| Who can see what | One panel on the main pages says exactly who sees answers, coverage, sessions, reviews and the log. |
| English and Italian interface | Switch in the sidebar; the page you are on and your identity are kept. |
| Offline demo mode | Runs with no API key on synthetic data. |
| Guided tutorial | A small 3D robot walks around the app, switches pages for you and writes the help for each step in a thought cloud. Start it from the sidebar. |
| Connect a model | Claude, OpenAI/Codex models, a local model, or the Claude Code / Codex tools already installed on your computer, connected from the sidebar for one browser session. The model then writes the questions and retest scenarios and scores answers. |
| Quick quiz | Five model-written questions in a row in the Defense simulator; practice only. |
| Docker image | `docker compose up` and open <http://localhost:8501>. |

## Screenshots

The loop above, as the app shows it. All screenshots use the synthetic demo data in offline demo mode.

| | |
|---|---|
| **1. Project Setup**: decision cards with their sources<br>![Project Setup](docs/screenshots/02_project_setup.png) | **2. Private Check**: each member sees only their own questions<br>![Private Check](docs/screenshots/03_private_check.png) |
| **3. Team Coverage**: who can explain which decision<br>![Team Coverage](docs/screenshots/04_team_coverage.png) | **4. Teach Each Other**: consent-gated peer-teaching missions<br>![Teach Each Other](docs/screenshots/05_teach_each_other.png) |
| **5. Defense Retest**: a new question, no hints<br>![Defense Retest](docs/screenshots/06_defense_retest.png) | **6. Evidence & Limits**: sources, action log and limits<br>![Evidence and Limits](docs/screenshots/07_evidence_limits.png) |
| **After the retest**: coverage 2/5, one single point of failure fewer<br>![Coverage after the retest](docs/screenshots/08_coverage_after_retest.png) | **Italian interface**: same page, same numbers<br>![Italian interface](docs/screenshots/09_italian_coverage.png) |
| **Human review queue**: answers without names, scored by a reviewer<br>![Review queue](docs/screenshots/10_review_queue.png) | **Defense simulator**: a mock oral, practice only<br>![Defense simulator](docs/screenshots/12_defense_simulator.png) |
| **Empty states** say what to do next<br>![Empty state](docs/screenshots/13_empty_state.png) | **On a phone**: the verdict first, stats stacked<br><img src="docs/screenshots/11_mobile_coverage.png" alt="Team Coverage on a phone" width="260"> |
| **Teaching session**: checklist and conversation starters<br>![Teaching session](docs/screenshots/14_teaching_session.png) | **The retest follows the session**: until it is held, the page says so<br>![Retest gate](docs/screenshots/15_retest_gate.png) |

There is also a static landing page, `web/index.html`, with a 3D knowledge map (`web/knowledge_map.html`). Open it in a browser; "Open the demo" links to the Streamlit app.

## Quick start

Requires Python 3.11 or newer.

**macOS / Linux**

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

**Windows (PowerShell or cmd)**

```
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
python -m streamlit run app.py
```

The app opens at <http://localhost:8501>. With the default `.env.example` it runs offline on the synthetic demo data and calls no AI model.

## Run with Docker

```bash
docker compose up --build
```

Open <http://localhost:8501>. The database and uploaded documents live in the `busfactor-data` volume, so they survive restarts. Demo mode is the default; for the live model:

```bash
DEMO_MODE=false LLM_API_KEY=sk-... docker compose up --build      # or connect a model from the sidebar instead
```

Without compose: `docker build -t busfactor . && docker run -p 8501:8501 -v busfactor-data:/data busfactor`.

To host the demo for others, [Streamlit Community Cloud](https://streamlit.io/cloud) can deploy `app.py` straight from the repository in demo mode (no secrets needed). Do not put real students' answers on a public instance: see [Limitations](#limitations).

## Configuration

Settings live in `.env` (copy it from `.env.example`; never commit it).

| Variable | Default | Meaning |
|---|---|---|
| `DEMO_MODE` | `true` | `true`: offline, no model calls, answers scored by a fixed keyword rubric. `false`: use the live model. |
| `LLM_PROVIDER` | `anthropic` | `anthropic` (Claude), `openai` (OpenAI, Codex models, or any OpenAI-compatible / local endpoint), or `claude-cli` / `codex-cli` (the installed tools, needs `BUSFACTOR_ENABLE_LOCAL_CLI=true`). |
| `BUSFACTOR_ENABLE_LOCAL_CLI` | `false` | Allow the command-line providers. They run a program as the user who started the server: your own computer only. |
| `BUSFACTOR_MODEL_CALL_LIMIT` | `50` | Model calls one browser session may make. After that the app uses the fixed templates until the user allows more (the sidebar shows the count and a **Stop the model** button). `0` means no limit. |
| `LLM_API_KEY` | empty | API key for a server-wide model, needed only when `DEMO_MODE=false`. A local model needs none. |
| `LLM_BASE_URL` | empty | `openai` provider only: the endpoint, for example `http://localhost:11434/v1` for Ollama. |
| `BUSFACTOR_ALLOW_PRIVATE_LLM_URLS` | `false` | Allow a model on a private network. Link-local and cloud-metadata addresses stay blocked. |
| `BUSFACTOR_PALETTE` | `brass` | Colour palette: `brass` (default), `classic`, `forest`, `teal`, `rose`, or the flat `mono`, `bordeaux`, `olive`, `slate` (see [Colour palettes](#colour-palettes)). |
| `LLM_MODEL` | `claude-opus-5-5` | Model used for extracting decisions, writing questions and grading answers. |
| `BUSFACTOR_DB` | `busfactor.db` in the repo root | Optional path to the SQLite database. |
| `BUSFACTOR_UPLOADS` | `uploads/` in the repo root | Optional folder for uploaded project documents. |
| `BUSFACTOR_REMINDER_DAYS` | `2` | Days an accepted mission can sit idle before both people are reminded. |
| `BUSFACTOR_FOLLOWUP_DAYS` | `3` | Days after a passed retest before the follow-up question opens. |

> With a model connected (from the sidebar or with `DEMO_MODE=false`), the project text and the students' answers are sent to the provider. Only use files you are allowed to share and members who agreed to take part.

## Using it for your own project

1. **Project Setup → Start a new project**: title, course, the report (PDF, Markdown or text) and the team's names. The project is added next to the demo; nothing is deleted. Switch projects in the sidebar. The app shows every member's **access code once**: save them.
2. **Add decisions**: by hand (paste the exact quote and its page; it is checked against the document), or let the live model propose up to 5. Every card starts as *proposed*. A member checks the quote, declares the owner and confirms it. Only confirmed cards are ever assessed.
3. **Private Check → My consent**: each member unlocks their account with their code, then opts in for themselves (assessment, mentoring, learning, and optionally human review). Every consent starts off. Withdrawing removes that member's answers from the team's coverage.
4. **Owner check**: the person who made a decision answers one independent question on it. Owning a decision is not proof of understanding it; only a full answer lets them mentor it.
5. Teammates take private checks, missions are proposed, and the learner takes the retest, as in the demo. **Team Coverage → Export** downloads the team report.

6. Optional: upload your **course material** (lecture notes, slides) in Project Setup. When nobody can explain a decision, the Teach page shows the page that talks about it, instead of a generic "ask the TA".
7. Before the oral, each member can run the **Defense simulator** (Defense Retest page) for random questions on any decision. It is practice only and never changes coverage or mentor eligibility.

Without the live model, your own project still works for review and questions, but answers are **not scored automatically**: they wait for human review, so coverage does not move.

## Access codes and human review

The demo is a fictional team, so it has no sign-in: "Who are you?" is a dropdown. **Projects you create in the app are protected by access codes**:

- Every member gets a personal code (for example `K7QM-2XPD`). The app shows the codes once, right after the project is created; only a salted PBKDF2 hash is stored. A member's answers and feedback appear only after their code is entered. Wrong guesses are throttled per browser session.
- The project also gets one **reviewer code**. It opens the **Review queue** (Evidence & Limits). Without the live model, or when the model is unsure, answers are not scored automatically; the reviewer scores them 0, 1 or 2 with an optional note.
- A reviewer sees only answers from members who ticked *"Allow a human reviewer to read my answers…"*, and never their names. The log records that a review happened, never the answer or the score. A reviewed retest updates the mission and coverage exactly like an automatic score.
- **Keep me signed in** (optional, per member) adds a signed token to the page link for 7 days so the code is not retyped on a refresh. Anyone who has that link can open that member's answers until it expires, so it must not be shared; **Sign out** removes it. Tokens are bound to one member and signed with a server secret.
- Projects created without codes (for example by script) keep the dropdown. **Project Setup → Access codes** turns them on, or issues new codes (which signs everyone out).

## Guided tutorial

Not sure what to press first? Click **Start the tutorial** in the sidebar (or **Take the 2-minute tutorial** on the Overview).
A small 3D robot called Bus walks to each part of the app, highlights it, **switches to the next page by itself** and writes
the help in a thought cloud above its head: pick a project, pick who you are, the six pages, "Your next step", the four
numbers, then each page in turn and, last, the optional model connection. 16 short steps, about two minutes.

![The tutorial robot](docs/screenshots/16_tutorial_robot.png)

- **Controls:** Next / Back / Skip tour in the cloud, the arrow keys, Esc to leave. It is available in English and Italian.
- **How it is built:** pure CSS 3D (no library) in `web/tutorial.js`, started by `ui/tutorial.py` only while the tour is on. The
  steps point at parts of the page by CSS selector or by a button's text; if something is not on screen the robot says the
  step from the middle of the page, so it never gets stuck. Help text is inserted as plain text, never as HTML.
- **Accessibility:** the cloud is a labelled dialog with keyboard control, and users who prefer reduced motion get no walking
  or bobbing animation (the robot just appears at each step).

![Tutorial walk-through](docs/tutorial.gif)

## Connect a model

Without a model the app is a demo: questions come from the synthetic bank and scoring is a keyword rubric. To use a real
model, open **Connect a model** in the sidebar:

1. Pick a provider: **Claude (Anthropic)**, or **OpenAI, Codex or a compatible / local model**. The second option takes any
   OpenAI-compatible endpoint: OpenAI itself (including the Codex models), or a model running on your own machine with
   Ollama or LM Studio (base URL such as `http://localhost:11434/v1`, no key needed).
2. Paste the API key, optionally a model name, tick the consent box and press **Connect and test**. One small request
   checks that the key and model work.

What the model then does: it **writes the Why and What-if questions** from the confirmed decision card, **writes a new retest
scenario** (with its own scoring points) every time, **scores answers** 0/1/2 with feedback, and **proposes decision cards**
from an uploaded report. Every question shows who wrote it (model, demo bank or template). The Defense simulator and the quick
quiz never run out of questions, because the model writes fresh scenarios.

How it is kept safe:

- **The key stays in that browser session's memory.** It is not written to the database, the logs or an export, it is not shown
  again after connecting, and **Disconnect** (or closing the session) removes it. Each session has its own connection: one
  person connecting a model does not connect it for anybody else.
- **Consent first.** The panel states that the project text and the team's answers are sent to the provider, and the Connect
  button stays disabled until it is ticked.
- **A user-supplied URL cannot reach internal services.** Only http(s) is accepted; link-local, cloud-metadata and private-network
  addresses are refused (a model on this machine is allowed; a private network needs `BUSFACTOR_ALLOW_PRIVATE_LLM_URLS=true`).
- **The model is not trusted blindly.** Output must match a JSON schema; invalid output is retried once and otherwise the
  answer is not scored and goes to human review. Answer requests and instructions to the grader are still blocked in code
  before anything is sent to the model.

**Use the Claude Code or Codex you already have (local only).** If Claude Code (`claude`) or the Codex CLI (`codex`) is installed
and logged in on your computer, the app can use it without any key. Because this runs a program as the user who started the
server, it is **off by default**: start the app with `BUSFACTOR_ENABLE_LOCAL_CLI=true` (your own computer only, never a
shared server), then pick *Claude Code on this computer* or *Codex CLI on this computer*. Each request starts the tool with the
prompt on stdin (never as an argument or through a shell), in a throw-away folder with a timeout:

- **Claude Code** runs with every tool switched off, no settings, hooks or slash commands, and no session saved.
- **Codex** runs ephemeral in a read-only sandbox. Read-only still lets an agent *read* files on the computer, so the panel
  warns about it; use it only with your own data.
- Each answer takes several seconds and counts against that tool's own plan.

**Check that it works** (a handful of small requests; the key is never printed):

```bash
python scripts/check_model.py                        # detects what is available on this computer
python scripts/check_model.py --provider claude-cli  # or codex-cli, anthropic, openai (add --base-url for a local model)
```

It runs the connection test, then a model-written question and retest scenario for the demo decision and model scoring of a
strong and a weak answer, and exits with 0 only if all of it worked. Run on the author's machine with both command-line tools,
it connected, wrote a question and a scenario with its own scoring points, and scored a strong answer 2/2 and a weak one 0/2.
Direct API keys and a local Ollama server could not be tried there (none available).

For a whole server, set `LLM_PROVIDER`, `LLM_API_KEY` (and `LLM_BASE_URL`) and `DEMO_MODE=false` instead; the panel then shows
that the server already has a model. "Codex" here means the OpenAI models served through the API; the Codex command-line
tool itself is not driven by the app.

## Colour palettes

The stylesheet is written in roles (background, surface, accent fill, accent text, second accent), so a palette only says what
each role looks like. Status colours (green fine, red risk, amber attention) are not part of a palette and keep their meaning.
Choose one with `BUSFACTOR_PALETTE`; the default, `brass`, matches `.streamlit/config.toml`. For another palette set the same primary colour in that file (the flags
`ui.palettes.streamlit_theme_flags("<name>")` print the matching values). Every palette is tested for contrast: white text on
every button fill and accent and muted text on every background are at least 4.5:1.

| Name | Look |
|---|---|
| `brass` (default) | Espresso & Brass: warm brown-black, brass buttons, sage secondary |
| `classic` | the original navy with blue and green |
| `forest` | deep green-black, emerald buttons, gold highlights |
| `teal` | ink teal, deep-teal buttons, lime accents |
| `rose` | neutral graphite, rose buttons, gold secondary |
| `mono` | flat: neutral black and grey, signal-yellow highlights and buttons |
| `bordeaux` | flat: wine-black, wine buttons, cream highlights |
| `olive` | flat: olive-black, olive buttons, sand highlights |
| `slate` | flat: cool slate, slate-teal buttons, amber highlights |

"Flat" palettes switch off every gradient, glow and grid texture and use solid colours only.

## Interface language

Pick **English** or **Italiano** at the top of the sidebar (or open the app with `?lang=it`). The page you are on, your project and your identity are kept when you switch. Only the interface is translated: decision cards, questions and feedback stay in the language of the documents, the demo data or the model, and answers can be written in any language. Some explanatory sentences produced by the coverage and mission logic are still English.

## Architecture

```
app.py (page config, sidebar, navigation)  →  ui/pages/*.py (one module per page)  →  ui/widgets.py, ui/theme.py
   │
   ▼
orchestrator.py ── runs the steps in order, logs each one (max 6 steps per action)
   │
   ├── ingestion.py / knowledge.py     read files, extract + verify decision cards
   ├── interview.py / rubrics.py       questions, 0/1/2 scoring, answer-request blocking
   ├── coverage.py / missions.py       coverage maths, mentor/learner matching, retest
   ├── auth.py                         hashed access codes for live projects
   ├── i18n.py                         English / Italian interface strings
   ├── llm_provider.py                 the single function that calls the model
   └── database.py / models.py         SQLite storage, private answers, shared Pydantic models
```

| File | Purpose |
|---|---|
| `ingestion.py` | Reads PDF, Markdown or text files page by page. Uploaded files are only read, never run. |
| `knowledge.py` | Extracts up to 5 decision cards and checks each quote. `confirm_card` handles the human review. |
| `llm_provider.py` | `complete_json(prompt, schema)`, the single function used to call the model. |
| `interview.py` | Creates the why / what-if questions and the new retest question. |
| `rubrics.py` | Scores answers 0/1/2 and blocks "give me the answer" during the retest. |
| `coverage.py` | Computes decision coverage. Plain Python, same input always gives the same result. |
| `missions.py` | Picks mentor and learner, handles consent and updates the mission after the retest. |
| `auth.py` | Issues and verifies member and reviewer access codes (salted PBKDF2). |
| `i18n.py` | `t("English text")` returns the Italian text when Italian is selected. |
| `models.py` | Shared data models. |
| `database.py` | SQLite storage, private answers, action log, loading the demo data. |
| `orchestrator.py` | Runs the steps in order and logs each one; also reminders, follow-up, review queue, defense simulator, course pointers and report export (Markdown, CSV, PDF). |
| `app.py` | Entry point: page config, sidebar (project, language, identity, navigation) and dispatch to the selected page. |
| `ui/pages/` | One module per page (`overview`, `setup`, `check`, `coverage`, `teach`, `retest`, `evidence`), each with `render()`. |
| `ui/widgets.py`, `ui/theme.py`, `ui/state.py` | Shared helpers and empty states, CSS and labels, and the per-session context (never a module global, so sessions cannot see each other). |

Repository layout:

```
app.py              Streamlit entry point
ui/                 interface: theme, widgets, per-session state, one module per page
src/busfactor/      application modules (above)
prompts/            model prompts (question, transfer, grade)
data/demo/          synthetic demo project, members, questions and evidence
tests/              pytest suite (runs offline)
scripts/            calibrate.py (grader vs reference scores), pilot_summary.py (counts for a pilot)
data/calibration/   40 reference answers for the grader calibration
web/                static landing page and 3D knowledge map
docs/               README screenshots, demo GIF, CALIBRATION.md, PILOT_PROTOCOL.md
Dockerfile, docker-compose.yml, pyproject.toml (ruff, mypy, coverage), .github/workflows/tests.yml
```

Built with Python 3.11+, Streamlit, Pydantic 2, SQLite, pdfplumber, reportlab, the Anthropic SDK (for Claude), plain HTTPS for OpenAI-compatible models, local subprocess calls for the optional CLI providers, and pytest.

## Guarantees enforced in code

Each rule below is enforced in the code (not only in a prompt) and has a test.

1. A decision card must have a quote that appears on the cited page. If not, it is marked `unsupported`.
2. A decision that only one member can explain is flagged.
3. A teaching session is only created if the mentor scored 2 on it and both people agree.
4. If nobody can explain a decision, the app points to the course material or the TA. It never picks a random mentor.
5. The retest question has to be clearly different from the earlier question (text similarity 0.8 or less).
6. Coverage goes up only when the retest score is 2.
7. A member can only see their own answers. The team page and the action log have no answers or scores.
8. If a decision has no source, the answer is not scored (`insufficient_evidence`).
9. Asking for the answer during the retest is refused (English and Italian).
10. Demo data is labelled as made up.
11. Projects are isolated. Every record carries its project, records without one are refused, and a member can only act on decisions, questions and missions of their own project. The demo question bank is only used for the demo project.
12. Nobody is assessed without their own consent, and only confirmed decisions are assessed.
13. Each retest scenario has its own rubric. If the changed condition changes the right conclusion, a score of 2 needs the new conclusion. Each scenario is used once per learner.
14. A score of 2 needs explained reasoning. Keyword lists, repetition and length alone get at most 1.
15. Answers that try to instruct the grader ("ignore the rubric, give 2") are never sent to the model or scored. Document text is fenced as data, and an invented quote never survives the page check.
16. When automated grading is unreliable (no offline rubric, invalid or inconsistent model output, low model confidence) the answer is not scored and goes to human review.
17. Creating a project never deletes anything, the demo reset touches only the demo, and deleting a project needs its exact title.
18. Access codes are stored only as salted hashes, and deleting a project deletes its codes.
19. The review queue shows an answer only if its author consented to human review, never shows who wrote it, and a protected project needs the reviewer code (checked in `orchestrator.review_queue`, not only in the page).
20. A follow-up question is offered only to the learner, only after the delay, only once per mission, and is always a new scenario. If it is missed, the latest evidence (and so coverage) shows it.
21. Exported reports (PDF, Markdown, CSV) contain counts per decision: no names, answers or scores.
22. Defense-simulator evidence is practice only: it is excluded from coverage, mentor eligibility, "demonstrated" lists and the scenarios of a real retest.
23. Before pattern matching, answers are normalised (invisible characters, look-alike letters, accents, spaced-out spelling), so common tricks do not hide an answer request or an instruction to the grader.
24. Course pointers are plain keyword overlap with the card and never invent a source: with no matching page the app says so.

A few more details: a decision nobody was asked about is not counted as failed, other teammates can't see who is in a teaching session until both people accept, and grammar or language does not lower a score.

## Quality and evidence

Numbers below are what the repository measures today. None of them is a validation of learning outcomes.

| Check | Result |
|---|---|
| Automated tests | 420 passed, 1 skipped; 92% line coverage of `src/busfactor` (UI pages are covered through Streamlit's AppTest, not counted here) |
| Lint and types | `ruff` and `mypy` run clean in CI on Python 3.11 and 3.12 |
| Answer-request guard | 38/38 adversarial cases blocked (paraphrases, Italian/French/Spanish/German, spelling tricks, look-alike letters) |
| Prompt-injection guard | 37/37 adversarial cases blocked (role changes, score demands, JSON, other languages, spacing tricks) |
| False positives | 0/15 real explanations blocked (answers that merely contain words like "ignore", "score" or "grade") |
| Contrast | 236 text samples on 5 rendered pages measured at WCAG AA (4.5:1 for normal text): none fail. The first pass had found 32 faint texts, all fixed. Large white or gradient headings cannot be sampled this way; by calculation they are above 9:1 |
| Grader calibration | offline keyword rubric: 72% exact agreement, 92% within one point, Cohen's kappa 0.60 on 40 reference answers (see below) |

The adversarial cases are in `tests/adversarial_cases.py`. They found real gaps: the first version of the guards missed 23 of 38 answer requests and 18 of 37 injections; the fix is in `rubrics.py`. Pattern matching can still be beaten by a determined writer, so a human reviewer remains the backstop.

**Grader calibration.** `python scripts/calibrate.py` compares the grader with reference scores for 40 synthetic answers (`data/calibration/answers.json`, report in [`docs/CALIBRATION.md`](docs/CALIBRATION.md)). Two caveats matter more than the number:

- the reference scores were **drafted by the developer**, not by an independent grader: a TA should re-score them before the numbers are quoted as evidence;
- the set is built to include hard cases (paraphrases, keyword lists), so the agreement is lower than it would be on ordinary answers. It shows where the offline keyword rubric is weak: it misses correct paraphrases (0/5) and gives a keyword list a 1 where the reference says 0. It is a stand-in for the model, which has not been calibrated; `--live` runs the same set through the model when a key is available.

**Pilot.** No pilot has been run. [`docs/PILOT_PROTOCOL.md`](docs/PILOT_PROTOCOL.md) describes how to run one with 2–3 consenting teams, and `scripts/pilot_summary.py` prints the counts (never answers or scores) to report.

## Accessibility

- **Contrast.** Text colours were measured on the rendered pages (colour, opacity and the pixels behind it): all measurable text passes WCAG AA. Streamlit's own caption opacity had made the sidebar hints 2.6–3.0:1 before.
- **Not colour alone.** Every status pill carries an icon shape as well as a colour (✓ ▲ ◐ ● ○ ◆); the coverage ring and verdict have text equivalents, and the 3D map has an `alt` text plus a text version under it.
- **Keyboard.** Every focusable control shows a 3px focus outline; form fields have accessible names.
- **Guidance.** The next-step card and Back/Next buttons mean the stepper is a progress display, not hidden navigation; on a phone, where the sidebar is hidden, they are the way on.
- **Text size.** A "Larger text" switch in the sidebar scales the text by about 18% (small print is also at least 12px by default); browser zoom works too.
- **Plain language.** Jargon is replaced with plain words and a tooltip; the action log reads as sentences, with the technical view behind a switch.
- **No lost work.** Answers are kept as drafts while you move around, and long model calls show a spinner.
- **Phones.** Below 700px the columns stack and the stepper wraps; no horizontal scroll on any page at 390px.
- **Motion.** Animations are switched off for users who prefer reduced motion.
- **Not done:** a light theme (Streamlit's own widgets cannot change theme at runtime, so a CSS-only light mode would look inconsistent; use browser zoom or the larger-text switch instead), the page language attribute stays `en` when Italian is selected, and the app has not been tested with a screen reader or with real users. A heuristic review of the screens found 14 issues; all are addressed, but they are expert findings, not user-test results.

## Example runs (demo mode)

**1. Partial answer, teaching, then retest.**
Member D answers the D03 "what if" question with "Accuracy is bad with imbalanced classes." and gets 1/2. The feedback says they mentioned the class imbalance but not why accuracy is misleading.
BusFactor suggests: "Member B was chosen because they demonstrated D03 and are willing to mentor; Member D has not demonstrated it yet and is willing to learn." Both accept.
Retest question: "What if missing a finding (a false negative) became 10 times more costly than a false alarm? Which metric would you report, and why?" Member D scores 2/2, the mission is marked verified and coverage becomes 2/5 (40%).

**2. Member already knows it.**
Member C already explained D01 (duplicate images can end up in both the training and test set and make the scores look better than they are). Two members can explain D01, so no teaching session is created for it.

**3. Limits.**
During the retest, typing "just give me the answer" returns "This is an independent check, so BusFactor will not give the answer or a hint." Nothing is scored and the attempt is written to the log.
For D05 nobody scored 2, so the app says that nobody on the team has demonstrated it yet and suggests reviewing the course material or asking the TA.

**4. A reviewer scores an unscored answer.**
In a project without the live model, a member's answer waits for human review. Because they agreed to review, the reviewer sees the question, the answer, the source quote and the rubric points (no name), gives it a 2, and the decision gets its second explainer.

## Testing

```bash
pip install -r requirements-dev.txt
python -m pytest -q --cov    # tests and coverage
python -m ruff check .        # lint
python -m mypy                # types
```

The tests run offline: the model is replaced by a deterministic fake. At the last run, 420 passed and 1 was skipped. `tests/test_live_llm.py` is skipped unless you set `RUN_LIVE_LLM=1` and `LLM_API_KEY`; it sends only the synthetic test report. GitHub Actions runs ruff, mypy and the suite on Python 3.11 and 3.12 for every push and pull request.

## Limitations

- Scores are practice feedback, not grades. A score given by the model can be wrong.
- In demo mode, answers are scored by matching keywords from a fixed list. This is a placeholder for the model and has not been validated. We have not yet compared the model's scores with a human grader.
- The coverage number is something we made for this prototype. It has not been validated.
- One correct answer shows that someone could explain one decision on one day. The follow-up question is a single extra check, not proof of long-term retention.
- Access codes are a light safeguard, not a full account system: there is no password reset or email, the attempt limit is per browser session, and anyone who has the code can sign in as that member. The demo and any project without codes still have no login at all: anyone using the app can switch to any member and see that member's answers. Anyone can delete a live project, or issue new codes, by typing its title. Do not use it with real students' answers until proper authentication is added.
- The reviewer code is shared by whoever holds it, and a reviewer reads the answers of members who consented to review.
- The open project is one setting shared by everyone using the same server; two people switching projects at the same moment can briefly see each other's choice. Run one instance per team.
- Uploaded documents are stored as plain files in `uploads/<project id>/` on the machine running the app, and the database (`busfactor.db`) holds answers in plain text. Deleting a project removes its documents and records.
- The live model's grading has not been calibrated against human graders yet. The code checks that its output is consistent and abstains when it is not, but a consistent grade can still be wrong.
- A model connected for a session keeps its key in the server's memory for that session; on a shared or public deployment that is only as private as the server. Questions and scores written by a model can be wrong or badly worded, and calls cost money on the provider's side. The base-URL check does not stop DNS-rebinding tricks.
- The Claude Code / Codex providers are experimental and meant for one person on their own computer. Codex's read-only sandbox does not stop it reading files; Claude Code runs with tools off. They are slower (a process per request) and their output format can change between versions.
- Injection detection uses patterns (English and Italian). A cleverly worded attempt can get past it; the model is also told to report instructions in the answer, and a 2 must agree with its own point-by-point judgement.
- The offline keyword rubric exists only for the synthetic demo and only for English (plus a few Italian words).
- Only the interface is translated into Italian. Some explanatory sentences from the coverage logic are English, and the report export is English.
- Reminders appear in the app when a member opens a page; there are no emails or push notifications.
- The retest follows the teaching session in the app (the page asks for the session first), but this is an interface step, not a hard rule in the backend, and a learner can tick "We already did the session".
- Drafts live in the browser session: closing the tab loses them.
- Sign-in uses shared codes, not accounts with email magic links; the page language attribute does not follow the interface language.
- The defense simulator is practice: it shows a scenario the learner may meet again in a real retest, so it is not a secret question bank. The demo has two scenarios per decision.
- Course pointers use keyword overlap, not semantic search: a page that explains the idea in other words can be missed.
- The grader calibration reference scores were written by the developer and the set is synthetic; the live model has not been run through it.
- We have not measured any learning results. The demo only shows how the process works.

## License

[MIT](LICENSE)

---

<div align="center">

Built for **Reply Student Tech Clash 2026, AI on Campus**.

</div>
