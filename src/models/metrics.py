"""Data models for test evaluation metrics and visualization outputs."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


class QualityCategory(Enum):
    """Quality classification for test questions."""
    GOOD = "good"
    REVIEW = "review"
    POOR = "poor"


@dataclass
class QuestionMetrics:
    """Metrics for a single test question.

    This represents the output from Agent 1 (Metrics Calculator) for each question.
    """
    question_id: str
    question_number: int

    # Basic statistics
    mean_score: float
    median_score: float
    std_dev: float
    min_score: float
    max_score: float

    # Item analysis metrics
    difficulty_index: float  # P-value: proportion correct (0-1)
    discrimination_index: float  # Point-biserial correlation or upper-lower 27%

    # Weight information
    current_weight: float
    recommended_weight: float
    max_possible_score: float

    # Quality assessment
    quality_category: QualityCategory
    is_curve_breaker: bool = False
    quality_notes: List[str] = field(default_factory=list)

    # Raw score distribution (for histograms)
    score_distribution: Optional[np.ndarray] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DataFrame creation."""
        return {
            'question_id': self.question_id,
            'question_number': self.question_number,
            'mean_score': self.mean_score,
            'median_score': self.median_score,
            'std_dev': self.std_dev,
            'min_score': self.min_score,
            'max_score': self.max_score,
            'difficulty_index': self.difficulty_index,
            'discrimination_index': self.discrimination_index,
            'current_weight': self.current_weight,
            'recommended_weight': self.recommended_weight,
            'max_possible_score': self.max_possible_score,
            'quality_category': self.quality_category.value,
            'is_curve_breaker': self.is_curve_breaker,
            'quality_notes': '; '.join(self.quality_notes),
        }


@dataclass
class TestStatistics:
    """Overall test statistics from Agent 1.

    Contains aggregate metrics for the entire test.
    """
    # Basic test info
    total_questions: int
    total_students: int
    max_possible_score: float

    # Score statistics
    mean_total_score: float
    median_total_score: float
    std_dev_total_score: float
    min_total_score: float
    max_total_score: float

    # Reliability
    cronbach_alpha: float
    sem: float  # Standard Error of Measurement

    # Distribution characteristics
    skewness: float
    kurtosis: float

    # Quality summary
    good_questions_count: int
    review_questions_count: int
    poor_questions_count: int

    # Percentile cutoffs
    upper_27_cutoff: float  # Score threshold for upper 27%
    lower_27_cutoff: float  # Score threshold for lower 27%

    # Student total scores (for distribution plot)
    student_total_scores: Optional[np.ndarray] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_questions': self.total_questions,
            'total_students': self.total_students,
            'max_possible_score': self.max_possible_score,
            'mean_total_score': self.mean_total_score,
            'median_total_score': self.median_total_score,
            'std_dev_total_score': self.std_dev_total_score,
            'min_total_score': self.min_total_score,
            'max_total_score': self.max_total_score,
            'cronbach_alpha': self.cronbach_alpha,
            'sem': self.sem,
            'skewness': self.skewness,
            'kurtosis': self.kurtosis,
            'good_questions_count': self.good_questions_count,
            'review_questions_count': self.review_questions_count,
            'poor_questions_count': self.poor_questions_count,
            'upper_27_cutoff': self.upper_27_cutoff,
            'lower_27_cutoff': self.lower_27_cutoff,
        }


@dataclass
class VisualizationOutput:
    """Output from the Visualization Generator agent.

    Contains paths to static images for Excel and Plotly figure objects for HTML.
    """
    # Excel static images (PNG paths)
    excel_images: Dict[str, str] = field(default_factory=dict)
    # Expected keys:
    # - 'difficulty_curve': path to difficulty curve plot
    # - 'scatter': path to discrimination vs difficulty scatter
    # - 'weights': path to weight comparison bar chart
    # - 'quality': path to quality distribution chart

    # Plotly interactive figures (figure objects)
    plotly_figures: Dict[str, Any] = field(default_factory=dict)
    # Expected keys:
    # - 'question_details': individual question analysis
    # - 'difficulty_curve': interactive difficulty curve
    # - 'scatter': interactive discrimination-difficulty scatter
    # - 'weights': interactive weight comparison
    # - 'heatmap': inter-question correlation matrix
    # - 'distribution': student score distribution

    def get_all_image_paths(self) -> List[str]:
        """Get list of all generated image file paths."""
        return list(self.excel_images.values())

    def has_all_excel_images(self) -> bool:
        """Check if all required Excel images are generated."""
        required = {'difficulty_curve', 'scatter', 'weights', 'quality'}
        return required.issubset(set(self.excel_images.keys()))

    def has_all_plotly_figures(self) -> bool:
        """Check if all required Plotly figures are generated."""
        required = {
            'question_details', 'difficulty_curve', 'scatter',
            'weights', 'heatmap', 'distribution'
        }
        return required.issubset(set(self.plotly_figures.keys()))


def create_metrics_dataframe(question_metrics: List[QuestionMetrics]) -> pd.DataFrame:
    """Convert list of QuestionMetrics to a pandas DataFrame.

    Args:
        question_metrics: List of QuestionMetrics objects from Agent 1

    Returns:
        DataFrame with one row per question and columns for all metrics
    """
    data = [qm.to_dict() for qm in question_metrics]
    df = pd.DataFrame(data)

    # Ensure proper ordering
    df = df.sort_values('question_number').reset_index(drop=True)

    return df
