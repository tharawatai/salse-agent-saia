"""
AI Module - محرك الذكاء الاصطناعي
يحتوي على:
- SmartGeminiEngine: محرك Gemini الذكي
- retry_with_backoff: منطق إعادة المحاولة
- prompts: بناء الـ prompts
"""
from .gemini_engine import SmartGeminiEngine, SMART_ANALYSIS_SCHEMA
from .retry import RetryConfig, retry_with_backoff
from .prompts import build_smart_prompt

__all__ = [
    'SmartGeminiEngine',
    'SMART_ANALYSIS_SCHEMA',
    'RetryConfig',
    'retry_with_backoff',
    'build_smart_prompt',
]
