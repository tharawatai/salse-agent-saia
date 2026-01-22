"""
AIAssistant Base Class
متوافق مع django_ai_assistant لكن يستخدم Gemini
"""
import abc
import inspect
import re
import logging
from typing import Any, ClassVar, Dict, List, Optional, Sequence, Type
from functools import wraps

logger = logging.getLogger(__name__)


def method_tool(*args, **kwargs):
    """
    Decorator لتحويل method إلى tool يمكن للـ AI استخدامه
    مستوحى من @method_tool في django_ai_assistant
    """
    def decorator(func):
        func._is_tool = True
        func._tool_maker_args = args
        func._tool_maker_kwargs = kwargs
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        wrapper._is_tool = True
        wrapper._tool_name = kwargs.get('name', func.__name__)
        wrapper._tool_description = kwargs.get('description', func.__doc__ or '')
        return wrapper
    
    # Support both @method_tool and @method_tool()
    if len(args) == 1 and callable(args[0]):
        func = args[0]
        func._is_tool = True
        func._tool_name = func.__name__
        func._tool_description = func.__doc__ or ''
        return func
    
    return decorator


class AIAssistant(abc.ABC):
    """
    Base class for AI Assistants - متوافق مع django_ai_assistant
    يستخدم Gemini بدلاً من OpenAI/LangChain
    
    Subclasses must define:
    - id: str
    - name: str  
    - instructions: str
    - model: str
    """
    
    id: ClassVar[str]
    name: ClassVar[str]
    instructions: str
    model: str = "gemini-2.0-flash"
    temperature: float = 0.7
    
    _user: Any = None
    _request: Any = None
    _view: Any = None
    _init_kwargs: Dict[str, Any]
    _method_tools: List[Dict]
    _registry: ClassVar[Dict[str, Type["AIAssistant"]]] = {}
    
    def __init__(self, *, user=None, request=None, view=None, **kwargs):
        self._user = user
        self._request = request
        self._view = view
        self._init_kwargs = kwargs
        self._set_method_tools()
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        
        if not hasattr(cls, 'id') or cls.id is None:
            return
        
        pattern = r'^[a-zA-Z0-9_-]+$'
        if not re.match(pattern, cls.id):
            raise ValueError(f"Assistant id '{cls.id}' invalid")
        
        cls._registry[cls.id] = cls
        logger.info(f"Registered assistant: {cls.id}")
    
    def _set_method_tools(self):
        tools = []
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if getattr(method, '_is_tool', False):
                tool_info = {
                    'name': getattr(method, '_tool_name', name),
                    'description': getattr(method, '_tool_description', ''),
                    'method': method,
                }
                tools.append(tool_info)
        self._method_tools = tools
    
    @classmethod
    def get_cls_registry(cls) -> Dict[str, Type["AIAssistant"]]:
        return cls._registry
    
    @classmethod
    def get_cls(cls, assistant_id: str) -> Type["AIAssistant"]:
        if assistant_id not in cls._registry:
            raise KeyError(f"Assistant '{assistant_id}' not found")
        return cls._registry[assistant_id]
    
    @classmethod
    def clear_cls_registry(cls) -> None:
        cls._registry.clear()
    
    def get_instructions(self) -> str:
        return self.instructions
    
    def get_model(self) -> str:
        return self.model
    
    def get_temperature(self) -> float:
        return self.temperature
    
    def get_tools(self) -> List[Dict]:
        return self._method_tools
    
    @abc.abstractmethod
    async def run(self, message: str, thread_id: Any = None, **kwargs) -> Any:
        pass
    
    def run_sync(self, message: str, thread_id: Any = None, **kwargs) -> Any:
        import asyncio
        return asyncio.run(self.run(message, thread_id, **kwargs))
