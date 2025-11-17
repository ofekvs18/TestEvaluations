"""Plotly interactive visualization generator for HTML reports.

Creates comprehensive interactive charts with tooltips, sorting, and drill-down capabilities.
"""

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from ..models.metrics import TestStatistics
from ..utils.colors import (
    COLORBLIND_PALETTE,
    QUALITY_COLORS,
    DIVERGING_COLORS,
    get_quality_colors_list,
)


class PlotlyVisualizationGenerator:
    """Generates interactive Plotly visualizations for HTML reports.

    Creates rich, interactive charts with hover tooltips, clickable elements,
    and comprehensive information displays.
    """

    def __init__(self):
        """Initialize the Plotly generator."""
        self._setup_template()

    def _setup_template(self) -> None:
        """Configure default Plotly template for consistent styling."""
        self.template = go.layout.Template()

        self.template.layout = go.Layout(
            font=dict(family="Arial, sans-serif", size=12),
            title=dict(font=dict(size=16, color="#333333")),
            paper_bgcolor="white",
            plot_bgcolor="white",
            hovermode="closest",
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Arial"
            ),
        )

    def generate_all(
        self,
        question_metrics_df: pd.DataFrame,
        test_statistics: TestStatistics,
        difficulty_order: List[int],
        curve_breakers: List[int],
        raw_student_data: Optional[pd.DataFrame] = None,
    ) -> Dict[str, Any]:
        """Generate all Plotly interactive figures.

        Args:
            question_metrics_df: DataFrame with question metrics
            test_statistics: Overall test statistics
            difficulty_order: Indices of questions sorted by difficulty
            curve_breakers: Indices of curve-breaking questions
            raw_student_data: Optional raw student score data for distributions

        Returns:
            Dictionary mapping chart names to Plotly figure objects
        """
        figures = {}

        # Generate each interactive figure
        figures['question_details'] = self.create_question_details(
            question_metrics_df, test_statistics
        )
        figures['difficulty_curve'] = self.create_interactive_difficulty_curve(
            question_metrics_df, difficulty_order, curve_breakers
        )
        figures['scatter'] = self.create_interactive_scatter(question_metrics_df)
        figures['weights'] = self.create_interactive_weights(question_metrics_df)
        figures['heatmap'] = self.create_correlation_heatmap(
            question_metrics_df, raw_student_data
        )
        figures['distribution'] = self.create_student_distribution(test_statistics)

        return figures

    def create_question_details(
        self,
        df: pd.DataFrame,
        test_statistics: TestStatistics,
    ) -> go.Figure:
        """Create scrollable individual question analysis section.

        Args:
            df: Question metrics DataFrame
            test_statistics: Overall test statistics

        Returns:
            Plotly figure with subplots for each question
        """
        n_questions = len(df)

        # Create subplots - 2 columns, enough rows for all questions
        n_rows = (n_questions + 1) // 2
        fig = make_subplots(
            rows=n_rows,
            cols=2,
            subplot_titles=[f"Question {int(row['question_number'])}" for _, row in df.iterrows()],
            vertical_spacing=0.08,
            horizontal_spacing=0.1,
        )

        for idx, (_, row) in enumerate(df.iterrows()):
            row_num = (idx // 2) + 1
            col_num = (idx % 2) + 1

            # Generate score distribution if available
            if row.get('score_distribution') is not None and len(row['score_distribution']) > 0:
                scores = row['score_distribution']
            else:
                # Simulate normal distribution for demonstration
                scores = np.random.normal(
                    row['mean_score'],
                    row['std_dev'] if row['std_dev'] > 0 else 0.5,
                    test_statistics.total_students
                )
                scores = np.clip(scores, row['min_score'], row['max_score'])

            # Histogram
            fig.add_trace(
                go.Histogram(
                    x=scores,
                    nbinsx=20,
                    name=f"Q{int(row['question_number'])}",
                    marker=dict(
                        color=QUALITY_COLORS[row['quality_category']],
                        line=dict(color='white', width=1)
                    ),
                    opacity=0.8,
                    showlegend=False,
                    hovertemplate=(
                        "Score Range: %{x}<br>"
                        "Count: %{y}<br>"
                        "<extra></extra>"
                    ),
                ),
                row=row_num,
                col=col_num,
            )

            # Add vertical lines for mean and median
            fig.add_vline(
                x=row['mean_score'],
                line=dict(color=COLORBLIND_PALETTE['blue'], width=2, dash='dash'),
                row=row_num,
                col=col_num,
            )
            fig.add_vline(
                x=row['median_score'],
                line=dict(color=COLORBLIND_PALETTE['orange'], width=2, dash='dot'),
                row=row_num,
                col=col_num,
            )

            # Add annotation with metrics
            annotation_text = (
                f"Mean: {row['mean_score']:.2f}<br>"
                f"Median: {row['median_score']:.2f}<br>"
                f"SD: {row['std_dev']:.2f}<br>"
                f"Difficulty: {row['difficulty_index']:.3f}<br>"
                f"Discrimination: {row['discrimination_index']:.3f}<br>"
                f"Quality: {row['quality_category'].upper()}"
            )

            fig.add_annotation(
                text=annotation_text,
                xref=f"x{idx+1 if idx > 0 else ''} domain",
                yref=f"y{idx+1 if idx > 0 else ''} domain",
                x=0.98,
                y=0.98,
                showarrow=False,
                font=dict(size=9),
                align="right",
                bgcolor="rgba(255, 255, 255, 0.9)",
                bordercolor="#cccccc",
                borderwidth=1,
                borderpad=4,
            )

        # Update layout
        fig.update_layout(
            height=300 * n_rows,
            title=dict(
                text="Individual Question Analysis",
                font=dict(size=18),
            ),
            template=self.template,
            showlegend=False,
        )

        # Update all x-axes
        fig.update_xaxes(title_text="Score", tickfont=dict(size=9))
        fig.update_yaxes(title_text="Frequency", tickfont=dict(size=9))

        return fig

    def create_interactive_difficulty_curve(
        self,
        df: pd.DataFrame,
        difficulty_order: List[int],
        curve_breakers: List[int],
    ) -> go.Figure:
        """Create interactive difficulty curve with toggle and tooltips.

        Args:
            df: Question metrics DataFrame
            difficulty_order: Indices sorted by difficulty
            curve_breakers: Indices of outlier questions

        Returns:
            Plotly figure with interactive difficulty curve
        """
        fig = go.Figure()

        # Original order trace
        fig.add_trace(
            go.Scatter(
                x=list(range(len(df))),
                y=df['difficulty_index'].values,
                mode='lines+markers',
                name='Original Order',
                marker=dict(
                    size=12,
                    color=COLORBLIND_PALETTE['blue'],
                    line=dict(color='white', width=2)
                ),
                line=dict(color=COLORBLIND_PALETTE['blue'], width=2),
                text=[f"Q{int(q)}" for q in df['question_number']],
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Position: %{x}<br>"
                    "Difficulty: %{y:.3f}<br>"
                    "<extra></extra>"
                ),
                visible=True,
            )
        )

        # Sorted order trace
        sorted_df = df.iloc[difficulty_order].reset_index(drop=True)
        fig.add_trace(
            go.Scatter(
                x=list(range(len(sorted_df))),
                y=sorted_df['difficulty_index'].values,
                mode='lines+markers',
                name='Sorted by Difficulty',
                marker=dict(
                    size=12,
                    color=COLORBLIND_PALETTE['orange'],
                    line=dict(color='white', width=2)
                ),
                line=dict(color=COLORBLIND_PALETTE['orange'], width=2),
                text=[f"Q{int(q)}" for q in sorted_df['question_number']],
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Position: %{x}<br>"
                    "Difficulty: %{y:.3f}<br>"
                    "<extra></extra>"
                ),
                visible='legendonly',
            )
        )

        # Ideal curve (for sorted view)
        ideal_y = np.linspace(
            sorted_df['difficulty_index'].max(),
            sorted_df['difficulty_index'].min(),
            len(sorted_df)
        )
        fig.add_trace(
            go.Scatter(
                x=list(range(len(sorted_df))),
                y=ideal_y,
                mode='lines',
                name='Ideal Curve',
                line=dict(color=COLORBLIND_PALETTE['black'], width=2, dash='dash'),
                opacity=0.5,
                hoverinfo='skip',
                visible='legendonly',
            )
        )

        # Mark curve breakers
        if curve_breakers:
            breaker_data = df.iloc[curve_breakers]
            fig.add_trace(
                go.Scatter(
                    x=curve_breakers,
                    y=breaker_data['difficulty_index'].values,
                    mode='markers',
                    name='Curve Breakers',
                    marker=dict(
                        size=20,
                        color='rgba(255, 255, 255, 0)',
                        line=dict(color=COLORBLIND_PALETTE['vermillion'], width=3)
                    ),
                    text=[f"Q{int(q)}" for q in breaker_data['question_number']],
                    hovertemplate=(
                        "<b>CURVE BREAKER: %{text}</b><br>"
                        "Difficulty: %{y:.3f}<br>"
                        "<extra></extra>"
                    ),
                )
            )

        # Reference lines
        fig.add_hline(
            y=0.3,
            line=dict(color=COLORBLIND_PALETTE['vermillion'], width=1, dash='dot'),
            annotation_text="Too Hard (< 30%)",
            annotation_position="bottom right",
        )
        fig.add_hline(
            y=0.7,
            line=dict(color=COLORBLIND_PALETTE['green'], width=1, dash='dot'),
            annotation_text="Too Easy (> 70%)",
            annotation_position="top right",
        )

        # Update layout
        fig.update_layout(
            title=dict(
                text="Interactive Difficulty Curve Analysis",
                font=dict(size=18),
            ),
            xaxis=dict(
                title="Question Position",
                gridcolor='lightgray',
                showgrid=True,
            ),
            yaxis=dict(
                title="Difficulty Index (P-value)",
                range=[-0.05, 1.05],
                gridcolor='lightgray',
                showgrid=True,
            ),
            template=self.template,
            hovermode='closest',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255, 255, 255, 0.9)",
            ),
            height=600,
        )

        # Add buttons for toggling views
        fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    direction="left",
                    buttons=[
                        dict(
                            args=[{"visible": [True, False, False, True]}],
                            label="Original Order",
                            method="restyle"
                        ),
                        dict(
                            args=[{"visible": [False, True, True, False]}],
                            label="Sorted Order",
                            method="restyle"
                        ),
                    ],
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    x=0.5,
                    xanchor="center",
                    y=1.15,
                    yanchor="top"
                ),
            ]
        )

        return fig

    def create_interactive_scatter(self, df: pd.DataFrame) -> go.Figure:
        """Create interactive discrimination-difficulty bubble chart.

        Args:
            df: Question metrics DataFrame

        Returns:
            Plotly figure with interactive scatter plot
        """
        # Create custom colors based on quality
        colors = df['quality_category'].map(QUALITY_COLORS).values

        fig = go.Figure()

        # Add bubbles for each question
        fig.add_trace(
            go.Scatter(
                x=df['difficulty_index'],
                y=df['discrimination_index'],
                mode='markers+text',
                marker=dict(
                    size=df['current_weight'] * 15,  # Size based on weight
                    color=colors,
                    line=dict(color='white', width=2),
                    opacity=0.8,
                    sizemode='diameter',
                    sizemin=10,
                ),
                text=[f"Q{int(q)}" for q in df['question_number']],
                textposition='top center',
                textfont=dict(size=10, color='#333333'),
                customdata=df[[
                    'question_number', 'mean_score', 'std_dev',
                    'current_weight', 'recommended_weight', 'quality_category'
                ]].values,
                hovertemplate=(
                    "<b>Question %{customdata[0]:.0f}</b><br>"
                    "Difficulty: %{x:.3f}<br>"
                    "Discrimination: %{y:.3f}<br>"
                    "Mean Score: %{customdata[1]:.2f}<br>"
                    "Std Dev: %{customdata[2]:.2f}<br>"
                    "Current Weight: %{customdata[3]:.1f}<br>"
                    "Recommended Weight: %{customdata[4]:.1f}<br>"
                    "Quality: %{customdata[5]}<br>"
                    "<extra></extra>"
                ),
                name='Questions',
            )
        )

        # Quadrant reference lines
        fig.add_hline(
            y=0.3,
            line=dict(color='black', width=2, dash='dash'),
        )
        fig.add_vline(
            x=0.5,
            line=dict(color='black', width=2, dash='dash'),
        )

        # Quadrant annotations
        annotations = [
            dict(x=0.75, y=0.65, text="<b>IDEAL</b><br>Easy & Discriminating", showarrow=False),
            dict(x=0.25, y=0.65, text="<b>CHALLENGING</b><br>Hard & Discriminating", showarrow=False),
            dict(x=0.75, y=0.15, text="<b>TOO EASY</b><br>Low Discrimination", showarrow=False),
            dict(x=0.25, y=0.15, text="<b>PROBLEMATIC</b><br>Hard & Poor Discrimination", showarrow=False),
        ]

        for ann in annotations:
            ann.update(
                font=dict(size=11, color='#666666'),
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='#cccccc',
                borderwidth=1,
                borderpad=4,
            )

        fig.update_layout(annotations=annotations)

        # Legend for quality categories (add invisible traces)
        for quality, color in QUALITY_COLORS.items():
            fig.add_trace(
                go.Scatter(
                    x=[None],
                    y=[None],
                    mode='markers',
                    marker=dict(size=15, color=color),
                    name=quality.capitalize(),
                    showlegend=True,
                )
            )

        # Update layout
        fig.update_layout(
            title=dict(
                text="Discrimination vs. Difficulty Analysis<br>"
                     "<sub>Bubble size represents question weight</sub>",
                font=dict(size=18),
            ),
            xaxis=dict(
                title="Difficulty Index (P-value)<br><sub>← Harder | Easier →</sub>",
                range=[-0.05, 1.05],
                gridcolor='lightgray',
                showgrid=True,
            ),
            yaxis=dict(
                title="Discrimination Index<br><sub>← Lower | Higher →</sub>",
                range=[-0.05, 0.8],
                gridcolor='lightgray',
                showgrid=True,
            ),
            template=self.template,
            hovermode='closest',
            height=700,
            legend=dict(
                title="Quality Category",
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99,
            ),
        )

        return fig

    def create_interactive_weights(self, df: pd.DataFrame) -> go.Figure:
        """Create interactive weight comparison chart with sorting.

        Args:
            df: Question metrics DataFrame

        Returns:
            Plotly figure with sortable weight comparison
        """
        fig = go.Figure()

        # Current weights
        fig.add_trace(
            go.Bar(
                name='Current Weight',
                x=[f"Q{int(q)}" for q in df['question_number']],
                y=df['current_weight'],
                marker_color=COLORBLIND_PALETTE['blue'],
                text=df['current_weight'].round(1),
                textposition='outside',
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Current Weight: %{y:.2f}<br>"
                    "<extra></extra>"
                ),
            )
        )

        # Recommended weights
        fig.add_trace(
            go.Bar(
                name='Recommended Weight',
                x=[f"Q{int(q)}" for q in df['question_number']],
                y=df['recommended_weight'],
                marker_color=COLORBLIND_PALETTE['orange'],
                text=df['recommended_weight'].round(1),
                textposition='outside',
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Recommended Weight: %{y:.2f}<br>"
                    "Change: %{customdata:+.2f}<br>"
                    "<extra></extra>"
                ),
                customdata=df['recommended_weight'] - df['current_weight'],
            )
        )

        # Add difference indicators
        for idx, row in df.iterrows():
            diff = row['recommended_weight'] - row['current_weight']
            if abs(diff) > 0.3:
                color = COLORBLIND_PALETTE['green'] if diff > 0 else COLORBLIND_PALETTE['vermillion']
                symbol = '▲' if diff > 0 else '▼'
                fig.add_annotation(
                    x=f"Q{int(row['question_number'])}",
                    y=max(row['current_weight'], row['recommended_weight']) + 0.5,
                    text=f"{symbol} {diff:+.1f}",
                    showarrow=False,
                    font=dict(color=color, size=10, family='Arial Black'),
                )

        # Update layout
        fig.update_layout(
            title=dict(
                text="Current vs. Recommended Question Weights",
                font=dict(size=18),
            ),
            xaxis=dict(
                title="Question",
                tickangle=-45,
            ),
            yaxis=dict(
                title="Weight",
                gridcolor='lightgray',
            ),
            barmode='group',
            template=self.template,
            height=500,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99,
            ),
        )

        # Add sorting buttons
        fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    direction="left",
                    buttons=[
                        dict(
                            args=[{
                                "x": [
                                    [f"Q{int(q)}" for q in df['question_number']],
                                    [f"Q{int(q)}" for q in df['question_number']],
                                ]
                            }],
                            label="By Question #",
                            method="restyle"
                        ),
                        dict(
                            args=[{
                                "x": [
                                    [f"Q{int(q)}" for q in df.sort_values('current_weight', ascending=False)['question_number']],
                                    [f"Q{int(q)}" for q in df.sort_values('current_weight', ascending=False)['question_number']],
                                ]
                            }],
                            label="By Current Weight",
                            method="restyle"
                        ),
                        dict(
                            args=[{
                                "x": [
                                    [f"Q{int(q)}" for q in df.sort_values('recommended_weight', ascending=False)['question_number']],
                                    [f"Q{int(q)}" for q in df.sort_values('recommended_weight', ascending=False)['question_number']],
                                ]
                            }],
                            label="By Recommended",
                            method="restyle"
                        ),
                    ],
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    x=0.5,
                    xanchor="center",
                    y=1.15,
                    yanchor="top"
                ),
            ]
        )

        return fig

    def create_correlation_heatmap(
        self,
        df: pd.DataFrame,
        raw_student_data: Optional[pd.DataFrame] = None,
    ) -> go.Figure:
        """Create inter-question correlation heatmap.

        Args:
            df: Question metrics DataFrame
            raw_student_data: Optional raw scores (students x questions)

        Returns:
            Plotly figure with correlation heatmap
        """
        # Compute correlation matrix
        if raw_student_data is not None and not raw_student_data.empty:
            corr_matrix = raw_student_data.corr()
        else:
            # Simulate correlation based on discrimination indices
            # (In practice, this would come from actual student data)
            n_questions = len(df)
            corr_matrix = np.eye(n_questions)

            # Add some structure based on difficulty similarity
            for i in range(n_questions):
                for j in range(i + 1, n_questions):
                    # Similar difficulty = higher correlation
                    diff_similarity = 1 - abs(
                        df.iloc[i]['difficulty_index'] - df.iloc[j]['difficulty_index']
                    )
                    corr = 0.2 + 0.5 * diff_similarity + np.random.normal(0, 0.1)
                    corr = np.clip(corr, -1, 1)
                    corr_matrix[i, j] = corr
                    corr_matrix[j, i] = corr

            corr_matrix = pd.DataFrame(
                corr_matrix,
                index=[f"Q{int(q)}" for q in df['question_number']],
                columns=[f"Q{int(q)}" for q in df['question_number']],
            )

        # Create heatmap
        fig = go.Figure(
            data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.index,
                colorscale='RdBu_r',
                zmid=0,
                zmin=-1,
                zmax=1,
                text=np.round(corr_matrix.values, 2),
                texttemplate="%{text}",
                textfont={"size": 9},
                hovertemplate=(
                    "%{y} vs %{x}<br>"
                    "Correlation: %{z:.3f}<br>"
                    "<extra></extra>"
                ),
                colorbar=dict(
                    title="Correlation",
                    titleside="right",
                ),
            )
        )

        # Highlight potentially redundant questions (high correlation)
        redundant_pairs = []
        for i in range(len(corr_matrix)):
            for j in range(i + 1, len(corr_matrix)):
                if corr_matrix.iloc[i, j] > 0.8:
                    redundant_pairs.append((corr_matrix.index[i], corr_matrix.columns[j]))

        # Add annotations for redundant pairs
        if redundant_pairs:
            annotation_text = "High correlation pairs (potential redundancy):<br>" + "<br>".join(
                [f"{p[0]} ↔ {p[1]}" for p in redundant_pairs[:5]]
            )
            fig.add_annotation(
                x=0.5,
                y=-0.15,
                xref="paper",
                yref="paper",
                text=annotation_text,
                showarrow=False,
                font=dict(size=10, color=COLORBLIND_PALETTE['vermillion']),
                bgcolor='rgba(255, 255, 255, 0.9)',
                bordercolor=COLORBLIND_PALETTE['vermillion'],
                borderwidth=1,
            )

        # Update layout
        fig.update_layout(
            title=dict(
                text="Inter-Question Correlation Matrix<br>"
                     "<sub>Identifies potentially redundant questions</sub>",
                font=dict(size=18),
            ),
            xaxis=dict(
                title="Question",
                tickangle=-45,
                side="bottom",
            ),
            yaxis=dict(
                title="Question",
                autorange="reversed",
            ),
            template=self.template,
            height=600,
            width=700,
        )

        return fig

    def create_student_distribution(
        self,
        test_statistics: TestStatistics,
    ) -> go.Figure:
        """Create student score distribution with percentile markers.

        Args:
            test_statistics: Overall test statistics

        Returns:
            Plotly figure with student distribution histogram
        """
        # Get or simulate student scores
        if (test_statistics.student_total_scores is not None and
                len(test_statistics.student_total_scores) > 0):
            scores = test_statistics.student_total_scores
        else:
            # Simulate distribution
            scores = np.random.normal(
                test_statistics.mean_total_score,
                test_statistics.std_dev_total_score,
                test_statistics.total_students
            )
            scores = np.clip(scores, test_statistics.min_total_score, test_statistics.max_total_score)

        fig = go.Figure()

        # Main histogram
        fig.add_trace(
            go.Histogram(
                x=scores,
                nbinsx=30,
                name='Score Distribution',
                marker=dict(
                    color=COLORBLIND_PALETTE['sky_blue'],
                    line=dict(color='white', width=1)
                ),
                opacity=0.8,
                hovertemplate=(
                    "Score Range: %{x}<br>"
                    "Count: %{y}<br>"
                    "<extra></extra>"
                ),
            )
        )

        # Add vertical lines for key statistics
        # Mean
        fig.add_vline(
            x=test_statistics.mean_total_score,
            line=dict(color=COLORBLIND_PALETTE['blue'], width=3),
            annotation_text=f"Mean: {test_statistics.mean_total_score:.1f}",
            annotation_position="top",
        )

        # Median
        fig.add_vline(
            x=test_statistics.median_total_score,
            line=dict(color=COLORBLIND_PALETTE['orange'], width=3, dash='dash'),
            annotation_text=f"Median: {test_statistics.median_total_score:.1f}",
            annotation_position="top left",
        )

        # Upper and lower 27% cutoffs
        fig.add_vline(
            x=test_statistics.upper_27_cutoff,
            line=dict(color=COLORBLIND_PALETTE['green'], width=2, dash='dot'),
            annotation_text=f"Upper 27%: {test_statistics.upper_27_cutoff:.1f}",
            annotation_position="top right",
        )

        fig.add_vline(
            x=test_statistics.lower_27_cutoff,
            line=dict(color=COLORBLIND_PALETTE['vermillion'], width=2, dash='dot'),
            annotation_text=f"Lower 27%: {test_statistics.lower_27_cutoff:.1f}",
            annotation_position="top left",
        )

        # Shade upper and lower 27% regions
        fig.add_vrect(
            x0=test_statistics.upper_27_cutoff,
            x1=test_statistics.max_total_score,
            fillcolor=COLORBLIND_PALETTE['green'],
            opacity=0.1,
            layer="below",
            line_width=0,
        )
        fig.add_vrect(
            x0=test_statistics.min_total_score,
            x1=test_statistics.lower_27_cutoff,
            fillcolor=COLORBLIND_PALETTE['vermillion'],
            opacity=0.1,
            layer="below",
            line_width=0,
        )

        # Add summary statistics box
        stats_text = (
            f"<b>Summary Statistics</b><br>"
            f"N Students: {test_statistics.total_students}<br>"
            f"Mean: {test_statistics.mean_total_score:.2f}<br>"
            f"Median: {test_statistics.median_total_score:.2f}<br>"
            f"Std Dev: {test_statistics.std_dev_total_score:.2f}<br>"
            f"Skewness: {test_statistics.skewness:.3f}<br>"
            f"Kurtosis: {test_statistics.kurtosis:.3f}<br>"
            f"Cronbach's α: {test_statistics.cronbach_alpha:.3f}<br>"
            f"SEM: {test_statistics.sem:.2f}"
        )

        fig.add_annotation(
            x=0.02,
            y=0.98,
            xref="paper",
            yref="paper",
            text=stats_text,
            showarrow=False,
            font=dict(size=11),
            align="left",
            bgcolor="rgba(255, 255, 255, 0.95)",
            bordercolor="#cccccc",
            borderwidth=1,
            borderpad=6,
        )

        # Update layout
        fig.update_layout(
            title=dict(
                text="Student Total Score Distribution",
                font=dict(size=18),
            ),
            xaxis=dict(
                title="Total Score",
                gridcolor='lightgray',
            ),
            yaxis=dict(
                title="Number of Students",
                gridcolor='lightgray',
            ),
            template=self.template,
            height=500,
            showlegend=False,
        )

        return fig
