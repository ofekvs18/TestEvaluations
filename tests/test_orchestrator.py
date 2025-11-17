"""Unit tests for the consolidated Test Analysis Orchestrator."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from orchestrator import TestAnalysisOrchestrator, DataLoader


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
def sample_csv_file():
    """Create a temporary CSV file for testing."""
    df = pd.DataFrame({
        'Student_ID': ['S001', 'S002', 'S003', 'S004', 'S005'],
        'Q1': [10, 8, 6, 4, 2],
        'Q2': [5, 5, 5, 5, 5],
        'Q3': [8, 6, 4, 2, 0]
    })

    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w') as f:
        temp_path = f.name

    df.to_csv(temp_path, index=False)

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
        df = DataLoader.load_file(Path(sample_excel_file))
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10
        assert len(df.columns) == 6

    def test_load_csv_file_success(self, sample_csv_file):
        """Test successful CSV file loading."""
        df = DataLoader.load_file(Path(sample_csv_file))
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
        assert len(df.columns) == 4

    def test_load_file_not_found(self):
        """Test loading non-existent file."""
        with pytest.raises(FileNotFoundError):
            DataLoader.load_file(Path("nonexistent.xlsx"))

    def test_load_file_invalid_format(self):
        """Test loading file with unsupported extension."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"not a valid file")
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                DataLoader.load_file(Path(temp_path))
        finally:
            os.unlink(temp_path)

    def test_validate_structure_valid(self, sample_excel_file):
        """Test validation of valid data structure."""
        df = DataLoader.load_file(Path(sample_excel_file))
        is_valid, message = DataLoader.validate_structure(df)
        assert is_valid is True
        assert "valid" in message.lower()

    def test_validate_structure_empty(self):
        """Test validation of empty DataFrame."""
        df = pd.DataFrame()
        is_valid, message = DataLoader.validate_structure(df)
        assert is_valid is False
        assert "empty" in message.lower()

    def test_validate_structure_single_column(self):
        """Test validation with only one column."""
        df = pd.DataFrame({'Student_ID': ['S1', 'S2']})
        is_valid, message = DataLoader.validate_structure(df)
        assert is_valid is False

    def test_validate_structure_no_numeric_columns(self):
        """Test validation with no numeric columns."""
        df = pd.DataFrame({
            'Student_ID': ['S1', 'S2'],
            'Name': ['Alice', 'Bob']
        })
        is_valid, message = DataLoader.validate_structure(df)
        assert is_valid is False
        assert "numeric" in message.lower()

    def test_parse_student_data(self, sample_excel_file):
        """Test parsing student data."""
        raw_df = DataLoader.load_file(Path(sample_excel_file))
        cleaned_df = DataLoader.parse_student_data(raw_df)

        assert isinstance(cleaned_df, pd.DataFrame)
        # Should have 10 students
        assert len(cleaned_df) == 10
        # Should have 6 columns (student ID + 5 questions)
        assert len(cleaned_df.columns) == 6
        # No NaN values after parsing
        assert cleaned_df.isnull().sum().sum() == 0

    def test_parse_student_data_renames_columns(self):
        """Test that non-standard column names are renamed."""
        df = pd.DataFrame({
            'Student': ['S1', 'S2'],
            1: [10, 8],
            2: [5, 5]
        })
        cleaned_df = DataLoader.parse_student_data(df)

        # Numeric columns should be renamed to Q1, Q2
        assert 'Q1' in cleaned_df.columns
        assert 'Q2' in cleaned_df.columns

    def test_parse_student_data_fills_nan(self):
        """Test that NaN values are filled with 0."""
        df = pd.DataFrame({
            'Student': ['S1', 'S2'],
            'Q1': [10, np.nan],
            'Q2': [np.nan, 5]
        })
        cleaned_df = DataLoader.parse_student_data(df)

        assert cleaned_df.isnull().sum().sum() == 0
        assert cleaned_df.loc[1, 'Q1'] == 0
        assert cleaned_df.loc[0, 'Q2'] == 0

    def test_calculate_basic_statistics(self):
        """Test basic statistics calculation."""
        df = pd.DataFrame({
            'Student': ['S1', 'S2', 'S3', 'S4', 'S5'],
            'Q1': [10, 8, 6, 4, 2],
            'Q2': [5, 5, 5, 5, 5]
        })

        stats = DataLoader.calculate_basic_statistics(df)

        assert stats['student_count'] == 5
        assert stats['question_count'] == 2
        assert 'mean_total_score' in stats
        assert 'std_total_score' in stats
        assert 'min_total_score' in stats
        assert 'max_total_score' in stats
        assert 'median_total_score' in stats
        assert 'max_points_per_question' in stats

        # Verify calculations
        assert stats['max_points_per_question']['Q1'] == 10
        assert stats['max_points_per_question']['Q2'] == 5

    def test_calculate_basic_statistics_values(self):
        """Test that basic statistics are calculated correctly."""
        df = pd.DataFrame({
            'Student': ['S1', 'S2', 'S3'],
            'Q1': [10, 10, 10],
            'Q2': [5, 5, 5]
        })

        stats = DataLoader.calculate_basic_statistics(df)

        # All students have same score: 15
        assert stats['mean_total_score'] == 15.0
        assert stats['std_total_score'] == 0.0
        assert stats['min_total_score'] == 15.0
        assert stats['max_total_score'] == 15.0


