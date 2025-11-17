"""
Weight Optimization Specialist for Test Evaluations.

This module calculates recommended weights for test questions based on metrics
and generates actionable insights for test improvement.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class WeightOptimizerConfig:
    """Configuration parameters for weight optimization."""
    alpha: float = 0.5  # Weight for discrimination index
    beta: float = 0.3   # Weight for difficulty penalty
    gamma: float = 0.2  # Weight for variance factor
    optimal_difficulty: float = 0.55  # Center of Gaussian curve
    difficulty_sigma: float = 0.15    # Spread of Gaussian curve


class WeightOptimizer:
    """
    Recommendation and weight optimization specialist.

    Receives metrics and generates actionable insights and optimal weights.
    """

    def __init__(self, config: Optional[WeightOptimizerConfig] = None):
        """Initialize the optimizer with configuration."""
        self.config = config or WeightOptimizerConfig()

    def optimize(
        self,
        question_metrics: pd.DataFrame,
        test_statistics: Dict[str, Any],
        current_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Main optimization function that generates all recommendations.

        Args:
            question_metrics: DataFrame with columns including:
                - question_id
                - difficulty (0-1 scale, proportion correct)
                - discrimination (discrimination index, 0-1)
                - std_dev (standard deviation of responses)
                - upper_group_correct (proportion in upper 27%)
                - lower_group_correct (proportion in lower 27%)
            test_statistics: Dictionary containing test-level metrics
            current_weights: Optional dict of current question weights

        Returns:
            Dictionary containing all optimization results and recommendations.
        """
        # Calculate recommended weights
        recommended_weights = self._calculate_recommended_weights(question_metrics)

        # Generate weight changes comparison
        weight_changes = self._generate_weight_changes(
            question_metrics, recommended_weights, current_weights
        )

        # Generate question-level recommendations
        question_recommendations = self._generate_question_recommendations(
            question_metrics, recommended_weights, current_weights
        )

        # Generate test-level recommendations
        test_recommendations = self._generate_test_recommendations(
            question_metrics, test_statistics
        )

        # Identify priority items
        priority_items = self._identify_priority_items(
            question_metrics, question_recommendations, current_weights
        )

        # Create Excel sheets
        excel_sheets = self._create_excel_sheets(
            question_metrics,
            recommended_weights,
            question_recommendations,
            test_recommendations
        )

        return {
            'recommended_weights': recommended_weights,
            'weight_changes': weight_changes,
            'question_recommendations': question_recommendations,
            'test_recommendations': test_recommendations,
            'priority_items': priority_items,
            'excel_sheets': excel_sheets
        }

    def _calculate_recommended_weights(
        self,
        question_metrics: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calculate recommended weights using the optimization formula.

        Formula:
        Recommended_Weight = (Discrimination_Index * α) +
                            (Difficulty_Penalty * β) +
                            (Variance_Factor * γ)
        """
        weights = {}

        for idx, row in question_metrics.iterrows():
            question_id = row['question_id']

            # Component 1: Discrimination Index (0-1)
            discrimination_component = max(0, row['discrimination']) * self.config.alpha

            # Component 2: Difficulty Penalty (Gaussian curve centered at optimal)
            difficulty = row['difficulty']
            difficulty_penalty = np.exp(
                -((difficulty - self.config.optimal_difficulty) ** 2) /
                (2 * self.config.difficulty_sigma ** 2)
            )
            difficulty_component = difficulty_penalty * self.config.beta

            # Component 3: Variance Factor (normalized by max possible std dev)
            # Max std dev for binary outcome = 0.5 (when p=0.5)
            max_std_dev = 0.5
            std_dev = row.get('std_dev', 0.5)
            variance_factor = std_dev / max_std_dev
            variance_component = variance_factor * self.config.gamma

            # Calculate raw weight
            raw_weight = discrimination_component + difficulty_component + variance_component
            weights[question_id] = raw_weight

        # Normalize weights to sum to 100%
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {
                qid: (w / total_weight) * 100
                for qid, w in weights.items()
            }

        return weights

    def _generate_weight_changes(
        self,
        question_metrics: pd.DataFrame,
        recommended_weights: Dict[str, float],
        current_weights: Optional[Dict[str, float]]
    ) -> pd.DataFrame:
        """Generate comparison between current and recommended weights."""
        data = []

        for idx, row in question_metrics.iterrows():
            question_id = row['question_id']
            recommended = recommended_weights.get(question_id, 0)

            if current_weights:
                current = current_weights.get(question_id, 0)
                change = recommended - current
                change_pct = (change / current * 100) if current > 0 else 0
            else:
                # Assume equal weights if not provided
                current = 100 / len(question_metrics)
                change = recommended - current
                change_pct = (change / current * 100) if current > 0 else 0

            data.append({
                'question_id': question_id,
                'current_weight': round(current, 2),
                'recommended_weight': round(recommended, 2),
                'absolute_change': round(change, 2),
                'percent_change': round(change_pct, 1),
                'change_direction': 'increase' if change > 0.5 else ('decrease' if change < -0.5 else 'stable')
            })

        return pd.DataFrame(data)

    def _generate_question_recommendations(
        self,
        question_metrics: pd.DataFrame,
        recommended_weights: Dict[str, float],
        current_weights: Optional[Dict[str, float]]
    ) -> pd.DataFrame:
        """Generate action recommendations for each question."""
        recommendations = []

        for idx, row in question_metrics.iterrows():
            question_id = row['question_id']
            discrimination = row['discrimination']
            difficulty = row['difficulty']
            std_dev = row.get('std_dev', 0.5)

            action = "Keep as-is"
            reason = "Metrics within acceptable range"
            suggested_changes = ""
            quality_score = self._calculate_quality_score(row)

            # Decision logic based on metrics
            if discrimination < 0:
                action = "Consider removing"
                reason = f"Negative discrimination ({discrimination:.3f}) indicates possible scoring error"
                suggested_changes = "Verify scoring key; consider removing or rescoring"
            elif discrimination < 0.15:
                if discrimination < 0.10:
                    action = "Consider removing"
                    reason = f"Very poor discrimination ({discrimination:.3f})"
                    suggested_changes = "Remove from test or completely rewrite"
                else:
                    action = "Review carefully"
                    reason = f"Poor discrimination ({discrimination:.3f})"
                    suggested_changes = "Rewrite distractors; check for ambiguity"
            elif difficulty < 0.20:
                action = "Review carefully"
                reason = f"Too difficult ({difficulty:.3f} correct rate)"
                suggested_changes = "Simplify question or check for errors"
            elif difficulty > 0.90:
                action = "Review carefully"
                reason = f"Too easy ({difficulty:.3f} correct rate)"
                suggested_changes = "Increase difficulty or remove if redundant"
            elif std_dev < 0.2:
                action = "Review carefully"
                reason = f"Low variance ({std_dev:.3f}) - most students answer same way"
                suggested_changes = "Check if question is trivial or unclear"
            else:
                # Check for weight mismatch
                rec_weight = recommended_weights.get(question_id, 0)
                if current_weights:
                    curr_weight = current_weights.get(question_id, 0)
                else:
                    curr_weight = 100 / len(question_metrics)

                weight_diff = abs(rec_weight - curr_weight)
                if weight_diff > 2:  # More than 2% difference
                    action = "Adjust weight"
                    reason = f"Good metrics but weight mismatch ({weight_diff:.1f}% difference)"
                    suggested_changes = f"Change weight from {curr_weight:.1f}% to {rec_weight:.1f}%"

            recommendations.append({
                'question_id': question_id,
                'action': action,
                'reason': reason,
                'suggested_changes': suggested_changes,
                'quality_score': round(quality_score, 2),
                'discrimination': round(discrimination, 3),
                'difficulty': round(difficulty, 3),
                'std_dev': round(std_dev, 3)
            })

        return pd.DataFrame(recommendations)

    def _calculate_quality_score(self, row: pd.Series) -> float:
        """Calculate overall quality score for a question (0-100)."""
        score = 0

        # Discrimination component (0-40 points)
        disc = max(0, row['discrimination'])
        if disc >= 0.40:
            score += 40
        elif disc >= 0.30:
            score += 35
        elif disc >= 0.20:
            score += 25
        elif disc >= 0.15:
            score += 15
        else:
            score += disc * 100  # Partial credit

        # Difficulty component (0-30 points)
        # Optimal around 0.55, penalize extremes
        diff = row['difficulty']
        diff_score = 30 * np.exp(-((diff - 0.55) ** 2) / (2 * 0.20 ** 2))
        score += diff_score

        # Variance component (0-30 points)
        # Higher variance is better (more discriminating)
        std = row.get('std_dev', 0.5)
        score += (std / 0.5) * 30

        return min(100, score)

    def _generate_test_recommendations(
        self,
        question_metrics: pd.DataFrame,
        test_statistics: Dict[str, Any]
    ) -> List[str]:
        """Generate overall test-level recommendations."""
        recommendations = []

        # Analyze difficulty distribution
        difficulties = question_metrics['difficulty'].values
        mean_diff = np.mean(difficulties)
        std_diff = np.std(difficulties)

        if mean_diff < 0.45:
            recommendations.append(
                f"TEST TOO DIFFICULT: Average difficulty is {mean_diff:.2f}. "
                f"Consider adding easier questions or simplifying existing ones."
            )
        elif mean_diff > 0.75:
            recommendations.append(
                f"TEST TOO EASY: Average difficulty is {mean_diff:.2f}. "
                f"Consider adding more challenging questions."
            )
        else:
            recommendations.append(
                f"Overall difficulty is appropriate (mean: {mean_diff:.2f})."
            )

        # Check difficulty spread
        if std_diff < 0.10:
            recommendations.append(
                "LOW DIFFICULTY SPREAD: Questions cluster at similar difficulty. "
                "Add variety in difficulty levels for better discrimination."
            )
        elif std_diff > 0.30:
            recommendations.append(
                "HIGH DIFFICULTY SPREAD: Large variance in question difficulty. "
                "Consider if the range is intentional."
            )

        # Analyze discrimination
        discriminations = question_metrics['discrimination'].values
        poor_disc_count = sum(d < 0.15 for d in discriminations)
        if poor_disc_count > 0:
            pct = (poor_disc_count / len(discriminations)) * 100
            recommendations.append(
                f"WARNING: {poor_disc_count} questions ({pct:.0f}%) have poor discrimination (<0.15). "
                f"Review these questions for clarity and relevance."
            )

        # Check for negative discrimination
        neg_disc_count = sum(d < 0 for d in discriminations)
        if neg_disc_count > 0:
            recommendations.append(
                f"CRITICAL: {neg_disc_count} questions have negative discrimination. "
                f"This may indicate scoring errors or misleading questions."
            )

        # Test reliability (if Cronbach's alpha provided)
        if 'cronbach_alpha' in test_statistics:
            alpha = test_statistics['cronbach_alpha']
            if alpha < 0.70:
                recommendations.append(
                    f"LOW RELIABILITY: Cronbach's alpha is {alpha:.3f}. "
                    f"Consider removing poorly performing questions to improve reliability."
                )
            elif alpha > 0.90:
                recommendations.append(
                    f"HIGH RELIABILITY: Cronbach's alpha is {alpha:.3f}. "
                    f"Test has excellent internal consistency."
                )
            else:
                recommendations.append(
                    f"ACCEPTABLE RELIABILITY: Cronbach's alpha is {alpha:.3f}."
                )

        # Check for redundant questions (similar difficulty and low unique contribution)
        recommendations.extend(self._check_question_clustering(question_metrics))

        # Suggested reordering
        reorder_suggestion = self._suggest_reordering(question_metrics)
        recommendations.append(reorder_suggestion)

        return recommendations

    def _check_question_clustering(
        self,
        question_metrics: pd.DataFrame
    ) -> List[str]:
        """Check for clusters of potentially redundant questions."""
        recommendations = []

        # Group questions by difficulty bins
        difficulty_bins = pd.cut(
            question_metrics['difficulty'],
            bins=[0, 0.3, 0.5, 0.7, 0.9, 1.0],
            labels=['Very Hard', 'Hard', 'Medium', 'Easy', 'Very Easy']
        )

        bin_counts = difficulty_bins.value_counts()

        # Check for missing difficulty levels
        for level in ['Very Hard', 'Hard', 'Medium', 'Easy', 'Very Easy']:
            if level not in bin_counts or bin_counts[level] == 0:
                recommendations.append(
                    f"MISSING DIFFICULTY LEVEL: No questions in '{level}' range. "
                    f"Consider adding questions at this difficulty."
                )

        # Check for over-concentration
        for level, count in bin_counts.items():
            if count > len(question_metrics) * 0.5:
                recommendations.append(
                    f"CONCENTRATION WARNING: {count} questions ({count/len(question_metrics)*100:.0f}%) "
                    f"are in the '{level}' difficulty range. Consider redistributing."
                )

        return recommendations

    def _suggest_reordering(self, question_metrics: pd.DataFrame) -> str:
        """Suggest optimal question ordering for better test flow."""
        # Sort by difficulty for progressive test
        sorted_by_difficulty = question_metrics.sort_values('difficulty', ascending=False)

        suggested_order = sorted_by_difficulty['question_id'].tolist()

        return (
            f"SUGGESTED REORDERING: For optimal test flow (easy to hard), "
            f"consider ordering questions as: {', '.join(map(str, suggested_order[:5]))}... "
            f"(showing first 5 of {len(suggested_order)} questions)"
        )

    def _identify_priority_items(
        self,
        question_metrics: pd.DataFrame,
        question_recommendations: pd.DataFrame,
        current_weights: Optional[Dict[str, float]]
    ) -> pd.DataFrame:
        """Identify top 5 questions needing immediate attention."""
        priority_items = []

        for idx, rec_row in question_recommendations.iterrows():
            question_id = rec_row['question_id']
            metrics_row = question_metrics[
                question_metrics['question_id'] == question_id
            ].iloc[0]

            priority = "Low"
            issue = ""

            # Determine priority based on action and metrics
            if rec_row['action'] == "Consider removing":
                priority = "High"
                if metrics_row['discrimination'] < 0:
                    issue = f"Negative discrimination ({metrics_row['discrimination']:.3f})"
                else:
                    issue = f"Very poor discrimination ({metrics_row['discrimination']:.3f})"
            elif rec_row['action'] == "Review carefully":
                priority = "Medium"
                issue = rec_row['reason']
            elif rec_row['action'] == "Adjust weight":
                priority = "Low"
                issue = rec_row['reason']

            if issue:
                current_weight = current_weights.get(question_id, 0) if current_weights else 0
                priority_items.append({
                    'question_id': question_id,
                    'current_weight': round(current_weight, 2),
                    'issue_description': issue,
                    'recommended_action': rec_row['action'],
                    'suggested_changes': rec_row['suggested_changes'],
                    'priority_level': priority,
                    'quality_score': rec_row['quality_score']
                })

        # Sort by priority (High > Medium > Low) and quality score
        priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
        priority_items.sort(key=lambda x: (priority_order[x['priority_level']], x['quality_score']))

        # Return top 5
        return pd.DataFrame(priority_items[:5])

    def _create_excel_sheets(
        self,
        question_metrics: pd.DataFrame,
        recommended_weights: Dict[str, float],
        question_recommendations: pd.DataFrame,
        test_recommendations: List[str]
    ) -> Dict[str, pd.DataFrame]:
        """Create formatted data for Excel output."""

        # Sheet 1: Question Analysis
        analysis_df = question_metrics.copy()
        analysis_df['recommended_weight'] = analysis_df['question_id'].map(recommended_weights)
        analysis_df['quality_score'] = question_recommendations.set_index('question_id').loc[
            analysis_df['question_id']
        ]['quality_score'].values

        # Add quality flags
        analysis_df['flag'] = ''
        for idx, row in analysis_df.iterrows():
            flags = []
            if row['discrimination'] < 0:
                flags.append('🔴 NEGATIVE_DISC')
            elif row['discrimination'] < 0.15:
                flags.append('🟠 POOR_DISC')
            if row['difficulty'] < 0.2:
                flags.append('🟡 TOO_HARD')
            elif row['difficulty'] > 0.9:
                flags.append('🟡 TOO_EASY')
            if row.get('std_dev', 0.5) < 0.2:
                flags.append('🟡 LOW_VAR')
            analysis_df.at[idx, 'flag'] = ' | '.join(flags) if flags else '🟢 OK'

        # Sheet 2: Question Rankings
        rankings_df = analysis_df[[
            'question_id', 'quality_score', 'discrimination', 'difficulty', 'recommended_weight'
        ]].copy()

        # Add various ranking columns
        rankings_df['rank_by_quality'] = rankings_df['quality_score'].rank(ascending=False).astype(int)
        rankings_df['rank_by_discrimination'] = rankings_df['discrimination'].rank(ascending=False).astype(int)
        rankings_df['rank_by_weight'] = rankings_df['recommended_weight'].rank(ascending=False).astype(int)

        rankings_df = rankings_df.sort_values('rank_by_quality')

        # Sheet 3: Distribution Details
        distribution_df = question_metrics[[
            'question_id', 'difficulty', 'std_dev'
        ]].copy()

        if 'upper_group_correct' in question_metrics.columns:
            distribution_df['upper_group_correct'] = question_metrics['upper_group_correct']
        if 'lower_group_correct' in question_metrics.columns:
            distribution_df['lower_group_correct'] = question_metrics['lower_group_correct']

        # Add percentile information
        distribution_df['difficulty_percentile'] = (
            distribution_df['difficulty'].rank(pct=True) * 100
        ).round(1)
        distribution_df['variance_percentile'] = (
            distribution_df['std_dev'].rank(pct=True) * 100
        ).round(1)

        # Sheet 4: Recommendations
        recommendations_df = question_recommendations.copy()

        # Add test-level recommendations as additional rows
        test_rec_df = pd.DataFrame([
            {
                'question_id': 'TEST_OVERALL',
                'action': 'TEST_RECOMMENDATION',
                'reason': rec,
                'suggested_changes': '',
                'quality_score': np.nan,
                'discrimination': np.nan,
                'difficulty': np.nan,
                'std_dev': np.nan
            }
            for rec in test_recommendations
        ])

        # Ensure consistent dtypes before concatenation
        for col in ['quality_score', 'discrimination', 'difficulty', 'std_dev']:
            if col in recommendations_df.columns:
                recommendations_df[col] = recommendations_df[col].astype(float)
            if col in test_rec_df.columns:
                test_rec_df[col] = test_rec_df[col].astype(float)

        recommendations_df = pd.concat([recommendations_df, test_rec_df], ignore_index=True)

        return {
            'question_analysis': analysis_df,
            'question_rankings': rankings_df,
            'distribution_details': distribution_df,
            'recommendations': recommendations_df
        }

    def save_to_excel(
        self,
        results: Dict[str, Any],
        output_path: str = 'test_optimization_results.xlsx'
    ) -> None:
        """
        Save all results to an Excel file with multiple sheets.

        Args:
            results: Output from optimize() method
            output_path: Path for the output Excel file
        """
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Save each sheet
            results['excel_sheets']['question_analysis'].to_excel(
                writer, sheet_name='Question Analysis', index=False
            )
            results['excel_sheets']['question_rankings'].to_excel(
                writer, sheet_name='Question Rankings', index=False
            )
            results['excel_sheets']['distribution_details'].to_excel(
                writer, sheet_name='Distribution Details', index=False
            )
            results['excel_sheets']['recommendations'].to_excel(
                writer, sheet_name='Recommendations', index=False
            )

            # Save weight changes
            results['weight_changes'].to_excel(
                writer, sheet_name='Weight Changes', index=False
            )

            # Save priority items
            if not results['priority_items'].empty:
                results['priority_items'].to_excel(
                    writer, sheet_name='Priority Items', index=False
                )

            # Save summary
            summary_df = pd.DataFrame({
                'Metric': ['Total Questions', 'Alpha', 'Beta', 'Gamma', 'Optimal Difficulty'],
                'Value': [
                    len(results['recommended_weights']),
                    self.config.alpha,
                    self.config.beta,
                    self.config.gamma,
                    self.config.optimal_difficulty
                ]
            })
            summary_df.to_excel(writer, sheet_name='Configuration', index=False)
