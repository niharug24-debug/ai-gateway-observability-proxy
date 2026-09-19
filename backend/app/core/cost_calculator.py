"""
Token & Cost Observability Engine.
Calculates token usage and exact dollar costs/savings based on model pricing catalogs.
"""

from typing import Dict, Any, Tuple


# Model pricing table per 1,000,000 tokens (USD)
# Format: {model_prefix: (prompt_cost_per_million, completion_cost_per_million)}
MODEL_PRICING_CATALOG: Dict[str, Tuple[float, float]] = {
    # OpenAI Models
    "gpt-4o": (5.00, 15.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-4": (30.00, 60.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    # Google Gemini Models
    "gemini-1.5-pro": (3.50, 10.50),
    "gemini-1.5-flash": (0.35, 1.05),
    # Anthropic Models
    "claude-3-5-sonnet": (3.00, 15.00),
    "claude-3-haiku": (0.25, 1.25),
    # Default fallback rate
    "default": (1.00, 3.00)
}


class CostCalculator:
    """
    Computes financial costs and savings based on token quantities and provider models.
    """
    @staticmethod
    def get_model_rates(model_name: str) -> Tuple[float, float]:
        """
        Retrieves (prompt_rate_per_million, completion_rate_per_million) for a model.
        """
        cleaned = model_name.lower().strip()
        for prefix, rates in MODEL_PRICING_CATALOG.items():
            if cleaned.startswith(prefix):
                return rates
        return MODEL_PRICING_CATALOG["default"]

    @classmethod
    def calculate_cost(
        cls,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        Calculates the estimated cost in USD for a completion.
        """
        prompt_rate, completion_rate = cls.get_model_rates(model_name)
        cost = (prompt_tokens / 1_000_000.0) * prompt_rate + \
               (completion_tokens / 1_000_000.0) * completion_rate
        return round(cost, 6)

    @classmethod
    def estimate_tokens_from_text(cls, text: str) -> int:
        """
        Heuristic token estimator (~4 characters per token in English).
        Used when raw tokenizer is unavailable or for fast approximations.
        """
        if not text:
            return 0
        return max(1, len(text) // 4)

    @classmethod
    def estimate_tokens_from_messages(cls, messages: list) -> int:
        """
        Estimates total prompt tokens from a list of chat messages.
        """
        total = 0
        for m in messages:
            content = m.get("content", "")
            if isinstance(content, str):
                total += cls.estimate_tokens_from_text(content) + 4  # Formatting overhead
            elif isinstance(content, list):
                total += len(content) * 10
        return max(1, total)
