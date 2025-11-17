#!/usr/bin/env python3
"""Example usage of the Visualization Generator Agent.

This script demonstrates how to use Agent 2 (Visualization Generator) with
sample data that simulates output from Agent 1 (Metrics Calculator).
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd

from src.agents.visualization_generator import VisualizationGenerator
from src.models.metrics import QuestionMetrics, TestStatistics, QualityCategory


def create_sample_question_metrics(n_questions: int = 10) -> list:
    """Create sample question metrics simulating Agent 1 output.

    Args:
        n_questions: Number of questions to simulate

    Returns:
        List of QuestionMetrics objects
    """
    np.random.seed(42)  # For reproducibility

    metrics = []
    for i in range(n_questions):
        # Simulate realistic test metrics
        difficulty = np.random.beta(5, 5)  # Most questions medium difficulty
        discrimination = max(0, min(1, 0.3 + np.random.normal(0, 0.15)))

        # Determine quality based on metrics
        if discrimination >= 0.3 and 0.3 <= difficulty <= 0.7:
            quality = QualityCategory.GOOD
        elif discrimination >= 0.2 or (0.2 <= difficulty <= 0.8):
            quality = QualityCategory.REVIEW
        else:
            quality = QualityCategory.POOR

        # Generate quality notes
        notes = []
        if difficulty < 0.3:
            notes.append("Too difficult")
        elif difficulty > 0.7:
            notes.append("Too easy")
        if discrimination < 0.2:
            notes.append("Low discrimination")
        if not notes:
            notes.append("Good psychometric properties")

        # Current and recommended weights
        current_weight = np.random.choice([1, 2, 3, 4, 5])
        recommended_weight = current_weight
        if quality == QualityCategory.POOR:
            recommended_weight = max(1, current_weight - 1)
        elif quality == QualityCategory.GOOD and discrimination > 0.4:
            recommended_weight = min(5, current_weight + 1)

        # Score distribution
        max_score = current_weight * 2  # 2 points per weight unit
        mean_score = difficulty * max_score
        std_score = max_score * 0.2
        scores = np.random.normal(mean_score, std_score, 100)
        scores = np.clip(scores, 0, max_score)

        question = QuestionMetrics(
            question_id=f"Q{i+1:03d}",
            question_number=i + 1,
            mean_score=float(np.mean(scores)),
            median_score=float(np.median(scores)),
            std_dev=float(np.std(scores)),
            min_score=float(np.min(scores)),
            max_score=float(np.max(scores)),
            difficulty_index=difficulty,
            discrimination_index=discrimination,
            current_weight=float(current_weight),
            recommended_weight=float(recommended_weight),
            max_possible_score=float(max_score),
            quality_category=quality,
            is_curve_breaker=False,
            quality_notes=notes,
            score_distribution=scores,
        )
        metrics.append(question)

    return metrics


def create_sample_test_statistics(question_metrics: list, n_students: int = 100) -> TestStatistics:
    """Create sample test statistics simulating Agent 1 output.

    Args:
        question_metrics: List of QuestionMetrics
        n_students: Number of students

    Returns:
        TestStatistics object
    """
    np.random.seed(42)

    # Calculate totals
    max_possible = sum(qm.max_possible_score for qm in question_metrics)

    # Simulate student total scores
    student_scores = np.random.normal(max_possible * 0.7, max_possible * 0.15, n_students)
    student_scores = np.clip(student_scores, 0, max_possible)

    # Count quality categories
    good_count = sum(1 for qm in question_metrics if qm.quality_category == QualityCategory.GOOD)
    review_count = sum(1 for qm in question_metrics if qm.quality_category == QualityCategory.REVIEW)
    poor_count = sum(1 for qm in question_metrics if qm.quality_category == QualityCategory.POOR)

    # Calculate percentiles for upper/lower 27%
    upper_27_cutoff = float(np.percentile(student_scores, 73))
    lower_27_cutoff = float(np.percentile(student_scores, 27))

    return TestStatistics(
        total_questions=len(question_metrics),
        total_students=n_students,
        max_possible_score=float(max_possible),
        mean_total_score=float(np.mean(student_scores)),
        median_total_score=float(np.median(student_scores)),
        std_dev_total_score=float(np.std(student_scores)),
        min_total_score=float(np.min(student_scores)),
        max_total_score=float(np.max(student_scores)),
        cronbach_alpha=0.85,  # Simulated reliability
        sem=float(np.std(student_scores) * np.sqrt(1 - 0.85)),
        skewness=float(pd.Series(student_scores).skew()),
        kurtosis=float(pd.Series(student_scores).kurtosis()),
        good_questions_count=good_count,
        review_questions_count=review_count,
        poor_questions_count=poor_count,
        upper_27_cutoff=upper_27_cutoff,
        lower_27_cutoff=lower_27_cutoff,
        student_total_scores=student_scores,
    )


def main():
    """Main example demonstrating the Visualization Generator agent."""
    print("=" * 70)
    print("Test Evaluation System - Visualization Generator (Agent 2)")
    print("=" * 70)
    print()

    # Step 1: Create sample data (simulating Agent 1 output)
    print("Step 1: Creating sample data (simulating Agent 1 output)...")
    question_metrics = create_sample_question_metrics(n_questions=12)
    test_statistics = create_sample_test_statistics(question_metrics, n_students=150)

    print(f"  - Generated {len(question_metrics)} question metrics")
    print(f"  - Test has {test_statistics.total_students} students")
    print(f"  - Max possible score: {test_statistics.max_possible_score:.1f}")
    print(f"  - Mean score: {test_statistics.mean_total_score:.2f}")
    print(f"  - Cronbach's α: {test_statistics.cronbach_alpha:.3f}")
    print()

    # Step 2: Initialize Visualization Generator
    print("Step 2: Initializing Visualization Generator agent...")
    generator = VisualizationGenerator(output_dir="output")
    print(f"  - Output directory: {generator.output_dir}")
    print()

    # Step 3: Generate all visualizations
    print("Step 3: Generating visualizations...")
    output = generator.generate(
        question_metrics=question_metrics,
        test_statistics=test_statistics,
    )

    # Step 4: Display summary
    print()
    print("Step 4: Visualization Generation Summary")
    print("-" * 70)
    summary = generator.get_summary(output)

    print(f"\nExcel Static Images ({summary['excel_images_generated']} generated):")
    for name, path in summary['excel_image_paths'].items():
        print(f"  - {name}: {path}")

    print(f"\nPlotly Interactive Figures ({summary['plotly_figures_generated']} generated):")
    for fig_type in summary['plotly_figure_types']:
        print(f"  - {fig_type}")

    print(f"\nAll Excel images complete: {summary['all_excel_complete']}")
    print(f"All Plotly figures complete: {summary['all_plotly_complete']}")

    # Step 5: Save interactive HTML report
    print()
    print("Step 5: Saving interactive HTML report...")
    html_path = generator.save_plotly_html(output, "test_evaluation_report.html")
    print(f"  - HTML report saved to: {html_path}")

    print()
    print("=" * 70)
    print("Visualization generation complete!")
    print(f"Check the 'output' directory for generated files.")
    print("=" * 70)

    return output


if __name__ == "__main__":
    main()
