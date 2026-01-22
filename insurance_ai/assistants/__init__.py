"""
SAIA Assistants Module
متوافق مع django_ai_assistant
"""
from .base import AIAssistant, method_tool
from .insurance_assistant import InsuranceAssistant

__all__ = [
    'AIAssistant',
    'method_tool',
    'InsuranceAssistant',
]
