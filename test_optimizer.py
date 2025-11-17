#!/usr/bin/env python3
"""
Unit tests for the Weight Optimization Specialist.

These tests verify the correctness of weight calculations and recommendation logic.
"""

import unittest
import pandas as pd
import numpy as np
from weight_optimizer import WeightOptimizer, WeightOptimizerConfig


class TestWeightOptimizer(unittest.TestCase):
    """Test cases for WeightOptimizer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = WeightOptimizerConfig(
            alpha=0.5,
            beta=0.3,
            gamma=0.2,
            optimal_difficulty=0.55,
            difficulty_sigma=0.15
        )
        self.optimizer = WeightOptimizer(self.config)

        # Create minimal test data
        self.basic_metrics = pd.DataFrame({
            'question_id': ['Q1', 'Q2', 'Q3'],
            'difficulty': [0.55, 0.80, 0.20],
            'discrimination': [0.40, 0.10, 0.35],
            'std_dev': [0.50, 0.40, 0.45],
            'upper_group_correct': [0.75, 0.85, 0.45],
            'lower_group_correct': [0.35, 0.75, 0.10]
        })

        self.test_stats = {
            'cronbach_alpha': 0.75,
            'mean_score': 70,
            'total_students': 100
        }

    def test_weights_sum_to_100(self):
        """Test that recommended weights sum to 100%."""
        results = self.optimizer.optimize(self.basic_metrics, self.test_stats)
        total = sum(results['recommended_weights'].values())
        self.assertAlmostEqual(total, 100.0, places=5)

    def test_optimal_difficulty_gets_highest_penalty_bonus(self):
        """Test that optimal difficulty (0.55) gets maximum difficulty bonus."""
        # Create two questions: one at optimal difficulty, one not
        metrics = pd.DataFrame({
            'question_id': ['Q_optimal', 'Q_extreme'],
            'difficulty': [0.55, 0.10],  # Optimal vs. very hard
            'discrimination': [0.30, 0.30],  # Same discrimination
            'std_dev': [0.50, 0.50],  # Same variance
            'upper_group_correct': [0.70, 0.30],
            'lower_group_correct': [0.40, 0.00]
        })

        results = self.optimizer.optimize(metrics, self.test_stats)
        weights = results['recommended_weights']

        # Q_optimal should have higher weight due to difficulty bonus
        self.assertGreater(weights['Q_optimal'], weights['Q_extreme'])

    def test_negative_discrimination_flagged(self):
        """Test that negative discrimination is flagged for removal."""
        metrics = pd.DataFrame({
            'question_id': ['Q_bad'],
            'difficulty': [0.50],
            'discrimination': [-0.10],  # Negative!
            'std_dev': [0.50],
            'upper_group_correct': [0.45],
            'lower_group_correct': [0.55]
        })

        results = self.optimizer.optimize(metrics, self.test_stats)
        rec_df = results['question_recommendations']

        action = rec_df[rec_df['question_id'] == 'Q_bad']['action'].iloc[0]
        self.assertEqual(action, "Consider removing")

    def test_poor_discrimination_flagged(self):
        """Test that poor discrimination (<0.15) is flagged."""
        metrics = pd.DataFrame({
            'question_id': ['Q_poor'],
            'difficulty': [0.50],
            'discrimination': [0.08],  # Very poor
            'std_dev': [0.50],
            'upper_group_correct': [0.54],
            'lower_group_correct': [0.46]
        })

        results = self.optimizer.optimize(metrics, self.test_stats)
        rec_df = results['question_recommendations']

        action = rec_df[rec_df['question_id'] == 'Q_poor']['action'].iloc[0]
        self.assertIn(action, ["Consider removing", "Review carefully"])

    def test_too_easy_question_flagged(self):
        """Test that very easy questions (>0.90) are flagged."""
        metrics = pd.DataFrame({
            'question_id': ['Q_easy'],
            'difficulty': [0.95],  # Too easy
            'discrimination': [0.25],
            'std_dev': [0.22],
            'upper_group_correct': [0.98],
            'lower_group_correct': [0.92]
        })

        results = self.optimizer.optimize(metrics, self.test_stats)
        rec_df = results['question_recommendations']

        action = rec_df[rec_df['question_id'] == 'Q_easy']['action'].iloc[0]
        reason = rec_df[rec_df['question_id'] == 'Q_easy']['reason'].iloc[0]

        self.assertEqual(action, "Review carefully")
        self.assertIn("easy", reason.lower())

    def test_too_hard_question_flagged(self):
        """Test that very hard questions (<0.20) are flagged."""
        metrics = pd.DataFrame({
            'question_id': ['Q_hard'],
            'difficulty': [0.15],  # Too hard
            'discrimination': [0.25],
            'std_dev': [0.36],
            'upper_group_correct': [0.30],
            'lower_group_correct': [0.05]
        })

        results = self.optimizer.optimize(metrics, self.test_stats)
        rec_df = results['question_recommendations']

        action = rec_df[rec_df['question_id'] == 'Q_hard']['action'].iloc[0]
        reason = rec_df[rec_df['question_id'] == 'Q_hard']['reason'].iloc[0]

        self.assertEqual(action, "Review carefully")
        self.assertIn("difficult", reason.lower())

    def test_high_discrimination_gets_higher_weight(self):
        """Test that higher discrimination leads to higher weight."""
        metrics = pd.DataFrame({
            'question_id': ['Q_high_disc', 'Q_low_disc'],
            'difficulty': [0.55, 0.55],  # Same difficulty
            'discrimination': [0.50, 0.20],  # Different discrimination
            'std_dev': [0.50, 0.50],  # Same variance
            'upper_group_correct': [0.80, 0.65],
            'lower_group_correct': [0.30, 0.45]
        })

        results = self.optimizer.optimize(metrics, self.test_stats)
        weights = results['recommended_weights']

        self.assertGreater(weights['Q_high_disc'], weights['Q_low_disc'])

    def test_weight_changes_calculated_correctly(self):
        """Test that weight change calculations are correct."""
        current_weights = {'Q1': 40.0, 'Q2': 30.0, 'Q3': 30.0}

        results = self.optimizer.optimize(
            self.basic_metrics, self.test_stats, current_weights
        )

        changes_df = results['weight_changes']

        # Verify structure
        self.assertIn('current_weight', changes_df.columns)
        self.assertIn('recommended_weight', changes_df.columns)
        self.assertIn('absolute_change', changes_df.columns)

        # Verify calculations
        for idx, row in changes_df.iterrows():
            calculated_change = row['recommended_weight'] - row['current_weight']
            self.assertAlmostEqual(
                row['absolute_change'], calculated_change, places=2
            )

    def test_priority_items_sorted_by_priority(self):
        """Test that priority items are sorted correctly."""
        # Create data with multiple issues
        metrics = pd.DataFrame({
            'question_id': ['Q_neg', 'Q_poor', 'Q_ok'],
            'difficulty': [0.50, 0.50, 0.55],
            'discrimination': [-0.05, 0.12, 0.40],  # Negative, poor, good
            'std_dev': [0.50, 0.50, 0.50],
            'upper_group_correct': [0.48, 0.56, 0.75],
            'lower_group_correct': [0.53, 0.44, 0.35]
        })

        results = self.optimizer.optimize(metrics, self.test_stats)
        priority_df = results['priority_items']

        # High priority should come first
        if len(priority_df) >= 2:
            first_priority = priority_df.iloc[0]['priority_level']
            self.assertEqual(first_priority, 'High')

    def test_excel_sheets_created(self):
        """Test that all required Excel sheets are created."""
        results = self.optimizer.optimize(self.basic_metrics, self.test_stats)

        expected_sheets = [
            'question_analysis',
            'question_rankings',
            'distribution_details',
            'recommendations'
        ]

        for sheet in expected_sheets:
            self.assertIn(sheet, results['excel_sheets'])
            self.assertIsInstance(results['excel_sheets'][sheet], pd.DataFrame)

    def test_test_recommendations_generated(self):
        """Test that test-level recommendations are generated."""
        results = self.optimizer.optimize(self.basic_metrics, self.test_stats)

        self.assertIsInstance(results['test_recommendations'], list)
        self.assertGreater(len(results['test_recommendations']), 0)

    def test_quality_score_in_valid_range(self):
        """Test that quality scores are between 0 and 100."""
        results = self.optimizer.optimize(self.basic_metrics, self.test_stats)
        rec_df = results['question_recommendations']

        for score in rec_df['quality_score']:
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)

    def test_custom_config_used(self):
        """Test that custom configuration is applied."""
        custom_config = WeightOptimizerConfig(
            alpha=0.7,
            beta=0.2,
            gamma=0.1,
            optimal_difficulty=0.60
        )

        optimizer = WeightOptimizer(custom_config)

        self.assertEqual(optimizer.config.alpha, 0.7)
        self.assertEqual(optimizer.config.optimal_difficulty, 0.60)

    def test_handles_single_question(self):
        """Test that optimizer handles single question correctly."""
        single_q = pd.DataFrame({
            'question_id': ['Q1'],
            'difficulty': [0.55],
            'discrimination': [0.40],
            'std_dev': [0.50],
            'upper_group_correct': [0.75],
            'lower_group_correct': [0.35]
        })

        results = self.optimizer.optimize(single_q, self.test_stats)

        # Single question should get 100% weight
        self.assertAlmostEqual(results['recommended_weights']['Q1'], 100.0, places=2)

    def test_cronbach_alpha_recommendation(self):
        """Test that Cronbach's alpha generates appropriate recommendation."""
        # Test with low alpha
        low_alpha_stats = {'cronbach_alpha': 0.65}
        results = self.optimizer.optimize(self.basic_metrics, low_alpha_stats)

        has_reliability_rec = any(
            'reliability' in rec.lower()
            for rec in results['test_recommendations']
        )
        self.assertTrue(has_reliability_rec)


class TestWeightOptimizerConfig(unittest.TestCase):
    """Test cases for WeightOptimizerConfig."""

    def test_default_values(self):
        """Test that default config values are set correctly."""
        config = WeightOptimizerConfig()

        self.assertEqual(config.alpha, 0.5)
        self.assertEqual(config.beta, 0.3)
        self.assertEqual(config.gamma, 0.2)
        self.assertEqual(config.optimal_difficulty, 0.55)
        self.assertEqual(config.difficulty_sigma, 0.15)

    def test_custom_values(self):
        """Test that custom values can be set."""
        config = WeightOptimizerConfig(
            alpha=0.6,
            beta=0.25,
            gamma=0.15,
            optimal_difficulty=0.50,
            difficulty_sigma=0.20
        )

        self.assertEqual(config.alpha, 0.6)
        self.assertEqual(config.beta, 0.25)
        self.assertEqual(config.gamma, 0.15)
        self.assertEqual(config.optimal_difficulty, 0.50)
        self.assertEqual(config.difficulty_sigma, 0.20)


if __name__ == '__main__':
    unittest.main(verbosity=2)
