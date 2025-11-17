"""Data loading and validation utilities for test analysis."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any


def load_excel_file(file_path: str) -> pd.DataFrame:
    """Load an Excel file containing student test performance data.

    Args:
        file_path: Path to the Excel file.

    Returns:
        DataFrame with student performance data.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the file format is invalid.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    if not path.suffix.lower() in ['.xlsx', '.xls']:
        raise ValueError(f"Invalid file format. Expected .xlsx or .xls, got {path.suffix}")

    try:
        df = pd.read_excel(file_path, engine='openpyxl' if path.suffix == '.xlsx' else 'xlrd')
    except Exception as e:
        raise ValueError(f"Failed to read Excel file: {e}")

    return df


def validate_data_structure(df: pd.DataFrame) -> Tuple[bool, str]:
    """Validate the structure of student performance data.

    Expected structure:
    - First column: Student ID or Name
    - Remaining columns: Question scores (Q1, Q2, ... or numeric headers)

    Args:
        df: Input DataFrame to validate.

    Returns:
        Tuple of (is_valid, message).
    """
    if df.empty:
        return False, "DataFrame is empty"

    if len(df.columns) < 2:
        return False, "DataFrame must have at least 2 columns (student ID + 1 question)"

    if df.isnull().all().any():
        return False, "Some columns contain only null values"

    # Check that numeric columns exist
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        return False, "No numeric columns found for question scores"

    return True, "Data structure is valid"


def parse_student_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, list]:
    """Parse raw data into clean student performance matrix.

    Args:
        df: Raw DataFrame from Excel file.

    Returns:
        Tuple of:
        - scores_df: DataFrame with students as rows, questions as columns (numeric only)
        - student_ids: Series of student identifiers
        - question_names: List of question column names
    """
    # Assume first column is student identifier
    student_ids = df.iloc[:, 0].astype(str)

    # Get all numeric columns (these are the question scores)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if not numeric_cols:
        # Try to convert remaining columns to numeric
        scores_df = df.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
        question_names = df.columns[1:].tolist()
    else:
        scores_df = df[numeric_cols].copy()
        question_names = numeric_cols

    # Rename columns to standard format if they're not already named
    if not all(isinstance(col, str) and col.startswith('Q') for col in question_names):
        new_names = [f"Q{i+1}" for i in range(len(question_names))]
        scores_df.columns = new_names
        question_names = new_names

    # Fill NaN with 0 (missing answers = 0 points)
    scores_df = scores_df.fillna(0)

    return scores_df, student_ids, question_names


def calculate_basic_statistics(scores_df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate basic statistics from the scores DataFrame.

    Args:
        scores_df: DataFrame with student scores (students × questions).

    Returns:
        Dictionary with basic statistics.
    """
    stats = {
        'student_count': len(scores_df),
        'question_count': len(scores_df.columns),
        'max_points_per_question': scores_df.max().to_dict(),
        'total_max_points': scores_df.max().sum(),
        'mean_total_score': scores_df.sum(axis=1).mean(),
        'std_total_score': scores_df.sum(axis=1).std(),
        'min_total_score': scores_df.sum(axis=1).min(),
        'max_total_score': scores_df.sum(axis=1).max(),
    }

    return stats


def infer_max_points(scores_df: pd.DataFrame,
                     provided_max: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    """Infer maximum points per question.

    Args:
        scores_df: DataFrame with student scores.
        provided_max: Optional dictionary of known max points.

    Returns:
        Dictionary mapping question names to max points.
    """
    if provided_max is not None:
        return provided_max

    # Infer from data - use the maximum observed score
    return scores_df.max().to_dict()
