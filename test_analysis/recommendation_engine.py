"""Agent 3: Recommendation Engine.

Generates actionable recommendations and optimal weights for test questions.
Uses the WeightOptimizer to calculate recommended weights based on discrimination,
difficulty, and variance metrics.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from dataclasses import dataclass
import sys
import os

# Add parent directory to path for weight_optimizer import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from weight_optimizer import WeightOptimizer, WeightOptimizerConfig
except ImportError:
    # Fallback if weight_optimizer is not available
    WeightOptimizer = None
    WeightOptimizerConfig = None


class RecommendationEngine:
    """Recommendation engine for test analysis.

    Uses weight optimization to generate actionable recommendations for each
    test question and overall test improvement insights.
    """

    def __init__(self,
                 scores_df: pd.DataFrame,
                 metrics_results: Dict[str, Any],
                 current_weights: Optional[Dict[str, float]] = None,
                 config: Optional[Dict[str, Any]] = None):
        """Initialize the recommendation engine.

        Args:
            scores_df: DataFrame with student scores.
            metrics_results: Results from MetricsCalculator containing
                           'question_metrics' and 'test_statistics'.
            current_weights: Optional current weights per question.
            config: Optional configuration parameters including:
                   - alpha: Weight for discrimination (default 0.5)
                   - beta: Weight for difficulty penalty (default 0.3)
                   - gamma: Weight for variance factor (default 0.2)
                   - optimal_difficulty: Center of Gaussian curve (default 0.55)
                   - difficulty_sigma: Spread of Gaussian curve (default 0.15)
        """
        self.scores_df = scores_df.copy()
        self.metrics_results = metrics_results
        self.current_weights = current_weights or {}
        self.config = config or {}

        # Initialize weight optimizer if available
        if WeightOptimizer is not None:
            optimizer_config = WeightOptimizerConfig(
                alpha=self.config.get('alpha', 0.5),
                beta=self.config.get('beta', 0.3),
                gamma=self.config.get('gamma', 0.2),
                optimal_difficulty=self.config.get('optimal_difficulty', 0.55),
                difficulty_sigma=self.config.get('difficulty_sigma', 0.15)
            )
            self.optimizer = WeightOptimizer(optimizer_config)
        else:
            self.optimizer = None

    def run(self) -> Dict[str, Any]:
        """Run all recommendation analyses.

        Returns:
            Dictionary containing:
            - status: 'success' or 'error'
            - recommended_weights: Dict of question_id to weight
            - weight_changes: DataFrame comparing current vs recommended
            - question_recommendations: DataFrame with per-question actions
            - test_recommendations: List of overall test insights
            - priority_items: DataFrame of top 5 urgent issues
            - excel_sheets: Dict of formatted DataFrames for Excel export
        """
        if self.optimizer is None:
            return {
                'status': 'error',
                'message': 'WeightOptimizer not available. Please ensure weight_optimizer.py is in the project root.',
                'recommendations': []
            }

        try:
            # Prepare question metrics DataFrame for the optimizer
            question_metrics = self._prepare_question_metrics()

            # Get test statistics
            test_statistics = self.metrics_results.get('test_statistics', {})

            # Run the optimizer
            optimization_results = self.optimizer.optimize(
                question_metrics=question_metrics,
                test_statistics=test_statistics,
                current_weights=self.current_weights if self.current_weights else None
            )

            # Add status and return
            return {
                'status': 'success',
                **optimization_results
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error during recommendation generation: {str(e)}',
                'recommendations': []
            }

    def _prepare_question_metrics(self) -> pd.DataFrame:
        """Prepare question metrics DataFrame for the optimizer.

        Transforms MetricsCalculator output into the format expected by WeightOptimizer.

        Returns:
            DataFrame with columns: question_id, difficulty, discrimination, std_dev,
                                   upper_group_correct, lower_group_correct
        """
        # Get the question metrics from metrics_results
        metrics_df = self.metrics_results.get('question_metrics', pd.DataFrame())

        if metrics_df.empty:
            raise ValueError("No question metrics available from MetricsCalculator")

        # Map column names from MetricsCalculator to WeightOptimizer format
        # The MetricsCalculator uses these column names:
        # - 'question': question identifier
        # - 'difficulty_index': proportion correct
        # - 'discrimination_index': discrimination value
        # - Also computes standard deviation per question

        prepared_df = pd.DataFrame()

        # Map question_id
        if 'question' in metrics_df.columns:
            prepared_df['question_id'] = metrics_df['question']
        else:
            prepared_df['question_id'] = metrics_df.index

        # Map difficulty (proportion correct, 0-1)
        if 'difficulty_index' in metrics_df.columns:
            prepared_df['difficulty'] = metrics_df['difficulty_index']
        elif 'difficulty' in metrics_df.columns:
            prepared_df['difficulty'] = metrics_df['difficulty']
        else:
            # Calculate from scores if not available
            prepared_df['difficulty'] = self._calculate_difficulty()

        # Map discrimination
        if 'discrimination_index' in metrics_df.columns:
            prepared_df['discrimination'] = metrics_df['discrimination_index']
        elif 'discrimination' in metrics_df.columns:
            prepared_df['discrimination'] = metrics_df['discrimination']
        else:
            prepared_df['discrimination'] = 0.0

        # Map or calculate standard deviation
        if 'std_dev' in metrics_df.columns:
            prepared_df['std_dev'] = metrics_df['std_dev']
        else:
            # Calculate std dev per question from scores
            prepared_df['std_dev'] = self._calculate_std_dev()

        # Map upper and lower group correct proportions
        if 'upper_group_mean' in metrics_df.columns:
            # Convert mean to proportion if scores are normalized 0-1
            prepared_df['upper_group_correct'] = metrics_df['upper_group_mean']
        else:
            prepared_df['upper_group_correct'] = prepared_df['difficulty'] + (prepared_df['discrimination'] / 2)

        if 'lower_group_mean' in metrics_df.columns:
            prepared_df['lower_group_correct'] = metrics_df['lower_group_mean']
        else:
            prepared_df['lower_group_correct'] = prepared_df['difficulty'] - (prepared_df['discrimination'] / 2)

        # Ensure values are in valid ranges
        prepared_df['upper_group_correct'] = prepared_df['upper_group_correct'].clip(0, 1)
        prepared_df['lower_group_correct'] = prepared_df['lower_group_correct'].clip(0, 1)

        return prepared_df

    def _calculate_difficulty(self) -> pd.Series:
        """Calculate difficulty index for each question from scores.

        Returns:
            Series of difficulty values (proportion correct, 0-1)
        """
        # Get question columns (all except the first which is student ID)
        question_cols = self.scores_df.columns[1:].tolist()

        difficulties = []
        for col in question_cols:
            # Assume max score per question is the maximum observed value
            max_score = self.scores_df[col].max()
            if max_score > 0:
                # Difficulty = mean score / max score
                difficulty = self.scores_df[col].mean() / max_score
            else:
                difficulty = 0.0
            difficulties.append(difficulty)

        return pd.Series(difficulties)

    def _calculate_std_dev(self) -> pd.Series:
        """Calculate standard deviation for each question from scores.

        Returns:
            Series of standard deviation values, normalized to 0-0.5 scale
        """
        question_cols = self.scores_df.columns[1:].tolist()

        std_devs = []
        for col in question_cols:
            max_score = self.scores_df[col].max()
            if max_score > 0:
                # Normalize scores to 0-1 scale, then calculate std dev
                normalized = self.scores_df[col] / max_score
                std_dev = normalized.std()
            else:
                std_dev = 0.0
            std_devs.append(std_dev)

        return pd.Series(std_devs)

    def get_summary(self) -> str:
        """Generate a text summary of recommendations.

        Returns:
            Formatted string with key recommendations.
        """
        results = self.run()

        if results['status'] != 'success':
            return f"Recommendation generation failed: {results.get('message', 'Unknown error')}"

        lines = []
        lines.append("=" * 60)
        lines.append("RECOMMENDATION SUMMARY")
        lines.append("=" * 60)

        # Test-level recommendations
        lines.append("\nTEST-LEVEL INSIGHTS:")
        lines.append("-" * 40)
        for i, rec in enumerate(results.get('test_recommendations', []), 1):
            lines.append(f"{i}. {rec}")

        # Priority items
        priority_df = results.get('priority_items', pd.DataFrame())
        if not priority_df.empty:
            lines.append("\nPRIORITY ITEMS (Top 5):")
            lines.append("-" * 40)
            for idx, row in priority_df.iterrows():
                lines.append(f"\n[{row['priority_level']}] {row['question_id']}")
                lines.append(f"  Issue: {row['issue_description']}")
                lines.append(f"  Action: {row['recommended_action']}")

        # Weight changes summary
        weight_changes = results.get('weight_changes', pd.DataFrame())
        if not weight_changes.empty:
            increases = (weight_changes['change_direction'] == 'increase').sum()
            decreases = (weight_changes['change_direction'] == 'decrease').sum()
            stable = (weight_changes['change_direction'] == 'stable').sum()

            lines.append("\nWEIGHT ADJUSTMENT SUMMARY:")
            lines.append("-" * 40)
            lines.append(f"  Increase weight: {increases} questions")
            lines.append(f"  Decrease weight: {decreases} questions")
            lines.append(f"  Keep stable: {stable} questions")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)

    def save_to_excel(self, results: Dict[str, Any], output_path: str) -> None:
        """Save recommendation results to Excel file.

        Args:
            results: Output from run() method
            output_path: Path for the output Excel file
        """
        if self.optimizer is not None:
            self.optimizer.save_to_excel(results, output_path)
        else:
            # Fallback if optimizer not available
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                if 'weight_changes' in results:
                    results['weight_changes'].to_excel(
                        writer, sheet_name='Weight Changes', index=False
                    )
                if 'question_recommendations' in results:
                    results['question_recommendations'].to_excel(
                        writer, sheet_name='Recommendations', index=False
                    )
