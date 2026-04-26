from typing import List
from pydantic import BaseModel, Field

from agents.skill_extractor import ExtractedSkill
from agents.scoring_agent import SkillScore

class SkillGap(BaseModel):
    skill: str
    required_proficiency: int
    actual_score: int
    importance_weight: int
    gap: int
    priority: int
    summary: str

class GapAnalysisAgent:
    """
    Computes the skill gap priority using deterministic math based on importance and deficit.
    priority = importance_weight * (required - actual)
    """
    
    def analyze_gaps(self, required_skills: List[ExtractedSkill], actual_scores: List[SkillScore]) -> List[SkillGap]:
        """
        Compares required skills vs assessed scores and ranks gaps by priority.
        """
        score_map = {score.skill: score for score in actual_scores}
        
        gaps = []
        for req in required_skills:
            # Default to 0 if the skill was not assessed properly
            actual = score_map.get(req.skill_name)
            actual_score = actual.score if actual else 0
            
            gap_value = req.required_proficiency - actual_score
            
            # If gap <= 0, candidate meets or exceeds requirement
            if gap_value < 0:
                gap_value = 0
                
            priority = gap_value * req.importance_weight
            
            summary = ""
            if gap_value > 0:
                summary = f"Candidate is missing {gap_value} points in a {'critical' if req.importance_weight >=4 else 'secondary'} skill."
            else:
                summary = "Requirement met."

            gaps.append(SkillGap(
                skill=req.skill_name,
                required_proficiency=req.required_proficiency,
                actual_score=actual_score,
                importance_weight=req.importance_weight,
                gap=gap_value,
                priority=priority,
                summary=summary
            ))
            
        # Sort by highest priority first
        gaps.sort(key=lambda x: x.priority, reverse=True)
        return gaps
