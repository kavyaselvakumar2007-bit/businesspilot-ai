import os
import sys
import pytest

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import SCORING_RULES, PRIORITY_TIERS
from agents.lead_analysis_agent import LeadAnalysisAgent

@pytest.fixture
def scoring_agent():
    return LeadAnalysisAgent()

def test_score_calculation_high_value(scoring_agent):
    """
    Test lead scoring for a high-value lead.
    - Revenue: $12,000,000 -> Expected bracket points: 30
    - Employees: 150 -> Expected bracket points: 15
    - Interactions: 8 -> Expected factor points: 8 * 3 = 24
    - Conversion rate: 0.75 -> Expected factor points: 0.75 * 20 = 15
    Expected score: 30 + 15 + 24 + 15 = 84
    """
    lead = {
        "annual_revenue": 12000000,
        "employee_count": 150,
        "interactions_count": 8,
        "estimated_conversion_rate": 0.75
    }
    
    score = scoring_agent.score_lead(lead, SCORING_RULES)
    assert score == 84

def test_score_calculation_low_value(scoring_agent):
    """
    Test lead scoring for a low-value lead.
    - Revenue: $500,000 -> Expected bracket points: 10
    - Employees: 10 -> Expected bracket points: 10
    - Interactions: 1 -> Expected factor points: 1 * 3 = 3
    - Conversion rate: 0.05 -> Expected factor points: 0.05 * 20 = 1
    Expected score: 10 + 10 + 3 + 1 = 24
    """
    lead = {
        "annual_revenue": 500000,
        "employee_count": 10,
        "interactions_count": 1,
        "estimated_conversion_rate": 0.05
    }
    
    score = scoring_agent.score_lead(lead, SCORING_RULES)
    assert score == 24

def test_score_capping(scoring_agent):
    """
    Test that lead scores are capped at a maximum of 100 points.
    - Huge revenue, employees, interactions, and conversion rate.
    """
    lead = {
        "annual_revenue": 500000000,  # 40 points
        "employee_count": 5000,       # 20 points
        "interactions_count": 30,      # 30 * 3 = 90 points
        "estimated_conversion_rate": 0.95 # 0.95 * 20 = 19 points
    }
    # Raw total: 40 + 20 + 90 + 19 = 169
    score = scoring_agent.score_lead(lead, SCORING_RULES)
    assert score == 100

def test_priority_tier_assignment(scoring_agent):
    """
    Test that priority tiers are correctly resolved based on scores.
    """
    # Hot threshold is >= 70
    # Warm is >= 40
    # Cold is < 40
    
    # We will simulate the priority tier assignment logic from execute()
    def get_tier(score):
        tier = "Cold"
        for t, min_score in sorted(PRIORITY_TIERS.items(), key=lambda x: x[1], reverse=True):
            if score >= min_score:
                tier = t
                break
        return tier

    assert get_tier(85) == "Hot"
    assert get_tier(70) == "Hot"
    assert get_tier(55) == "Warm"
    assert get_tier(40) == "Warm"
    assert get_tier(25) == "Cold"
