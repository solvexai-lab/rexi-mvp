"""Tests for RAG evaluation service (ragas + deepeval).

Tests graceful degradation and mocked evaluation paths.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestEvaluationService:
    """Test EvaluationService initialization and status."""

    def test_status_returns_dict(self):
        """status() must return availability info for both libraries."""
        from app.services.evaluation_service import evaluation_service
        status = evaluation_service.status
        assert "ragas" in status
        assert "deepeval" in status
        assert "available" in status["ragas"]
        assert "available" in status["deepeval"]

    def test_available_checks_both_libraries(self):
        """available should be True if at least one library works."""
        from app.services.evaluation_service import evaluation_service
        avail = evaluation_service.available
        assert isinstance(avail, bool)


class TestEvaluateRAG:
    """Test evaluate_rag() with mocked evaluators."""

    def test_evaluate_rag_returns_warning_when_unavailable(self):
        """When no eval library works, return warning dict."""
        from app.services.evaluation_service import EvaluationService

        svc = EvaluationService()
        with patch("app.services.evaluation_service._deepeval_available", False), \
             patch("app.services.evaluation_service._ragas_available", False):
            result = svc.evaluate_rag(
                question="What is the liability cap?",
                answer="₹50Cr",
                contexts=["Clause 12.3: Liability shall not exceed ₹50Cr."],
            )

        assert "warning" in result
        assert "status" in result

    def test_evaluate_rag_with_mocked_deepeval(self):
        """Test evaluate_rag using mocked deepeval metrics."""
        from app.services.evaluation_service import EvaluationService

        svc = EvaluationService()

        mock_metric = MagicMock()
        mock_metric.score = 0.95
        mock_metric.reason = "The answer is fully supported by the context."

        with patch("app.services.evaluation_service._deepeval_available", True), \
             patch("app.services.evaluation_service._ragas_available", False), \
             patch("deepeval.metrics.FaithfulnessMetric") as MockFaith, \
             patch("deepeval.metrics.AnswerRelevancyMetric") as MockRel, \
             patch("deepeval.metrics.ContextualPrecisionMetric") as MockPrec, \
             patch("deepeval.metrics.ContextualRecallMetric") as MockRecall:

            MockFaith.return_value = mock_metric
            MockRel.return_value = mock_metric
            MockPrec.return_value = mock_metric
            MockRecall.return_value = mock_metric

            result = svc.evaluate_rag(
                question="What is the liability cap?",
                answer="₹50Cr",
                contexts=["Clause 12.3: Liability shall not exceed ₹50Cr."],
            )

        assert "deepeval_faithfulness" in result
        assert result["deepeval_faithfulness"] == 0.95
        assert "deepeval_answer_relevancy" in result

    def test_evaluate_chat_response_with_mocked_deepeval(self):
        """Test evaluate_chat_response with mocked deepeval."""
        from app.services.evaluation_service import EvaluationService

        svc = EvaluationService()

        mock_metric = MagicMock()
        mock_metric.score = 0.88
        mock_metric.reason = "Relevant to the question."

        with patch("app.services.evaluation_service._deepeval_available", True), \
             patch("deepeval.metrics.AnswerRelevancyMetric") as MockRel:

            MockRel.return_value = mock_metric
            result = svc.evaluate_chat_response(
                question="What is the liability cap?",
                answer="₹50Cr",
            )

        assert result["answer_relevancy"] == 0.88
        assert result["reason"] == "Relevant to the question."

    def test_evaluate_rag_with_mocked_ragas(self):
        """Test evaluate_rag using mocked ragas."""
        from app.services.evaluation_service import EvaluationService

        svc = EvaluationService()

        # Mock _evaluate_with_ragas directly to avoid ragas import issues
        with patch("app.services.evaluation_service._ragas_available", True), \
             patch("app.services.evaluation_service._deepeval_available", False), \
             patch.object(svc, "_evaluate_with_ragas", return_value={
                 "ragas_faithfulness": 0.92,
                 "ragas_answer_relevancy": 0.88,
             }):

            result = svc.evaluate_rag(
                question="What is the liability cap?",
                answer="₹50Cr",
                contexts=["Clause 12.3: Liability shall not exceed ₹50Cr."],
            )

        assert "ragas_faithfulness" in result
        assert result["ragas_faithfulness"] == 0.92

    def test_evaluate_rag_handles_exception_gracefully(self):
        """If evaluator throws, error is captured but not raised."""
        from app.services.evaluation_service import EvaluationService

        svc = EvaluationService()

        with patch("app.services.evaluation_service._deepeval_available", True), \
             patch("app.services.evaluation_service._ragas_available", False), \
             patch("deepeval.metrics.FaithfulnessMetric") as MockFaith, \
             patch("deepeval.metrics.AnswerRelevancyMetric") as MockRel, \
             patch("deepeval.metrics.ContextualPrecisionMetric") as MockPrec, \
             patch("deepeval.metrics.ContextualRecallMetric") as MockRecall:

            mock_metric = MagicMock()
            mock_metric.measure.side_effect = RuntimeError("API rate limit")
            MockFaith.return_value = mock_metric
            MockRel.return_value = mock_metric
            MockPrec.return_value = mock_metric
            MockRecall.return_value = mock_metric

            result = svc.evaluate_rag(
                question="What is the liability cap?",
                answer="₹50Cr",
                contexts=["Clause 12.3: Liability shall not exceed ₹50Cr."],
            )

        assert "deepeval_faithfulness_error" in result
