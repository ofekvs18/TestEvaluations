"""
Visualization Generation Agent (Agent 2)

Creates interactive and static visualizations for test analysis.
"""

import io
from typing import Any, Dict, List

import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for thread safety
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class VisualizationAgent:
    """Agent responsible for generating visualizations."""

    def generate_visualizations(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate all visualizations for the test analysis.

        Args:
            data: DataFrame with student responses

        Returns:
            Dictionary containing Plotly figures and static images
        """
        if data.empty:
            return self._empty_visualizations()

        # Extract question columns (skip first column which is student ID)
        question_cols = data.columns[1:]
        scores = data[question_cols].values

        # Generate Plotly HTML figures
        plotly_figures = self._generate_plotly_figures(scores, question_cols)

        # Generate static images for Excel
        static_images = self._generate_static_images(scores, question_cols)

        # Generate per-question score distribution data
        question_distributions = self._generate_question_score_distributions(scores, question_cols)

        return {
            "plotly_figures": plotly_figures,
            "static_images": static_images,
            "question_distributions": question_distributions
        }

    def _generate_plotly_figures(
        self,
        scores: np.ndarray,
        question_cols: pd.Index
    ) -> Dict[str, Any]:
        """Generate interactive Plotly figures."""
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots

            # Question Analysis Figure
            question_fig = self._create_question_analysis_plotly(scores, question_cols)

            # Test-level figures
            test_figs = self._create_test_level_plotly(scores)

            return {
                "question_analysis": question_fig.to_html(include_plotlyjs=False, full_html=False),
                "test_level": [fig.to_html(include_plotlyjs=False, full_html=False) for fig in test_figs]
            }
        except ImportError:
            return {
                "question_analysis": "<p>Plotly not available</p>",
                "test_level": []
            }

    def _create_question_analysis_plotly(
        self,
        scores: np.ndarray,
        question_cols: pd.Index
    ):
        """Create question-level analysis Plotly figure."""
        import plotly.graph_objects as go

        # Calculate metrics per question
        difficulties = np.mean(scores, axis=0)
        total_scores = scores.sum(axis=1)

        discriminations = []
        for i in range(scores.shape[1]):
            if np.std(scores[:, i]) == 0:
                discriminations.append(0)
            else:
                corr = np.corrcoef(scores[:, i], total_scores)[0, 1]
                discriminations.append(corr if not np.isnan(corr) else 0)

        fig = go.Figure()

        # Scatter plot of difficulty vs discrimination
        fig.add_trace(go.Scatter(
            x=difficulties,
            y=discriminations,
            mode='markers+text',
            text=[str(q) for q in question_cols],
            textposition='top center',
            marker=dict(size=12, color=discriminations, colorscale='RdYlGn', showscale=True),
            name='Questions'
        ))

        # Add reference lines
        fig.add_hline(y=0.3, line_dash="dash", line_color="orange",
                      annotation_text="Min Discrimination")
        fig.add_vline(x=0.3, line_dash="dash", line_color="gray")
        fig.add_vline(x=0.7, line_dash="dash", line_color="gray")

        fig.update_layout(
            title="Question Difficulty vs Discrimination",
            xaxis_title="Difficulty (Proportion Correct)",
            yaxis_title="Discrimination (Correlation with Total)",
            height=600,
            width=900
        )

        return fig

    def _create_test_level_plotly(self, scores: np.ndarray) -> List:
        """Create test-level Plotly figures."""
        import plotly.graph_objects as go

        figures = []

        # Score Distribution
        total_scores = scores.sum(axis=1)

        fig1 = go.Figure()
        fig1.add_trace(go.Histogram(
            x=total_scores,
            nbinsx=20,
            name='Score Distribution'
        ))
        fig1.update_layout(
            title="Score Distribution",
            xaxis_title="Total Score",
            yaxis_title="Frequency",
            height=400
        )
        figures.append(fig1)

        # Item Difficulty Distribution
        difficulties = np.mean(scores, axis=0)

        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(
            x=difficulties,
            nbinsx=10,
            name='Difficulty Distribution'
        ))
        fig2.add_vline(x=0.3, line_dash="dash", line_color="red")
        fig2.add_vline(x=0.7, line_dash="dash", line_color="red")
        fig2.update_layout(
            title="Question Difficulty Distribution",
            xaxis_title="Difficulty",
            yaxis_title="Number of Questions",
            height=400
        )
        figures.append(fig2)

        return figures

    def _generate_static_images(
        self,
        scores: np.ndarray,
        question_cols: pd.Index
    ) -> List[Dict[str, Any]]:
        """Generate static matplotlib images for Excel embedding."""
        images = []

        # Score Distribution
        fig, ax = plt.subplots(figsize=(10, 6))
        total_scores = scores.sum(axis=1)
        ax.hist(total_scores, bins=20, edgecolor='black', alpha=0.7)
        ax.set_title('Score Distribution', fontsize=14, fontweight='bold')
        ax.set_xlabel('Total Score')
        ax.set_ylabel('Frequency')
        ax.grid(True, alpha=0.3)

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        images.append({
            "title": "Score Distribution",
            "image_bytes": buf.getvalue()
        })
        plt.close(fig)

        # Question Weights (Max Scores) Analysis
        fig, ax = plt.subplots(figsize=(12, 6))
        max_scores = scores.max(axis=0)
        question_labels = [str(q) for q in question_cols]

        bars = ax.bar(range(len(question_labels)), max_scores, edgecolor='black', alpha=0.7, color='steelblue')
        ax.set_title('Question Weights (Maximum Possible Scores)', fontsize=14, fontweight='bold')
        ax.set_xlabel('Question')
        ax.set_ylabel('Max Score (Weight)')
        ax.set_xticks(range(len(question_labels)))
        ax.set_xticklabels(question_labels, rotation=45, ha='right')
        ax.grid(True, alpha=0.3, axis='y')

        # Add value labels on bars
        for i, (bar, score) in enumerate(zip(bars, max_scores)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(score)}',
                   ha='center', va='bottom', fontsize=9, fontweight='bold')

        # Add summary statistics
        total_weight = max_scores.sum()
        mean_weight = max_scores.mean()
        ax.text(0.02, 0.98, f'Total: {int(total_weight)} points\nMean: {mean_weight:.1f} points',
               transform=ax.transAxes, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
               fontsize=10)

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        images.append({
            "title": "Question Weights Analysis",
            "image_bytes": buf.getvalue()
        })
        plt.close(fig)

        # Difficulty-Discrimination Scatter
        fig, ax = plt.subplots(figsize=(10, 8))
        difficulties = np.mean(scores, axis=0)

        discriminations = []
        for i in range(scores.shape[1]):
            if np.std(scores[:, i]) == 0:
                discriminations.append(0)
            else:
                corr = np.corrcoef(scores[:, i], total_scores)[0, 1]
                discriminations.append(corr if not np.isnan(corr) else 0)

        scatter = ax.scatter(difficulties, discriminations, c=discriminations,
                             cmap='RdYlGn', s=100, edgecolors='black', linewidths=1)
        plt.colorbar(scatter, label='Discrimination')

        ax.axhline(y=0.3, color='orange', linestyle='--', label='Min Discrimination')
        ax.axvline(x=0.3, color='gray', linestyle='--', alpha=0.5)
        ax.axvline(x=0.7, color='gray', linestyle='--', alpha=0.5)

        ax.set_title('Question Difficulty vs Discrimination', fontsize=14, fontweight='bold')
        ax.set_xlabel('Difficulty (Proportion Correct)')
        ax.set_ylabel('Discrimination')
        ax.legend()
        ax.grid(True, alpha=0.3)

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        images.append({
            "title": "Difficulty vs Discrimination",
            "image_bytes": buf.getvalue()
        })
        plt.close(fig)

        return images

    def _generate_question_score_distributions(
        self,
        scores: np.ndarray,
        question_cols: pd.Index
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate score distribution data for each question.

        Args:
            scores: NumPy array of student scores
            question_cols: Index of question column names

        Returns:
            Dictionary mapping question_id to distribution data
        """
        distributions = {}

        for idx, question_id in enumerate(question_cols):
            q_scores = scores[:, idx]
            max_score = int(np.max(q_scores))

            # Count students for each possible score
            score_counts = {}
            for score_value in range(max_score + 1):
                count = np.sum(q_scores == score_value)
                score_counts[score_value] = int(count)

            # Calculate percentages
            total_students = len(q_scores)
            score_percentages = {
                score: (count / total_students * 100) if total_students > 0 else 0
                for score, count in score_counts.items()
            }

            distributions[str(question_id)] = {
                "max_score": max_score,
                "score_counts": score_counts,
                "score_percentages": score_percentages,
                "total_students": total_students,
                "mean_score": float(np.mean(q_scores)),
                "median_score": float(np.median(q_scores)),
                "std_dev": float(np.std(q_scores))
            }

        return distributions

    def _empty_visualizations(self) -> Dict[str, Any]:
        """Return empty visualizations structure."""
        return {
            "plotly_figures": {
                "question_analysis": "<p>No data available</p>",
                "test_level": []
            },
            "static_images": [],
            "question_distributions": {}
        }