class TestOrchestratorInitialization:
    """Test orchestrator initialization."""

    def test_initialization(self, sample_excel_file):
        """Test proper initialization."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file)

        assert orchestrator.data_path == Path(sample_excel_file)
        assert orchestrator.weights_path is None
        assert orchestrator.output_dir == Path("results")

        assert orchestrator.status['data_loaded'] is False
        assert orchestrator.status['data_validated'] is False
        assert orchestrator.status['data_parsed'] is False

    def test_initialization_with_weights_path(self, sample_excel_file):
        """Test initialization with weights file path."""
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            weights_path = f.name
            pd.DataFrame({'Q1': [1.5], 'Q2': [2.0]}).to_csv(weights_path, index=False)

        try:
            orchestrator = TestAnalysisOrchestrator(
                sample_excel_file,
                weights_path=weights_path
            )
            assert orchestrator.weights_path == Path(weights_path)
        finally:
            os.unlink(weights_path)

    def test_initialization_with_custom_output_dir(self, sample_excel_file):
        """Test initialization with custom output directory."""
        orchestrator = TestAnalysisOrchestrator(
            sample_excel_file,
            output_dir="/custom/output"
        )
        assert orchestrator.output_dir == Path("/custom/output")


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
        assert orchestrator.status['basic_stats_calculated'] is True

        assert orchestrator.raw_data is not None
        assert orchestrator.cleaned_data is not None
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

    def test_timestamp_set_after_loading(self, sample_excel_file):
        """Test that timestamp is set after loading."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file)
        orchestrator.load_and_validate_data()

        assert orchestrator.timestamps['data_ready'] is not None


