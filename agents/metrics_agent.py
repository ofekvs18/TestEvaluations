"""
Metrics Calculation Agent (Agent 1)

Calculates test metrics including difficulty, discrimination, and reliability.
"""

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd


class MetricsAgent:
    """Agent responsible for calculating test metrics."""

    def calculate_metrics(
        self,
        data: pd.DataFrame,
        weights: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive test metrics.

        Args:
            data: DataFrame with student responses
            weights: Optional DataFrame with question weights

        Returns:
            Dictionary containing test statistics and question metrics
        """
        # Assume first column is student ID, rest are question responses
        if data.empty:
            return self._empty_metrics()

        # Identify student and question columns
        student_col = data.columns[0]
        question_cols = data.columns[1:]

        # Extract scores matrix
        scores = data[question_cols].values

        # Calculate test-level statistics
        total_scores = scores.sum(axis=1)
        max_possible_score = scores.max(axis=0).sum()  # Sum of max scores per question

        test_statistics = {
            "total_students": len(data),
            "total_questions": len(question_cols),
            "mean_score": float(np.mean(total_scores)),
            "mean_score_percentage": float(np.mean(total_scores) / max_possible_score * 100) if max_possible_score > 0 else 0.0,
            "std_deviation": float(np.std(total_scores)),
            "min_score": float(np.min(total_scores)),
            "max_score": float(np.max(total_scores)),
            "median_score": float(np.median(total_scores)),
            "cronbach_alpha": self._calculate_cronbach_alpha(scores),
            "test_date": "N/A"
        }

        # Calculate question-level metrics
        question_metrics = []
        for idx, col in enumerate(question_cols):
            q_scores = scores[:, idx]

            # Difficulty (proportion correct)
            difficulty = np.mean(q_scores)

            # Discrimination (point-biserial correlation with total)
            discrimination = self._calculate_discrimination(q_scores, total_scores)

            question_metrics.append({
                "question_id": col,
                "difficulty": float(difficulty),
                "discrimination": float(discrimination),
                "variance": float(np.var(q_scores)),
                "mean": float(np.mean(q_scores))
            })

        return {
            "test_statistics": test_statistics,
            "question_metrics": question_metrics
        }

    def _calculate_cronbach_alpha(self, scores: np.ndarray) -> float:
        """Calculate Cronbach's alpha reliability coefficient."""
        n_items = scores.shape[1]
        if n_items < 2:
            return 0.0

        item_variances = np.var(scores, axis=0, ddof=1)
        total_variance = np.var(scores.sum(axis=1), ddof=1)

        if total_variance == 0:
            return 0.0

        alpha = (n_items / (n_items - 1)) * (1 - item_variances.sum() / total_variance)
        return float(alpha)

    def _calculate_discrimination(
        self,
        item_scores: np.ndarray,
        total_scores: np.ndarray
    ) -> float:
        """Calculate point-biserial correlation for discrimination."""
        if np.std(item_scores) == 0 or np.std(total_scores) == 0:
            return 0.0

        correlation = np.corrcoef(item_scores, total_scores)[0, 1]
        return float(correlation) if not np.isnan(correlation) else 0.0

    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure."""
        return {
            "test_statistics": {
                "total_students": 0,
                "total_questions": 0,
                "mean_score": 0.0,
                "std_deviation": 0.0,
                "cronbach_alpha": 0.0
            },
            "question_metrics": []
        }
