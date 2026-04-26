from typing import List, Optional, Literal
from pydantic import BaseModel, Field
import json
from utils.ai_router import ai_router
from agents.gap_analysis_agent import SkillGap


# ─── Pydantic Models ──────────────────────────────────────────────────────────

class DocLink(BaseModel):
    title: str
    url: str
    description: str


class YouTubeVideo(BaseModel):
    title: str
    url: str
    channel: str
    why: str


class YouTubeLevels(BaseModel):
    easy: YouTubeVideo
    medium: YouTubeVideo
    hard: YouTubeVideo


class ExtraResource(BaseModel):
    title: str
    url: str
    type: Literal["article", "book", "course", "repo", "tool", "cheatsheet"]
    description: str


class WeekTopic(BaseModel):
    week_label: str = Field(description="e.g. 'Week 1' or 'Week 2-3'")
    title: str = Field(description="Short, punchy title for this week's focus")
    objective: str = Field(description="One sentence: what the candidate will achieve this week")
    what_to_study: List[str] = Field(description="3-4 specific topics to study this week")
    documentation: List[DocLink] = Field(description="2-3 real documentation links directly relevant to this week")
    youtube: YouTubeLevels = Field(description="3 YouTube videos at easy/medium/hard levels")
    extra_resources: List[ExtraResource] = Field(description="3-4 extra resources: mix of article, cheatsheet, repo, tool")
    hands_on: str = Field(description="One specific, buildable project for this week")
    milestone: str = Field(description="One testable outcome: 'You can do X without looking it up'")


class SkillLearningPlan(BaseModel):
    skill_name: str
    category: Literal["STRONG", "DEVELOPING", "GAP"]
    total_weeks: int
    current_level: int
    target_level: int
    color: Literal["red", "amber", "green"]
    assessment_reasoning: str = Field(description="Internal logic for the score")
    candidate_feedback: str = Field(description="Direct, personalized feedback for the candidate about their performance")
    topics: List[WeekTopic]


class DetailedLearningPlan(BaseModel):
    candidate_name: str
    target_role: str
    total_weeks: int
    skills: List[SkillLearningPlan]


# ─── System Prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert curriculum designer and senior engineer for NeuralHire.

Generate a MASTERY INTELLIGENCE BLUEPRINT as structured JSON data.

CORE LOGIC:
- GAP skills (Score 0-4): Provide 4 weeks of depth. color: "red", category: "GAP"
- DEVELOPING skills (Score 5-7): Provide 2 weeks of focus. color: "amber", category: "DEVELOPING"
- STRONG skills (Score 8-10): Provide 0 weeks (Mastery). color: "green", category: "STRONG", topics: []

RULES:
1. NEURAL QUALITY: Every 'candidate_feedback' must be unique. Reference their specific performance. 
   - If they did well, tell them why. 
   - If they struggled, identify the specific concept they missed.
2. ADJACENT SKILLS: Identify 'Leverage Points' where one skill unlocks another.
3. REAL RESOURCES:
   - Documentation: MDN, roadmap.sh, official sites only.
   - YouTube: Exactly 3 levels (Easy/Medium/Hard). Real channels (Fireship, Corey Schafer, etc.).
4. MILESTONES: Each week must end with a 'Hands-on Milestone' project that is observable.

OUTPUT: Valid JSON only."""


# ─── Agent ────────────────────────────────────────────────────────────────────

class LearningPlanAgent:
    """
    Generates a god-level, detailed week-by-week learning plan
    with curated documentation, YouTube videos at 3 levels, hands-on projects,
    and testable milestones.
    """

    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT

    async def agenerate_plan(
        self,
        prioritized_gaps: List[SkillGap],
        candidate_name: str = "Candidate",
        target_role: str = "Software Engineer"
    ) -> DetailedLearningPlan:
        """Generates the detailed plan using async parallel racing."""
        gaps_data = []
        for g in prioritized_gaps:
            category = "GAP" if g.actual_score <= 4 else ("DEVELOPING" if g.actual_score <= 7 else "STRONG")
            gaps_data.append({
                "skill_name": g.skill,
                "required_level": g.required_proficiency,
                "current_level": g.actual_score,
                "target_level": g.required_proficiency,
                "category": category,
                "summary": g.summary
            })

        prompt = (
            f"candidate_name: {candidate_name}\n"
            f"target_role: {target_role}\n"
            f"skill_assessments: {json.dumps(gaps_data, indent=2)}\n\n"
            "Generate the complete detailed learning plan strictly following all rules. "
            "Return ONLY valid JSON."
        )

        return await ai_router.acomplete(
            prompt=prompt,
            system_prompt=self.system_prompt,
            response_model=DetailedLearningPlan,
            parallel_count=3 # Fire 3 keys in parallel for maximum speed
        )
