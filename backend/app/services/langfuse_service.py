"""Langfuse observability integration.

Lightweight wrapper around Langfuse SDK for tracing AI calls.
Gracefully degrades to no-op when Langfuse is not configured.

Usage:
    from app.services.langfuse_service import langfuse_observer, get_langfuse

    @langfuse_observer()
    async def my_ai_function(...):
        ...

Or manual tracing:
    lf = get_langfuse()
    if lf:
        trace = lf.trace(name="custom-trace")
        generation = trace.generation(name="gemini-call", model="gemini-2.0-flash")
        generation.end(output=response_text)
"""
import os
from functools import wraps
from typing import Optional, Callable, Any

from app.core.config import get_settings

_langfuse_instance: Optional[Any] = None
_langfuse_available: Optional[bool] = None


def get_langfuse():
    """Get Langfuse client. Lazy init. Returns None if not configured."""
    global _langfuse_instance, _langfuse_available

    if _langfuse_available is False:
        return None

    if _langfuse_instance is not None:
        return _langfuse_instance

    settings = get_settings()
    if not settings.langfuse_enabled:
        _langfuse_available = False
        return None

    if not settings.langfuse_secret_key or not settings.langfuse_public_key:
        print("[Langfuse] Missing keys. Set LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY.")
        _langfuse_available = False
        return None

    try:
        from langfuse import Langfuse
        _langfuse_instance = Langfuse(
            secret_key=settings.langfuse_secret_key,
            public_key=settings.langfuse_public_key,
            host=settings.langfuse_base_url,
        )
        _langfuse_available = True
        print(f"[Langfuse] Connected to {settings.langfuse_base_url}")
        return _langfuse_instance
    except Exception as e:
        print(f"[Langfuse] Init failed: {e}")
        _langfuse_available = False
        return None


def langfuse_observer(name: Optional[str] = None, capture_input: bool = True, capture_output: bool = True):
    """Decorator that traces function execution via Langfuse.

    Works with both sync and async functions.
    If Langfuse is not configured, acts as a pass-through (zero overhead).
    """
    def decorator(func: Callable) -> Callable:
        trace_name = name or func.__name__

        if hasattr(func, "__aiter__") or hasattr(func, "__anext__"):
            # Generator/async iterator — skip decorator, manual trace recommended
            return func

        if hasattr(func, "__await__") or hasattr(func, "__wrapped__"):
            # Async function
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                lf = get_langfuse()
                if lf is None:
                    return await func(*args, **kwargs)

                import inspect
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()

                input_data = dict(bound.arguments) if capture_input else None
                # Remove session/DB objects from input (not serializable)
                if input_data:
                    input_data = {
                        k: (str(v) if not isinstance(v, (str, int, float, bool, list, dict, type(None))) else v)
                        for k, v in input_data.items()
                    }

                trace = lf.trace(name=trace_name, input=input_data)
                try:
                    result = await func(*args, **kwargs)
                    if capture_output:
                        trace.update(output=_serialize_output(result))
                    else:
                        trace.update(output={"status": "completed"})
                    return result
                except Exception as e:
                    trace.update(output={"error": str(e)}, status_message="error")
                    raise

            return async_wrapper
        else:
            # Sync function
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                lf = get_langfuse()
                if lf is None:
                    return func(*args, **kwargs)

                import inspect
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()

                input_data = dict(bound.arguments) if capture_input else None
                if input_data:
                    input_data = {
                        k: (str(v) if not isinstance(v, (str, int, float, bool, list, dict, type(None))) else v)
                        for k, v in input_data.items()
                    }

                trace = lf.trace(name=trace_name, input=input_data)
                try:
                    result = func(*args, **kwargs)
                    if capture_output:
                        trace.update(output=_serialize_output(result))
                    else:
                        trace.update(output={"status": "completed"})
                    return result
                except Exception as e:
                    trace.update(output={"error": str(e)}, status_message="error")
                    raise

            return sync_wrapper

    return decorator


def trace_generation(
    trace_name: str,
    generation_name: str,
    model: str,
    input_text: str,
    output_text: Optional[str] = None,
    metadata: Optional[dict] = None,
):
    """Manually log a generation (LLM call) to Langfuse.

    Useful for SSE streaming where decorator doesn't work.
    """
    lf = get_langfuse()
    if lf is None:
        return None

    trace = lf.trace(name=trace_name)
    generation = trace.generation(
        name=generation_name,
        model=model,
        input=input_text,
        output=output_text,
        metadata=metadata or {},
    )
    return trace, generation


def score_trace(trace_id: str, name: str, value: float, comment: Optional[str] = None):
    """Attach a score to a trace (e.g., user thumbs up/down)."""
    lf = get_langfuse()
    if lf is None:
        return
    try:
        lf.score(trace_id=trace_id, name=name, value=value, comment=comment)
    except Exception as e:
        print(f"[Langfuse] Score failed: {e}")


def _serialize_output(obj: Any) -> Any:
    """Safely serialize output for Langfuse tracing."""
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    if isinstance(obj, list):
        return [_serialize_output(i) for i in obj[:20]]  # limit list size
    if isinstance(obj, dict):
        return {k: _serialize_output(v) for k, v in list(obj.items())[:50]}
    try:
        return obj.model_dump() if hasattr(obj, "model_dump") else str(obj)
    except Exception:
        return str(obj)
