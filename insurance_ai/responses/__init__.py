"""
Responses Module - توليد الردود
يحتوي على:
- OffersResponses: ردود العروض
- ProfileResponses: ردود البيانات الشخصية
- PolicyResponses: ردود الوثائق
- ServicesResponses: ردود الخدمات
"""
from .offers_responses import OffersResponses
from .profile_responses import ProfileResponses
from .policy_responses import PolicyResponses
from .services_responses import ServicesResponses

__all__ = [
    'OffersResponses',
    'ProfileResponses',
    'PolicyResponses',
    'ServicesResponses',
]
