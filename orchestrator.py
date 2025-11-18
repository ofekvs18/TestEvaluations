"""
Test Analysis Orchestrator - Main Coordinator

This is the primary orchestrator that coordinates the test analysis workflow:
1. Loads and validates input Excel/CSV data
2. Parses student performance data into a clean pandas DataFrame
3. Calculates basic statistics (max points, student count, etc.)
4. Dispatches work to three specialized agents running in parallel
5. Collects results from all agents
6. Combines outputs into final deliverables via Assembly Agent
"""

import argparse
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

import pandas as pd
import numpy as np

from agents.metrics_agent import MetricsAgent
from agents.visualization_agent import VisualizationAgent
from agents.recommendations_agent import RecommendationsAgent
from agents.assembly_agent import AssemblyAgent


class DataLoader:
    """Handles data loading, validation, and parsing."""

    @staticmethod
    def load_file(file_path: Path) -> pd.DataFrame:
        """Load data from Excel or CSV file.

        Args:
            file_path: Path to the input file

        Returns:
            DataFrame with raw data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is unsupported
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")

        suffix = file_path.suffix.lower()
        if suffix in ['.xlsx', '.xls']:
            return pd.read_excel(file_path, engine='openpyxl' if suffix == '.xlsx' else 'xlrd')
        elif suffix == '.csv':
            return pd.read_csv(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}. Expected .xlsx, .xls, or .csv")

    @staticmethod
    def validate_structure(df: pd.DataFrame) -> Tuple[bool, str]:
        """Validate the structure of student performance data.

        Expected structure:
        - First column: Student ID or Name
        - Remaining columns: Question scores (numeric)

        Args:
            df: Input DataFrame to validate

        Returns:
            Tuple of (is_valid, message)
        """
        if df.empty:
            return False, "DataFrame is empty"

        if len(df.columns) < 2:
            return False, "DataFrame must have at least 2 columns (student ID + 1 question)"

        if df.isnull().all().any():
            return False, "Some columns contain only null values"

        # Check that numeric columns exist (excluding first column)
        numeric_cols = df.iloc[:, 1:].select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            return False, "No numeric columns found for question scores"

        return True, "Data structure is valid"

    @staticmethod
    def parse_student_data(df: pd.DataFrame) -> pd.DataFrame:
        """Parse raw data into clean student performance matrix.

        Args:
            df: Raw DataFrame from file

        Returns:
            Cleaned DataFrame with student scores
        """
        # Make a copy to avoid modifying original
        cleaned_df = df.copy()

        # Standardize column names for questions
        if len(cleaned_df.columns) > 1:
            # Keep first column name, rename numeric columns to Q1, Q2, etc.
            first_col = cleaned_df.columns[0]
            question_cols = cleaned_df.columns[1:]

            new_col_names = {first_col: first_col}
            for i, col in enumerate(question_cols):
                if not (isinstance(col, str) and col.startswith('Q')):
                    new_col_names[col] = f"Q{i+1}"

            cleaned_df = cleaned_df.rename(columns=new_col_names)

        # Fill NaN values with 0 (missing = 0 points)
        cleaned_df = cleaned_df.fillna(0)

        # Ensure numeric columns are float
        for col in cleaned_df.columns[1:]:
            cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce').fillna(0)

        return cleaned_df

    @staticmethod
    def calculate_basic_statistics(df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic statistics from the data.

        Args:
            df: DataFrame with student scores

        Returns:
            Dictionary with basic statistics
        """
        # Assume first column is student ID, rest are questions
        scores = df.iloc[:, 1:].values
        total_scores = scores.sum(axis=1)

        stats = {
            'student_count': len(df),
            'question_count': len(df.columns) - 1,
            'max_points_per_question': {
                col: float(df[col].max()) for col in df.columns[1:]
            },
            'total_max_points': float(scores.max().sum()),
            'mean_total_score': float(np.mean(total_scores)),
            'std_total_score': float(np.std(total_scores)),
            'min_total_score': float(np.min(total_scores)),
            'max_total_score': float(np.max(total_scores)),
            'median_total_score': float(np.median(total_scores))
        }

        return stats


