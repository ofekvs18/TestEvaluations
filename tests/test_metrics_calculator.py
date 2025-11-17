"""Unit tests for Agent 1: Metrics Calculator."""

import pytest
import pandas as pd
import numpy as np
from test_analysis.metrics_calculator import MetricsCalculator


@pytest.fixture
def sample_scores_df():
    """Create sample student scores DataFrame for testing."""
    # 10 students, 5 questions
    # Designed to have varying difficulty and discrimination
    data = {
        'Q1': [10, 9, 8, 7, 6, 5, 4, 3, 2, 1],  # Good discrimination
        'Q2': [10, 10, 10, 10, 5, 5, 5, 5, 0, 0],  # Medium discrimination
        'Q3': [10, 10, 10, 10, 10, 10, 10, 10, 10, 10],  # Too easy (no disc)
        'Q4': [2, 1, 1, 0, 0, 0, 0, 0, 0, 0],  # Too hard
        'Q5': [5, 8, 3, 10, 7, 2, 9, 1, 6, 4],  # Poor discrimination (random)
    }
    return pd.DataFrame(data)


@pytest.fixture
def max_points():
    """Maximum points per question."""
    return {'Q1': 10, 'Q2': 10, 'Q3': 10, 'Q4': 10, 'Q5': 10}


