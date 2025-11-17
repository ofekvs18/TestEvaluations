"""Excel static visualization generator using matplotlib and seaborn.

Creates publication-ready static charts for embedding in Excel reports.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns

from ..models.metrics import TestStatistics
from ..utils.colors import (
    COLORBLIND_PALETTE,
    QUALITY_COLORS,
    get_quality_colors_list,
    get_discrimination_quality_color,
)


class ExcelVisualizationGenerator:
    """Generates static visualizations for Excel reports.

    Creates high-quality, publication-ready charts using matplotlib and seaborn.
    All charts are designed to be colorblind-friendly.
    """

    def __init__(self, output_dir: str = "output"):
        """Initialize the generator.

        Args:
            output_dir: Directory to save generated images
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Set matplotlib style for professional appearance
        self._setup_style()

    def _setup_style(self) -> None:
        """Configure matplotlib for professional, colorblind-friendly plots."""
        plt.style.use('seaborn-v0_8-whitegrid')
        plt.rcParams.update({
            'font.size': 10,
            'axes.titlesize': 12,
            'axes.labelsize': 11,
            'xtick.labelsize': 9,
            'ytick.labelsize': 9,
            'legend.fontsize': 9,
            'figure.titlesize': 14,
            'figure.dpi': 150,
            'savefig.dpi': 300,
            'savefig.bbox': 'tight',
            'figure.facecolor': 'white',
            'axes.facecolor': 'white',
            'axes.edgecolor': '#333333',
            'axes.linewidth': 1.0,
            'grid.alpha': 0.3,
        })

    def generate_all(
        self,
        question_metrics_df: pd.DataFrame,
        test_statistics: TestStatistics,
        difficulty_order: List[int],
        curve_breakers: List[int],
    ) -> Dict[str, str]:
        """Generate all Excel visualizations.

        Args:
            question_metrics_df: DataFrame with question metrics
            test_statistics: Overall test statistics
            difficulty_order: Indices of questions sorted by difficulty
            curve_breakers: Indices of curve-breaking questions

        Returns:
            Dictionary mapping chart names to file paths
        """
        paths = {}

        # Generate each chart
        paths['difficulty_curve'] = self.create_difficulty_curve(
            question_metrics_df, difficulty_order, curve_breakers
        )
        paths['scatter'] = self.create_discrimination_difficulty_scatter(
            question_metrics_df
        )
        paths['weights'] = self.create_weights_comparison(question_metrics_df)
        paths['quality'] = self.create_quality_distribution(question_metrics_df)

        return paths

    def create_difficulty_curve(
        self,
        df: pd.DataFrame,
        difficulty_order: List[int],
        curve_breakers: List[int],
    ) -> str:
        """Create difficulty curve chart with outliers marked.

        Args:
            df: Question metrics DataFrame
            difficulty_order: Indices sorted by difficulty
            curve_breakers: Indices of outlier questions

        Returns:
            Path to saved image
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        # Sort by difficulty order
        sorted_df = df.iloc[difficulty_order].reset_index(drop=True)

        # Plot actual difficulty curve
        x = range(len(sorted_df))
        y = sorted_df['difficulty_index'].values

        ax.plot(
            x, y,
            marker='o',
            linewidth=2,
            markersize=8,
            color=COLORBLIND_PALETTE['blue'],
            label='Actual Difficulty',
            zorder=5
        )

        # Create ideal smooth curve (linear from easy to hard)
        ideal_y = np.linspace(max(y), min(y), len(y))
        ax.plot(
            x, ideal_y,
            linewidth=2,
            linestyle='--',
            color=COLORBLIND_PALETTE['black'],
            alpha=0.5,
            label='Ideal Curve',
            zorder=3
        )

        # Mark curve breakers (outliers)
        if curve_breakers:
            breaker_indices = []
            breaker_values = []
            for idx in curve_breakers:
                # Find position in sorted order
                pos = np.where(sorted_df['question_number'] == df.iloc[idx]['question_number'])[0]
                if len(pos) > 0:
                    breaker_indices.append(pos[0])
                    breaker_values.append(sorted_df.iloc[pos[0]]['difficulty_index'])

            ax.scatter(
                breaker_indices,
                breaker_values,
                s=200,
                facecolors='none',
                edgecolors=COLORBLIND_PALETTE['vermillion'],
                linewidths=3,
                label='Curve Breakers',
                zorder=10
            )

        # Add question labels
        for i, row in sorted_df.iterrows():
            ax.annotate(
                f"Q{int(row['question_number'])}",
                (i, row['difficulty_index']),
                xytext=(0, 10),
                textcoords='offset points',
                ha='center',
                fontsize=7,
                alpha=0.8
            )

        # Reference lines
        ax.axhline(y=0.3, color=COLORBLIND_PALETTE['orange'], linestyle=':', alpha=0.7, linewidth=1)
        ax.axhline(y=0.7, color=COLORBLIND_PALETTE['orange'], linestyle=':', alpha=0.7, linewidth=1)

        ax.text(len(x) - 0.5, 0.31, 'Too Hard', ha='right', fontsize=8, color=COLORBLIND_PALETTE['orange'])
        ax.text(len(x) - 0.5, 0.71, 'Too Easy', ha='right', fontsize=8, color=COLORBLIND_PALETTE['orange'])

        # Formatting
        ax.set_xlabel('Question (sorted by difficulty)', fontweight='bold')
        ax.set_ylabel('Difficulty Index (P-value)', fontweight='bold')
        ax.set_title('Test Difficulty Curve Analysis', fontweight='bold', pad=20)
        ax.set_ylim(-0.05, 1.05)
        ax.set_xlim(-0.5, len(x) - 0.5)
        ax.legend(loc='upper right', framealpha=0.9)
        ax.grid(True, alpha=0.3)

        # Save
        filepath = self.output_dir / 'difficulty_curve.png'
        fig.savefig(filepath)
        plt.close(fig)

        return str(filepath)

    def create_discrimination_difficulty_scatter(self, df: pd.DataFrame) -> str:
        """Create 4-quadrant scatter plot of discrimination vs difficulty.

        Args:
            df: Question metrics DataFrame

        Returns:
            Path to saved image
        """
        fig, ax = plt.subplots(figsize=(10, 10))

        # Assign colors based on quality category
        colors = df['quality_category'].map(QUALITY_COLORS).values

        # Create scatter plot
        scatter = ax.scatter(
            df['difficulty_index'],
            df['discrimination_index'],
            c=colors,
            s=150,
            alpha=0.8,
            edgecolors='white',
            linewidths=1.5,
            zorder=5
        )

        # Add question number labels
        for idx, row in df.iterrows():
            ax.annotate(
                f"Q{int(row['question_number'])}",
                (row['difficulty_index'], row['discrimination_index']),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=8,
                fontweight='bold',
                alpha=0.9
            )

        # Quadrant lines
        ax.axhline(y=0.3, color=COLORBLIND_PALETTE['black'], linestyle='--', linewidth=1.5, alpha=0.7)
        ax.axvline(x=0.5, color=COLORBLIND_PALETTE['black'], linestyle='--', linewidth=1.5, alpha=0.7)

        # Quadrant labels with backgrounds
        bbox_props = dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8, edgecolor='gray')

        ax.text(0.75, 0.55, 'IDEAL\n(Easy & Discriminating)',
                ha='center', va='center', fontsize=9, fontweight='bold', bbox=bbox_props)
        ax.text(0.25, 0.55, 'REVIEW\n(Hard & Discriminating)',
                ha='center', va='center', fontsize=9, fontweight='bold', bbox=bbox_props)
        ax.text(0.75, 0.15, 'TOO EASY\n(Easy & Low Discrimination)',
                ha='center', va='center', fontsize=9, fontweight='bold', bbox=bbox_props)
        ax.text(0.25, 0.15, 'PROBLEMATIC\n(Hard & Low Discrimination)',
                ha='center', va='center', fontsize=9, fontweight='bold', bbox=bbox_props)

        # Reference zones with subtle coloring
        ax.axhspan(0.3, 1.0, xmin=0.5, xmax=1.0, alpha=0.05, color=QUALITY_COLORS['good'])
        ax.axhspan(0, 0.3, xmin=0, xmax=0.5, alpha=0.05, color=QUALITY_COLORS['poor'])

        # Legend for quality categories
        legend_elements = [
            mpatches.Patch(facecolor=QUALITY_COLORS['good'], label='Good Quality'),
            mpatches.Patch(facecolor=QUALITY_COLORS['review'], label='Needs Review'),
            mpatches.Patch(facecolor=QUALITY_COLORS['poor'], label='Poor Quality'),
        ]
        ax.legend(handles=legend_elements, loc='upper left', framealpha=0.9)

        # Formatting
        ax.set_xlabel('Difficulty Index (P-value)\n← Harder | Easier →', fontweight='bold', fontsize=11)
        ax.set_ylabel('Discrimination Index\n← Lower | Higher →', fontweight='bold', fontsize=11)
        ax.set_title('Item Discrimination vs. Difficulty Analysis', fontweight='bold', pad=20, fontsize=14)
        ax.set_xlim(-0.05, 1.05)
        ax.set_ylim(-0.05, 1.0)
        ax.grid(True, alpha=0.3)

        # Save
        filepath = self.output_dir / 'discrimination_difficulty_scatter.png'
        fig.savefig(filepath)
        plt.close(fig)

        return str(filepath)

    def create_weights_comparison(self, df: pd.DataFrame) -> str:
        """Create grouped bar chart comparing current vs recommended weights.

        Args:
            df: Question metrics DataFrame

        Returns:
            Path to saved image
        """
        fig, ax = plt.subplots(figsize=(14, 6))

        x = np.arange(len(df))
        width = 0.35

        # Create bars
        bars1 = ax.bar(
            x - width/2,
            df['current_weight'],
            width,
            label='Current Weight',
            color=COLORBLIND_PALETTE['blue'],
            alpha=0.8,
            edgecolor='white',
            linewidth=1
        )
        bars2 = ax.bar(
            x + width/2,
            df['recommended_weight'],
            width,
            label='Recommended Weight',
            color=COLORBLIND_PALETTE['orange'],
            alpha=0.8,
            edgecolor='white',
            linewidth=1
        )

        # Add value labels on bars
        def add_value_labels(bars):
            for bar in bars:
                height = bar.get_height()
                ax.annotate(
                    f'{height:.1f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center',
                    va='bottom',
                    fontsize=7,
                    fontweight='bold'
                )

        add_value_labels(bars1)
        add_value_labels(bars2)

        # Highlight significant differences
        for i, row in df.iterrows():
            diff = row['recommended_weight'] - row['current_weight']
            if abs(diff) > 0.5:  # Significant difference threshold
                color = COLORBLIND_PALETTE['green'] if diff > 0 else COLORBLIND_PALETTE['vermillion']
                arrow_y = max(row['current_weight'], row['recommended_weight']) + 0.3
                ax.annotate(
                    '',
                    xy=(i + width/2, row['recommended_weight']),
                    xytext=(i - width/2, row['current_weight']),
                    arrowprops=dict(arrowstyle='->', color=color, lw=2)
                )

        # Formatting
        ax.set_xlabel('Question Number', fontweight='bold')
        ax.set_ylabel('Weight', fontweight='bold')
        ax.set_title('Current vs. Recommended Question Weights', fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels([f"Q{int(q)}" for q in df['question_number']], rotation=45, ha='right')
        ax.legend(loc='upper right', framealpha=0.9)
        ax.grid(True, axis='y', alpha=0.3)

        # Add average lines
        avg_current = df['current_weight'].mean()
        avg_recommended = df['recommended_weight'].mean()
        ax.axhline(y=avg_current, color=COLORBLIND_PALETTE['blue'], linestyle=':', alpha=0.7, linewidth=1.5)
        ax.axhline(y=avg_recommended, color=COLORBLIND_PALETTE['orange'], linestyle=':', alpha=0.7, linewidth=1.5)

        ax.text(len(x) - 0.5, avg_current + 0.1, f'Avg Current: {avg_current:.2f}',
                ha='right', fontsize=8, color=COLORBLIND_PALETTE['blue'])
        ax.text(len(x) - 0.5, avg_recommended + 0.1, f'Avg Recommended: {avg_recommended:.2f}',
                ha='right', fontsize=8, color=COLORBLIND_PALETTE['orange'])

        plt.tight_layout()

        # Save
        filepath = self.output_dir / 'weights_comparison.png'
        fig.savefig(filepath)
        plt.close(fig)

        return str(filepath)

    def create_quality_distribution(self, df: pd.DataFrame) -> str:
        """Create chart showing distribution of question quality categories.

        Args:
            df: Question metrics DataFrame

        Returns:
            Path to saved image
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Count categories
        quality_counts = df['quality_category'].value_counts()

        # Ensure all categories are present
        all_categories = ['good', 'review', 'poor']
        counts = [quality_counts.get(cat, 0) for cat in all_categories]
        colors = get_quality_colors_list()
        labels = ['Good', 'Needs Review', 'Poor']

        # Pie chart
        wedges, texts, autotexts = ax1.pie(
            counts,
            labels=labels,
            colors=colors,
            autopct=lambda pct: f'{pct:.1f}%\n({int(pct/100*sum(counts))})',
            startangle=90,
            explode=[0.02, 0.02, 0.02],
            shadow=False,
            textprops={'fontsize': 10, 'fontweight': 'bold'}
        )

        # Style autopct text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        ax1.set_title('Quality Distribution (Pie Chart)', fontweight='bold', pad=20)

        # Bar chart
        bars = ax2.bar(labels, counts, color=colors, edgecolor='white', linewidth=2)

        # Add value labels
        for bar, count in zip(bars, counts):
            percentage = (count / sum(counts)) * 100 if sum(counts) > 0 else 0
            ax2.annotate(
                f'{count}\n({percentage:.1f}%)',
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center',
                va='bottom',
                fontsize=11,
                fontweight='bold'
            )

        ax2.set_xlabel('Quality Category', fontweight='bold')
        ax2.set_ylabel('Number of Questions', fontweight='bold')
        ax2.set_title('Quality Distribution (Bar Chart)', fontweight='bold', pad=20)
        ax2.grid(True, axis='y', alpha=0.3)

        # Overall title
        fig.suptitle('Test Question Quality Assessment', fontsize=14, fontweight='bold', y=1.02)

        plt.tight_layout()

        # Save
        filepath = self.output_dir / 'quality_distribution.png'
        fig.savefig(filepath)
        plt.close(fig)

        return str(filepath)
