"""
Tri-Cameral Council - The three internal minds of Doloris
"""
import json
import logging
from typing import Dict, Any
from openai import AsyncOpenAI
from app.config import EMPATH_MODEL, AUDITOR_MODEL, EXECUTIVE_MODEL, OPENAI_API_KEY
from app.models.schemas import EmpathOutput, AuditorOutput, ExecutiveOutput, ThoughtTrace
from app.cognitive.prompts import (
    EMPATH_SYSTEM_PROMPT,
    AUDITOR_SYSTEM_PROMPT,
    EXECUTIVE_SYSTEM_PROMPT
)

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

class TriCameralCouncil:
    """
    The Ghost - Three internal minds that deliberate before action
    
    Empath → Auditor → Executive
    """
    
    async def deliberate(self, user_message: str, turn_id: str, context: Dict[str, Any] = None) -> ThoughtTrace:
        """
        Run the full Tri-Cameral Council deliberation
        
        Args:
            user_message: What the user said
            turn_id: Unique turn identifier
            context: User context (preferences, recent history, etc.)
        
        Returns:
            ThoughtTrace with all three agents' outputs
        """
        logger.info(f"[COUNCIL] Starting deliberation for turn {turn_id}")
        
        # Phase 1: Empath
        empath_output = await self._run_empath(user_message, context)
        logger.info(f"[EMPATH] Proposal: {empath_output.proposal}")
        
        # Phase 2: Auditor
        auditor_output = await self._run_auditor(user_message, empath_output, context)
        logger.info(f"[AUDITOR] Flags: {auditor_output.flags}")
        
        # Phase 3: Executive
        executive_output = await self._run_executive(user_message, empath_output, auditor_output, context)
        logger.info(f"[EXECUTIVE] Decision: {executive_output.decision}")
        
        # Calculate costs
        total_tokens = empath_output.tokens + auditor_output.tokens + executive_output.tokens
        total_cost = self._estimate_cost(total_tokens)
        
        return ThoughtTrace(
            turn_id=turn_id,
            empath=empath_output,
            auditor=auditor_output,
            executive=executive_output,
            total_tokens=total_tokens,
            total_cost_usd=total_cost
        )
    
    async def _run_empath(self, user_message: str, context: Dict[str, Any]) -> EmpathOutput:
        """
        Empath: Simulates user desires and proposes optimal path
        """
        messages = [
            {"role": "system", "content": EMPATH_SYSTEM_PROMPT},
            {"role": "user", "content": self._build_empath_prompt(user_message, context)}
        ]
        
        response = await client.chat.completions.create(
            model=EMPATH_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return EmpathOutput(
            summary=result["summary"],
            proposal=result["proposal"],
            predicted_intent=result["predicted_intent"],
            emotional_context=result["emotional_context"],
            tokens=response.usage.total_tokens
        )
    
    async def _run_auditor(self, user_message: str, empath: EmpathOutput, context: Dict[str, Any]) -> AuditorOutput:
        """
        Auditor: Flags risks, constraints, and ethical issues
        """
        messages = [
            {"role": "system", "content": AUDITOR_SYSTEM_PROMPT},
            {"role": "user", "content": self._build_auditor_prompt(user_message, empath, context)}
        ]
        
        response = await client.chat.completions.create(
            model=AUDITOR_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.3  # More conservative
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return AuditorOutput(
            summary=result["summary"],
            flags=result.get("flags", []),
            risks=result.get("risks", []),
            constraints=result.get("constraints", []),
            tokens=response.usage.total_tokens
        )
    
    async def _run_executive(
        self, 
        user_message: str, 
        empath: EmpathOutput, 
        auditor: AuditorOutput,
        context: Dict[str, Any]
    ) -> ExecutiveOutput:
        """
        Executive: Makes final decision synthesizing Empath + Auditor
        """
        messages = [
            {"role": "system", "content": EXECUTIVE_SYSTEM_PROMPT},
            {"role": "user", "content": self._build_executive_prompt(user_message, empath, auditor, context)}
        ]
        
        response = await client.chat.completions.create(
            model=EXECUTIVE_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.5  # Balanced
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return ExecutiveOutput(
            summary=result["summary"],
            decision=result["decision"],
            reasoning=result["reasoning"],
            final_intent=result["final_intent"],
            final_args=result.get("final_args", {}),
            confidence=result["confidence"],
            tokens=response.usage.total_tokens
        )
    
    def _build_empath_prompt(self, user_message: str, context: Dict[str, Any]) -> str:
        """Build prompt for Empath with context"""
        context_str = ""
        if context:
            context_str = f"\n\nUser context:\n{json.dumps(context, indent=2)}"
        
        return f"""User message: "{user_message}"{context_str}

What does the user truly want? Propose the optimal path."""
    
    def _build_auditor_prompt(self, user_message: str, empath: EmpathOutput, context: Dict[str, Any]) -> str:
        """Build prompt for Auditor"""
        return f"""User message: "{user_message}"

Empath proposes: "{empath.proposal}"
Predicted intent: {empath.predicted_intent}

Flag any risks, constraints, or missing information."""
    
    def _build_executive_prompt(
        self, 
        user_message: str, 
        empath: EmpathOutput, 
        auditor: AuditorOutput,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for Executive"""
        return f"""User message: "{user_message}"

Empath proposes: "{empath.proposal}"

Auditor flags: {json.dumps(auditor.flags)}
Auditor risks: {json.dumps(auditor.risks)}

Make the final decision. Synthesize Empath's optimism with Auditor's caution.

If risks are serious → ask user first.
If aligned → proceed.
If unsure → clarify."""
    
    def _estimate_cost(self, total_tokens: int) -> float:
        """Estimate cost in USD (rough approximation)"""
        # All models now gpt-4o-mini: $0.15 per 1M input tokens, $0.60 per 1M output tokens
        # Using average estimate for simplicity
        cost_per_token = 0.30 / 1_000_000
        return total_tokens * cost_per_token


# Global instance
council = TriCameralCouncil()
