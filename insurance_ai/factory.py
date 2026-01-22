"""
Factory - إنشاء وإدارة المحرك
"""
import logging
from typing import Optional

from .engine import ProfessionalInsuranceEngineV2
from .context import get_context_store, reset_context_store

logger = logging.getLogger(__name__)


# Global engine instance
_engine_instance: Optional[ProfessionalInsuranceEngineV2] = None


def get_professional_engine() -> ProfessionalInsuranceEngineV2:
    """
    الحصول على instance من المحرك
    
    Returns:
        ProfessionalInsuranceEngineV2: المحرك
    """
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = ProfessionalInsuranceEngineV2()
    return _engine_instance


def reset_professional_engine():
    """إعادة تعيين المحرك"""
    global _engine_instance
    _engine_instance = None
    reset_context_store()
    logger.info("🔄 Engine reset")