class TestAnalysisOrchestrator:
    """Main orchestrator that coordinates the entire test analysis pipeline."""

    def __init__(
        self,
        data_path: str,
        output_dir: str = "results"
    ):
        """Initialize the orchestrator.

        Question weights are automatically determined from the maximum score
        achieved by any student for each question in the answers data.

        Args:
            data_path: Path to input Excel/CSV data file
            output_dir: Directory for output files
        """
        self.data_path = Path(data_path)
        self.output_dir = Path(output_dir)

        # Data containers
        self.raw_data: Optional[pd.DataFrame] = None
        self.cleaned_data: Optional[pd.DataFrame] = None
        self.basic_stats: Optional[Dict[str, Any]] = None

        # Agent results
        self.metrics_results: Optional[Dict[str, Any]] = None
        self.visualization_results: Optional[Dict[str, Any]] = None
        self.recommendation_results: Optional[Dict[str, Any]] = None

        # Status tracking
        self.status = {
            'data_loaded': False,
            'data_validated': False,
            'data_parsed': False,
            'basic_stats_calculated': False,
            'agents_completed': {
                'metrics': False,
                'visualization': False,
                'recommendations': False
            },
            'assembly_completed': False
        }

        # Timestamps for tracking
        self.timestamps = {
            'start': None,
            'data_ready': None,
            'agents_done': None,
            'assembly_done': None
        }

    def load_and_validate_data(self) -> bool:
        """Load, validate, and parse input data.

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"Loading data from: {self.data_path}")

            # Step 1: Load raw data
            self.raw_data = DataLoader.load_file(self.data_path)
            self.status['data_loaded'] = True
            print(f"  ✓ Loaded {len(self.raw_data)} rows, {len(self.raw_data.columns)} columns")

            # Step 2: Validate structure
            is_valid, message = DataLoader.validate_structure(self.raw_data)
            if not is_valid:
                raise ValueError(f"Data validation failed: {message}")
            self.status['data_validated'] = True
            print(f"  ✓ Data structure validated: {message}")

            # Step 3: Parse and clean data
            self.cleaned_data = DataLoader.parse_student_data(self.raw_data)
            self.status['data_parsed'] = True
            print(f"  ✓ Data cleaned and standardized")

            # Step 4: Calculate basic statistics
            self.basic_stats = DataLoader.calculate_basic_statistics(self.cleaned_data)
            self.status['basic_stats_calculated'] = True

            print(f"\nBasic Statistics:")
            print(f"  - Students: {self.basic_stats['student_count']}")
            print(f"  - Questions: {self.basic_stats['question_count']}")
            print(f"  - Mean Total Score: {self.basic_stats['mean_total_score']:.2f}")
            print(f"  - Std Dev: {self.basic_stats['std_total_score']:.2f}")
            print(f"  ✓ Question weights will be auto-detected from maximum scores")

            self.timestamps['data_ready'] = datetime.now()
            return True

        except Exception as e:
            print(f"  ✗ Error loading data: {e}")
            return False

    def _run_metrics_agent(self) -> Dict[str, Any]:
        """Execute Agent 1: Metrics Calculator.

        Returns:
            Metrics calculation results
        """
        agent = MetricsAgent()
        return agent.calculate_metrics(self.cleaned_data)

    def _run_visualization_agent(self) -> Dict[str, Any]:
        """Execute Agent 2: Visualization Generator.

        Returns:
            Visualization generation results
        """
        agent = VisualizationAgent()
        return agent.generate_visualizations(self.cleaned_data)

    def _run_recommendations_agent(self) -> Dict[str, Any]:
        """Execute Agent 3: Recommendation Engine.

        Returns:
            Recommendation engine results
        """
        agent = RecommendationsAgent()
        return agent.generate_recommendations(self.cleaned_data)

    def run_agents(self, parallel: bool = True) -> bool:
        """Execute all three specialized agents.

        Args:
            parallel: If True, run agents in parallel; otherwise sequential

        Returns:
            True if all agents completed successfully
        """
        if not self.status['basic_stats_calculated']:
            print("Error: Data must be loaded before running agents")
            return False

        try:
            print("\nStarting analysis agents...")

            if parallel:
                # Run all three agents in parallel using ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=3) as executor:
                    futures = {
                        executor.submit(self._run_metrics_agent): "metrics",
                        executor.submit(self._run_visualization_agent): "visualization",
                        executor.submit(self._run_recommendations_agent): "recommendations"
                    }

                    for future in as_completed(futures):
                        agent_name = futures[future]
                        try:
                            result = future.result()

                            if agent_name == "metrics":
                                self.metrics_results = result
                                self.status['agents_completed']['metrics'] = True
                            elif agent_name == "visualization":
                                self.visualization_results = result
                                self.status['agents_completed']['visualization'] = True
                            elif agent_name == "recommendations":
                                self.recommendation_results = result
                                self.status['agents_completed']['recommendations'] = True

                            print(f"  ✓ Agent {agent_name.capitalize()} completed")

                        except Exception as e:
                            print(f"  ✗ Agent {agent_name.capitalize()} failed: {e}")
                            if agent_name == "metrics":
                                self.metrics_results = {"error": str(e)}
                            elif agent_name == "visualization":
                                self.visualization_results = {"error": str(e)}
                            elif agent_name == "recommendations":
                                self.recommendation_results = {"error": str(e)}
            else:
                # Run sequentially (useful for debugging)
                print("  Running Agent 1 (Metrics Calculator)...")
                self.metrics_results = self._run_metrics_agent()
                self.status['agents_completed']['metrics'] = True
                print("    ✓ Completed")

                print("  Running Agent 2 (Visualization Generator)...")
                self.visualization_results = self._run_visualization_agent()
                self.status['agents_completed']['visualization'] = True
                print("    ✓ Completed")

                print("  Running Agent 3 (Recommendation Engine)...")
                self.recommendation_results = self._run_recommendations_agent()
                self.status['agents_completed']['recommendations'] = True
                print("    ✓ Completed")

            self.timestamps['agents_done'] = datetime.now()
            return all(self.status['agents_completed'].values())

        except Exception as e:
            print(f"  ✗ Error running agents: {e}")
            return False

    def assemble_final_outputs(self) -> Dict[str, Any]:
        """Assemble all agent outputs into final deliverables.

        Returns:
            Dictionary with status and file paths
        """
        if not all(self.status['agents_completed'].values()):
            return {
                'status': 'error',
                'message': 'All agents must complete before assembly'
            }

        try:
            print("\nAssembling final reports...")

            # Create output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # Use Assembly Agent to create final deliverables
            assembly_agent = AssemblyAgent(output_dir=str(self.output_dir))
            result = assembly_agent.assemble(
                metrics_output=self.metrics_results,
                visualizations_output=self.visualization_results,
                recommendations_output=self.recommendation_results,
                original_filename=str(self.data_path.name)
            )

            self.status['assembly_completed'] = True
            self.timestamps['assembly_done'] = datetime.now()

            return result

        except Exception as e:
            print(f"  ✗ Error assembling outputs: {e}")
            return {'status': 'error', 'message': str(e)}

    def run(self, parallel: bool = True) -> Dict[str, Any]:
        """Execute the complete analysis pipeline.

        Args:
            parallel: If True, run agents in parallel

        Returns:
            Dictionary with complete results including file paths
        """
        self.timestamps['start'] = datetime.now()

        print("=" * 60)
        print("TEST ANALYSIS ORCHESTRATOR")
        print("=" * 60)

        # Step 1: Load and validate data
        print("\n[Step 1/3] Loading and validating data...")
        if not self.load_and_validate_data():
            return {
                'success': False,
                'error': 'Data loading failed',
                'status': self.status
            }

        # Step 2: Run analysis agents
        print("\n[Step 2/3] Running analysis agents...")
        if not self.run_agents(parallel=parallel):
            return {
                'success': False,
                'error': 'Agent execution failed',
                'status': self.status
            }

        # Step 3: Assemble final outputs
        print("\n[Step 3/3] Assembling final outputs...")
        assembly_result = self.assemble_final_outputs()

        # Calculate execution time (handle case where assembly failed)
        end_time = self.timestamps.get('assembly_done') or datetime.now()
        total_time = (end_time - self.timestamps['start']).total_seconds()

        # Compile final results
        final_result = {
            'success': assembly_result.get('status') == 'success',
            'basic_stats': self.basic_stats,
            'metrics_results': self.metrics_results,
            'visualization_results': self.visualization_results,
            'recommendation_results': self.recommendation_results,
            'output_files': assembly_result.get('files', {}),
            'status': self.status,
            'execution_time_seconds': total_time,
            'timestamps': {
                k: v.isoformat() if v else None
                for k, v in self.timestamps.items()
            }
        }

        print("\n" + "=" * 60)
        if final_result['success']:
            print("✓ Analysis completed successfully!")
            print(f"Total execution time: {total_time:.2f} seconds")
        else:
            print("✗ Analysis completed with errors")

        return final_result


def main():
    """Main entry point for the test analysis system."""
    parser = argparse.ArgumentParser(
        description="Test Analysis Orchestrator - Analyze test performance and generate comprehensive reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s student_scores.xlsx
  %(prog)s test_data.csv --weights weights.csv --output-dir ./reports
  %(prog)s exam_results.xlsx --sequential

Output Files:
  - Excel workbook with multiple analysis sheets
  - Interactive HTML report with visualizations
  - Plain text summary report
"""
    )

    parser.add_argument(
        "input_data",
        help="Path to input data file (Excel .xlsx/.xls or CSV .csv)"
    )

    parser.add_argument(
        "--weights",
        help="Path to optional weights CSV file",
        default=None
    )

    parser.add_argument(
        "--output-dir",
        help="Output directory for generated reports (default: results)",
        default="results"
    )

    parser.add_argument(
        "--sequential",
        help="Run agents sequentially instead of in parallel (useful for debugging)",
        action="store_true",
        default=False
    )

    args = parser.parse_args()

    try:
        # Create and run orchestrator
        orchestrator = TestAnalysisOrchestrator(
            data_path=args.input_data,
            weights_path=args.weights,
            output_dir=args.output_dir
        )

        # Execute pipeline
        result = orchestrator.run(parallel=not args.sequential)

        # Report results
        if result.get('success'):
            print("\nGenerated files:")
            for file_type, file_path in result.get('output_files', {}).items():
                print(f"  - {file_type.capitalize()}: {file_path}")

            sys.exit(0)
        else:
            print(f"\nError: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
