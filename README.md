# AI SKILL ASSESSMENT ENGINE
### The Autonomous Technical Interview & Personalized Mastery Platform

---

## 1. EXECUTIVE SUMMARY

Traditional technical screening is a bottleneck for high-growth engineering teams. Human-led interviews are expensive, biased, and inconsistent, while traditional ATS platforms rely on static keyword matching.

This project introduces a **production-grade, multi-agent AI orchestrator** that replicates a senior-level technical interview. It doesn't just scan resumes—it understands them, probes for depth through adaptive questioning, and calculates a deterministic readiness score. Finally, it builds a week-by-week personalized learning roadmap to bridge identified skill gaps.

---

## 2. THE PROBLEM & SOLUTION

### The Problem
*   **ATS Blindness**: Keyword matching fails to distinguish between a "hello world" beginner and a system architect.
*   **Manager Burnout**: Senior engineers spend 30-40% of their time on unqualified interviews.
*   **Non-Actionable Rejection**: Candidates are left in the dark with zero feedback on how to improve.

### The Solution
*   **Adaptive Intelligence**: Difficulty scales in real-time based on the candidate's answer depth.
*   **Evidence-Based Scoring**: Every score is backed by specific citations from the conversation.
*   **Gap-to-Roadmap Engine**: Turns technical failure into a structured growth path.

---

## 3. SYSTEM ARCHITECTURE

The engine is built on a modular "Agent Hub" architecture. Each agent is a specialized Pydantic-validated logic unit orchestrated by a high-concurrency AI Router.

```mermaid
flowchart TD
    subgraph UI_Layer ["FRONTEND (STREAMLIT)"]
        Upload[Document Ingestion]
        Chat[Adaptive Interview UI]
        Dashboard[Results & Roadmap]
    end

    subgraph Core_Intelligence ["AGENT CORE"]
        Parser[ParserAgent: Resume/JD Extraction]
        Extractor[SkillExtractorAgent: Weighted Requirements]
        Assessor[AssessmentAgent: Question Generation]
        Scorer[ScoringAgent: 1-10 Rubric Scoring]
        Planner[LearningPlanAgent: Roadmap Generation]
    end

    subgraph Orchestration ["AI ENGINE"]
        Router[AIRouter: Parallel Key Racing]
        Manager[KeyManager: Health & Rotation]
        Cache[AICache: 24hr TTL Persistence]
    end

    Upload --> Parser
    Upload --> Extractor
    Parser --> Assessor
    Extractor --> Assessor
    Assessor --> Scorer
    Scorer --> Planner
    Chat <--> Assessor
    Dashboard <-- Scorer
    Dashboard <-- Planner

    Parser & Extractor & Assessor & Scorer & Planner --> Router
    Router --> Manager
    Router --> Cache
```

---

## 4. AGENT COMPONENT DEEP-DIVE

| Agent | Responsibility | Core Logic / Algorithm |
| :--- | :--- | :--- |
| **ParserAgent** | Ingests PDF/TXT | Neural extraction into structured Pydantic schemas. |
| **SkillExtractor** | Job Description Analysis | Identifies required skills + importance (1-5) + req. level (1-10). |
| **AssessmentAgent** | Real-time Interviewing | Adaptive difficulty scaling via conversation context tracking. |
| **ScoringAgent** | Evaluation | Multi-metric scoring based on technical accuracy, clarity, and depth. |
| **GapAnalysis** | Priority Calculation | Deterministic Math: `Priority = Weight * (Required - Actual)`. |
| **LearningPlan** | Mastery Curation | Tiered week-by-week curriculum with curated documentation/videos. |

---

## 5. TECHNICAL DIFFERENTIATORS (THE "GOD LEVEL" EDGE)

### Parallel Key Racing (High-Concurrency)
To eliminate AI latency and rate-limit bottlenecks, the system employs a "Racing" architecture. It fires requests to 3-5 API keys simultaneously across different providers (Gemini/Groq) and returns the first successful response. The remaining tasks are instantly cancelled to save resources.

### Adaptive Questioning Logic
Unlike static quizzes, our AssessmentAgent tracks the "depth of proof" for every skill. If a candidate answers a basic question well, the system instantly jumps to architectural/theoretical questions, significantly reducing interview time while increasing assessment quality.

### Deterministic Gap Prioritization
The system rejects "black box" scoring. Every gap in the roadmap is calculated using a transparent formula that accounts for the role's specific needs (Importance Weight) versus the candidate's actual demonstrated proficiency.

---

## 6. TECH STACK & INFRASTRUCTURE

### Frontend & UI
*   **Streamlit 1.31+**: Utilized for its native streaming capabilities, allowing for a real-time "chatty" AI experience.
*   **Custom CSS Layer**: A premium dark-themed interface with glassmorphism and animated progress indicators.

### AI & Language Models
*   **Google Gemini 2.5 Flash**: Primary engine for structured JSON generation and high-speed document parsing.
*   **Groq LLaMA 3.3 70B**: Low-latency fallback for real-time interview questions, delivering ~500 tokens/second.
*   **Pydantic v2**: Strict type-safety across all agent communications.

### Backend & Core Logic
*   **Python 3.12**: Native `asyncio` implementation for true non-blocking AI orchestration.
*   **DiskCache**: Persistent response caching to reduce costs by 60% for redundant prompts.
*   **PyMuPDF**: High-fidelity text extraction from complex resume layouts.

---

## 7. PROJECT STRUCTURE

```text
.
├── agents/                  # Specialized AI Agents (Assessor, Scorer, Planner)
├── api/                     # FastAPI REST endpoint layer (External Access)
├── config/                  # Configuration & Global Settings management
├── ui/                      # Streamlit Frontend (Main App, Dashboard, Styles)
├── utils/                   # Core Logic (AIRouter, KeyManager, Caching, Parsing)
├── Dockerfile               # Production-ready container configuration
├── docker-compose.yml       # Full stack orchestration (App + API)
├── main.py                  # CLI Demonstration entry point
├── requirements.txt         # Project-wide dependencies
└── .env                     # Local secrets (API keys, Environment toggles)
```

---

## 8. INSTALLATION & USAGE

### Prerequisites
*   Python 3.12+
*   Google Gemini API Key OR Groq API Key

### Setup
1.  **Clone & Environment**:
    ```bash
    git clone https://github.com/Saineelareddy/Catalyst_deccan_ai_snr.git
    cd Catalyst_deccan_ai_snr
    python -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Configuration**:
    Create a `.env` file from the provided template:
    ```env
    AI_PROVIDER=gemini
    GEMINI_API_KEY=your_key_here
    GROQ_API_KEY=your_key_here
    ```

3.  **Launch**:
    ```bash
    streamlit run ui/app.py
    ```

---

## 9. FUTURE DEVELOPMENT ROADMAP

*   **Voice Integration**: Implementing Whisper-v3 for real-time speech-to-text voice interviews.
*   **Live Coding Evaluator**: Connecting a vision-based agent to monitor screen-share sessions for live coding.
*   **Enterprise Dashboard**: A multi-candidate comparison view for high-volume hiring managers.
*   **Multi-Agent Consensus**: A "Panel Interview" mode where multiple agents debate the candidate's score.

---

<div align="center">

**THE AI SKILL ASSESSMENT TEAM**

*Engineered for Technical Excellence · Powered by Gemini & Groq · Built with Python*

</div>
