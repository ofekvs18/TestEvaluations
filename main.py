#!/usr/bin/env python3
"""
Main Orchestrator for Test Analysis System

Coordinates the parallel execution of analysis agents and assembles final reports.
"""

import argparse
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, Optional

import pandas as pd

from agents.assembly_agent import AssemblyAgent
from agents.metrics_agent import MetricsAgent
from agents.visualization_agent import VisualizationAgent
from agents.recommendations_agent import RecommendationsAgent


class Orchestrator:
    """Orchestrates the test analysis workflow."""

    def __init__(
        self,
        data_path: str,
        weights_path: Optional[str] = None,
        output_dir: str = "."
    ):
        """
        Initialize the orchestrator.

        Args:
            data_path: Path to input Excel/CSV data file
            weights_path: Optional path to weights CSV file
            output_dir: Directory for output files
        """
        self.data_path = Path(data_path)
        self.weights_path = Path(weights_path) if weights_path else None
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Validate input file
        if not self.data_path.exists():
            raise FileNotFoundError(f"Input file not found: {self.data_path}")

        if self.weights_path and not self.weights_path.exists():
            raise FileNotFoundError(f"Weights file not found: {self.weights_path}")

        # Load data
        self.data = self._load_data()
        self.weights = self._load_weights() if self.weights_path else None

    def _load_data(self) -> pd.DataFrame:
        """Load input data from Excel or CSV file."""
        if self.data_path.suffix.lower() in ['.xlsx', '.xls']:
            return pd.read_excel(self.data_path)
        elif self.data_path.suffix.lower() == '.csv':
            return pd.read_csv(self.data_path)
        else:
            raise ValueError(f"Unsupported file format: {self.data_path.suffix}")

    def _load_weights(self) -> Optional[pd.DataFrame]:
        """Load optional weights from CSV file."""
        if self.weights_path:
            return pd.read_csv(self.weights_path)
        return None

    def run_analysis(self) -> Dict[str, Any]:
        """
        Run the complete test analysis workflow.

        Returns:
            Dictionary containing results and file paths
        """
        print(f"Starting analysis of {self.data_path.name}")
        print(f"Data shape: {self.data.shape}")

        # Spawn agents in parallel
        print("\nLaunching analysis agents in parallel...")

        # Prepare data for parallel processing
        data_dict = self.data.to_dict('records')
        weights_dict = self.weights.to_dict('records') if self.weights is not None else None

        # Run agents in parallel using multiprocessing
        with ProcessPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(
                    self._run_metrics_agent, data_dict, weights_dict
                ): "metrics",
                executor.submit(
                    self._run_visualization_agent, data_dict
                ): "visualizations",
                executor.submit(
                    self._run_recommendations_agent, data_dict
                ): "recommendations"
            }

            results = {}
            for future in as_completed(futures):
                agent_name = futures[future]
                try:
                    results[agent_name] = future.result()
                    print(f"  ✓ {agent_name.capitalize()} agent completed")
                except Exception as e:
                    print(f"  ✗ {agent_name.capitalize()} agent failed: {str(e)}")
                    results[agent_name] = {"error": str(e)}

        # Pass all results to Assembly Agent
        print("\nAssembling final reports...")
        assembly_agent = AssemblyAgent(output_dir=str(self.output_dir))
        final_result = assembly_agent.assemble(
            metrics_output=results.get("metrics", {}),
            visualizations_output=results.get("visualizations", {}),
            recommendations_output=results.get("recommendations", {}),
            original_filename=str(self.data_path.name)
        )

        return final_result

    @staticmethod
    def _run_metrics_agent(data_dict: list, weights_dict: Optional[list]) -> Dict[str, Any]:
        """Run the metrics calculation agent."""
        agent = MetricsAgent()
        data_df = pd.DataFrame(data_dict)
        weights_df = pd.DataFrame(weights_dict) if weights_dict else None
        return agent.calculate_metrics(data_df, weights_df)

    @staticmethod
    def _run_visualization_agent(data_dict: list) -> Dict[str, Any]:
        """Run the visualization generation agent."""
        agent = VisualizationAgent()
        data_df = pd.DataFrame(data_dict)
        return agent.generate_visualizations(data_df)

    @staticmethod
    def _run_recommendations_agent(data_dict: list) -> Dict[str, Any]:
        """Run the recommendations analysis agent."""
        agent = RecommendationsAgent()
        data_df = pd.DataFrame(data_dict)
        return agent.generate_recommendations(data_df)


def main():
    """Main entry point for the test analysis system."""
    parser = argparse.ArgumentParser(
        description="Test Analysis System - Analyze test performance and generate reports"
    )
    parser.add_argument(
        "input_data",
        help="Path to input data file (Excel or CSV)"
    )
    parser.add_argument(
        "--weights",
        help="Path to weights CSV file (optional)",
        default=None
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory for generated reports",
        default="results"
    )

    args = parser.parse_args()

    try:
        # Create orchestrator
        orchestrator = Orchestrator(
            data_path=args.input_data,
            weights_path=args.weights,
            output_dir=args.output_dir
        )

        # Run analysis
        result = orchestrator.run_analysis()

        # Report completion
        if result.get("status") == "success":
            print("\n✓ Analysis complete!")
            print("\nGenerated files:")
            for file_type, file_path in result.get("files", {}).items():
                print(f"  - {file_type}: {file_path}")

            sys.exit(0)
        else:
            print("\n✗ Analysis completed with errors")
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
