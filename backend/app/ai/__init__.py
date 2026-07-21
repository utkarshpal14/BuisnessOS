"""
AI Intelligence layer for BusinessOS AI.

Layers:
- intelligence_service.py : BusinessSnapshot -> LLM prompt (no API calls)
- llm_adapter.py           : LLMAdapter interface + placeholder/mock provider adapters
- agent.py                 : AIAgent, the Planner-facing BaseAgent implementation

Nothing in this package calls a real external LLM API yet -- MockLLMAdapter is the only
adapter that returns something from generate(), and it does so deterministically from
the prompt text alone. Wiring a real provider later means filling in ClaudeAdapter's or
OpenAIAdapter's generate() method, without touching AIAgent, AIIntelligenceService, or
anything upstream (Enterprise Agent, Planner, Sales/Finance agents).
"""

__all__ = [
    "AIAgent",
    "AIIntelligenceService",
    "LLMAdapter",
    "ClaudeAdapter",
    "OpenAIAdapter",
    "MockLLMAdapter",
]
