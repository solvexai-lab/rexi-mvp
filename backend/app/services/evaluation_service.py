"""RAG evaluation service — wraps ragas and deepeval.

Provides unified evaluation metrics for REXI's AI features:
  - Faithfulness: Is the answer grounded in retrieved context?
  - Answer Relevancy: Does the answer address the question?
  - Context Precision: Is retrieved context relevant?
  - Context Recall: Was all necessary info retrieved?

Graceful degradation: If ragas/deepeval are unavailable or unconfigured,
returns empty scores with a warning. No eval calls = no API cost.
"""
import os
from typing import Dict, List, Optional

# Lazy imports — these modules make API calls only when evaluate() is called
_ragas_available: Optional[bool] = None
_deepeval_available: Optional[bool] = None
_ragas_error: Optional[str] = None
_deepeval_error: Optional[str] = None


def _check_ragas():
    global _ragas_available, _ragas_error
    if _ragas_available is not None:
        return
    try:
        import ragas
        from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
        _ragas_available = True
    except Exception as e:
        _ragas_error = str(e)
        _ragas_available = False


def _check_deepeval():
    global _deepeval_available, _deepeval_error
    if _deepeval_available is not None:
        return
    try:
        import deepeval
        from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric, ContextualPrecisionMetric, ContextualRecallMetric
        _deepeval_available = True
    except Exception as e:
        _deepeval_error = str(e)
        _deepeval_available = False


class EvaluationService:
    """Evaluate RAG pipeline quality.

    Usage:
        from app.services.evaluation_service import evaluation_service

        scores = await evaluation_service.evaluate_rag(
            question="What is the liability cap?",
            answer="The liability cap is ₹50Cr.",
            contexts=["Clause 12.3: Liability shall not exceed ₹50Cr."],
        )
        # scores = {"faithfulness": 0.95, "answer_relevancy": 0.88, ...}
    """

    def __init__(self):
        self._gemini_key = os.getenv("GEMINI_API_KEY", "")
        self._openai_key = os.getenv("OPENAI_API_KEY", "")

    @property
    def available(self) -> bool:
        _check_ragas()
        _check_deepeval()
        return bool(_ragas_available or _deepeval_available)

    @property
    def status(self) -> Dict:
        _check_ragas()
        _check_deepeval()
        return {
            "ragas": {"available": _ragas_available, "error": _ragas_error},
            "deepeval": {"available": _deepeval_available, "error": _deepeval_error},
            "evaluator_api": "gemini" if self._gemini_key else ("openai" if self._openai_key else "none"),
        }

    def evaluate_rag(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None,
    ) -> Dict:
        """Run RAG evaluation metrics.

        Returns scores 0.0-1.0 for each metric.
        If no evaluator is available, returns empty dict with warning.
        """
        if not self.available:
            return {
                "warning": "No evaluation library available. Install ragas/deepeval and set GEMINI_API_KEY.",
                "status": self.status,
            }

        result = {"question": question, "answer": answer}

        # Try deepeval first (usually lighter dependency chain)
        if _deepeval_available:
            try:
                result.update(self._evaluate_with_deepeval(question, answer, contexts, ground_truth))
            except Exception as e:
                result["deepeval_error"] = str(e)

        # Try ragas as secondary
        if _ragas_available:
            try:
                result.update(self._evaluate_with_ragas(question, answer, contexts, ground_truth))
            except Exception as e:
                result["ragas_error"] = str(e)

        return result

    def _evaluate_with_deepeval(
        self, question: str, answer: str, contexts: List[str], ground_truth: Optional[str] = None
    ) -> Dict:
        from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric, ContextualPrecisionMetric, ContextualRecallMetric
        from deepeval.test_case import LLMTestCase

        test_case = LLMTestCase(
            input=question,
            actual_output=answer,
            retrieval_context=contexts,
            expected_output=ground_truth or "",
        )

        scores = {}
        metrics = [
            ("faithfulness", FaithfulnessMetric(threshold=0.5)),
            ("answer_relevancy", AnswerRelevancyMetric(threshold=0.5)),
            ("context_precision", ContextualPrecisionMetric(threshold=0.5)),
            ("context_recall", ContextualRecallMetric(threshold=0.5)),
        ]

        for name, metric in metrics:
            try:
                metric.measure(test_case)
                scores[f"deepeval_{name}"] = round(metric.score, 4)
                scores[f"deepeval_{name}_reason"] = metric.reason
            except Exception as e:
                scores[f"deepeval_{name}_error"] = str(e)

        return scores

    def _evaluate_with_ragas(
        self, question: str, answer: str, contexts: List[str], ground_truth: Optional[str] = None
    ) -> Dict:
        from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
        from ragas import evaluate
        from datasets import Dataset

        data = {
            "question": [question],
            "answer": [answer],
            "contexts": [contexts],
        }
        if ground_truth:
            data["ground_truth"] = [ground_truth]

        dataset = Dataset.from_dict(data)
        metrics = [faithfulness, answer_relevancy, context_precision, context_recall]

        result = evaluate(dataset=dataset, metrics=metrics)
        scores = {}
        for metric_name in result.keys():
            val = result[metric_name][0]
            scores[f"ragas_{metric_name}"] = round(float(val), 4) if val is not None else None

        return scores

    def evaluate_chat_response(
        self,
        question: str,
        answer: str,
        contract_id: Optional[str] = None,
    ) -> Dict:
        """Quick evaluation for chat responses (no retrieval context needed)."""
        if not self.available:
            return {"warning": "Evaluation unavailable"}

        scores = {}

        if _deepeval_available:
            from deepeval.metrics import AnswerRelevancyMetric
            from deepeval.test_case import LLMTestCase

            test_case = LLMTestCase(input=question, actual_output=answer)
            metric = AnswerRelevancyMetric(threshold=0.5)
            try:
                metric.measure(test_case)
                scores["answer_relevancy"] = round(metric.score, 4)
                scores["reason"] = metric.reason
            except Exception as e:
                scores["error"] = str(e)

        return scores


evaluation_service = EvaluationService()
