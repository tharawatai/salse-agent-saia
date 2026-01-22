from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class InsuranceAiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'insurance_ai'
    verbose_name = 'المساعد الذكي للتأمين'
    
    def ready(self):
        """
        تحميل المساعدين عند بدء التطبيق
        يسجلهم تلقائياً في الـ registry
        """
        try:
            # Import assistants to register them
            from .assistants import InsuranceAssistant
            
            # Log registered assistants
            from .assistants.base import AIAssistant
            registry = AIAssistant.get_cls_registry()
            
            logger.info(f"🤖 Registered {len(registry)} AI assistants: {list(registry.keys())}")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not load assistants: {e}")
