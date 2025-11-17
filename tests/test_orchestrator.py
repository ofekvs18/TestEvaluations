"""Unit tests for Test Analysis Orchestrator."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from test_analysis.orchestrator import TestAnalysisOrchestrator
from test_analysis.data_loader import (
    load_excel_file,
    validate_data_structure,
    parse_student_data,
    calculate_basic_statistics,
    infer_max_points
)


@pytest.fixture
def sample_excel_file():
    """Create a temporary Excel file for testing."""
    df = pd.DataFrame({
        'Student_ID': ['S001', 'S002', 'S003', 'S004', 'S005',
                       'S006', 'S007', 'S008', 'S009', 'S010'],
        'Q1': [10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
        'Q2': [10, 10, 10, 10, 5, 5, 5, 5, 0, 0],
        'Q3': [8, 7, 9, 6, 7, 8, 5, 6, 7, 8],
        'Q4': [10, 8, 9, 7, 6, 8, 5, 4, 3, 2],
        'Q5': [5, 8, 3, 10, 7, 2, 9, 1, 6, 4]
    })

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        temp_path = f.name

    df.to_excel(temp_path, index=False, engine='openpyxl')

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def output_dir():
    """Create temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestDataLoader:
    """Test data loading utilities."""

    def test_load_excel_file_success(self, sample_excel_file):
        """Test successful Excel file loading."""
        df = load_excel_file(sample_excel_file)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10
        assert len(df.columns) == 6

    def test_load_excel_file_not_found(self):
        """Test loading non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_excel_file("nonexistent.xlsx")

    def test_load_excel_file_invalid_format(self, sample_excel_file):
        """Test loading file with wrong extension."""
        # Create a file with wrong extension
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"not an excel file")
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                load_excel_file(temp_path)
        finally:
            os.unlink(temp_path)

    def test_validate_data_structure_valid(self, sample_excel_file):
        """Test validation of valid data structure."""
        df = load_excel_file(sample_excel_file)
        is_valid, message = validate_data_structure(df)
        assert is_valid is True

    def test_validate_data_structure_empty(self):
        """Test validation of empty DataFrame."""
        df = pd.DataFrame()
        is_valid, message = validate_data_structure(df)
        assert is_valid is False

    def test_validate_data_structure_single_column(self):
        """Test validation with only one column."""
        df = pd.DataFrame({'Student_ID': ['S1', 'S2']})
        is_valid, message = validate_data_structure(df)
        assert is_valid is False

    def test_parse_student_data(self, sample_excel_file):
        """Test parsing student data."""
        raw_df = load_excel_file(sample_excel_file)
        scores_df, student_ids, question_names = parse_student_data(raw_df)

        assert isinstance(scores_df, pd.DataFrame)
        assert isinstance(student_ids, pd.Series)
        assert isinstance(question_names, list)

        # Should have 10 students
        assert len(scores_df) == 10
        assert len(student_ids) == 10

        # Should have 5 questions (excluding student ID)
        assert len(scores_df.columns) == 5

        # No NaN values after parsing
        assert scores_df.isnull().sum().sum() == 0

    def test_calculate_basic_statistics(self):
        """Test basic statistics calculation."""
        df = pd.DataFrame({
            'Q1': [10, 8, 6, 4, 2],
            'Q2': [5, 5, 5, 5, 5]
        })

        stats = calculate_basic_statistics(df)

        assert stats['student_count'] == 5
        assert stats['question_count'] == 2
        assert 'mean_total_score' in stats
        assert 'std_total_score' in stats
        assert 'max_points_per_question' in stats

    def test_infer_max_points_default(self):
        """Test inferring max points from data."""
        df = pd.DataFrame({
            'Q1': [10, 8, 6, 4, 2],
            'Q2': [5, 4, 3, 2, 1]
        })

        max_pts = infer_max_points(df)

        assert max_pts['Q1'] == 10
        assert max_pts['Q2'] == 5

    def test_infer_max_points_provided(self):
        """Test using provided max points."""
        df = pd.DataFrame({
            'Q1': [10, 8, 6, 4, 2],
            'Q2': [5, 4, 3, 2, 1]
        })

        provided = {'Q1': 15, 'Q2': 10}
        max_pts = infer_max_points(df, provided)

        assert max_pts == provided


class TestOrchestratorInitialization:
    """Test orchestrator initialization."""

    def test_initialization(self, sample_excel_file):
        """Test proper initialization."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file)

        assert orchestrator.excel_file_path == sample_excel_file
        assert orchestrator.current_weights == {}
        assert orchestrator.provided_max_points is None
        assert orchestrator.config == {}

        assert orchestrator.status['data_loaded'] is False
        assert orchestrator.status['data_validated'] is False
        assert orchestrator.status['data_parsed'] is False

    def test_initialization_with_weights(self, sample_excel_file):
        """Test initialization with provided weights."""
        weights = {'Q1': 2.0, 'Q2': 1.5}
        orchestrator = TestAnalysisOrchestrator(
            sample_excel_file,
            current_weights=weights
        )

        assert orchestrator.current_weights == weights

    def test_initialization_with_config(self, sample_excel_file):
        """Test initialization with configuration."""
        config = {
            'metrics': {'upper_lower_percent': 0.3},
            'visualization': {'figure_dpi': 150}
        }
        orchestrator = TestAnalysisOrchestrator(
            sample_excel_file,
            config=config
        )

        assert orchestrator.config == config