class TestOrchestratorAgentExecution:
    """Test agent execution functionality."""

    def test_run_agents_parallel(self, sample_excel_file):
        """Test parallel agent execution."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file)
        orchestrator.load_and_validate_data()

        result = orchestrator.run_agents(parallel=True)

        assert result is True
        assert orchestrator.status['agents_completed']['metrics'] is True
        assert orchestrator.status['agents_completed']['visualization'] is True
        assert orchestrator.status['agents_completed']['recommendations'] is True

        assert orchestrator.metrics_results is not None
        assert orchestrator.visualization_results is not None
        assert orchestrator.recommendation_results is not None

    def test_run_agents_sequential(self, sample_excel_file):
        """Test sequential agent execution."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file)
        orchestrator.load_and_validate_data()

        result = orchestrator.run_agents(parallel=False)

        assert result is True
        assert orchestrator.status['agents_completed']['metrics'] is True
        assert orchestrator.status['agents_completed']['visualization'] is True
        assert orchestrator.status['agents_completed']['recommendations'] is True

    def test_metrics_results_structure(self, sample_excel_file):
        """Test that metrics results have correct structure."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file)
        orchestrator.load_and_validate_data()
        orchestrator.run_agents()

        metrics = orchestrator.metrics_results

        assert 'test_statistics' in metrics
        assert 'question_metrics' in metrics

        # Test statistics should have expected fields
        test_stats = metrics['test_statistics']
        assert 'total_students' in test_stats
        assert 'total_questions' in test_stats
        assert 'mean_score' in test_stats
        assert 'cronbach_alpha' in test_stats

    def test_visualization_results_structure(self, sample_excel_file):
        """Test that visualization results have correct structure."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file)
        orchestrator.load_and_validate_data()
        orchestrator.run_agents()

        viz = orchestrator.visualization_results

        assert 'plotly_figures' in viz
        assert 'static_images' in viz

    def test_recommendation_results_structure(self, sample_excel_file):
        """Test that recommendation results have correct structure."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file)
        orchestrator.load_and_validate_data()
        orchestrator.run_agents()

        rec = orchestrator.recommendation_results

        assert 'question_analysis' in rec
        assert 'recommendations' in rec
        assert 'key_insights' in rec
        assert 'quality_distribution' in rec

    def test_run_agents_before_data_load(self, sample_excel_file):
        """Test that agents can't run before data is loaded."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file)
        # Don't load data first

        result = orchestrator.run_agents()
        assert result is False

    def test_timestamp_set_after_agents(self, sample_excel_file):
        """Test that timestamp is set after agents complete."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file)
        orchestrator.load_and_validate_data()
        orchestrator.run_agents()

        assert orchestrator.timestamps['agents_done'] is not None


class TestOrchestratorAssembly:
    """Test assembly and output generation."""

    def test_assemble_final_outputs(self, sample_excel_file, output_dir):
        """Test final output assembly."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file, output_dir=output_dir)
        orchestrator.load_and_validate_data()
        orchestrator.run_agents()

        result = orchestrator.assemble_final_outputs()

        assert result['status'] == 'success'
        assert 'files' in result
        assert orchestrator.status['assembly_completed'] is True

    def test_assemble_creates_files(self, sample_excel_file, output_dir):
        """Test that assembly creates all expected files."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file, output_dir=output_dir)
        orchestrator.load_and_validate_data()
        orchestrator.run_agents()

        result = orchestrator.assemble_final_outputs()

        files = result['files']
        assert 'excel' in files
        assert 'html' in files
        assert 'summary' in files

        # Verify files exist
        assert os.path.exists(files['excel'])
        assert os.path.exists(files['html'])
        assert os.path.exists(files['summary'])

    def test_assemble_before_agents_complete(self, sample_excel_file, output_dir):
        """Test that assembly fails before agents complete."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file, output_dir=output_dir)
        orchestrator.load_and_validate_data()
        # Don't run agents

        result = orchestrator.assemble_final_outputs()

        assert result['status'] == 'error'

    def test_timestamp_set_after_assembly(self, sample_excel_file, output_dir):
        """Test that timestamp is set after assembly."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file, output_dir=output_dir)
        orchestrator.load_and_validate_data()
        orchestrator.run_agents()
        orchestrator.assemble_final_outputs()

        assert orchestrator.timestamps['assembly_done'] is not None


class TestOrchestratorCompleteRun:
    """Test complete orchestrator run."""

    def test_complete_run(self, sample_excel_file, output_dir):
        """Test complete analysis pipeline."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file, output_dir=output_dir)
        results = orchestrator.run()

        assert results['success'] is True
        assert 'basic_stats' in results
        assert 'metrics_results' in results
        assert 'visualization_results' in results
        assert 'recommendation_results' in results
        assert 'output_files' in results
        assert 'execution_time_seconds' in results

        # Verify all output files were created
        for file_type, path in results['output_files'].items():
            assert os.path.exists(path), f"{file_type} file not created"

    def test_complete_run_with_csv(self, sample_csv_file, output_dir):
        """Test complete run with CSV input."""
        orchestrator = TestAnalysisOrchestrator(sample_csv_file, output_dir=output_dir)
        results = orchestrator.run()

        assert results['success'] is True

    def test_complete_run_creates_output_directory(self, sample_excel_file):
        """Test that output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_output_dir = os.path.join(tmpdir, "new_dir", "nested")

            orchestrator = TestAnalysisOrchestrator(
                sample_excel_file,
                output_dir=new_output_dir
            )
            results = orchestrator.run()

            assert results['success'] is True
            assert os.path.exists(new_output_dir)

    def test_complete_run_parallel_vs_sequential(self, sample_excel_file, output_dir):
        """Test that parallel and sequential runs produce same status."""
        orchestrator1 = TestAnalysisOrchestrator(sample_excel_file, output_dir=output_dir)
        results1 = orchestrator1.run(parallel=True)

        with tempfile.TemporaryDirectory() as tmpdir2:
            orchestrator2 = TestAnalysisOrchestrator(sample_excel_file, output_dir=tmpdir2)
            results2 = orchestrator2.run(parallel=False)

        assert results1['success'] == results2['success']
        assert results1['status'] == results2['status']

    def test_status_tracking(self, sample_excel_file, output_dir):
        """Test that status is properly tracked throughout pipeline."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file, output_dir=output_dir)
        results = orchestrator.run()

        status = results['status']
        assert status['data_loaded'] is True
        assert status['data_validated'] is True
        assert status['data_parsed'] is True
        assert status['basic_stats_calculated'] is True
        assert status['agents_completed']['metrics'] is True
        assert status['agents_completed']['visualization'] is True
        assert status['agents_completed']['recommendations'] is True
        assert status['assembly_completed'] is True

    def test_timestamps_all_recorded(self, sample_excel_file, output_dir):
        """Test that all timestamps are recorded."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file, output_dir=output_dir)
        results = orchestrator.run()

        timestamps = results['timestamps']
        assert timestamps['start'] is not None
        assert timestamps['data_ready'] is not None
        assert timestamps['agents_done'] is not None
        assert timestamps['assembly_done'] is not None

    def test_execution_time_calculation(self, sample_excel_file, output_dir):
        """Test that execution time is calculated."""
        orchestrator = TestAnalysisOrchestrator(sample_excel_file, output_dir=output_dir)
        results = orchestrator.run()

        assert results['execution_time_seconds'] > 0
        assert isinstance(results['execution_time_seconds'], float)


class TestOrchestratorEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_data_handling(self):
        """Test handling of empty or near-empty data."""
        df = pd.DataFrame({
            'Student': ['S1'],
            'Q1': [10]
        })

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            temp_path = f.name

        df.to_excel(temp_path, index=False)

        try:
            orchestrator = TestAnalysisOrchestrator(temp_path)
            result = orchestrator.load_and_validate_data()
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_all_zeros_data(self):
        """Test handling of data with all zeros."""
        df = pd.DataFrame({
            'Student': ['S1', 'S2'],
            'Q1': [0, 0],
            'Q2': [0, 0]
        })

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            temp_path = f.name

        df.to_excel(temp_path, index=False)

        try:
            with tempfile.TemporaryDirectory() as output_dir:
                orchestrator = TestAnalysisOrchestrator(temp_path, output_dir=output_dir)
                results = orchestrator.run()
                # Should still succeed even with zeros
                assert results['success'] is True
        finally:
            os.unlink(temp_path)

    def test_large_number_of_questions(self):
        """Test handling of many questions."""
        # Create data with 50 questions
        data = {'Student': [f'S{i}' for i in range(10)]}
        for q in range(50):
            data[f'Q{q+1}'] = np.random.randint(0, 11, 10)

        df = pd.DataFrame(data)

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            temp_path = f.name

        df.to_excel(temp_path, index=False)

        try:
            orchestrator = TestAnalysisOrchestrator(temp_path)
            result = orchestrator.load_and_validate_data()
            assert result is True
            assert orchestrator.basic_stats['question_count'] == 50
        finally:
            os.unlink(temp_path)
