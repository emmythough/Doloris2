"""
Model Router - Intelligent model selection for cost optimization

Tier 1 (gpt-4o-mini): Fast, cheap - intent detection, simple responses
Tier 2 (gpt-4o): Main brain - conversations, tool calling
Tier 3 (o1-mini): Deep reasoning - complex analysis, research
"""

import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

class ModelTier(Enum):
    TIER_1 = "gpt-4o-mini"      # Fast & cheap
    TIER_2 = "gpt-4o"            # Main brain
    TIER_3 = "o1-mini"           # Deep reasoning

class ModelRouter:
    """Decides which model to use based on message intent"""
    
    # Keywords that suggest simple intent (Tier 1)
    SIMPLE_KEYWORDS = [
        "hi", "hello", "hey", "thanks", "thank you", "ok", "okay",
        "yes", "no", "sure", "got it", "cool", "nice"
    ]
    
    # Keywords that suggest deep reasoning needed (Tier 3)
    DEEP_KEYWORDS = [
        "analyze", "research", "explain in detail", "compare",
        "pros and cons", "evaluate", "investigate", "study"
    ]
    
    @staticmethod
    def select_model(
        message: str,
        has_tools: bool = False,
        user_preference: Optional[str] = None,
        file_attached: bool = False
    ) -> ModelTier:
        """
        Select the appropriate model tier
        
        Args:
            message: User's message text
            has_tools: Whether tools are available for this request
            user_preference: User's thinking_mode preference
            file_attached: Whether user attached a file
        
        Returns:
            ModelTier enum
        """
        message_lower = message.lower().strip()
        
        # User explicitly requested deep thinking
        if user_preference == "deep":
            logger.info("User preference: deep → Tier 3")
            return ModelTier.TIER_3
        
        # Check for deep reasoning keywords
        if any(keyword in message_lower for keyword in ModelRouter.DEEP_KEYWORDS):
            logger.info("Deep reasoning keywords detected → Tier 3")
            return ModelTier.TIER_3
        
        # File attached - use main brain for understanding
        if file_attached:
            logger.info("File attached → Tier 2")
            return ModelTier.TIER_2
        
        # Tools required - use main brain
        if has_tools:
            logger.info("Tools required → Tier 2")
            return ModelTier.TIER_2
        
        # Simple greeting or acknowledgment
        if any(keyword == message_lower for keyword in ModelRouter.SIMPLE_KEYWORDS):
            logger.info("Simple intent detected → Tier 1")
            return ModelTier.TIER_1
        
        # Very short message (likely simple)
        if len(message.split()) <= 3:
            logger.info("Short message → Tier 1")
            return ModelTier.TIER_1
        
        # Default to Tier 2 (main brain)
        logger.info("Default → Tier 2")
        return ModelTier.TIER_2
    
    @staticmethod
    def get_model_name(tier: ModelTier) -> str:
        """Get the actual OpenAI model name"""
        return tier.value