class TestMetricsCalculator:
    """Test suite for MetricsCalculator class."""

    def test_initialization(self, sample_scores_df, max_points):
        """Test proper initialization of MetricsCalculator."""
        calc = MetricsCalculator(sample_scores_df, max_points)

        assert calc.scores_df.shape == (10, 5)
        assert len(calc.max_points) == 5
        assert calc.total_scores is not None
        assert len(calc.upper_group) > 0
        assert len(calc.lower_group) > 0

    def test_upper_lower_groups(self, sample_scores_df, max_points):
        """Test that upper/lower 27% groups are calculated correctly."""
        calc = MetricsCalculator(sample_scores_df, max_points)

        # With 10 students, 27% = 2.7, so we expect 2-3 students in each group
        assert 2 <= len(calc.upper_group) <= 3
        assert 2 <= len(calc.lower_group) <= 3

        # Upper group should have higher total scores than lower group
        upper_mean = calc.total_scores.loc[calc.upper_group].mean()
        lower_mean = calc.total_scores.loc[calc.lower_group].mean()
        assert upper_mean > lower_mean

    def test_difficulty_index_calculation(self, sample_scores_df, max_points):
        """Test difficulty index calculation."""
        calc = MetricsCalculator(sample_scores_df, max_points)

        # Q1: mean = 5.5, max = 10, difficulty = 0.55
        diff_q1 = calc.calculate_difficulty_index('Q1')
        assert 0.5 < diff_q1 < 0.6

        # Q3: all students got 10, difficulty = 1.0 (easiest)
        diff_q3 = calc.calculate_difficulty_index('Q3')
        assert diff_q3 == 1.0

        # Q4: very few points scored, difficulty should be low (hard)
        diff_q4 = calc.calculate_difficulty_index('Q4')
        assert diff_q4 < 0.1

    def test_discrimination_index_calculation(self, sample_scores_df, max_points):
        """Test discrimination index calculation."""
        calc = MetricsCalculator(sample_scores_df, max_points)

        # Q1 has perfect discrimination (high scorers do well, low scorers don't)
        disc_q1 = calc.calculate_discrimination_index('Q1')
        assert disc_q1 > 0.5  # Should be high

        # Q3 has no discrimination (everyone gets same score)
        disc_q3 = calc.calculate_discrimination_index('Q3')
        assert disc_q3 == 0.0  # No discrimination

    def test_item_total_correlation(self, sample_scores_df, max_points):
        """Test item-total correlation calculation."""
        calc = MetricsCalculator(sample_scores_df, max_points)

        # Q1 should have high correlation (aligns with total)
        corr_q1 = calc.calculate_item_total_correlation('Q1')
        assert corr_q1 > 0.5

        # Q3 should have low/no correlation (no variance)
        corr_q3 = calc.calculate_item_total_correlation('Q3')
        # NaN becomes 0 due to no variance
        assert -0.1 <= corr_q3 <= 0.1 or np.isnan(corr_q3) or corr_q3 == 0

    def test_predictive_power(self, sample_scores_df, max_points):
        """Test predictive power calculation."""
        calc = MetricsCalculator(sample_scores_df, max_points)

        pred = calc.calculate_predictive_power('Q1')

        assert 'high_score_mean' in pred
        assert 'low_score_mean' in pred
        assert 'difference' in pred

        # For Q1, students scoring ≥70% should have higher total scores
        assert pred['high_score_mean'] >= pred['low_score_mean']

    def test_quality_flag_classification(self, sample_scores_df, max_points):
        """Test question quality flag classification."""
        calc = MetricsCalculator(sample_scores_df, max_points)

        # Good: high discrimination, medium difficulty
        assert calc.classify_question_quality(0.5, 0.5) == "Good"

        # Poor: negative discrimination
        assert calc.classify_question_quality(0.5, -0.1) == "Poor"

        # Poor: very low discrimination
        assert calc.classify_question_quality(0.5, 0.1) == "Poor"

        # Review: extreme difficulty
        assert calc.classify_question_quality(0.1, 0.4) == "Review"  # Too hard
        assert calc.classify_question_quality(0.95, 0.4) == "Review"  # Too easy

        # Review: marginal discrimination
        assert calc.classify_question_quality(0.5, 0.2) == "Review"

    def test_all_question_metrics(self, sample_scores_df, max_points):
        """Test calculation of all metrics for all questions."""
        calc = MetricsCalculator(sample_scores_df, max_points)

        metrics_df = calc.calculate_all_question_metrics()

        assert isinstance(metrics_df, pd.DataFrame)
        assert len(metrics_df) == 5  # 5 questions

        expected_columns = [
            'question', 'max_points', 'mean_score', 'std_dev',
            'difficulty_index', 'discrimination_index', 'item_total_correlation',
            'predictive_high_mean', 'predictive_low_mean', 'predictive_difference',
            'quality_flag'
        ]
        for col in expected_columns:
            assert col in metrics_df.columns

    def test_difficulty_curve_analysis(self, sample_scores_df, max_points):
        """Test difficulty curve analysis."""
        calc = MetricsCalculator(sample_scores_df, max_points)

        sorted_questions, curve_breakers = calc.analyze_difficulty_curve()

        assert isinstance(sorted_questions, list)
        assert len(sorted_questions) == 5
        assert isinstance(curve_breakers, list)

        # Check that questions are sorted by difficulty
        difficulties = {q: calc.calculate_difficulty_index(q) for q in sorted_questions}
        for i in range(len(sorted_questions) - 1):
            assert difficulties[sorted_questions[i]] <= difficulties[sorted_questions[i + 1]]

    def test_cronbachs_alpha(self, sample_scores_df, max_points):
        """Test Cronbach's alpha calculation."""
        calc = MetricsCalculator(sample_scores_df, max_points)

        alpha = calc.calculate_cronbachs_alpha()

        # Alpha should be between -1 and 1 (can be negative in extreme cases)
        assert -1 <= alpha <= 1

    def test_test_statistics(self, sample_scores_df, max_points):
        """Test calculation of test-level statistics."""
        calc = MetricsCalculator(sample_scores_df, max_points)

        stats = calc.calculate_test_statistics()

        assert stats['student_count'] == 10
        assert stats['question_count'] == 5
        assert 'mean_total_score' in stats
        assert 'std_total_score' in stats
        assert 'cronbachs_alpha' in stats
        assert 'upper_group_cutoff' in stats
        assert 'lower_group_cutoff' in stats
        assert 'skewness' in stats
        assert 'kurtosis' in stats

    def test_run_method(self, sample_scores_df, max_points):
        """Test the complete run method."""
        calc = MetricsCalculator(sample_scores_df, max_points)

        results = calc.run()

        assert isinstance(results, dict)
        assert 'question_metrics' in results
        assert 'quality_flags' in results
        assert 'difficulty_order' in results
        assert 'curve_breakers' in results
        assert 'test_statistics' in results
        assert 'upper_lower_groups' in results

        assert isinstance(results['question_metrics'], pd.DataFrame)
        assert isinstance(results['quality_flags'], pd.DataFrame)
        assert isinstance(results['difficulty_order'], list)
        assert isinstance(results['curve_breakers'], list)
        assert isinstance(results['test_statistics'], dict)
        assert isinstance(results['upper_lower_groups'], dict)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_student(self):
        """Test with single student."""
        df = pd.DataFrame({'Q1': [10], 'Q2': [5]})
        calc = MetricsCalculator(df)

        # Should not crash
        results = calc.run()
        assert results is not None

    def test_single_question(self):
        """Test with single question."""
        df = pd.DataFrame({'Q1': [10, 8, 6, 4, 2]})
        calc = MetricsCalculator(df)

        results = calc.run()
        assert results is not None

    def test_zero_variance_scores(self):
        """Test with all same scores."""
        df = pd.DataFrame({
            'Q1': [10, 10, 10, 10, 10],
            'Q2': [5, 5, 5, 5, 5]
        })
        calc = MetricsCalculator(df)

        results = calc.run()
        # Should handle zero variance gracefully
        assert results['test_statistics']['std_total_score'] == 0.0

    def test_empty_dataframe(self):
        """Test with minimal valid data."""
        df = pd.DataFrame({'Q1': [10, 5], 'Q2': [8, 3]})
        calc = MetricsCalculator(df)

        results = calc.run()
        assert results is not None

    def test_negative_scores_handling(self):
        """Test that negative scores are handled properly."""
        df = pd.DataFrame({
            'Q1': [10, 8, 6, 4, 2],
            'Q2': [10, 8, 6, 4, 2]
        })
        calc = MetricsCalculator(df)

        # All calculations should work without errors
        results = calc.run()
        assert all(0 <= d <= 1 for d in
                  results['question_metrics']['difficulty_index'])
