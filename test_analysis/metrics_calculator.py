"""Agent 1: Statistical Metrics Calculator.

Calculates all question-level and test-level statistics for student performance data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple


class MetricsCalculator:
    """Statistical metrics calculator for test analysis.

    Calculates difficulty indices, discrimination indices, item-total correlations,
    and other psychometric measures for educational test items.
    """

    def __init__(self,
                 scores_df: pd.DataFrame,
                 max_points: Optional[Dict[str, float]] = None,
                 config: Optional[Dict[str, Any]] = None):
        """Initialize the metrics calculator.

        Args:
            scores_df: DataFrame with students as rows, questions as columns.
            max_points: Optional dictionary of max points per question.
            config: Optional configuration parameters.
        """
        self.scores_df = scores_df.copy()
        self.max_points = max_points or scores_df.max().to_dict()
        self.config = config or {}

        # Default configuration
        self.difficulty_threshold_low = self.config.get('difficulty_threshold_low', 0.3)
        self.difficulty_threshold_high = self.config.get('difficulty_threshold_high', 0.8)
        self.discrimination_good = self.config.get('discrimination_good', 0.3)
        self.discrimination_review = self.config.get('discrimination_review', 0.15)
        self.upper_lower_percent = self.config.get('upper_lower_percent', 0.27)
        self.predictive_threshold = self.config.get('predictive_threshold', 0.7)
        self.curve_deviation_threshold = self.config.get('curve_deviation_threshold', 0.15)

        # Calculate total scores once
        self.total_scores = self.scores_df.sum(axis=1)

        # Calculate upper and lower groups
        self.upper_group, self.lower_group = self._calculate_upper_lower_groups()

    def _calculate_upper_lower_groups(self) -> Tuple[pd.Index, pd.Index]:
        """Calculate upper and lower 27% groups based on total scores.

        Returns:
            Tuple of (upper_group_indices, lower_group_indices).
        """
        n = len(self.scores_df)
        n_group = max(1, int(n * self.upper_lower_percent))

        sorted_indices = self.total_scores.sort_values(ascending=False).index
        upper_group = sorted_indices[:n_group]
        lower_group = sorted_indices[-n_group:]

        return upper_group, lower_group

    def calculate_difficulty_index(self, question: str) -> float:
        """Calculate difficulty index for a question.

        Difficulty = Mean score / Max points
        Range: 0 (hardest) to 1 (easiest)

        Args:
            question: Column name of the question.

        Returns:
            Difficulty index (0-1).
        """
        mean_score = self.scores_df[question].mean()
        max_score = self.max_points.get(question, self.scores_df[question].max())

        if max_score == 0:
            return 0.0

        return mean_score / max_score

    def calculate_discrimination_index(self, question: str) -> float:
        """Calculate discrimination index using upper/lower 27% method.

        Discrimination = (upper_mean - lower_mean) / max_points
        Range: -1 to 1 (higher is better)

        Args:
            question: Column name of the question.

        Returns:
            Discrimination index.
        """
        upper_mean = self.scores_df.loc[self.upper_group, question].mean()
        lower_mean = self.scores_df.loc[self.lower_group, question].mean()
        max_score = self.max_points.get(question, self.scores_df[question].max())

        if max_score == 0:
            return 0.0

        return (upper_mean - lower_mean) / max_score

    def calculate_item_total_correlation(self, question: str) -> float:
        """Calculate point-biserial correlation between item and total score.

        Uses corrected item-total correlation (excludes the item from total).

        Args:
            question: Column name of the question.

        Returns:
            Correlation coefficient (-1 to 1).
        """
        # Calculate total score excluding this question
        total_minus_item = self.total_scores - self.scores_df[question]

        # Calculate correlation
        correlation = self.scores_df[question].corr(total_minus_item)

        return correlation if not np.isnan(correlation) else 0.0

    def calculate_predictive_power(self, question: str) -> Dict[str, float]:
        """Calculate predictive power of question performance on total score.

        Compares average total score of students scoring ≥70% vs <70% on question.

        Args:
            question: Column name of the question.

        Returns:
            Dictionary with high_score_mean, low_score_mean, and difference.
        """
        max_score = self.max_points.get(question, self.scores_df[question].max())
        threshold = max_score * self.predictive_threshold

        high_performers = self.scores_df[question] >= threshold
        low_performers = ~high_performers

        high_mean = self.total_scores[high_performers].mean() if high_performers.any() else 0
        low_mean = self.total_scores[low_performers].mean() if low_performers.any() else 0

        return {
            'high_score_mean': float(high_mean) if not np.isnan(high_mean) else 0.0,
            'low_score_mean': float(low_mean) if not np.isnan(low_mean) else 0.0,
            'difference': float(high_mean - low_mean) if not (np.isnan(high_mean) or np.isnan(low_mean)) else 0.0
        }

    def classify_question_quality(self,
                                   difficulty: float,
                                   discrimination: float) -> str:
        """Classify question quality based on metrics.

        Args:
            difficulty: Difficulty index (0-1).
            discrimination: Discrimination index.

        Returns:
            Quality flag: "Good", "Review", or "Poor".
        """
        # Check for poor discrimination
        if discrimination < self.discrimination_review or discrimination < 0:
            return "Poor"

        # Check for good question
        if (discrimination > self.discrimination_good and
            self.difficulty_threshold_low < difficulty < self.difficulty_threshold_high):
            return "Good"

        # Check for extreme difficulty
        if difficulty <= self.difficulty_threshold_low or difficulty >= self.difficulty_threshold_high:
            return "Review"

        # Medium discrimination range
        if self.discrimination_review <= discrimination <= self.discrimination_good:
            return "Review"

        return "Review"

    def calculate_all_question_metrics(self) -> pd.DataFrame:
        """Calculate all metrics for all questions.

        Returns:
            DataFrame with all metrics per question.
        """
        metrics = []

        for question in self.scores_df.columns:
            difficulty = self.calculate_difficulty_index(question)
            discrimination = self.calculate_discrimination_index(question)
            std_dev = self.scores_df[question].std()
            item_total_corr = self.calculate_item_total_correlation(question)
            predictive = self.calculate_predictive_power(question)
            quality_flag = self.classify_question_quality(difficulty, discrimination)

            metrics.append({
                'question': question,
                'max_points': self.max_points.get(question, self.scores_df[question].max()),
                'mean_score': self.scores_df[question].mean(),
                'std_dev': std_dev,
                'difficulty_index': difficulty,
                'discrimination_index': discrimination,
                'item_total_correlation': item_total_corr,
                'predictive_high_mean': predictive['high_score_mean'],
                'predictive_low_mean': predictive['low_score_mean'],
                'predictive_difference': predictive['difference'],
                'quality_flag': quality_flag
            })

        return pd.DataFrame(metrics)

    def analyze_difficulty_curve(self) -> Tuple[List[str], List[str]]:
        """Analyze difficulty curve and identify questions breaking the curve.

        Returns:
            Tuple of (sorted_questions, curve_breakers).
        """
        # Calculate difficulty for all questions
        difficulties = {q: self.calculate_difficulty_index(q)
                       for q in self.scores_df.columns}

        # Sort questions by difficulty (hardest to easiest)
        sorted_questions = sorted(difficulties.keys(), key=lambda x: difficulties[x])

        # Calculate expected linear progression
        n = len(sorted_questions)
        curve_breakers = []

        for i, question in enumerate(sorted_questions):
            # Expected difficulty at this position (linear progression)
            expected_difficulty = (i + 1) / (n + 1)
            actual_difficulty = difficulties[question]

            # Check if deviation exceeds threshold
            if abs(actual_difficulty - expected_difficulty) > self.curve_deviation_threshold:
                curve_breakers.append(question)

        return sorted_questions, curve_breakers

    def calculate_cronbachs_alpha(self) -> float:
        """Calculate Cronbach's alpha for test reliability.

        Returns:
            Cronbach's alpha coefficient (0-1).
        """
        n_items = len(self.scores_df.columns)
        if n_items < 2:
            return 0.0

        # Variance of each item
        item_variances = self.scores_df.var(axis=0).sum()

        # Variance of total scores
        total_variance = self.total_scores.var()

        if total_variance == 0:
            return 0.0

        alpha = (n_items / (n_items - 1)) * (1 - item_variances / total_variance)

        return float(alpha)

    def calculate_test_statistics(self) -> Dict[str, Any]:
        """Calculate overall test-level statistics.

        Returns:
            Dictionary of test statistics.
        """
        return {
            'student_count': len(self.scores_df),
            'question_count': len(self.scores_df.columns),
            'mean_total_score': float(self.total_scores.mean()),
            'std_total_score': float(self.total_scores.std()),
            'min_total_score': float(self.total_scores.min()),
            'max_total_score': float(self.total_scores.max()),
            'median_total_score': float(self.total_scores.median()),
            'cronbachs_alpha': self.calculate_cronbachs_alpha(),
            'upper_group_cutoff': float(self.total_scores.loc[self.upper_group].min()),
            'lower_group_cutoff': float(self.total_scores.loc[self.lower_group].max()),
            'skewness': float(self.total_scores.skew()),
            'kurtosis': float(self.total_scores.kurtosis())
        }

    def run(self) -> Dict[str, Any]:
        """Run all metric calculations and return comprehensive results.

        Returns:
            Dictionary with all calculated metrics and analyses.
        """
        question_metrics = self.calculate_all_question_metrics()
        difficulty_order, curve_breakers = self.analyze_difficulty_curve()
        test_statistics = self.calculate_test_statistics()

        # Extract quality flags
        quality_flags = question_metrics[['question', 'quality_flag']].copy()

        return {
            'question_metrics': question_metrics,
            'quality_flags': quality_flags,
            'difficulty_order': difficulty_order,
            'curve_breakers': curve_breakers,
            'test_statistics': test_statistics,
            'upper_lower_groups': {
                'upper_group': self.upper_group.tolist(),
                'lower_group': self.lower_group.tolist()
            }
        }
