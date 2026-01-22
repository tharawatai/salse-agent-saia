"""
SAIA Insurance - Professional Cache Manager
نظام إدارة الكاش الاحترافي مع Redis

المميزات:
- تخزين بيانات المستخدم بمعرف فريد (UUID)
- حفظ تلقائي في قاعدة البيانات عند اكتمال العملية
- دعم TTL مع تجديد تلقائي
- Atomic operations للأمان
- Fallback للذاكرة المحلية
"""
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, TypeVar, Generic
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod

from django.conf import settings
from django.db import transaction
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Enums & Constants
# ═══════════════════════════════════════════════════════════════

class SessionStatus(str, Enum):
    """حالة الجلسة"""
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class CachePrefix:
    """بادئات مفاتيح الكاش"""
    SESSION = "session"
    USER = "user"
    VEHICLE = "vehicle"
    PROFILE = "profile"
    OFFERS = "offers"
    ORDER = "order"
    TEMP = "temp"


# TTL Settings (بالثواني)
class TTLConfig:
    SESSION = 86400      # 24 ساعة
    TEMP_DATA = 3600     # ساعة واحدة
    OFFERS = 1800        # 30 دقيقة
    LOCK = 30            # 30 ثانية


# 🆕 إعدادات الأداء
class PerformanceConfig:
    """إعدادات تحسين الأداء"""
    # تعطيل الحفظ التلقائي في DB (يحفظ فقط عند الاكتمال)
    LAZY_DB_PERSIST = True
    # المراحل التي تتطلب حفظ في DB
    PERSIST_STAGES = {
        'confirming_vehicle',
        'confirming_profile', 
        'payment_pending',
        'completed',
    }
    # الحد الأقصى للرسائل قبل الحفظ الإجباري
    MAX_MESSAGES_BEFORE_PERSIST = 10


# ═══════════════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════════════

