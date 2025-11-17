"""Agent 2: Visualization Generator.

This agent receives calculated metrics from Agent 1 (Metrics Calculator) and generates
comprehensive visualizations for both Excel (static) and HTML (interactive) outputs.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from ..models.metrics import (
    QuestionMetrics,
    TestStatistics,
    VisualizationOutput,
    create_metrics_dataframe,
)
from .excel_visualizations import ExcelVisualizationGenerator
from .plotly_visualizations import PlotlyVisualizationGenerator

logger = logging.getLogger(__name__)


class VisualizationGenerator:
    """Agent 2: Visualization Generator.

    This agent is responsible for generating all charts and visualizations
    based on the metrics calculated by Agent 1. It produces:

    1. Static Excel-ready images (matplotlib/seaborn)
    2. Interactive Plotly HTML figures

    All visualizations are designed to be colorblind-friendly and
    publication-ready.
    """

    def __init__(self, output_dir: str = "output"):
        """Initialize the Visualization Generator agent.

        Args:
            output_dir: Directory to save generated images
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize sub-generators
        self.excel_generator = ExcelVisualizationGenerator(output_dir)
        self.plotly_generator = PlotlyVisualizationGenerator()

        logger.info(f"Visualization Generator initialized with output directory: {output_dir}")

    def generate(
        self,
        question_metrics: Union[List[QuestionMetrics], pd.DataFrame],
        test_statistics: Union[TestStatistics, Dict[str, Any]],
        difficulty_order: Optional[List[int]] = None,
        curve_breakers: Optional[List[int]] = None,
        raw_student_data: Optional[pd.DataFrame] = None,
    ) -> VisualizationOutput:
        """Generate all visualizations from Agent 1's metrics.

        This is the main entry point for the visualization generation pipeline.

        Args:
            question_metrics: Question metrics from Agent 1 (list or DataFrame)
            test_statistics: Overall test statistics from Agent 1
            difficulty_order: Optional pre-computed difficulty order indices
            curve_breakers: Optional pre-identified curve-breaking question indices
            raw_student_data: Optional raw student scores (students x questions DataFrame)

        Returns:
            VisualizationOutput containing paths to Excel images and Plotly figures
        """
        logger.info("Starting visualization generation...")

        # Convert inputs to standard formats
        if isinstance(question_metrics, list):
            question_metrics_df = create_metrics_dataframe(question_metrics)
        else:
            question_metrics_df = question_metrics.copy()

        if isinstance(test_statistics, dict):
            test_statistics = self._dict_to_test_statistics(test_statistics)

        # Compute difficulty order if not provided
        if difficulty_order is None:
            difficulty_order = self._compute_difficulty_order(question_metrics_df)
            logger.info("Computed difficulty order from metrics")

        # Identify curve breakers if not provided
        if curve_breakers is None:
            curve_breakers = self._identify_curve_breakers(question_metrics_df, difficulty_order)
            logger.info(f"Identified {len(curve_breakers)} curve-breaking questions")

        # Update curve breaker flags in DataFrame
        question_metrics_df['is_curve_breaker'] = False
        for idx in curve_breakers:
            question_metrics_df.loc[idx, 'is_curve_breaker'] = True

        # Generate Excel static visualizations
        logger.info("Generating Excel static visualizations...")
        excel_images = self.excel_generator.generate_all(
            question_metrics_df,
            test_statistics,
            difficulty_order,
            curve_breakers,
        )
        logger.info(f"Generated {len(excel_images)} Excel images")

        # Generate Plotly interactive visualizations
        logger.info("Generating Plotly interactive visualizations...")
        plotly_figures = self.plotly_generator.generate_all(
            question_metrics_df,
            test_statistics,
            difficulty_order,
            curve_breakers,
            raw_student_data,
        )
        logger.info(f"Generated {len(plotly_figures)} Plotly figures")

        # Create output object
        output = VisualizationOutput(
            excel_images=excel_images,
            plotly_figures=plotly_figures,
        )

        # Validate output
        if not output.has_all_excel_images():
            logger.warning("Not all expected Excel images were generated")
        if not output.has_all_plotly_figures():
            logger.warning("Not all expected Plotly figures were generated")

        logger.info("Visualization generation complete!")

        return output

    def _compute_difficulty_order(self, df: pd.DataFrame) -> List[int]:
        """Compute the order of questions sorted by difficulty index.

        Args:
            df: Question metrics DataFrame

        Returns:
            List of DataFrame indices sorted by difficulty (easiest to hardest)
        """
        # Sort by difficulty index (descending = easiest first)
        sorted_indices = df['difficulty_index'].sort_values(ascending=False).index.tolist()
        return sorted_indices

    def _identify_curve_breakers(
        self,
        df: pd.DataFrame,
        difficulty_order: List[int],
    ) -> List[int]:
        """Identify questions that break the expected difficulty curve.

        Curve breakers are questions that don't follow the expected monotonic
        difficulty pattern and may indicate issues with question quality.

        Args:
            df: Question metrics DataFrame
            difficulty_order: Indices sorted by difficulty

        Returns:
            List of indices for curve-breaking questions
        """
        curve_breakers = []

        # Get sorted difficulties
        sorted_difficulties = df.loc[difficulty_order, 'difficulty_index'].values

        # Check for deviations from monotonic decrease
        for i in range(1, len(sorted_difficulties) - 1):
            # Check if this point breaks monotonicity significantly
            expected = (sorted_difficulties[i-1] + sorted_difficulties[i+1]) / 2
            actual = sorted_difficulties[i]

            # If deviation is more than 15% of range, flag as curve breaker
            deviation = abs(actual - expected)
            range_val = sorted_difficulties[0] - sorted_difficulties[-1]

            if range_val > 0 and (deviation / range_val) > 0.15:
                curve_breakers.append(difficulty_order[i])

        # Also flag questions with extreme difficulty (< 0.2 or > 0.9)
        for idx, row in df.iterrows():
            if row['difficulty_index'] < 0.2 or row['difficulty_index'] > 0.9:
                if idx not in curve_breakers:
                    curve_breakers.append(idx)

        # Flag questions with very low discrimination
        for idx, row in df.iterrows():
            if row['discrimination_index'] < 0.1:
                if idx not in curve_breakers:
                    curve_breakers.append(idx)

        return sorted(set(curve_breakers))

    def _dict_to_test_statistics(self, stats_dict: Dict[str, Any]) -> TestStatistics:
        """Convert a dictionary to TestStatistics object.

        Args:
            stats_dict: Dictionary with test statistics

        Returns:
            TestStatistics object
        """
        return TestStatistics(
            total_questions=stats_dict.get('total_questions', 0),
            total_students=stats_dict.get('total_students', 0),
            max_possible_score=stats_dict.get('max_possible_score', 100),
            mean_total_score=stats_dict.get('mean_total_score', 0),
            median_total_score=stats_dict.get('median_total_score', 0),
            std_dev_total_score=stats_dict.get('std_dev_total_score', 0),
            min_total_score=stats_dict.get('min_total_score', 0),
            max_total_score=stats_dict.get('max_total_score', 100),
            cronbach_alpha=stats_dict.get('cronbach_alpha', 0),
            sem=stats_dict.get('sem', 0),
            skewness=stats_dict.get('skewness', 0),
            kurtosis=stats_dict.get('kurtosis', 0),
            good_questions_count=stats_dict.get('good_questions_count', 0),
            review_questions_count=stats_dict.get('review_questions_count', 0),
            poor_questions_count=stats_dict.get('poor_questions_count', 0),
            upper_27_cutoff=stats_dict.get('upper_27_cutoff', 75),
            lower_27_cutoff=stats_dict.get('lower_27_cutoff', 25),
            student_total_scores=stats_dict.get('student_total_scores', None),
        )

    def save_plotly_html(
        self,
        output: VisualizationOutput,
        filename: str = "interactive_report.html",
    ) -> str:
        """Save all Plotly figures to a single HTML file.

        Args:
            output: VisualizationOutput from generate()
            filename: Name of the HTML file to create

        Returns:
            Path to the saved HTML file
        """
        from plotly.io import to_html

        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            '<meta charset="utf-8">',
            "<title>Test Evaluation Interactive Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }",
            ".chart-container { background: white; padding: 20px; margin: 20px 0; ",
            "  border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
            "h1 { color: #333; border-bottom: 3px solid #0072B2; padding-bottom: 10px; }",
            "h2 { color: #555; margin-top: 30px; }",
            ".description { color: #666; margin-bottom: 15px; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>Test Evaluation Interactive Report</h1>",
            '<p class="description">Generated by Visualization Generator Agent</p>',
        ]

        # Add each figure with descriptions
        figure_info = {
            'distribution': {
                'title': 'Student Score Distribution',
                'desc': 'Overall distribution of student total scores with key statistics.'
            },
            'difficulty_curve': {
                'title': 'Difficulty Curve Analysis',
                'desc': 'Question difficulty progression with outlier detection.'
            },
            'scatter': {
                'title': 'Discrimination vs. Difficulty',
                'desc': 'Item quality analysis based on psychometric properties.'
            },
            'weights': {
                'title': 'Weight Recommendations',
                'desc': 'Comparison of current vs. recommended question weights.'
            },
            'heatmap': {
                'title': 'Inter-Question Correlations',
                'desc': 'Correlation matrix to identify redundant questions.'
            },
            'question_details': {
                'title': 'Individual Question Analysis',
                'desc': 'Detailed score distributions and metrics for each question.'
            },
        }

        for key, info in figure_info.items():
            if key in output.plotly_figures:
                html_parts.append('<div class="chart-container">')
                html_parts.append(f'<h2>{info["title"]}</h2>')
                html_parts.append(f'<p class="description">{info["desc"]}</p>')
                html_parts.append(
                    to_html(
                        output.plotly_figures[key],
                        full_html=False,
                        include_plotlyjs='cdn' if key == 'distribution' else False
                    )
                )
                html_parts.append('</div>')

        html_parts.extend([
            "</body>",
            "</html>",
        ])

        # Save to file
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_parts))

        logger.info(f"Saved interactive HTML report to {filepath}")

        return str(filepath)

    def get_summary(self, output: VisualizationOutput) -> Dict[str, Any]:
        """Get a summary of the generated visualizations.

        Args:
            output: VisualizationOutput from generate()

        Returns:
            Dictionary with summary information
        """
        return {
            'excel_images_generated': len(output.excel_images),
            'excel_image_paths': output.excel_images,
            'plotly_figures_generated': len(output.plotly_figures),
            'plotly_figure_types': list(output.plotly_figures.keys()),
            'all_excel_complete': output.has_all_excel_images(),
            'all_plotly_complete': output.has_all_plotly_figures(),
        }
