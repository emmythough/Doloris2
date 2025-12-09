"""
Model Router - Intelligent model selection for cost optimization

Tier 0 (gpt-4o-mini): Ultra-cheap - Short reactions, yes/no, thanks
Tier 1 (gpt-4o-mini): Balance - General conversation, simple tasks
Tier 2 (gpt-4o): Standard - Tool usage, memory writes, calendar, file analysis
Tier 3 (o1-mini): Reasoning - Complex reasoning, planning
Tier 4 (o1-mini/o1-preview): Deep - Explicit deep thinking or max intelligence
"""

import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

class ModelTier(Enum):
    TIER_0 = "gpt-4o-mini"      # Ultra-cheap (was gpt-5-nano)
    TIER_1 = "gpt-4o-mini"      # Balance (was gpt-5-mini)
    TIER_2 = "gpt-4o-mini"      # Standard - switched from gpt-4o for cost savings
    TIER_3 = "o1-mini"          # Reasoning (was gpt-5.1)
    TIER_4_DEEP = "o1-mini"     # Deep
    TIER_4_MAX = "o1-preview"   # Max Intelligence (was o3-pro)

class ModelRouter:
    """Decides which model to use based on message intent"""
    
    # Keywords for Tier 0 (Nano)
    SHORT_ACKNOWLEDGEMENTS = [
        "ok", "okay", "k", "yes", "no", "yep", "nope", 
        "thanks", "thx", "cool", "nice", "got it", "sure", 
        "hi", "hello", "hey", "yo"
    ]
    
    # Keywords for Tier 3 (Reasoning)
    REASONING_KEYWORDS = [
        "analyze", "compare", "evaluate", "investigate", "study",
        "plan", "strategy", "why", "how to", "explain"
    ]
    
    # Keywords for Tier 4 (Deep/Max)
    DEEP_KEYWORDS = ["deep", "think hard", "complex"]
    MAX_KEYWORDS = ["deep research", "maximum intelligence", "max intelligence"]
    
    @staticmethod
    def select_model(
        message: str,
        context: str = "",
        has_tools: bool = False,
        user_preference: Optional[str] = None,
        file_attached: bool = False
    ) -> ModelTier:
        """
        Select the appropriate model tier
        """
        text = message.lower().strip()
        
        # Tier 4: Explicit Deep/Max Request
        if any(k in text for k in ModelRouter.MAX_KEYWORDS):
            logger.info("Max intelligence requested → Tier 4 (o1-preview)")
            return ModelTier.TIER_4_MAX
            
        if any(k in text for k in ModelRouter.DEEP_KEYWORDS) or user_preference == "deep":
            logger.info("Deep thinking requested → Tier 4 (o1-mini)")
            return ModelTier.TIER_4_DEEP
            
        # Tier 3: Complex Reasoning
        if any(k in text for k in ModelRouter.REASONING_KEYWORDS):
            logger.info("Reasoning needed → Tier 3 (o1-mini)")
            return ModelTier.TIER_3
            
        # Tier 2: Tools, Files, Long Context
        if has_tools or file_attached or len(context) > 2000:
            logger.info("Tools/Files/Context → Tier 2 (gpt-4o)")
            return ModelTier.TIER_2
            
        # Tier 0: Short Acknowledgements
        if len(text) < 12 or text in ModelRouter.SHORT_ACKNOWLEDGEMENTS:
            logger.info("Short acknowledgement → Tier 0 (gpt-4o-mini)")
            return ModelTier.TIER_0
            
        # Tier 1: Default (General Conversation)
        logger.info("General conversation → Tier 1 (gpt-4o-mini)")
        return ModelTier.TIER_1
    
    @staticmethod
    def get_model_name(tier: ModelTier) -> str:
        """Get the actual OpenAI model name"""
        return tier.value