@dataclass
class CachedVehicleData:
    """بيانات السيارة المخزنة"""
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    value: Optional[float] = None
    plate_no: Optional[str] = None
    service_type: Optional[str] = None
    confirmed: bool = False
    
    def is_complete(self) -> bool:
        """هل البيانات مكتملة؟"""
        return all([self.brand, self.model, self.year, self.value, self.plate_no])
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CachedVehicleData':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CachedProfileData:
    """بيانات العميل المخزنة"""
    national_id: Optional[str] = None
    birth_date: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    confirmed: bool = False
    
    def is_complete(self) -> bool:
        """هل البيانات مكتملة؟"""
        return all([self.national_id, self.birth_date])
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CachedProfileData':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CachedOfferData:
    """بيانات العرض المخزنة"""
    offer_id: int
    company: str
    coverage_type: str
    base_price: float
    discount: float
    vat: float
    final_price: float
    company_rating: float = 0.0
    features: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CachedOfferData':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class UserSession:
    """جلسة المستخدم الكاملة"""
    session_id: str
    user_identifier: str  # phone أو user_id
    current_stage: str = "greeting"
    status: SessionStatus = SessionStatus.ACTIVE
    
    # البيانات المجمعة
    vehicle: CachedVehicleData = field(default_factory=CachedVehicleData)
    profile: CachedProfileData = field(default_factory=CachedProfileData)
    
    # العروض
    available_offers: List[Dict] = field(default_factory=list)
    selected_offer: Optional[Dict] = None
    selected_offer_id: Optional[int] = None
    
    # نتائج العملية
    order_id: Optional[int] = None
    order_code: Optional[str] = None
    invoice_id: Optional[int] = None
    invoice_no: Optional[str] = None
    policy_id: Optional[int] = None
    policy_no: Optional[str] = None
    
    # التتبع
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    
    # سجل الرسائل
    message_count: int = 0
    last_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """تحويل لـ dictionary"""
        return {
            'session_id': self.session_id,
            'user_identifier': self.user_identifier,
            'current_stage': self.current_stage,
            'status': self.status.value if isinstance(self.status, SessionStatus) else self.status,
            'vehicle': self.vehicle.to_dict() if isinstance(self.vehicle, CachedVehicleData) else self.vehicle,
            'profile': self.profile.to_dict() if isinstance(self.profile, CachedProfileData) else self.profile,
            'available_offers': self.available_offers,
            'selected_offer': self.selected_offer,
            'selected_offer_id': self.selected_offer_id,
            'order_id': self.order_id,
            'order_code': self.order_code,
            'invoice_id': self.invoice_id,
            'invoice_no': self.invoice_no,
            'policy_id': self.policy_id,
            'policy_no': self.policy_no,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'completed_at': self.completed_at,
            'message_count': self.message_count,
            'last_message': self.last_message,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserSession':
        """إنشاء من dictionary"""
        vehicle_data = data.get('vehicle', {})
        profile_data = data.get('profile', {})
        
        return cls(
            session_id=data.get('session_id', ''),
            user_identifier=data.get('user_identifier', ''),
            current_stage=data.get('current_stage', 'greeting'),
            status=SessionStatus(data.get('status', 'active')),
            vehicle=CachedVehicleData.from_dict(vehicle_data) if vehicle_data else CachedVehicleData(),
            profile=CachedProfileData.from_dict(profile_data) if profile_data else CachedProfileData(),
            available_offers=data.get('available_offers', []),
            selected_offer=data.get('selected_offer'),
            selected_offer_id=data.get('selected_offer_id'),
            order_id=data.get('order_id'),
            order_code=data.get('order_code'),
            invoice_id=data.get('invoice_id'),
            invoice_no=data.get('invoice_no'),
            policy_id=data.get('policy_id'),
            policy_no=data.get('policy_no'),
            created_at=data.get('created_at', datetime.now().isoformat()),
            updated_at=data.get('updated_at', datetime.now().isoformat()),
            completed_at=data.get('completed_at'),
            message_count=data.get('message_count', 0),
            last_message=data.get('last_message'),
        )
    
    def mark_completed(self):
        """تحديد الجلسة كمكتملة"""
        self.status = SessionStatus.COMPLETED
        self.completed_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()


# ═══════════════════════════════════════════════════════════════
# Cache Backend Interface
# ═══════════════════════════════════════════════════════════════

class CacheBackend(ABC):
    """واجهة الكاش الأساسية"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        pass
    
    @abstractmethod
    def set(self, key: str, value: str, ttl: int = None) -> bool:
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        pass
    
    @abstractmethod
    def expire(self, key: str, ttl: int) -> bool:
        pass
    
    @abstractmethod
    def keys(self, pattern: str) -> List[str]:
        pass


class RedisCacheBackend(CacheBackend):
    """Redis Cache Backend"""
    
    def __init__(self):
        self._client = None
        self._connected = False
        self._connect()
    
    def _connect(self):
        try:
            import redis
            redis_url = getattr(settings, 'REDIS_URL', None)
            if redis_url:
                self._client = redis.from_url(redis_url, decode_responses=True)
                self._client.ping()
                self._connected = True
                logger.info("✅ Redis cache backend connected")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
            self._connected = False
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    def get(self, key: str) -> Optional[str]:
        if not self._connected:
            return None
        try:
            return self._client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None
    
    def set(self, key: str, value: str, ttl: int = None) -> bool:
        if not self._connected:
            return False
        try:
            if ttl:
                return self._client.setex(key, ttl, value)
            return self._client.set(key, value)
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        if not self._connected:
            return False
        try:
            return self._client.delete(key) > 0
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        if not self._connected:
            return False
        try:
            return self._client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        if not self._connected:
            return False
        try:
            return self._client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Redis EXPIRE error: {e}")
            return False
    
    def keys(self, pattern: str) -> List[str]:
        if not self._connected:
            return []
        try:
            return self._client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis KEYS error: {e}")
            return []
    
    def acquire_lock(self, lock_name: str, ttl: int = TTLConfig.LOCK) -> bool:
        """الحصول على قفل"""
        if not self._connected:
            return True  # في حالة عدم وجود Redis، نسمح بالعملية
        try:
            return self._client.set(f"lock:{lock_name}", "1", nx=True, ex=ttl)
        except Exception as e:
            logger.error(f"Redis LOCK error: {e}")
            return True
    
    def release_lock(self, lock_name: str) -> bool:
        """تحرير القفل"""
        if not self._connected:
            return True
        try:
            return self._client.delete(f"lock:{lock_name}") > 0
        except Exception as e:
            logger.error(f"Redis UNLOCK error: {e}")
            return True


class MemoryCacheBackend(CacheBackend):
    """Memory Cache Backend (Fallback)"""
    
    def __init__(self):
        self._store: Dict[str, Dict] = {}  # {key: {value, expires_at}}
        logger.info("ℹ️ Using memory cache backend")
    
    def _cleanup_expired(self):
        """تنظيف المفاتيح المنتهية"""
        now = datetime.now()
        expired = [k for k, v in self._store.items() if v.get('expires_at') and v['expires_at'] < now]
        for k in expired:
            del self._store[k]
    
    def get(self, key: str) -> Optional[str]:
        self._cleanup_expired()
        item = self._store.get(key)
        if item:
            if item.get('expires_at') and item['expires_at'] < datetime.now():
                del self._store[key]
                return None
            return item['value']
        return None
    
    def set(self, key: str, value: str, ttl: int = None) -> bool:
        expires_at = datetime.now() + timedelta(seconds=ttl) if ttl else None
        self._store[key] = {'value': value, 'expires_at': expires_at}
        return True
    
    def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False
    
    def exists(self, key: str) -> bool:
        self._cleanup_expired()
        return key in self._store
    
    def expire(self, key: str, ttl: int) -> bool:
        if key in self._store:
            self._store[key]['expires_at'] = datetime.now() + timedelta(seconds=ttl)
            return True
        return False
    
    def keys(self, pattern: str) -> List[str]:
        self._cleanup_expired()
        import fnmatch
        return [k for k in self._store.keys() if fnmatch.fnmatch(k, pattern)]


# ═══════════════════════════════════════════════════════════════
# Session Cache Manager - المدير الرئيسي
# ═══════════════════════════════════════════════════════════════

class SessionCacheManager:
    """
    مدير جلسات المستخدمين الاحترافي
    
    المميزات:
    - إنشاء جلسات بمعرف فريد UUID
    - تخزين مؤقت في Redis/Memory
    - حفظ تلقائي في DB عند الاكتمال
    - تجديد TTL تلقائي
    - دعم Atomic operations
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # اختيار Backend
        self._redis = RedisCacheBackend()
        if self._redis.is_connected:
            self._backend = self._redis
            self._use_redis = True
        else:
            self._backend = MemoryCacheBackend()
            self._use_redis = False
        
        self._initialized = True
        logger.info(f"✅ SessionCacheManager initialized (Redis: {self._use_redis})")
    
    def _make_key(self, prefix: str, identifier: str) -> str:
        """إنشاء مفتاح الكاش"""
        return f"saia:{prefix}:{identifier}"
    
    def generate_session_id(self) -> str:
        """إنشاء معرف جلسة فريد"""
        return str(uuid.uuid4())
    
    # ═══════════════════════════════════════════════════════════
    # Session Operations
    # ═══════════════════════════════════════════════════════════
    
    def create_session(self, user_identifier: str, channel: str = 'whatsapp') -> UserSession:
        """
        إنشاء جلسة جديدة للمستخدم
        
        Args:
            user_identifier: رقم الهاتف أو معرف المستخدم
            channel: قناة التواصل (whatsapp, web_chat, api)
        
        Returns:
            UserSession: الجلسة الجديدة
        """
        session_id = self.generate_session_id()
        
        session = UserSession(
            session_id=session_id,
            user_identifier=user_identifier,
            current_stage="greeting",
            status=SessionStatus.ACTIVE
        )
        
        # حفظ في الكاش
        self._save_session_to_cache(session)
        
        # ربط المستخدم بالجلسة
        self._link_user_to_session(user_identifier, session_id)
        
        # حفظ في قاعدة البيانات
        self._persist_session_to_db(session_id, user_identifier, channel)
        
        logger.info(f"🆕 Created session {session_id[:8]}... for user {user_identifier}")
        return session
    
    def _persist_session_to_db(self, session_id: str, user_identifier: str, channel: str = 'whatsapp'):
        """حفظ الجلسة في قاعدة البيانات"""
        try:
            from .data_persistence_service import SessionPersistenceService
            from asgiref.sync import async_to_sync
            import asyncio
            
            # التحقق من وجود event loop
            try:
                loop = asyncio.get_running_loop()
                # نحن في async context - استخدم thread
                import threading
                def _save():
                    SessionPersistenceService.get_or_create_db_session(
                        session_id=session_id,
                        user_identifier=user_identifier,
                        channel=channel
                    )
                thread = threading.Thread(target=_save)
                thread.start()
            except RuntimeError:
                # لا يوجد event loop - استدعاء مباشر
                SessionPersistenceService.get_or_create_db_session(
                    session_id=session_id,
                    user_identifier=user_identifier,
                    channel=channel
                )
        except Exception as e:
            logger.warning(f"⚠️ Failed to persist session to DB: {e}")
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """
        جلب جلسة بالمعرف
        
        Args:
            session_id: معرف الجلسة
        
        Returns:
            UserSession أو None
        """
        key = self._make_key(CachePrefix.SESSION, session_id)
        data = self._backend.get(key)
        
        if data:
            session = UserSession.from_dict(json.loads(data))
            # تجديد TTL
            self._backend.expire(key, TTLConfig.SESSION)
            return session
        
        return None
    
    def get_session_by_user(self, user_identifier: str) -> Optional[UserSession]:
        """
        جلب جلسة المستخدم النشطة
        
        Args:
            user_identifier: رقم الهاتف أو معرف المستخدم
        
        Returns:
            UserSession أو None
        """
        # جلب معرف الجلسة المرتبط بالمستخدم
        user_key = self._make_key(CachePrefix.USER, user_identifier)
        session_id = self._backend.get(user_key)
        
        if session_id:
            session = self.get_session(session_id)
            if session and session.status == SessionStatus.ACTIVE:
                return session
        
        return None
    
    def get_or_create_session(self, user_identifier: str) -> UserSession:
        """
        جلب أو إنشاء جلسة للمستخدم
        
        Args:
            user_identifier: رقم الهاتف أو معرف المستخدم
        
        Returns:
            UserSession
        """
        session = self.get_session_by_user(user_identifier)
        if session:
            logger.info(f"📦 Retrieved existing session {session.session_id[:8]}... for {user_identifier}")
            return session
        
        return self.create_session(user_identifier)
    
    def update_session(self, session: UserSession) -> bool:
        """
        تحديث الجلسة في الكاش
        
        Args:
            session: الجلسة المحدثة
        
        Returns:
            bool: نجاح العملية
        """
        session.updated_at = datetime.now().isoformat()
        return self._save_session_to_cache(session)
    
    def _save_session_to_cache(self, session: UserSession) -> bool:
        """حفظ الجلسة في الكاش"""
        key = self._make_key(CachePrefix.SESSION, session.session_id)
        data = json.dumps(session.to_dict(), ensure_ascii=False)
        return self._backend.set(key, data, TTLConfig.SESSION)
    
    def _link_user_to_session(self, user_identifier: str, session_id: str):
        """ربط المستخدم بالجلسة"""
        user_key = self._make_key(CachePrefix.USER, user_identifier)
        self._backend.set(user_key, session_id, TTLConfig.SESSION)
    
    def delete_session(self, session_id: str) -> bool:
        """حذف جلسة"""
        session = self.get_session(session_id)
        if session:
            # حذف ربط المستخدم
            user_key = self._make_key(CachePrefix.USER, session.user_identifier)
            self._backend.delete(user_key)
        
        # حذف الجلسة
        key = self._make_key(CachePrefix.SESSION, session_id)
        return self._backend.delete(key)
    
    # ═══════════════════════════════════════════════════════════
    # Smart Data Completeness Check
    # ═══════════════════════════════════════════════════════════
    
    def check_stage_data_complete(self, session_id: str, stage: str) -> Dict[str, Any]:
        """
        التحقق من اكتمال بيانات المرحلة
        
        Returns:
            Dict with:
            - is_complete: bool
            - missing_fields: list
            - can_proceed: bool
        """
        session = self.get_session(session_id)
        if not session:
            return {"is_complete": False, "missing_fields": ["session"], "can_proceed": False}
        
        result = {"is_complete": False, "missing_fields": [], "can_proceed": False}
        
        if stage in ["collecting_vehicle", "confirming_vehicle"]:
            # التحقق من بيانات السيارة
            v = session.vehicle
            missing = []
            if not v.brand: missing.append("brand")
            if not v.model: missing.append("model")
            if not v.year: missing.append("year")
            if not v.value: missing.append("value")
            if not v.plate_no: missing.append("plate_no")
            
            result["missing_fields"] = missing
            result["is_complete"] = len(missing) == 0
            result["can_proceed"] = result["is_complete"]
            
        elif stage in ["collecting_profile", "confirming_profile"]:
            # التحقق من بيانات العميل
            p = session.profile
            missing = []
            if not p.national_id: missing.append("national_id")
            if not p.birth_date: missing.append("birth_date")
            
            result["missing_fields"] = missing
            result["is_complete"] = len(missing) == 0
            result["can_proceed"] = result["is_complete"]
            
        elif stage == "showing_offers":
            # التحقق من وجود عروض
            result["is_complete"] = len(session.available_offers) > 0
            result["can_proceed"] = result["is_complete"]
            
        elif stage == "offer_details":
            # التحقق من اختيار عرض
            result["is_complete"] = session.selected_offer is not None
            result["can_proceed"] = result["is_complete"]
            
        elif stage == "order_summary":
            # التحقق من اكتمال كل البيانات
            v_complete = session.vehicle.is_complete()
            p_complete = session.profile.is_complete()
            o_selected = session.selected_offer is not None
            
            result["is_complete"] = v_complete and p_complete and o_selected
            result["can_proceed"] = result["is_complete"]
            
        else:
            result["is_complete"] = True
            result["can_proceed"] = True
        
        return result
    
    def get_session_progress(self, session_id: str) -> Dict[str, Any]:
        """
        الحصول على تقدم الجلسة
        
        Returns:
            Dict with progress info
        """
        session = self.get_session(session_id)
        if not session:
            return {}
        
        return {
            "session_id": session.session_id,
            "current_stage": session.current_stage,
            "vehicle_complete": session.vehicle.is_complete(),
            "vehicle_confirmed": session.vehicle.confirmed,
            "profile_complete": session.profile.is_complete(),
            "profile_confirmed": session.profile.confirmed,
            "offers_shown": len(session.available_offers) > 0,
            "offer_selected": session.selected_offer is not None,
            "order_created": session.order_id is not None,
            "message_count": session.message_count,
        }
    
    # ═══════════════════════════════════════════════════════════
    # Data Update Operations
    # ═══════════════════════════════════════════════════════════
    
    def update_vehicle_data(self, session_id: str, **kwargs) -> bool:
        """
        تحديث بيانات السيارة
        
        Args:
            session_id: معرف الجلسة
            **kwargs: البيانات (brand, model, year, value, plate_no, service_type)
        
        Returns:
            bool: نجاح العملية
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        # تصفية القيم الفارغة و 'null' strings
        clean_kwargs = {}
        for key, value in kwargs.items():
            if hasattr(session.vehicle, key) and value is not None:
                # تجاهل قيم 'null' string
                if isinstance(value, str) and value.lower() in ['null', 'none', '']:
                    continue
                setattr(session.vehicle, key, value)
                clean_kwargs[key] = value
        
        if clean_kwargs:
            logger.debug(f"📝 Vehicle: {clean_kwargs}")
        
        # حفظ في الكاش فقط (سريع جداً)
        result = self.update_session(session)
        
        # 🆕 حفظ في DB فقط إذا LAZY_DB_PERSIST معطل أو البيانات مكتملة ومؤكدة
        if not PerformanceConfig.LAZY_DB_PERSIST:
            if session.vehicle.is_complete():
                self._persist_vehicle_to_db(session_id, session.vehicle)
        
        return result
        
        return result
    
    def _persist_vehicle_to_db(self, session_id: str, vehicle_data):
        """حفظ بيانات السيارة المكتملة في قاعدة البيانات"""
        try:
            from .data_persistence_service import SessionPersistenceService
            import asyncio
            import threading
            
            # تحويل البيانات للـ dict
            if hasattr(vehicle_data, 'to_dict'):
                data = vehicle_data.to_dict()
            else:
                data = vehicle_data
            
            def _save():
                SessionPersistenceService.update_vehicle_data(
                    session_id,
                    brand=data.get('brand'),
                    model=data.get('model'),
                    year=data.get('year'),
                    value=data.get('value'),
                    plate_no=data.get('plate_no'),
                    service_type=data.get('service_type'),
                    is_confirmed=data.get('confirmed', False)
                )
            
            try:
                asyncio.get_running_loop()
                thread = threading.Thread(target=_save)
                thread.start()
            except RuntimeError:
                _save()
        except Exception as e:
            logger.warning(f"⚠️ Failed to persist vehicle data to DB: {e}")
    
    def update_profile_data(self, session_id: str, **kwargs) -> bool:
        """
        تحديث بيانات العميل
        
        Args:
            session_id: معرف الجلسة
            **kwargs: البيانات (national_id, birth_date, full_name, phone, email)
        
        Returns:
            bool: نجاح العملية
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        # تصفية القيم الفارغة و 'null' strings
        clean_kwargs = {}
        for key, value in kwargs.items():
            if hasattr(session.profile, key) and value is not None:
                # تجاهل قيم 'null' string
                if isinstance(value, str) and value.lower() in ['null', 'none', '']:
                    continue
                setattr(session.profile, key, value)
                clean_kwargs[key] = value
        
        if clean_kwargs:
            logger.debug(f"📝 Profile: {clean_kwargs}")
        
        # حفظ في الكاش فقط (سريع جداً)
        result = self.update_session(session)
        
        # 🆕 حفظ في DB فقط إذا LAZY_DB_PERSIST معطل
        if not PerformanceConfig.LAZY_DB_PERSIST:
            if session.profile.is_complete():
                self._persist_profile_to_db(session_id, session.profile)
        
        return result
    
    def _persist_profile_to_db(self, session_id: str, profile_data):
        """حفظ بيانات العميل المكتملة في قاعدة البيانات"""
        try:
            from .data_persistence_service import SessionPersistenceService
            import asyncio
            import threading
            
            # تحويل البيانات للـ dict
            if hasattr(profile_data, 'to_dict'):
                data = profile_data.to_dict()
            else:
                data = profile_data
            
            def _save():
                SessionPersistenceService.update_profile_data(
                    session_id,
                    national_id=data.get('national_id'),
                    birth_date=data.get('birth_date'),
                    full_name=data.get('full_name'),
                    phone=data.get('phone'),
                    email=data.get('email'),
                    is_confirmed=data.get('confirmed', False)
                )
            
            try:
                asyncio.get_running_loop()
                thread = threading.Thread(target=_save)
                thread.start()
            except RuntimeError:
                _save()
        except Exception as e:
            logger.warning(f"⚠️ Failed to persist profile data to DB: {e}")
    
    def set_available_offers(self, session_id: str, offers: List[Dict]) -> bool:
        """تعيين العروض المتاحة - يحفظ في DB فقط إذا كانت هناك عروض"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.available_offers = offers
        logger.info(f"📋 Set {len(offers)} offers for session {session_id[:8]}...")
        
        # حفظ في الكاش أولاً
        result = self.update_session(session)
        
        # حفظ في DB فقط إذا كانت هناك عروض فعلية
        if offers and len(offers) > 0:
            logger.info(f"✅ Offers available - persisting to DB")
            self._persist_offers_to_db(session_id, shown_offers=offers)
        
        return result
    
    def _persist_offers_to_db(self, session_id: str, **kwargs):
        """حفظ بيانات العروض في قاعدة البيانات"""
        try:
            from .data_persistence_service import SessionPersistenceService
            import asyncio
            import threading
            
            def _save():
                SessionPersistenceService.save_offers_data(session_id, **kwargs)
            
            try:
                asyncio.get_running_loop()
                thread = threading.Thread(target=_save)
                thread.start()
            except RuntimeError:
                _save()
        except Exception as e:
            logger.warning(f"⚠️ Failed to persist offers to DB: {e}")
    
    def select_offer(self, session_id: str, offer_index: int) -> Optional[Dict]:
        """
        اختيار عرض
        
        Args:
            session_id: معرف الجلسة
            offer_index: رقم العرض (1-based)
        
        Returns:
            Dict: العرض المختار أو None
        """
        session = self.get_session(session_id)
        if not session or not session.available_offers:
            return None
        
        if 1 <= offer_index <= len(session.available_offers):
            offer = session.available_offers[offer_index - 1]
            session.selected_offer = offer
            session.selected_offer_id = offer.get('id')
            self.update_session(session)
            
            # حفظ في قاعدة البيانات
            self._persist_offers_to_db(
                session_id,
                selected_offer_id=offer.get('id'),
                selected_offer_data=offer
            )
            
            logger.info(f"✅ Selected offer #{offer_index} for session {session_id[:8]}...")
            return offer
        
        return None
    
    def set_selected_offer(self, session_id: str, offer: Dict) -> bool:
        """
        تعيين العرض المختار مباشرة
        
        Args:
            session_id: معرف الجلسة
            offer: بيانات العرض
        
        Returns:
            bool: نجاح العملية
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.selected_offer = offer
        session.selected_offer_id = offer.get('id')
        
        # حفظ في قاعدة البيانات
        self._persist_offers_to_db(
            session_id,
            selected_offer_id=offer.get('id'),
            selected_offer_data=offer
        )
        
        logger.info(f"✅ Set selected offer for session {session_id[:8]}...")
        return self.update_session(session)
    
    def update_stage(self, session_id: str, stage: str) -> bool:
        """تحديث المرحلة الحالية - Cache First"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        old_stage = session.current_stage
        
        # لا تحفظ إذا لم تتغير المرحلة
        if old_stage == stage:
            return True
        
        session.current_stage = stage
        logger.debug(f"📍 {old_stage} → {stage}")
        
        # 🆕 حفظ في DB فقط عند المراحل المهمة
        if stage in PerformanceConfig.PERSIST_STAGES:
            self._persist_stage_to_db(session_id, stage, old_stage)
        
        return self.update_session(session)
    
    def _persist_stage_to_db(self, session_id: str, new_stage: str, old_stage: str = None):
        """حفظ تغيير المرحلة في قاعدة البيانات"""
        if PerformanceConfig.LAZY_DB_PERSIST and new_stage not in PerformanceConfig.PERSIST_STAGES:
            return  # تخطي الحفظ
        
        try:
            from .data_persistence_service import SessionPersistenceService
            import asyncio
            import threading
            
            def _save():
                SessionPersistenceService.update_session_stage(
                    session_id=session_id,
                    new_stage=new_stage,
                    trigger_type='ai_decision'
                )
            
            try:
                asyncio.get_running_loop()
                thread = threading.Thread(target=_save)
                thread.start()
            except RuntimeError:
                _save()
        except Exception as e:
            logger.warning(f"⚠️ Failed to persist stage to DB: {e}")
    
    def increment_message_count(self, session_id: str, message: str, role: str = 'user') -> bool:
        """زيادة عداد الرسائل وحفظ الرسالة"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.message_count += 1
        session.last_message = message[:200] if message else None
        
        # حفظ الرسالة في قاعدة البيانات
        self._persist_message_to_db(session_id, role, message)
        
        return self.update_session(session)
    
    def _persist_message_to_db(self, session_id: str, role: str, content: str):
        """حفظ الرسالة في قاعدة البيانات"""
        try:
            from .data_persistence_service import SessionPersistenceService
            import asyncio
            import threading
            
            def _save():
                SessionPersistenceService.save_message(
                    session_id=session_id,
                    role=role,
                    content=content
                )
            
            try:
                asyncio.get_running_loop()
                thread = threading.Thread(target=_save)
                thread.start()
            except RuntimeError:
                _save()
        except Exception as e:
            logger.warning(f"⚠️ Failed to persist message to DB: {e}")


    # ═══════════════════════════════════════════════════════════
    # Completion & Database Persistence
    # ═══════════════════════════════════════════════════════════
    
    async def complete_session_and_persist(
        self,
        session_id: str,
        order_id: int,
        order_code: str,
        invoice_id: int,
        invoice_no: str,
        policy_id: int = None,
        policy_no: str = None
    ) -> bool:
        """
        إكمال الجلسة وحفظ البيانات في قاعدة البيانات
        
        Args:
            session_id: معرف الجلسة
            order_id: معرف الطلب
            order_code: رمز الطلب
            invoice_id: معرف الفاتورة
            invoice_no: رقم الفاتورة
            policy_id: معرف الوثيقة (اختياري)
            policy_no: رقم الوثيقة (اختياري)
        
        Returns:
            bool: نجاح العملية
        """
        session = self.get_session(session_id)
        if not session:
            logger.error(f"❌ Session not found: {session_id}")
            return False
        
        # تحديث بيانات الطلب
        session.order_id = order_id
        session.order_code = order_code
        session.invoice_id = invoice_id
        session.invoice_no = invoice_no
        
        if policy_id:
            session.policy_id = policy_id
            session.policy_no = policy_no
        
        # تحديد كمكتمل
        session.mark_completed()
        
        # حفظ في قاعدة البيانات
        try:
            await self._persist_to_database(session)
            logger.info(f"✅ Session {session_id[:8]}... completed and persisted to DB")
            
            # حذف من الكاش بعد الحفظ الناجح
            # (اختياري - يمكن الإبقاء عليها لفترة قصيرة)
            # self.delete_session(session_id)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to persist session: {e}")
            # الإبقاء على الجلسة في الكاش للمحاولة لاحقاً
            self.update_session(session)
            return False
    
    async def _persist_to_database(self, session: UserSession):
        """
        حفظ بيانات الجلسة في قاعدة البيانات
        """
        from insurance_core.models import User, Vehicle, InsuranceOrder
        from whatsapp_integration.models import WhatsAppSession
        
        @sync_to_async
        def _save():
            with transaction.atomic():
                # تحديث أو إنشاء سجل WhatsApp Session
                wa_session, created = WhatsAppSession.objects.update_or_create(
                    phone_number=session.user_identifier,
                    defaults={
                        'current_stage': session.current_stage,
                        'context_data': session.to_dict(),
                    }
                )
                
                # تحديث الطلب إذا وجد
                if session.order_id:
                    try:
                        order = InsuranceOrder.objects.get(id=session.order_id)
                        # يمكن إضافة أي تحديثات إضافية هنا
                        order.save()
                    except InsuranceOrder.DoesNotExist:
                        pass
                
                logger.info(f"💾 Persisted session data to DB for {session.user_identifier}")
        
        await _save()
    
    async def sync_session_to_db(self, session_id: str) -> bool:
        """
        مزامنة الجلسة مع قاعدة البيانات (بدون إكمال)
        مفيد للحفظ الدوري
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        try:
            await self._persist_to_database(session)
            return True
        except Exception as e:
            logger.error(f"❌ Sync failed: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════
    # Utility Methods
    # ═══════════════════════════════════════════════════════════
    
    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """
        الحصول على ملخص الجلسة
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        return {
            'session_id': session.session_id,
            'user': session.user_identifier,
            'stage': session.current_stage,
            'status': session.status.value,
            'vehicle_complete': session.vehicle.is_complete(),
            'profile_complete': session.profile.is_complete(),
            'has_offers': len(session.available_offers) > 0,
            'offer_selected': session.selected_offer is not None,
            'order_created': session.order_id is not None,
            'policy_issued': session.policy_id is not None,
            'message_count': session.message_count,
            'created_at': session.created_at,
            'updated_at': session.updated_at,
        }
    
    def get_active_sessions_count(self) -> int:
        """عدد الجلسات النشطة"""
        pattern = self._make_key(CachePrefix.SESSION, "*")
        return len(self._backend.keys(pattern))
    
    def cleanup_expired_sessions(self) -> int:
        """تنظيف الجلسات المنتهية (للـ Memory backend)"""
        if isinstance(self._backend, MemoryCacheBackend):
            self._backend._cleanup_expired()
            return 0
        return 0
    
    # ═══════════════════════════════════════════════════════════
    # 🆕 Clear Operations - للتعديل والرجوع والإلغاء
    # ═══════════════════════════════════════════════════════════
    
    def clear_session(self, session_id: str) -> bool:
        """
        مسح جلسة كاملة (للإلغاء)
        
        Args:
            session_id: معرف الجلسة
        
        Returns:
            bool: نجاح العملية
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        # إنشاء جلسة جديدة فارغة بنفس المعرف
        new_session = UserSession(
            session_id=session.session_id,
            user_identifier=session.user_identifier,
            current_stage="greeting",
            status=SessionStatus.ACTIVE
        )
        
        logger.info(f"🗑️ Cleared session {session_id[:8]}...")
        return self._save_session_to_cache(new_session)
    
    def clear_vehicle_data(self, session_id: str) -> bool:
        """
        مسح بيانات السيارة (للتعديل)
        
        Args:
            session_id: معرف الجلسة
        
        Returns:
            bool: نجاح العملية
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        # الاحتفاظ بنوع التأمين
        service_type = session.vehicle.service_type
        
        # مسح بيانات السيارة
        session.vehicle = CachedVehicleData()
        if service_type:
            session.vehicle.service_type = service_type
        
        # مسح العروض (ستتغير بتغير السيارة)
        session.available_offers = []
        session.selected_offer = None
        session.selected_offer_id = None
        
        logger.info(f"🗑️ Cleared vehicle data for session {session_id[:8]}...")
        return self.update_session(session)
    
    def clear_profile_data(self, session_id: str) -> bool:
        """
        مسح البيانات الشخصية (للتعديل)
        
        Args:
            session_id: معرف الجلسة
        
        Returns:
            bool: نجاح العملية
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        # الاحتفاظ برقم الهاتف
        phone = session.profile.phone
        
        # مسح البيانات الشخصية
        session.profile = CachedProfileData()
        if phone:
            session.profile.phone = phone
        
        logger.info(f"🗑️ Cleared profile data for session {session_id[:8]}...")
        return self.update_session(session)
    
    def clear_selected_offer(self, session_id: str) -> bool:
        """
        مسح العرض المختار (لتغيير العرض)
        
        Args:
            session_id: معرف الجلسة
        
        Returns:
            bool: نجاح العملية
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.selected_offer = None
        session.selected_offer_id = None
        
        logger.info(f"🗑️ Cleared selected offer for session {session_id[:8]}...")
        return self.update_session(session)
    
    def reset_to_stage(self, session_id: str, target_stage: str) -> bool:
        """
        إعادة الجلسة لمرحلة معينة مع مسح البيانات اللاحقة
        
        Args:
            session_id: معرف الجلسة
            target_stage: المرحلة المستهدفة
        
        Returns:
            bool: نجاح العملية
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        # تحديد ما يجب مسحه حسب المرحلة المستهدفة
        stages_order = [
            'greeting', 'service_details', 'collecting_vehicle', 'confirming_vehicle',
            'showing_offers', 'offer_details', 'collecting_profile', 'confirming_profile',
            'order_summary', 'confirmation', 'payment_pending', 'completed'
        ]
        
        try:
            target_index = stages_order.index(target_stage)
        except ValueError:
            target_index = 0
            target_stage = 'greeting'
        
        # مسح البيانات حسب المرحلة
        if target_index <= stages_order.index('collecting_vehicle'):
            # مسح كل شيء
            session.vehicle = CachedVehicleData()
            session.profile = CachedProfileData()
            session.available_offers = []
            session.selected_offer = None
            session.selected_offer_id = None
            session.order_id = None
            session.invoice_id = None
            session.policy_id = None
        
        elif target_index <= stages_order.index('showing_offers'):
            # مسح العروض وما بعدها
            session.available_offers = []
            session.selected_offer = None
            session.selected_offer_id = None
            session.profile = CachedProfileData()
            session.order_id = None
            session.invoice_id = None
            session.policy_id = None
        
        elif target_index <= stages_order.index('collecting_profile'):
            # مسح البيانات الشخصية وما بعدها
            session.profile = CachedProfileData()
            session.order_id = None
            session.invoice_id = None
            session.policy_id = None
        
        elif target_index <= stages_order.index('order_summary'):
            # مسح الطلب وما بعده
            session.order_id = None
            session.invoice_id = None
            session.policy_id = None
        
        session.current_stage = target_stage
        logger.info(f"🔄 Reset session {session_id[:8]}... to stage {target_stage}")
        return self.update_session(session)


# ═══════════════════════════════════════════════════════════════
# Factory & Singleton Access
# ═══════════════════════════════════════════════════════════════

_cache_manager: Optional[SessionCacheManager] = None


# ═══════════════════════════════════════════════════════════════
# Insurance Services & Offers Cache
# ═══════════════════════════════════════════════════════════════

class InsuranceDataCache:
    """
    كاش لبيانات التأمين (الخدمات والعروض)
    يجلب من DB ويخزن في Redis/Memory للوصول السريع
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._cache_manager = get_cache_manager()
        self._backend = self._cache_manager._backend
        self._initialized = True
        logger.info("✅ InsuranceDataCache initialized")
    
    def _make_key(self, prefix: str, identifier: str = "") -> str:
        """إنشاء مفتاح الكاش"""
        if identifier:
            return f"saia:insurance:{prefix}:{identifier}"
        return f"saia:insurance:{prefix}"
    
    # ═══════════════════════════════════════════════════════════
    # Insurance Services Cache
    # ═══════════════════════════════════════════════════════════
    
    def get_insurance_services(self) -> List[Dict]:
        """
        جلب خدمات التأمين من الكاش أو DB
        """
        cache_key = self._make_key("services", "all")
        
        # محاولة الجلب من الكاش
        cached = self._backend.get(cache_key)
        if cached:
            logger.debug("📦 Insurance services from cache")
            return json.loads(cached)
        
        # جلب من DB
        from insurance_core.models import InsuranceService
        services = list(InsuranceService.active.values(
            'id', 'service_code', 'name_ar', 'name_en', 
            'service_type', 'description'
        ))
        
        # حفظ في الكاش (TTL: ساعة)
        self._backend.set(cache_key, json.dumps(services, ensure_ascii=False), 3600)
        logger.info(f"💾 Cached {len(services)} insurance services")
        
        return services
    
    def get_service_by_type(self, service_type: str) -> Optional[Dict]:
        """
        جلب خدمة تأمين حسب النوع
        service_type: 'comprehensive' أو 'tpl'
        """
        services = self.get_insurance_services()
        
        type_mapping = {
            'comprehensive': 'AUTO_COMP',
            'tpl': 'AUTO_TPL',
            'vip': 'AUTO_VIP'
        }
        
        db_type = type_mapping.get(service_type, service_type)
        
        for service in services:
            if service.get('service_type') == db_type:
                return service
        
        return None
    
    # ═══════════════════════════════════════════════════════════
    # Insurance Offers Cache
    # ═══════════════════════════════════════════════════════════
    
    def get_offer_details(self, offer_id: int) -> Optional[Dict]:
        """
        جلب تفاصيل عرض كاملة من الكاش أو DB
        """
        cache_key = self._make_key("offer", str(offer_id))
        
        # محاولة الجلب من الكاش
        cached = self._backend.get(cache_key)
        if cached:
            logger.debug(f"📦 Offer {offer_id} from cache")
            return json.loads(cached)
        
        # جلب من DB مع العلاقات
        from insurance_core.models import InsuranceOffer
        try:
            offer = InsuranceOffer.objects.select_related(
                'company', 'service'
            ).get(id=offer_id, is_active=True)
            
            # حساب السعر
            pricing = offer.calculate_final_price(has_njm_discount=True)
            
            offer_data = {
                'id': offer.id,
                'offer_code': offer.offer_code,
                'coverage_type': offer.coverage_type,
                'coverage_type_display': offer.get_coverage_type_display(),
                
                # بيانات الشركة
                'company': {
                    'id': offer.company.id,
                    'code': offer.company.company_code,
                    'name_ar': offer.company.name_ar,
                    'name_en': offer.company.name_en,
                    'logo_url': offer.company.logo_url,
                    'rating': float(offer.company.rating_score),
                },
                
                # بيانات الخدمة
                'service': {
                    'id': offer.service.id,
                    'code': offer.service.service_code,
                    'name_ar': offer.service.name_ar,
                    'name_en': offer.service.name_en,
                    'description': offer.service.description,
                },
                
                # التسعير
                'pricing': {
                    'base_price': pricing['base_price'],
                    'discount': pricing['discount'],
                    'discount_percentage': float(offer.njm_discount_pct),
                    'price_after_discount': pricing['price_after_discount'],
                    'vat_rate': float(offer.vat_rate),
                    'vat': pricing['vat'],
                    'final_price': pricing['final_price'],
                },
                
                # المتطلبات
                'requirements': {
                    'min_age': offer.min_age,
                    'max_age': offer.max_age,
                    'min_vehicle_year': offer.min_vehicle_year,
                    'max_vehicle_value': float(offer.max_vehicle_value) if offer.max_vehicle_value else None,
                },
                
                # المزايا والإضافات
                'features': offer.included_features_json or [],
                'deductible_options': offer.deductible_options or [],
                'optional_addons': offer.optional_addons_json or [],
            }
            
            # حفظ في الكاش (TTL: 30 دقيقة)
            self._backend.set(cache_key, json.dumps(offer_data, ensure_ascii=False), 1800)
            logger.info(f"💾 Cached offer details: {offer_id}")
            
            return offer_data
            
        except InsuranceOffer.DoesNotExist:
            logger.warning(f"⚠️ Offer not found: {offer_id}")
            return None
    
    def get_offers_by_type(self, coverage_type: str, limit: int = 5) -> List[Dict]:
        """
        جلب عروض حسب نوع التغطية
        """
        cache_key = self._make_key("offers_list", coverage_type)
        
        # محاولة الجلب من الكاش
        cached = self._backend.get(cache_key)
        if cached:
            logger.debug(f"📦 Offers list ({coverage_type}) from cache")
            return json.loads(cached)
        
        # جلب من DB
        from insurance_core.models import InsuranceOffer
        offers = InsuranceOffer.objects.select_related(
            'company', 'service'
        ).filter(
            coverage_type=coverage_type,
            is_active=True
        ).order_by('price_base')[:limit]
        
        offers_list = []
        for offer in offers:
            pricing = offer.calculate_final_price(has_njm_discount=True)
            offers_list.append({
                'id': offer.id,
                'company': offer.company.name_ar,
                'company_rating': float(offer.company.rating_score),
                'coverage_type': offer.get_coverage_type_display(),
                'base_price': pricing['base_price'],
                'discount': pricing['discount'],
                'vat': pricing['vat'],
                'final_price': pricing['final_price'],
                'features': offer.included_features_json or [],
            })
        
        # حفظ في الكاش (TTL: 30 دقيقة)
        self._backend.set(cache_key, json.dumps(offers_list, ensure_ascii=False), 1800)
        logger.info(f"💾 Cached {len(offers_list)} offers ({coverage_type})")
        
        return offers_list
    
    def invalidate_offers_cache(self):
        """إبطال كاش العروض (عند تحديث البيانات)"""
        # حذف كاش قوائم العروض
        for coverage_type in ['comprehensive', 'tpl', 'vip']:
            key = self._make_key("offers_list", coverage_type)
            self._backend.delete(key)
        
        logger.info("🗑️ Offers cache invalidated")
    
    def invalidate_services_cache(self):
        """إبطال كاش الخدمات"""
        key = self._make_key("services", "all")
        self._backend.delete(key)
        logger.info("🗑️ Services cache invalidated")


# Singleton instance
_insurance_cache: Optional[InsuranceDataCache] = None


def get_insurance_cache() -> InsuranceDataCache:
    """الحصول على instance من كاش التأمين"""
    global _insurance_cache
    if _insurance_cache is None:
        _insurance_cache = InsuranceDataCache()
    return _insurance_cache


def get_cache_manager() -> SessionCacheManager:
    """الحصول على instance من مدير الكاش"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = SessionCacheManager()
    return _cache_manager


def reset_cache_manager():
    """إعادة تعيين مدير الكاش"""
    global _cache_manager
    _cache_manager = None
    logger.info("🔄 Cache manager reset")


# ═══════════════════════════════════════════════════════════════
# Async Helper Functions
# ═══════════════════════════════════════════════════════════════

async def get_or_create_user_session(user_identifier: str) -> UserSession:
    """Helper async لجلب أو إنشاء جلسة"""
    manager = get_cache_manager()
    return manager.get_or_create_session(user_identifier)


async def update_session_vehicle(session_id: str, **kwargs) -> bool:
    """Helper async لتحديث بيانات السيارة"""
    manager = get_cache_manager()
    return manager.update_vehicle_data(session_id, **kwargs)


async def update_session_profile(session_id: str, **kwargs) -> bool:
    """Helper async لتحديث بيانات العميل"""
    manager = get_cache_manager()
    return manager.update_profile_data(session_id, **kwargs)


async def complete_and_persist(
    session_id: str,
    order_id: int,
    order_code: str,
    invoice_id: int,
    invoice_no: str,
    policy_id: int = None,
    policy_no: str = None
) -> bool:
    """Helper async لإكمال الجلسة وحفظها"""
    manager = get_cache_manager()
    return await manager.complete_session_and_persist(
        session_id, order_id, order_code, invoice_id, invoice_no, policy_id, policy_no
    )
