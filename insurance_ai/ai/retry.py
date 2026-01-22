"""
Retry Logic - منطق إعادة المحاولة مع Exponential Backoff
"""
import asyncio
import logging

logger = logging.getLogger(__name__)


class RetryConfig:
    """إعدادات إعادة المحاولة"""
    MAX_RETRIES = 3
    BASE_DELAY = 1.0  # ثانية
    MAX_DELAY = 10.0  # ثواني
    EXPONENTIAL_BASE = 2


async def retry_with_backoff(func, *args, **kwargs):
    """
    تنفيذ دالة مع إعادة المحاولة عند الفشل
    
    Args:
        func: الدالة المراد تنفيذها (async)
        *args: المعاملات الموضعية
        **kwargs: المعاملات المسماة
    
    Returns:
        نتيجة الدالة
    
    Raises:
        آخر استثناء في حالة فشل كل المحاولات
    """
    last_exception = None
    
    for attempt in range(RetryConfig.MAX_RETRIES):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < RetryConfig.MAX_RETRIES - 1:
                delay = min(
                    RetryConfig.BASE_DELAY * (RetryConfig.EXPONENTIAL_BASE ** attempt),
                    RetryConfig.MAX_DELAY
                )
                logger.warning(f"⚠️ Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"❌ All {RetryConfig.MAX_RETRIES} attempts failed: {e}")
    
    raise last_exception