class TestOrchestratorDataLoading:
    """Test orchestrator data loading functionality."""

    def test_load_and_validate_data_success(self, sample_excel_file):
        """Test successful data loading and validation."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file)
        result = orchestrator.load_and_validate_data()

        assert result is True
        assert orchestrator.status['data_loaded'] is True
        assert orchestrator.status['data_validated'] is True
        assert orchestrator.status['data_parsed'] is True

        assert orchestrator.scores_df is not None
        assert orchestrator.student_ids is not None
        assert orchestrator.question_names is not None
        assert orchestrator.max_points is not None
        assert orchestrator.basic_stats is not None

    def test_load_and_validate_data_failure(self):
        """Test failed data loading."""
        orchestrator = TestAnalysisOrchestrator("nonexistent.xlsx")
        result = orchestrator.load_and_validate_data()

        assert result is False
        assert orchestrator.status['data_loaded'] is False

    def test_basic_stats_after_loading(self, sample_excel_file):
        """Test that basic statistics are calculated after loading."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file)
        orchestrator.load_and_validate_data()

        stats = orchestrator.basic_stats

        assert stats['student_count'] == 10
        assert stats['question_count'] == 5
        assert 'mean_total_score' in stats
        assert stats['mean_total_score'] > 0

    def test_default_weights_set(self, sample_excel_file):
        """Test that default weights are set after loading."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file)
        orchestrator.load_and_validate_data()

        # Should have weights for all questions
        assert len(orchestrator.current_weights) == 5
        # All default to 1.0
        assert all(w == 1.0 for w in orchestrator.current_weights.values())


class TestOrchestratorAgentExecution:
    """Test agent execution functionality."""

    def test_run_agents_parallel(self, sample_excel_file):
        """Test parallel agent execution."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file)
        orchestrator.load_and_validate_data()

        result = orchestrator.run_agents_parallel()

        assert result is True
        assert orchestrator.status['agents_completed']['metrics'] is True
        assert orchestrator.status['agents_completed']['visualization'] is True
        assert orchestrator.status['agents_completed']['recommendations'] is True

        assert orchestrator.metrics_results is not None
        assert orchestrator.visualization_results is not None
        assert orchestrator.recommendation_results is not None

    def test_metrics_results_structure(self, sample_excel_file):
        """Test that metrics results have correct structure."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file)
        orchestrator.load_and_validate_data()
        orchestrator.run_agents_parallel()

        metrics = orchestrator.metrics_results

        assert 'question_metrics' in metrics
        assert 'quality_flags' in metrics
        assert 'difficulty_order' in metrics
        assert 'curve_breakers' in metrics
        assert 'test_statistics' in metrics
        assert 'upper_lower_groups' in metrics

    def test_run_agents_before_data_load(self, sample_excel_file):
        """Test that agents can't run before data is loaded."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file)
        # Don't load data first

        result = orchestrator.run_agents_parallel()
        assert result is False


