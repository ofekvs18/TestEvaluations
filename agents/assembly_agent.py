"""
Final Assembly Agent for Test Analysis System

Receives outputs from all three analysis agents and creates final deliverables:
- Excel workbook with multiple sheets
- Interactive HTML report
- Summary text report
"""

import io
import base64
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import ColorScaleRule, CellIsRule
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.chart import PieChart, BarChart, Reference
from openpyxl.chart.series import DataPoint
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.drawing.image import Image as XLImage
from openpyxl.drawing.fill import SolidColorFillProperties, ColorChoice


class AssemblyAgent:
    """Final assembly agent that combines outputs from all analysis agents."""

    def __init__(self, output_dir: str = "."):
        """
        Initialize the assembly agent.

        Args:
            output_dir: Directory to save output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def assemble(
        self,
        metrics_output: Dict[str, Any],
        visualizations_output: Dict[str, Any],
        recommendations_output: Dict[str, Any],
        original_filename: str
    ) -> Dict[str, Any]:
        """
        Assemble all agent outputs into final deliverables.

        Args:
            metrics_output: Output from Agent 1 (metrics calculation)
            visualizations_output: Output from Agent 2 (visualizations)
            recommendations_output: Output from Agent 3 (recommendations)
            original_filename: Original input filename for naming outputs

        Returns:
            Dictionary with status and file paths
        """
        base_name = Path(original_filename).stem

        # Create all output files
        excel_path = self._create_excel_workbook(
            metrics_output, visualizations_output, recommendations_output, base_name
        )

        html_path = self._create_html_report(
            metrics_output, visualizations_output, recommendations_output, base_name
        )

        summary_path = self._create_summary_text(
            metrics_output, visualizations_output, recommendations_output, base_name
        )

        # Print summary to console
        self._print_summary(metrics_output, recommendations_output)

        return {
            "status": "success",
            "files": {
                "excel": str(excel_path),
                "html": str(html_path),
                "summary": str(summary_path)
            }
        }

    def _create_excel_workbook(
        self,
        metrics_output: Dict[str, Any],
        visualizations_output: Dict[str, Any],
        recommendations_output: Dict[str, Any],
        base_name: str
    ) -> Path:
        """Create multi-sheet Excel workbook."""
        wb = Workbook()

        # Remove default sheet
        wb.remove(wb.active)

        # Sheet 1: Question Analysis
        self._add_question_analysis_sheet(wb, recommendations_output)

        # Sheet 2: Recommendations
        self._add_recommendations_sheet(wb, recommendations_output)

        # Sheet 3: Visualizations
        self._add_visualizations_sheet(wb, visualizations_output)

        # Sheet 4: Question Score Distributions
        self._add_question_distributions_sheet(wb, visualizations_output, recommendations_output)

        # Save workbook
        output_path = self.output_dir / f"{base_name}_analysis.xlsx"
        wb.save(output_path)

        return output_path

    def _add_question_analysis_sheet(self, wb: Workbook, recommendations_output: Dict[str, Any]):
        """Add Question Analysis sheet with formatted data."""
        ws = wb.create_sheet("Question Analysis")

        # Get question analysis data
        question_data = recommendations_output.get("question_analysis", [])
        if not question_data:
            ws.cell(row=1, column=1, value="No question analysis data available")
            return

        # Add metric explanations and thresholds at the top
        ws.cell(row=1, column=1, value="Metrics Explanation:")
        ws.cell(row=1, column=1).font = Font(bold=True, size=12)

        explanations = [
            ("Difficulty", "How hard the question is (0=very easy, 1=very hard). Higher values mean fewer students answered correctly."),
            ("Discrimination", "How well the question differentiates between high and low performers. Higher values are better."),
            ("", ""),  # Blank row
            ("Quality Thresholds:", ""),
            ("Discrimination", "< 0.15 = Poor | 0.15-0.30 = Low | >= 0.30 = Good"),
            ("Difficulty", "< 0.20 (too easy) or > 0.80 (too hard) = Poor | 0.20-0.80 = Acceptable | 0.30-0.70 = Ideal"),
        ]

        current_row = 2
        for label, value in explanations:
            if label:
                ws.cell(row=current_row, column=1, value=label).font = Font(bold=True)
            ws.cell(row=current_row, column=2, value=value)
            current_row += 1

        # Add spacing
        current_row += 1

        # Convert to DataFrame for easier handling
        df = pd.DataFrame(question_data)

        # Write headers
        headers = list(df.columns)
        header_row = current_row
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=header_row, column=col_idx, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Write data
        data_start_row = header_row + 1
        for row_idx, row in enumerate(df.itertuples(index=False), data_start_row):
            for col_idx, value in enumerate(row, 1):
                # Convert lists to comma-separated strings for Excel compatibility
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                ws.cell(row=row_idx, column=col_idx, value=value)

        # Auto-adjust column widths
        self._auto_adjust_columns(ws)

        # Add filters (from header row to end)
        ws.auto_filter.ref = f"A{header_row}:{ws.dimensions.split(':')[1]}"

    def _add_classification_breakdown_sheet(self, wb: Workbook, recommendations_output: Dict[str, Any]):
        """Add Classification Decision Logic sheet showing why each question was classified."""
        ws = wb.create_sheet("Classification Decision Logic")

        # Get question analysis data
        question_data = recommendations_output.get("question_analysis", [])
        if not question_data:
            ws.cell(row=1, column=1, value="No question analysis data available")
            return

        # Add title
        title_cell = ws.cell(row=1, column=1, value="Question Classification Decision Breakdown")
        title_cell.font = Font(bold=True, size=16, color="FFFFFF")
        title_cell.fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
        ws.merge_cells('A1:D1')

        # Add explanation
        explanation = ws.cell(row=2, column=1,
            value="This sheet explains the step-by-step decision logic for classifying each question's quality.")
        explanation.font = Font(italic=True)
        ws.merge_cells('A2:D2')

        # Add thresholds reference
        ws.cell(row=4, column=1, value="Quality Thresholds Reference:")
        ws.cell(row=4, column=1).font = Font(bold=True, size=12)

        thresholds = [
            ("Discrimination", "< 0.15 = Poor | 0.15-0.30 = Low | ≥ 0.30 = Good"),
            ("Difficulty", "< 0.20 or > 0.80 = Poor | 0.20-0.80 = Acceptable | 0.30-0.70 = Ideal"),
            ("", ""),
        ]

        current_row = 5
        for label, value in thresholds:
            ws.cell(row=current_row, column=1, value=label).font = Font(bold=True)
            ws.cell(row=current_row, column=2, value=value)
            current_row += 1

        # Headers for question breakdown
        current_row += 1
        headers = ["Question", "Difficulty", "Discrimination", "Quality", "Decision Logic Explanation"]
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=current_row, column=col_idx, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        current_row += 1

        # Add each question's breakdown
        for q_data in question_data:
            question_id = q_data.get("question_id", "N/A")
            difficulty = q_data.get("difficulty", 0.0)
            discrimination = q_data.get("discrimination", 0.0)
            quality = q_data.get("quality", "N/A")
            explanation = q_data.get("classification_reason", "No explanation available")

            # Question ID
            ws.cell(row=current_row, column=1, value=question_id)

            # Difficulty with color coding
            diff_cell = ws.cell(row=current_row, column=2, value=f"{difficulty:.3f}")
            if difficulty < 0.2 or difficulty > 0.8:
                diff_cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")  # Red
            elif 0.3 <= difficulty <= 0.7:
                diff_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")  # Green
            else:
                diff_cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")  # Yellow

            # Discrimination with color coding
            disc_cell = ws.cell(row=current_row, column=3, value=f"{discrimination:.3f}")
            if discrimination < 0.15:
                disc_cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")  # Red
            elif discrimination >= 0.3:
                disc_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")  # Green
            else:
                disc_cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")  # Yellow

            # Quality with color coding
            quality_cell = ws.cell(row=current_row, column=4, value=quality)
            quality_cell.font = Font(bold=True)
            if quality == "Good":
                quality_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")  # Green
            elif quality == "Review":
                quality_cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")  # Yellow
            else:
                quality_cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")  # Red

            # Explanation with word wrap
            explanation_cell = ws.cell(row=current_row, column=5, value=explanation)
            explanation_cell.alignment = Alignment(wrap_text=True, vertical="top")

            current_row += 1

        # Set column widths
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 12
        ws.column_dimensions['E'].width = 100  # Wide for explanation

        # Set row heights for better readability
        for row_num in range(9, current_row):
            ws.row_dimensions[row_num].height = 40

    def _add_question_rankings_sheet(self, wb: Workbook, recommendations_output: Dict[str, Any]):
        """Add Question Rankings sheet."""
        ws = wb.create_sheet("Question Rankings")

        rankings = recommendations_output.get("question_rankings", {})
        if not rankings:
            ws.cell(row=1, column=1, value="No ranking data available")
            return

        current_row = 1

        # Add each ranking category
        for category, questions in rankings.items():
            # Category header
            cell = ws.cell(row=current_row, column=1, value=category.replace("_", " ").title())
            cell.font = Font(bold=True, size=14)
            current_row += 1

            if isinstance(questions, list) and questions:
                # Write question data
                if isinstance(questions[0], dict):
                    df = pd.DataFrame(questions)

                    # Headers
                    for col_idx, col in enumerate(df.columns, 1):
                        cell = ws.cell(row=current_row, column=col_idx, value=col)
                        cell.font = Font(bold=True)
                        cell.fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
                    current_row += 1

                    # Data
                    for _, row in df.iterrows():
                        for col_idx, value in enumerate(row, 1):
                            # Convert lists to comma-separated strings
                            if isinstance(value, list):
                                value = ", ".join(str(v) for v in value)
                            ws.cell(row=current_row, column=col_idx, value=value)
                        current_row += 1
                else:
                    # Simple list
                    for item in questions:
                        ws.cell(row=current_row, column=1, value=str(item))
                        current_row += 1

            current_row += 1  # Empty row between categories

        self._auto_adjust_columns(ws)

    def _add_distribution_details_sheet(self, wb: Workbook, recommendations_output: Dict[str, Any]):
        """Add Distribution Details sheet."""
        ws = wb.create_sheet("Distribution Details")

        distributions = recommendations_output.get("distribution_details", {})
        if not distributions:
            ws.cell(row=1, column=1, value="No distribution data available")
            return

        current_row = 1

        for category, data in distributions.items():
            # Category header
            cell = ws.cell(row=current_row, column=1, value=category.replace("_", " ").title())
            cell.font = Font(bold=True, size=14)
            current_row += 1

            if isinstance(data, dict):
                for key, value in data.items():
                    ws.cell(row=current_row, column=1, value=key)
                    # Convert lists to comma-separated strings
                    if isinstance(value, list):
                        value = ", ".join(str(v) for v in value)
                    ws.cell(row=current_row, column=2, value=value)
                    current_row += 1
            elif isinstance(data, list):
                for item in data:
                    ws.cell(row=current_row, column=1, value=str(item))
                    current_row += 1

            current_row += 1

        self._auto_adjust_columns(ws)

    def _add_recommendations_sheet(self, wb: Workbook, recommendations_output: Dict[str, Any]):
        """Add Recommendations sheet."""
        ws = wb.create_sheet("Recommendations")

        recommendations = recommendations_output.get("recommendations", [])
        if not recommendations:
            ws.cell(row=1, column=1, value="No recommendations available")
            return

        # Header
        cell = ws.cell(row=1, column=1, value="Test Improvement Recommendations")
        cell.font = Font(bold=True, size=16)

        current_row = 3

        if isinstance(recommendations, list):
            for idx, rec in enumerate(recommendations, 1):
                if isinstance(rec, dict):
                    # Priority
                    priority = rec.get("priority", "Medium")
                    priority_cell = ws.cell(row=current_row, column=1, value=f"Priority: {priority}")

                    # Color code by priority
                    if priority.lower() == "high":
                        priority_cell.font = Font(color="FF0000", bold=True)
                    elif priority.lower() == "medium":
                        priority_cell.font = Font(color="FFA500", bold=True)
                    else:
                        priority_cell.font = Font(color="008000", bold=True)

                    current_row += 1

                    # Recommendation text
                    rec_text = rec.get("recommendation", rec.get("text", str(rec)))
                    ws.cell(row=current_row, column=1, value=rec_text)
                    current_row += 1

                    # Question IDs if available
                    if "question_ids" in rec:
                        ws.cell(row=current_row, column=1, value=f"Affected Questions: {', '.join(map(str, rec['question_ids']))}")
                        current_row += 1

                    current_row += 1  # Empty row
                else:
                    ws.cell(row=current_row, column=1, value=str(rec))
                    current_row += 1

        self._auto_adjust_columns(ws)

    def _add_visualizations_sheet(self, wb: Workbook, visualizations_output: Dict[str, Any]):
        """Add Visualizations sheet with embedded images."""
        ws = wb.create_sheet("Visualizations")

        static_images = visualizations_output.get("static_images", [])
        if not static_images:
            ws.cell(row=1, column=1, value="No visualizations available")
            return

        current_row = 1

        for img_data in static_images:
            if isinstance(img_data, dict):
                # Add title
                title = img_data.get("title", "Visualization")
                cell = ws.cell(row=current_row, column=1, value=title)
                cell.font = Font(bold=True, size=12)
                current_row += 2

                # Add image
                img_bytes = img_data.get("image_bytes")
                if img_bytes:
                    try:
                        # Create image from bytes
                        img_stream = io.BytesIO(img_bytes)
                        xl_img = XLImage(img_stream)

                        # Resize if needed
                        xl_img.width = min(xl_img.width, 800)
                        xl_img.height = min(xl_img.height, 600)

                        # Add to worksheet
                        ws.add_image(xl_img, f"A{current_row}")

                        # Move down to accommodate image
                        current_row += int(xl_img.height / 15) + 5
                    except Exception as e:
                        ws.cell(row=current_row, column=1, value=f"Error loading image: {str(e)}")
                        current_row += 2

            current_row += 2

    def _add_question_distributions_sheet(self, wb: Workbook, visualizations_output: Dict[str, Any], recommendations_output: Dict[str, Any]):
        """Add Question Score Distributions sheet showing how many students got each score."""
        ws = wb.create_sheet("Question Score Distributions")

        distributions = visualizations_output.get("question_distributions", {})
        if not distributions:
            ws.cell(row=1, column=1, value="No distribution data available")
            return

        # Get question analysis for difficulty and discrimination metrics
        question_analysis = recommendations_output.get("question_analysis", [])
        question_metrics = {q["question_id"]: q for q in question_analysis}

        # Add title
        title_cell = ws.cell(row=1, column=1, value="Per-Question Score Distribution")
        title_cell.font = Font(bold=True, size=16, color="FFFFFF")
        title_cell.fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
        ws.merge_cells('A1:E1')

        # Add explanation
        explanation = ws.cell(row=2, column=1,
            value="Shows how many students achieved each possible score for each question.")
        explanation.font = Font(italic=True)
        ws.merge_cells('A2:E2')

        # Add metric explanations
        current_row = 4
        ws.cell(row=current_row, column=1, value="Metrics Explanation:")
        ws.cell(row=current_row, column=1).font = Font(bold=True, size=11)
        current_row += 1

        explanations = [
            ("Difficulty:", "How hard the question is (0=very easy, 1=very hard). Higher values mean fewer students answered correctly."),
            ("Discrimination:", "How well the question differentiates between high and low performers. Higher values are better."),
        ]

        for label, value in explanations:
            ws.cell(row=current_row, column=1, value=label).font = Font(bold=True)
            ws.cell(row=current_row, column=2, value=value)
            ws.merge_cells(start_row=current_row, start_column=2, end_row=current_row, end_column=6)
            current_row += 1

        current_row += 1  # Add spacing

        # Add quality thresholds
        ws.cell(row=current_row, column=1, value="Quality Thresholds:")
        ws.cell(row=current_row, column=1).font = Font(bold=True, size=11)
        current_row += 1

        thresholds = [
            ("Discrimination:", "< 0.15 = Poor | 0.15-0.30 = Low | >= 0.30 = Good"),
            ("Difficulty:", "< 0.20 (too easy) or > 0.80 (too hard) = Poor | 0.20-0.80 = Acceptable | 0.30-0.70 = Ideal"),
        ]

        for label, value in thresholds:
            ws.cell(row=current_row, column=1, value=label).font = Font(bold=True)
            ws.cell(row=current_row, column=2, value=value)
            ws.merge_cells(start_row=current_row, start_column=2, end_row=current_row, end_column=6)
            current_row += 1

        current_row += 1  # Add spacing

        # Process each question
        for question_id, dist_data in distributions.items():
            # Question header
            header_cell = ws.cell(row=current_row, column=1, value=f"Question: {question_id}")
            header_cell.font = Font(bold=True, size=14, color="FFFFFF")
            header_cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=5)
            current_row += 1

            # Get metrics for this question
            metrics = question_metrics.get(question_id, {})
            difficulty = metrics.get("difficulty", 0)
            discrimination = metrics.get("discrimination", 0)
            quality = metrics.get("quality", "N/A")

            # Statistics summary - Row 1
            stats_row = current_row
            ws.cell(row=stats_row, column=1, value="Max Score:").font = Font(bold=True)
            ws.cell(row=stats_row, column=2, value=dist_data.get("max_score", 0))
            ws.cell(row=stats_row, column=3, value="Mean:").font = Font(bold=True)
            ws.cell(row=stats_row, column=4, value=f"{dist_data.get('mean_score', 0):.2f}")
            ws.cell(row=stats_row, column=5, value="Quality:").font = Font(bold=True)
            ws.cell(row=stats_row, column=6, value=quality)
            current_row += 1

            # Statistics summary - Row 2
            ws.cell(row=current_row, column=1, value="Total Students:").font = Font(bold=True)
            ws.cell(row=current_row, column=2, value=dist_data.get("total_students", 0))
            ws.cell(row=current_row, column=3, value="Std Dev:").font = Font(bold=True)
            ws.cell(row=current_row, column=4, value=f"{dist_data.get('std_dev', 0):.2f}")
            current_row += 1

            # Statistics summary - Row 3 (difficulty and discrimination)
            ws.cell(row=current_row, column=1, value="Difficulty:").font = Font(bold=True)
            ws.cell(row=current_row, column=2, value=f"{difficulty:.3f}")
            ws.cell(row=current_row, column=3, value="Discrimination:").font = Font(bold=True)
            ws.cell(row=current_row, column=4, value=f"{discrimination:.3f}")
            current_row += 1

            # Statistics summary - Row 4 (issues)
            issues = metrics.get("issues", [])
            issues_text = ", ".join(issues) if issues else "No issues"
            ws.cell(row=current_row, column=1, value="Issues:").font = Font(bold=True)
            issues_cell = ws.cell(row=current_row, column=2, value=issues_text)
            ws.merge_cells(start_row=current_row, start_column=2, end_row=current_row, end_column=6)

            # Color code based on issues
            if any(keyword in issues_text.lower() for keyword in ["negative", "very poor", "too difficult", "too easy"]):
                issues_cell.font = Font(color="C00000")  # Red for serious issues
            elif "no" in issues_text.lower() and "issues" in issues_text.lower():
                issues_cell.font = Font(color="00B050")  # Green for no issues
            else:
                issues_cell.font = Font(color="FF9900")  # Orange for minor issues

            current_row += 2

            # Distribution table headers
            headers = ["Score", "# Students", "Percentage"]
            for col_idx, header in enumerate(headers, 1):
                cell = ws.cell(row=current_row, column=col_idx, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
                cell.alignment = Alignment(horizontal="center")
            current_row += 1

            # Distribution data - save the starting row for the chart
            data_start_row = current_row
            score_counts = dist_data.get("score_counts", {})
            score_percentages = dist_data.get("score_percentages", {})
            max_count = max(score_counts.values()) if score_counts else 1

            for score in sorted(score_counts.keys()):
                count = score_counts[score]
                percentage = score_percentages.get(score, 0)

                # Score value
                ws.cell(row=current_row, column=1, value=f"Score {score}").alignment = Alignment(horizontal="center")

                # Student count
                count_cell = ws.cell(row=current_row, column=2, value=count)
                count_cell.alignment = Alignment(horizontal="center")

                # Color code based on count
                if count > 0:
                    intensity = int(200 - (count / max_count * 150))  # Darker for more students
                    count_cell.fill = PatternFill(
                        start_color=f"9999{intensity:02X}",
                        end_color=f"9999{intensity:02X}",
                        fill_type="solid"
                    )

                # Percentage (store as numeric value for charting)
                pct_cell = ws.cell(row=current_row, column=3, value=percentage)
                pct_cell.number_format = '0.0"%"'  # Display as percentage with 1 decimal
                pct_cell.alignment = Alignment(horizontal="center")

                current_row += 1

            # Create pie chart for this question
            data_end_row = current_row - 1

            if data_end_row >= data_start_row:
                chart = PieChart()
                chart.title = f"{question_id} Score Distribution"
                chart.height = 6   # Height in cm (smaller)
                chart.width = 8   # Width in cm (smaller)

                # Data for pie chart: student counts
                labels = Reference(ws, min_col=1, min_row=data_start_row, max_row=data_end_row)
                data = Reference(ws, min_col=2, min_row=data_start_row, max_row=data_end_row)

                chart.add_data(data, titles_from_data=False)
                chart.set_categories(labels)

                # Apply gradient colors from red (low scores) to green (high scores)
                max_score = dist_data.get("max_score", 1)
                num_slices = data_end_row - data_start_row + 1

                # Create gradient colors
                for idx in range(num_slices):
                    # Calculate color based on position (0 = red, max = green)
                    ratio = idx / max(1, max_score)

                    # RGB gradient: Red -> Yellow -> Green
                    if ratio < 0.5:
                        # Red to Yellow (decrease blue, increase green)
                        r = 255
                        g = int(255 * (ratio * 2))
                        b = 0
                    else:
                        # Yellow to Green (decrease red, keep green high)
                        r = int(255 * (1 - (ratio - 0.5) * 2))
                        g = 255
                        b = 0

                    # Convert to hex color
                    color_hex = f"{r:02X}{g:02X}{b:02X}"

                    # Create data point with color
                    pt = DataPoint(idx=idx)

                    # Create graphical properties with solid fill
                    gp = GraphicalProperties()
                    gp.solidFill = ColorChoice(srgbClr=color_hex)
                    pt.graphicalProperties = gp

                    chart.series[0].data_points.append(pt)

                # Position chart to the right of the data (column E)
                chart_anchor = f"E{data_start_row - 5}"
                ws.add_chart(chart, chart_anchor)

            current_row += 2  # Space before next question

        # Set column widths
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 15

    def _apply_conditional_formatting(self, ws, df: pd.DataFrame, header_row: int = 1):
        """Apply conditional formatting to metrics."""
        # Find difficulty and discrimination columns
        data_start_row = header_row + 1
        data_end_row = header_row + len(df)

        for col_idx, col_name in enumerate(df.columns, 1):
            col_letter = ws.cell(row=header_row, column=col_idx).column_letter

            if "difficulty" in col_name.lower():
                # Color scale for difficulty (0.3-0.7 is ideal)
                ws.conditional_formatting.add(
                    f"{col_letter}{data_start_row}:{col_letter}{data_end_row}",
                    ColorScaleRule(
                        start_type="num", start_value=0, start_color="FF0000",
                        mid_type="num", mid_value=0.5, mid_color="00FF00",
                        end_type="num", end_value=1, end_color="FF0000"
                    )
                )

            elif "discrimination" in col_name.lower():
                # Color scale for discrimination (higher is better)
                ws.conditional_formatting.add(
                    f"{col_letter}{data_start_row}:{col_letter}{data_end_row}",
                    ColorScaleRule(
                        start_type="num", start_value=0, start_color="FF0000",
                        mid_type="num", mid_value=0.3, mid_color="FFFF00",
                        end_type="num", end_value=0.6, end_color="00FF00"
                    )
                )

            elif "status" in col_name.lower() or "quality" in col_name.lower():
                # Highlight by status
                ws.conditional_formatting.add(
                    f"{col_letter}2:{col_letter}{len(df) + 1}",
                    CellIsRule(
                        operator="containsText",
                        formula=['"Poor"'],
                        fill=PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                    )
                )

    def _auto_adjust_columns(self, ws):
        """Auto-adjust column widths based on content."""
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter

            for cell in column:
                try:
                    if cell.value:
                        cell_length = len(str(cell.value))
                        if cell_length > max_length:
                            max_length = cell_length
                except Exception:
                    pass

            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

    def _create_html_report(
        self,
        metrics_output: Dict[str, Any],
        visualizations_output: Dict[str, Any],
        recommendations_output: Dict[str, Any],
        base_name: str
    ) -> Path:
        """Create interactive HTML report with embedded Plotly figures."""

        # Get Plotly HTML components
        plotly_figures = visualizations_output.get("plotly_figures", {})
        question_figure = plotly_figures.get("question_analysis", "")
        test_figures = plotly_figures.get("test_level", [])

        # Build summary section
        summary_html = self._build_summary_section(metrics_output, recommendations_output)

        # Build recommendations section
        recommendations_html = self._build_recommendations_section(recommendations_output)

        # Combine test-level figures
        test_figures_html = ""
        if isinstance(test_figures, list):
            for fig_html in test_figures:
                test_figures_html += f"<div class='plot-container'>{fig_html}</div>\n"
        elif isinstance(test_figures, str):
            test_figures_html = f"<div class='plot-container'>{test_figures}</div>"

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Analysis Report - {base_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}

        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}

        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }}

        section {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}

        .stat-card {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }}

        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #2980b9;
        }}

        .stat-label {{
            font-size: 0.9em;
            color: #7f8c8d;
            text-transform: uppercase;
        }}

        .plot-container {{
            margin: 20px 0;
        }}

        .recommendation {{
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 5px solid #3498db;
            background: #f8f9fa;
        }}

        .recommendation.high {{
            border-left-color: #e74c3c;
            background: #fdf2f2;
        }}

        .recommendation.medium {{
            border-left-color: #f39c12;
            background: #fef9e7;
        }}

        .recommendation.low {{
            border-left-color: #27ae60;
            background: #f0fdf4;
        }}

        .priority-tag {{
            font-weight: bold;
            text-transform: uppercase;
            font-size: 0.85em;
        }}

        .high .priority-tag {{ color: #e74c3c; }}
        .medium .priority-tag {{ color: #f39c12; }}
        .low .priority-tag {{ color: #27ae60; }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}

        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}

        th {{
            background-color: #3498db;
            color: white;
        }}

        tr:hover {{
            background-color: #f5f5f5;
        }}

        .quality-good {{ color: #27ae60; font-weight: bold; }}
        .quality-review {{ color: #f39c12; font-weight: bold; }}
        .quality-poor {{ color: #e74c3c; font-weight: bold; }}

        footer {{
            text-align: center;
            padding: 20px;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <h1>Test Analysis Report</h1>
    <p><em>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</em></p>

    <section id="summary">
        <h2>Summary Statistics</h2>
        {summary_html}
    </section>

    <section id="questions">
        <h2>Individual Question Analysis</h2>
        <div class="plot-container">
            {question_figure}
        </div>
    </section>

    <section id="overall">
        <h2>Overall Test Visualizations</h2>
        {test_figures_html}
    </section>

    <section id="recommendations">
        <h2>Recommendations</h2>
        {recommendations_html}
    </section>

    <footer>
        <p>Test Analysis Report | Generated by Test Analysis System</p>
    </footer>
</body>
</html>"""

        output_path = self.output_dir / f"{base_name}_report.html"
        output_path.write_text(html_content, encoding='utf-8')

        return output_path

    def _build_summary_section(
        self,
        metrics_output: Dict[str, Any],
        recommendations_output: Dict[str, Any]
    ) -> str:
        """Build HTML for summary statistics section."""
        test_stats = metrics_output.get("test_statistics", {})
        quality_dist = recommendations_output.get("quality_distribution", {})

        total_students = test_stats.get("total_students", "N/A")
        total_questions = test_stats.get("total_questions", "N/A")
        mean_score = test_stats.get("mean_score", "N/A")
        mean_score_pct = test_stats.get("mean_score_percentage", None)
        std_dev = test_stats.get("std_deviation", "N/A")
        reliability = test_stats.get("cronbach_alpha", "N/A")

        # Format numeric values
        if isinstance(mean_score, (int, float)):
            if mean_score_pct is not None:
                mean_score = f"{mean_score:.1f} ({mean_score_pct:.1f}%)"
            else:
                mean_score = f"{mean_score:.2f}"
        if isinstance(std_dev, (int, float)):
            std_dev = f"{std_dev:.2f}"
        if isinstance(reliability, (int, float)):
            reliability = f"{reliability:.3f}"

        good_questions = quality_dist.get("good", 0)
        review_questions = quality_dist.get("review", 0)
        poor_questions = quality_dist.get("poor", 0)

        total = good_questions + review_questions + poor_questions
        if total > 0:
            good_pct = good_questions / total * 100
            review_pct = review_questions / total * 100
            poor_pct = poor_questions / total * 100
        else:
            good_pct = review_pct = poor_pct = 0

        return f"""
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total_students}</div>
                <div class="stat-label">Total Students</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_questions}</div>
                <div class="stat-label">Total Questions</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{mean_score}</div>
                <div class="stat-label">Mean Score</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{std_dev}</div>
                <div class="stat-label">Standard Deviation</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{reliability}</div>
                <div class="stat-label">Reliability (α)</div>
            </div>
        </div>

        <h3>Question Quality Distribution</h3>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value quality-good">{good_questions}</div>
                <div class="stat-label">Good Questions ({good_pct:.1f}%)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value quality-review">{review_questions}</div>
                <div class="stat-label">Need Review ({review_pct:.1f}%)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value quality-poor">{poor_questions}</div>
                <div class="stat-label">Poor Questions ({poor_pct:.1f}%)</div>
            </div>
        </div>
        """

    def _build_recommendations_section(self, recommendations_output: Dict[str, Any]) -> str:
        """Build HTML for recommendations section."""
        recommendations = recommendations_output.get("recommendations", [])

        if not recommendations:
            return "<p>No recommendations available.</p>"

        html_parts = []

        for rec in recommendations:
            if isinstance(rec, dict):
                priority = rec.get("priority", "medium").lower()
                text = rec.get("recommendation", rec.get("text", str(rec)))
                question_ids = rec.get("question_ids", [])

                questions_html = ""
                if question_ids:
                    questions_html = f"<p><strong>Affected Questions:</strong> {', '.join(map(str, question_ids))}</p>"

                html_parts.append(f"""
                <div class="recommendation {priority}">
                    <span class="priority-tag">{priority} priority</span>
                    <p>{text}</p>
                    {questions_html}
                </div>
                """)
            else:
                html_parts.append(f"""
                <div class="recommendation">
                    <p>{str(rec)}</p>
                </div>
                """)

        return "\n".join(html_parts)

    def _create_summary_text(
        self,
        metrics_output: Dict[str, Any],
        visualizations_output: Dict[str, Any],
        recommendations_output: Dict[str, Any],
        base_name: str
    ) -> Path:
        """Create plain text summary report."""
        test_stats = metrics_output.get("test_statistics", {})
        quality_dist = recommendations_output.get("quality_distribution", {})
        recommendations = recommendations_output.get("recommendations", [])

        # Extract values
        test_date = test_stats.get("test_date", datetime.now().strftime("%Y-%m-%d"))
        total_students = test_stats.get("total_students", "N/A")
        total_questions = test_stats.get("total_questions", "N/A")
        mean_score = test_stats.get("mean_score", "N/A")
        mean_score_pct = test_stats.get("mean_score_percentage", None)
        std_dev = test_stats.get("std_deviation", "N/A")
        reliability = test_stats.get("cronbach_alpha", "N/A")

        # Format values
        if isinstance(mean_score, (int, float)):
            if mean_score_pct is not None:
                mean_score_str = f"{mean_score:.1f} ({mean_score_pct:.1f}%)"
            else:
                mean_score_str = f"{mean_score:.2f}"
        else:
            mean_score_str = str(mean_score)

        if isinstance(std_dev, (int, float)):
            std_dev_str = f"{std_dev:.2f}"
        else:
            std_dev_str = str(std_dev)

        if isinstance(reliability, (int, float)):
            reliability_str = f"{reliability:.3f}"
        else:
            reliability_str = str(reliability)

        # Quality distribution
        good_q = quality_dist.get("good", 0)
        review_q = quality_dist.get("review", 0)
        poor_q = quality_dist.get("poor", 0)
        total_q = good_q + review_q + poor_q

        if total_q > 0:
            good_pct = good_q / total_q * 100
            review_pct = review_q / total_q * 100
            poor_pct = poor_q / total_q * 100
        else:
            good_pct = review_pct = poor_pct = 0

        # Build top priority recommendations
        top_recommendations = []
        for rec in recommendations[:5]:  # Top 5
            if isinstance(rec, dict):
                priority = rec.get("priority", "Medium")
                text = rec.get("recommendation", rec.get("text", str(rec)))
                top_recommendations.append(f"  [{priority}] {text}")
            else:
                top_recommendations.append(f"  - {str(rec)}")

        top_recs_text = "\n".join(top_recommendations) if top_recommendations else "  No recommendations available"

        # Get key insights
        key_insights = recommendations_output.get("key_insights", [])
        insights_text = ""
        for insight in key_insights:
            insights_text += f"  - {insight}\n"

        if not insights_text:
            insights_text = "  No specific insights available\n"

        summary_text = f"""TEST ANALYSIS SUMMARY
{'=' * 50}
Test Date: {test_date}
Total Students: {total_students}
Total Questions: {total_questions}

OVERALL TEST STATISTICS
{'=' * 50}
Mean Score: {mean_score_str}
Standard Deviation: {std_dev_str}
Reliability (Cronbach's α): {reliability_str}

QUESTION QUALITY DISTRIBUTION
{'=' * 50}
Good Questions: {good_q} ({good_pct:.1f}%)
Review Needed: {review_q} ({review_pct:.1f}%)
Poor Questions: {poor_q} ({poor_pct:.1f}%)

TOP PRIORITY RECOMMENDATIONS
{'=' * 50}
{top_recs_text}

DETAILED FINDINGS
{'=' * 50}
{insights_text}
OUTPUT FILES
{'=' * 50}
Detailed Analysis: {base_name}_analysis.xlsx
Interactive Report: {base_name}_report.html

Report generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

        output_path = self.output_dir / f"{base_name}_summary.txt"
        output_path.write_text(summary_text, encoding='utf-8')

        return output_path

    def _print_summary(self, metrics_output: Dict[str, Any], recommendations_output: Dict[str, Any]):
        """Print summary to console."""
        test_stats = metrics_output.get("test_statistics", {})
        quality_dist = recommendations_output.get("quality_distribution", {})

        print("\n" + "=" * 50)
        print("TEST ANALYSIS COMPLETE")
        print("=" * 50)

        print(f"\nStudents: {test_stats.get('total_students', 'N/A')}")
        print(f"Questions: {test_stats.get('total_questions', 'N/A')}")

        mean_score = test_stats.get("mean_score", "N/A")
        mean_score_pct = test_stats.get("mean_score_percentage", None)
        if isinstance(mean_score, (int, float)):
            if mean_score_pct is not None:
                print(f"Mean Score: {mean_score:.1f} ({mean_score_pct:.1f}%)")
            else:
                print(f"Mean Score: {mean_score:.2f}")
        else:
            print(f"Mean Score: {mean_score}")

        reliability = test_stats.get("cronbach_alpha", "N/A")
        if isinstance(reliability, (int, float)):
            print(f"Reliability (α): {reliability:.3f}")
        else:
            print(f"Reliability (α): {reliability}")

        print(f"\nQuestion Quality:")
        print(f"  Good: {quality_dist.get('good', 0)}")
        print(f"  Review Needed: {quality_dist.get('review', 0)}")
        print(f"  Poor: {quality_dist.get('poor', 0)}")

        print("\n" + "=" * 50)
