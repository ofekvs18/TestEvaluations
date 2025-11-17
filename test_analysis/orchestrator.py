"""Test Analysis Orchestrator.

Main coordinator that loads data, validates it, and dispatches work to specialized agents.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from datetime import datetime

from .data_loader import (
    load_excel_file,
    validate_data_structure,
    parse_student_data,
    calculate_basic_statistics,
    infer_max_points
)
from .metrics_calculator import MetricsCalculator
from .visualization_generator import VisualizationGenerator
from .recommendation_engine import RecommendationEngine


class TestAnalysisOrchestrator:
    """Main orchestrator for test analysis system.

    Coordinates data loading, validation, and parallel agent execution.
    """

    def __init__(self,
                 excel_file_path: str,
                 current_weights: Optional[Dict[str, float]] = None,
                 max_points: Optional[Dict[str, float]] = None,
                 config: Optional[Dict[str, Any]] = None):
        """Initialize the orchestrator.

        Args:
            excel_file_path: Path to the Excel file with student data.
            current_weights: Optional dictionary of current question weights.
            max_points: Optional dictionary of max points per question.
            config: Optional configuration for agents and thresholds.
        """
        self.excel_file_path = excel_file_path
        self.current_weights = current_weights or {}
        self.provided_max_points = max_points
        self.config = config or {}

        # Data containers
        self.raw_df: Optional[pd.DataFrame] = None
        self.scores_df: Optional[pd.DataFrame] = None
        self.student_ids: Optional[pd.Series] = None
        self.question_names: Optional[list] = None
        self.max_points: Optional[Dict[str, float]] = None
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
            'agents_completed': {
                'metrics': False,
                'visualization': False,
                'recommendations': False
            },
            'output_generated': False
        }

    def load_and_validate_data(self) -> bool:
        """Load Excel file and validate data structure.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Load Excel file
            self.raw_df = load_excel_file(self.excel_file_path)
            self.status['data_loaded'] = True

            # Validate structure
            is_valid, message = validate_data_structure(self.raw_df)
            if not is_valid:
                raise ValueError(f"Data validation failed: {message}")
            self.status['data_validated'] = True

            # Parse into clean format
            self.scores_df, self.student_ids, self.question_names = parse_student_data(self.raw_df)
            self.status['data_parsed'] = True

            # Infer or use provided max points
            self.max_points = infer_max_points(self.scores_df, self.provided_max_points)

            # Calculate basic statistics
            self.basic_stats = calculate_basic_statistics(self.scores_df)

            # Set default weights if not provided
            if not self.current_weights:
                self.current_weights = {q: 1.0 for q in self.question_names}

            return True

        except Exception as e:
            print(f"Error loading data: {e}")
            return False

    def _run_metrics_agent(self) -> Dict[str, Any]:
        """Run Agent 1: Metrics Calculator.

        Returns:
            Metrics calculation results.
        """
        agent = MetricsCalculator(
            scores_df=self.scores_df,
            max_points=self.max_points,
            config=self.config.get('metrics', {})
        )
        return agent.run()

    def _run_visualization_agent(self, metrics_results: Dict[str, Any]) -> Dict[str, Any]:
        """Run Agent 2: Visualization Generator.

        Args:
            metrics_results: Results from metrics calculator.

        Returns:
            Visualization generation results.
        """
        agent = VisualizationGenerator(
            scores_df=self.scores_df,
            metrics_results=metrics_results,
            config=self.config.get('visualization', {})
        )
        return agent.run()

    def _run_recommendation_agent(self, metrics_results: Dict[str, Any]) -> Dict[str, Any]:
        """Run Agent 3: Recommendation Engine.

        Args:
            metrics_results: Results from metrics calculator.

        Returns:
            Recommendation engine results.
        """
        agent = RecommendationEngine(
            scores_df=self.scores_df,
            metrics_results=metrics_results,
            current_weights=self.current_weights,
            config=self.config.get('recommendations', {})
        )
        return agent.run()

    def run_agents_parallel(self) -> bool:
        """Run all three agents in parallel.

        Note: Agent 2 and 3 depend on Agent 1 results, so we run Agent 1 first,
        then Agent 2 and 3 in parallel.

        Returns:
            True if all agents completed successfully.
        """
        if not self.status['data_parsed']:
            print("Error: Data must be loaded and parsed before running agents")
            return False

        try:
            # Step 1: Run Metrics Calculator (Agent 1) first
            print("Starting Agent 1: Metrics Calculator...")
            self.metrics_results = self._run_metrics_agent()
            self.status['agents_completed']['metrics'] = True
            print("Agent 1 completed.")

            # Step 2: Run Visualization and Recommendation agents in parallel
            print("Starting Agent 2 (Visualization) and Agent 3 (Recommendations) in parallel...")

            with ThreadPoolExecutor(max_workers=2) as executor:
                future_viz = executor.submit(
                    self._run_visualization_agent,
                    self.metrics_results
                )
                future_rec = executor.submit(
                    self._run_recommendation_agent,
                    self.metrics_results
                )

                # Collect results
                self.visualization_results = future_viz.result()
                self.status['agents_completed']['visualization'] = True
                print("Agent 2 (Visualization) completed.")

                self.recommendation_results = future_rec.result()
                self.status['agents_completed']['recommendations'] = True
                print("Agent 3 (Recommendations) completed.")

            return True

        except Exception as e:
            print(f"Error running agents: {e}")
            return False

    def generate_excel_output(self, output_path: str) -> bool:
        """Generate combined Excel workbook with all results.

        Args:
            output_path: Path for output Excel file.

        Returns:
            True if successful.
        """
        if not all(self.status['agents_completed'].values()):
            print("Error: All agents must complete before generating output")
            return False

        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Sheet 1: Raw Scores
                self.scores_df.to_excel(writer, sheet_name='Raw_Scores', index=False)

                # Sheet 2: Question Metrics (from Agent 1)
                if self.metrics_results and 'question_metrics' in self.metrics_results:
                    self.metrics_results['question_metrics'].to_excel(
                        writer, sheet_name='Question_Metrics', index=False
                    )

                # Sheet 3: Test Statistics (from Agent 1)
                if self.metrics_results and 'test_statistics' in self.metrics_results:
                    stats_df = pd.DataFrame([self.metrics_results['test_statistics']])
                    stats_df.to_excel(writer, sheet_name='Test_Statistics', index=False)

                # Sheet 4: Quality Flags (from Agent 1)
                if self.metrics_results and 'quality_flags' in self.metrics_results:
                    self.metrics_results['quality_flags'].to_excel(
                        writer, sheet_name='Quality_Flags', index=False
                    )

                # Placeholder sheets for Agent 2 and 3 results
                # These will be populated when full implementations are merged

            print(f"Excel output saved to: {output_path}")
            return True

        except Exception as e:
            print(f"Error generating Excel output: {e}")
            return False

    def generate_html_report(self, output_path: str) -> bool:
        """Generate combined HTML report with all results.

        Args:
            output_path: Path for output HTML file.

        Returns:
            True if successful.
        """
        if not all(self.status['agents_completed'].values()):
            print("Error: All agents must complete before generating report")
            return False

        try:
            html_content = self._build_html_report()

            with open(output_path, 'w') as f:
                f.write(html_content)

            print(f"HTML report saved to: {output_path}")
            return True

        except Exception as e:
            print(f"Error generating HTML report: {e}")
            return False

    def _build_html_report(self) -> str:
        """Build HTML report content.

        Returns:
            HTML string.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Test Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 2px solid #ddd; padding-bottom: 5px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f5f5f5; }}
        .good {{ background-color: #d4edda; }}
        .review {{ background-color: #fff3cd; }}
        .poor {{ background-color: #f8d7da; }}
        .stats-box {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: white; border-radius: 3px; }}
    </style>
</head>
<body>
    <h1>Test Analysis Report</h1>
    <p><strong>Generated:</strong> {timestamp}</p>
    <p><strong>Source File:</strong> {self.excel_file_path}</p>

    <h2>Basic Statistics</h2>
    <div class="stats-box">
"""

        # Add basic stats
        if self.basic_stats:
            html += f"""
        <div class="metric"><strong>Students:</strong> {self.basic_stats['student_count']}</div>
        <div class="metric"><strong>Questions:</strong> {self.basic_stats['question_count']}</div>
        <div class="metric"><strong>Mean Score:</strong> {self.basic_stats['mean_total_score']:.2f}</div>
        <div class="metric"><strong>Std Dev:</strong> {self.basic_stats['std_total_score']:.2f}</div>
"""

        html += """
    </div>

    <h2>Question Metrics (Agent 1 Results)</h2>
"""

        # Add question metrics table
        if self.metrics_results and 'question_metrics' in self.metrics_results:
            df = self.metrics_results['question_metrics']
            html += """
    <table>
        <tr>
            <th>Question</th>
            <th>Max Points</th>
            <th>Mean Score</th>
            <th>Difficulty</th>
            <th>Discrimination</th>
            <th>Item-Total Corr</th>
            <th>Quality Flag</th>
        </tr>
"""
            for _, row in df.iterrows():
                flag_class = row['quality_flag'].lower()
                html += f"""
        <tr>
            <td>{row['question']}</td>
            <td>{row['max_points']:.2f}</td>
            <td>{row['mean_score']:.2f}</td>
            <td>{row['difficulty_index']:.3f}</td>
            <td>{row['discrimination_index']:.3f}</td>
            <td>{row['item_total_correlation']:.3f}</td>
            <td class="{flag_class}">{row['quality_flag']}</td>
        </tr>
"""
            html += "    </table>\n"

        # Add test statistics
        html += """
    <h2>Test-Level Statistics</h2>
    <div class="stats-box">
"""
        if self.metrics_results and 'test_statistics' in self.metrics_results:
            stats = self.metrics_results['test_statistics']
            html += f"""
        <div class="metric"><strong>Cronbach's Alpha:</strong> {stats.get('cronbachs_alpha', 0):.3f}</div>
        <div class="metric"><strong>Median Score:</strong> {stats.get('median_total_score', 0):.2f}</div>
        <div class="metric"><strong>Skewness:</strong> {stats.get('skewness', 0):.3f}</div>
        <div class="metric"><strong>Kurtosis:</strong> {stats.get('kurtosis', 0):.3f}</div>
"""

        html += """
    </div>

    <h2>Visualization Results (Agent 2)</h2>
    <p><em>Stub - Full implementation pending merge</em></p>

    <h2>Recommendations (Agent 3)</h2>
    <p><em>Stub - Full implementation pending merge</em></p>

</body>
</html>
"""
        return html

    def generate_summary_text(self) -> str:
        """Generate plain text summary report.

        Returns:
            Summary text string.
        """
        if not all(self.status['agents_completed'].values()):
            return "Error: All agents must complete before generating summary"

        lines = [
            "=" * 60,
            "TEST ANALYSIS SUMMARY REPORT",
            "=" * 60,
            f"Source: {self.excel_file_path}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "BASIC STATISTICS",
            "-" * 40
        ]

        if self.basic_stats:
            lines.extend([
                f"Total Students: {self.basic_stats['student_count']}",
                f"Total Questions: {self.basic_stats['question_count']}",
                f"Mean Total Score: {self.basic_stats['mean_total_score']:.2f}",
                f"Std Dev: {self.basic_stats['std_total_score']:.2f}",
                f"Min Score: {self.basic_stats['min_total_score']:.2f}",
                f"Max Score: {self.basic_stats['max_total_score']:.2f}",
            ])

        lines.extend([
            "",
            "TEST RELIABILITY",
            "-" * 40
        ])

        if self.metrics_results and 'test_statistics' in self.metrics_results:
            alpha = self.metrics_results['test_statistics'].get('cronbachs_alpha', 0)
            lines.append(f"Cronbach's Alpha: {alpha:.3f}")

        lines.extend([
            "",
            "QUESTION QUALITY SUMMARY",
            "-" * 40
        ])

        if self.metrics_results and 'quality_flags' in self.metrics_results:
            flags = self.metrics_results['quality_flags']['quality_flag'].value_counts()
            for flag, count in flags.items():
                lines.append(f"{flag}: {count} questions")

        lines.extend([
            "",
            "DIFFICULTY CURVE ANALYSIS",
            "-" * 40
        ])

        if self.metrics_results and 'curve_breakers' in self.metrics_results:
            breakers = self.metrics_results['curve_breakers']
            if breakers:
                lines.append(f"Questions breaking curve: {', '.join(breakers)}")
            else:
                lines.append("No questions significantly break the difficulty curve")

        lines.extend([
            "",
            "=" * 60
        ])

        return "\n".join(lines)

    def run(self, output_dir: str = "./output") -> Dict[str, Any]:
        """Run complete analysis pipeline.

        Args:
            output_dir: Directory for output files.

        Returns:
            Dictionary with analysis results and file paths.
        """
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Step 1: Load and validate data
        print("Step 1: Loading and validating data...")
        if not self.load_and_validate_data():
            return {'success': False, 'error': 'Data loading failed'}

        print(f"Loaded {self.basic_stats['student_count']} students, "
              f"{self.basic_stats['question_count']} questions")

        # Step 2: Run agents in parallel
        print("\nStep 2: Running analysis agents...")
        if not self.run_agents_parallel():
            return {'success': False, 'error': 'Agent execution failed'}

        # Step 3: Generate outputs
        print("\nStep 3: Generating output files...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        excel_path = output_path / f"test_analysis_{timestamp}.xlsx"
        html_path = output_path / f"test_analysis_{timestamp}.html"
        summary_path = output_path / f"test_analysis_{timestamp}.txt"

        self.generate_excel_output(str(excel_path))
        self.generate_html_report(str(html_path))

        summary_text = self.generate_summary_text()
        with open(summary_path, 'w') as f:
            f.write(summary_text)
        print(f"Summary text saved to: {summary_path}")

        self.status['output_generated'] = True

        return {
            'success': True,
            'basic_stats': self.basic_stats,
            'metrics_results': self.metrics_results,
            'visualization_results': self.visualization_results,
            'recommendation_results': self.recommendation_results,
            'output_files': {
                'excel': str(excel_path),
                'html': str(html_path),
                'summary': str(summary_path)
            },
            'status': self.status
        }
