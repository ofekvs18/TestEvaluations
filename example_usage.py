#!/usr/bin/env python3
"""
Example usage of the Weight Optimization Specialist.

This script demonstrates how to use the WeightOptimizer to analyze
test question metrics and generate recommendations.
"""

import pandas as pd
import numpy as np
from weight_optimizer import WeightOptimizer, WeightOptimizerConfig


def create_sample_data():
    """Create sample question metrics data for demonstration."""

    # Sample data representing 10 questions with various characteristics
    data = {
        'question_id': [f'Q{i:02d}' for i in range(1, 11)],
        'difficulty': [
            0.85,  # Q01: Easy question
            0.55,  # Q02: Optimal difficulty
            0.25,  # Q03: Hard question
            0.92,  # Q04: Very easy
            0.58,  # Q05: Good difficulty
            0.10,  # Q06: Very hard
            0.67,  # Q07: Slightly easy
            0.50,  # Q08: Medium
            0.75,  # Q09: Easy-medium
            0.40,  # Q10: Medium-hard
        ],
        'discrimination': [
            0.35,   # Q01: Good discrimination
            0.45,   # Q02: Excellent discrimination
            0.12,   # Q03: Poor discrimination
            0.08,   # Q04: Very poor discrimination
            0.52,   # Q05: Excellent discrimination
            -0.05,  # Q06: Negative discrimination (problem!)
            0.28,   # Q07: Moderate discrimination
            0.38,   # Q08: Good discrimination
            0.22,   # Q09: Fair discrimination
            0.42,   # Q10: Good discrimination
        ],
        'std_dev': [
            0.36,  # Q01
            0.50,  # Q02: Maximum variance
            0.43,  # Q03
            0.27,  # Q04
            0.49,  # Q05
            0.30,  # Q06
            0.47,  # Q07
            0.50,  # Q08
            0.43,  # Q09
            0.49,  # Q10
        ],
        'upper_group_correct': [
            0.95,  # Q01
            0.82,  # Q02
            0.38,  # Q03
            0.96,  # Q04
            0.85,  # Q05
            0.08,  # Q06
            0.78,  # Q07
            0.70,  # Q08
            0.88,  # Q09
            0.65,  # Q10
        ],
        'lower_group_correct': [
            0.60,  # Q01
            0.37,  # Q02
            0.26,  # Q03
            0.88,  # Q04
            0.33,  # Q05
            0.13,  # Q06
            0.50,  # Q07
            0.32,  # Q08
            0.66,  # Q09
            0.23,  # Q10
        ],
    }

    return pd.DataFrame(data)


def create_sample_test_statistics():
    """Create sample test-level statistics."""
    return {
        'total_students': 150,
        'mean_score': 68.5,
        'std_score': 12.3,
        'min_score': 35,
        'max_score': 95,
        'cronbach_alpha': 0.78,
        'sem': 5.76,  # Standard Error of Measurement
        'test_time_minutes': 60
    }


def main():
    """Main demonstration function."""
    print("=" * 60)
    print("Weight Optimization Specialist - Example Usage")
    print("=" * 60)

    # Create sample data
    question_metrics = create_sample_data()
    test_statistics = create_sample_test_statistics()

    # Optional: Define current weights (if they exist)
    # Assuming equal weights initially (10% each for 10 questions)
    current_weights = {f'Q{i:02d}': 10.0 for i in range(1, 11)}

    print("\nInput Question Metrics:")
    print("-" * 60)
    print(question_metrics.to_string())

    print("\n\nTest Statistics:")
    print("-" * 60)
    for key, value in test_statistics.items():
        print(f"  {key}: {value}")

    # Initialize optimizer with custom configuration
    config = WeightOptimizerConfig(
        alpha=0.5,  # Weight for discrimination
        beta=0.3,   # Weight for difficulty penalty
        gamma=0.2,  # Weight for variance
        optimal_difficulty=0.55,
        difficulty_sigma=0.15
    )

    optimizer = WeightOptimizer(config)

    # Run optimization
    print("\n\nRunning Optimization...")
    print("=" * 60)

    results = optimizer.optimize(
        question_metrics=question_metrics,
        test_statistics=test_statistics,
        current_weights=current_weights
    )

    # Display results
    print("\n1. RECOMMENDED WEIGHTS:")
    print("-" * 60)
    for qid, weight in sorted(results['recommended_weights'].items()):
        current = current_weights.get(qid, 10.0)
        change = weight - current
        arrow = "↑" if change > 0.5 else ("↓" if change < -0.5 else "→")
        print(f"  {qid}: {weight:6.2f}% (current: {current:.2f}%, change: {change:+.2f}% {arrow})")

    print("\n\n2. WEIGHT CHANGES SUMMARY:")
    print("-" * 60)
    print(results['weight_changes'].to_string())

    print("\n\n3. QUESTION RECOMMENDATIONS:")
    print("-" * 60)
    for idx, row in results['question_recommendations'].iterrows():
        print(f"\n  {row['question_id']}:")
        print(f"    Action: {row['action']}")
        print(f"    Reason: {row['reason']}")
        if row['suggested_changes']:
            print(f"    Suggestion: {row['suggested_changes']}")
        print(f"    Quality Score: {row['quality_score']:.2f}/100")

    print("\n\n4. TEST-LEVEL RECOMMENDATIONS:")
    print("-" * 60)
    for i, rec in enumerate(results['test_recommendations'], 1):
        print(f"\n  {i}. {rec}")

    print("\n\n5. PRIORITY ITEMS (Top 5):")
    print("-" * 60)
    if not results['priority_items'].empty:
        for idx, row in results['priority_items'].iterrows():
            print(f"\n  [{row['priority_level']}] {row['question_id']}")
            print(f"    Issue: {row['issue_description']}")
            print(f"    Action: {row['recommended_action']}")
            print(f"    Suggestion: {row['suggested_changes']}")
    else:
        print("  No critical priority items identified.")

    # Save to Excel
    output_file = 'test_optimization_results.xlsx'
    print(f"\n\nSaving detailed results to {output_file}...")
    optimizer.save_to_excel(results, output_file)
    print(f"Results saved successfully!")

    print("\n\nExcel Sheets Created:")
    print("-" * 60)
    for sheet_name in results['excel_sheets'].keys():
        df = results['excel_sheets'][sheet_name]
        print(f"  - {sheet_name}: {len(df)} rows, {len(df.columns)} columns")

    print("\n" + "=" * 60)
    print("Optimization Complete!")
    print("=" * 60)

    return results


if __name__ == "__main__":
    results = main()
