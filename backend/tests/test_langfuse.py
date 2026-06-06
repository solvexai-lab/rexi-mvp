"""Tests for Langfuse integration.

Tests graceful degradation (no-op when disabled) and
active tracing (when enabled + mocked).
"""
import pytest
from unittest.mock import MagicMock, patch


class TestLangfuseService:
    """Test Langfuse service initialization."""

    def test_get_langfuse_returns_none_when_disabled(self):
        """When LANGFUSE_ENABLED=false, get_langfuse() returns None."""
        from app.services.langfuse_service import get_langfuse
        # Default from .env is disabled
        lf = get_langfuse()
        assert lf is None

    def test_get_langfuse_returns_none_when_keys_missing(self):
        """When keys are missing, get_langfuse() returns None."""
        from app.services.langfuse_service import get_langfuse
        with patch("app.services.langfuse_service._langfuse_instance", None), \
             patch("app.services.langfuse_service._langfuse_available", None):
            with patch("app.core.config.get_settings") as mock_settings:
                mock_settings.return_value = MagicMock(
                    langfuse_enabled=True,
                    langfuse_secret_key="",
                    langfuse_public_key="",
                    langfuse_base_url="https://cloud.langfuse.com",
                )
                lf = get_langfuse()
                assert lf is None

    def test_get_langfuse_initializes_when_configured(self):
        """When configured, get_langfuse() returns a Langfuse client."""
        from app.services.langfuse_service import get_langfuse
        mock_client = MagicMock()
        with patch("app.services.langfuse_service._langfuse_instance", mock_client), \
             patch("app.services.langfuse_service._langfuse_available", True):
            lf = get_langfuse()
            assert lf is not None
            assert lf is mock_client


class TestLangfuseObserver:
    """Test @langfuse_observer() decorator."""

    def test_decorator_passes_through_when_disabled(self):
        """When langfuse is disabled, decorator is a no-op pass-through."""
        from app.services.langfuse_service import langfuse_observer

        @langfuse_observer(name="test.trace")
        async def async_func(x: int):
            return x * 2

        import asyncio
        result = asyncio.run(async_func(5))
        assert result == 10

    def test_decorator_passes_through_for_sync_when_disabled(self):
        """Sync functions also pass through when disabled."""
        from app.services.langfuse_service import langfuse_observer

        @langfuse_observer(name="test.sync")
        def sync_func(x: int):
            return x + 1

        assert sync_func(5) == 6

    def test_decorator_traces_when_enabled(self):
        """When enabled and mocked, decorator creates traces."""
        from app.services.langfuse_service import langfuse_observer

        mock_lf = MagicMock()
        mock_trace = MagicMock()
        mock_lf.trace.return_value = mock_trace

        with patch("app.services.langfuse_service.get_langfuse", return_value=mock_lf):
            @langfuse_observer(name="test.traced")
            async def async_traced(x: int):
                return x * 3

            import asyncio
            result = asyncio.run(async_traced(7))

        assert result == 21
        mock_lf.trace.assert_called_once()
        mock_trace.update.assert_called_once()

    def test_decorator_captures_error(self):
        """When function raises, trace gets error status."""
        from app.services.langfuse_service import langfuse_observer

        mock_lf = MagicMock()
        mock_trace = MagicMock()
        mock_lf.trace.return_value = mock_trace

        with patch("app.services.langfuse_service.get_langfuse", return_value=mock_lf):
            @langfuse_observer(name="test.error")
            async def async_error():
                raise ValueError("boom")

            import asyncio
            with pytest.raises(ValueError):
                asyncio.run(async_error())

        mock_trace.update.assert_called_once()
        args = mock_trace.update.call_args[1]
        assert "error" in args.get("output", {})


class TestTraceGeneration:
    """Test manual trace_generation helper."""

    def test_trace_generation_when_disabled(self):
        """When disabled, returns None."""
        from app.services.langfuse_service import trace_generation
        result = trace_generation("trace", "gen", "gemini", "hello")
        assert result is None

    def test_trace_generation_when_enabled(self):
        """When enabled, creates trace and generation."""
        from app.services.langfuse_service import trace_generation

        mock_lf = MagicMock()
        mock_trace = MagicMock()
        mock_generation = MagicMock()
        mock_lf.trace.return_value = mock_trace
        mock_trace.generation.return_value = mock_generation

        with patch("app.services.langfuse_service.get_langfuse", return_value=mock_lf):
            trace, gen = trace_generation(
                trace_name="my-trace",
                generation_name="gemini-call",
                model="gemini-2.0-flash",
                input_text="question",
                output_text="answer",
                metadata={"contract_id": "c1"},
            )

        mock_lf.trace.assert_called_once_with(name="my-trace")
        mock_trace.generation.assert_called_once()


class TestScoreTrace:
    """Test score_trace helper."""

    def test_score_trace_when_disabled(self):
        """When disabled, does nothing."""
        from app.services.langfuse_service import score_trace
        score_trace("trace-123", "user_feedback", 1.0, "Good answer")

    def test_score_trace_when_enabled(self):
        """When enabled, calls langfuse.score."""
        from app.services.langfuse_service import score_trace

        mock_lf = MagicMock()
        with patch("app.services.langfuse_service.get_langfuse", return_value=mock_lf):
            score_trace("trace-123", "user_feedback", 1.0, "Good answer")
            mock_lf.score.assert_called_once_with(
                trace_id="trace-123", name="user_feedback", value=1.0, comment="Good answer"
            )
