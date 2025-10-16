"""
Cost Tracker for OpenAI API Usage

Tracks token usage and calculates costs based on OpenAI pricing.
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class CostTracker:
    """Track OpenAI API costs"""
    
    # GPT-4o-mini pricing (as of October 2025)
    # Source: https://openai.com/api/pricing/
    INPUT_COST_PER_1M = 0.150  # $0.15 per 1M input tokens
    OUTPUT_COST_PER_1M = 0.600  # $0.60 per 1M output tokens
    
    @staticmethod
    def calculate_cost(input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost in USD for token usage.
        
        Args:
            input_tokens: Number of input (prompt) tokens
            output_tokens: Number of output (completion) tokens
        
        Returns:
            Total cost in USD
        """
        input_cost = (input_tokens / 1_000_000) * CostTracker.INPUT_COST_PER_1M
        output_cost = (output_tokens / 1_000_000) * CostTracker.OUTPUT_COST_PER_1M
        total_cost = input_cost + output_cost
        
        logger.debug(
            f"Cost calculation: {input_tokens} input + {output_tokens} output = ${total_cost:.4f}"
        )
        
        return total_cost
    
    @staticmethod
    def estimate_monthly_cost(suggestions_per_day: int, avg_tokens_per_suggestion: int = 800) -> Dict:
        """
        Estimate monthly cost based on daily suggestion volume.
        
        Args:
            suggestions_per_day: Number of suggestions generated per day
            avg_tokens_per_suggestion: Average total tokens per suggestion
        
        Returns:
            Dictionary with cost estimates
        """
        # Assume 60% input, 40% output (typical ratio)
        input_tokens = int(avg_tokens_per_suggestion * 0.6)
        output_tokens = int(avg_tokens_per_suggestion * 0.4)
        
        cost_per_suggestion = CostTracker.calculate_cost(input_tokens, output_tokens)
        daily_cost = cost_per_suggestion * suggestions_per_day
        monthly_cost = daily_cost * 30
        
        return {
            'suggestions_per_day': suggestions_per_day,
            'avg_tokens_per_suggestion': avg_tokens_per_suggestion,
            'cost_per_suggestion_usd': round(cost_per_suggestion, 4),
            'daily_cost_usd': round(daily_cost, 2),
            'monthly_cost_usd': round(monthly_cost, 2),
            'assumptions': {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'days_per_month': 30
            }
        }
    
    @staticmethod
    def check_budget_alert(total_cost: float, budget: float = 10.0) -> Dict:
        """
        Check if cost is approaching budget and return alert info.
        
        Args:
            total_cost: Current total cost
            budget: Monthly budget in USD (default: $10)
        
        Returns:
            Dictionary with alert status and details
        """
        usage_percent = (total_cost / budget) * 100
        
        alert_level = "ok"
        if usage_percent >= 90:
            alert_level = "critical"
        elif usage_percent >= 75:
            alert_level = "warning"
        elif usage_percent >= 50:
            alert_level = "info"
        
        return {
            'alert_level': alert_level,
            'total_cost_usd': round(total_cost, 2),
            'budget_usd': budget,
            'usage_percent': round(usage_percent, 1),
            'remaining_usd': round(budget - total_cost, 2),
            'should_alert': alert_level in ['warning', 'critical']
        }