class TestOrchestratorOutputGeneration:
    """Test output generation functionality."""

    def test_generate_excel_output(self, sample_excel_file, output_dir):
        """Test Excel output generation."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file)
        orchestrator.load_and_validate_data()
        orchestrator.run_agents_parallel()

        output_path = os.path.join(output_dir, "test_output.xlsx")
        result = orchestrator.generate_excel_output(output_path)

        assert result is True
        assert os.path.exists(output_path)

        # Verify file can be read back
        xl = pd.ExcelFile(output_path)
        assert 'Raw_Scores' in xl.sheet_names
        assert 'Question_Metrics' in xl.sheet_names
        assert 'Test_Statistics' in xl.sheet_names

    def test_generate_html_report(self, sample_excel_file, output_dir):
        """Test HTML report generation."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file)
        orchestrator.load_and_validate_data()
        orchestrator.run_agents_parallel()

        output_path = os.path.join(output_dir, "test_report.html")
        result = orchestrator.generate_html_report(output_path)

        assert result is True
        assert os.path.exists(output_path)

        # Verify it's valid HTML
        with open(output_path, 'r') as f:
            content = f.read()
            assert '<!DOCTYPE html>' in content
            assert '<html>' in content
            assert 'Test Analysis Report' in content

    def test_generate_summary_text(self, sample_excel_file):
        """Test summary text generation."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file)
        orchestrator.load_and_validate_data()
        orchestrator.run_agents_parallel()

        summary = orchestrator.generate_summary_text()

        assert isinstance(summary, str)
        assert 'TEST ANALYSIS SUMMARY REPORT' in summary
        assert 'Total Students:' in summary
        assert 'Total Questions:' in summary
        assert "Cronbach's Alpha:" in summary

    def test_output_before_agents_complete(self, sample_excel_file, output_dir):
        """Test that output can't be generated before agents complete."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file)
        orchestrator.load_and_validate_data()
        # Don't run agents

        output_path = os.path.join(output_dir, "test_output.xlsx")
        result = orchestrator.generate_excel_output(output_path)

        assert result is False


class TestOrchestratorCompleteRun:
    """Test complete orchestrator run."""

    def test_complete_run(self, sample_excel_file, output_dir):
        """Test complete analysis pipeline."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file)
        results = orchestrator.run(output_dir)

        assert results['success'] is True
        assert 'basic_stats' in results
        assert 'metrics_results' in results
        assert 'visualization_results' in results
        assert 'recommendation_results' in results
        assert 'output_files' in results

        # Verify all output files were created
        for file_type, path in results['output_files'].items():
            assert os.path.exists(path), f"{file_type} file not created"

    def test_complete_run_with_custom_weights(self, sample_excel_file, output_dir):
        """Test complete run with custom weights."""
        weights = {'Q1': 2.0, 'Q2': 1.5, 'Q3': 1.0, 'Q4': 1.0, 'Q5': 0.5}
        orchestrator = TestAnalysisOrchestrator(
            sample_excel_file,
            current_weights=weights
        )
        results = orchestrator.run(output_dir)

        assert results['success'] is True

    def test_complete_run_creates_output_directory(self, sample_excel_file):
        """Test that output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_output_dir = os.path.join(tmpdir, "new_dir", "nested")

            orchestrator = TestAnalysisOrchestrator(sample_excel_file)
            results = orchestrator.run(new_output_dir)

            assert results['success'] is True
            assert os.path.exists(new_output_dir)

    def test_status_tracking(self, sample_excel_file, output_dir):
        """Test that status is properly tracked throughout pipeline."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file)
        results = orchestrator.run(output_dir)

        status = results['status']
        assert status['data_loaded'] is True
        assert status['data_validated'] is True
        assert status['data_parsed'] is True
        assert status['agents_completed']['metrics'] is True
        assert status['agents_completed']['visualization'] is True
        assert status['agents_completed']['recommendations'] is True
        assert status['output_generated'] is True
