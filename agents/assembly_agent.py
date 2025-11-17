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
from openpyxl.drawing.image import Image as XLImage


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

        # Sheet 2: Question Rankings
        self._add_question_rankings_sheet(wb, recommendations_output)

        # Sheet 3: Distribution Details
        self._add_distribution_details_sheet(wb, recommendations_output)

        # Sheet 4: Recommendations
        self._add_recommendations_sheet(wb, recommendations_output)

        # Sheet 5: Visualizations
        self._add_visualizations_sheet(wb, visualizations_output)

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

        # Convert to DataFrame for easier handling
        df = pd.DataFrame(question_data)

        # Write headers
        headers = list(df.columns)
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Write data
        for row_idx, row in enumerate(df.itertuples(index=False), 2):
            for col_idx, value in enumerate(row, 1):
                # Convert lists to comma-separated strings for Excel compatibility
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                ws.cell(row=row_idx, column=col_idx, value=value)

        # Apply conditional formatting for difficulty and discrimination
        self._apply_conditional_formatting(ws, df)

        # Auto-adjust column widths
        self._auto_adjust_columns(ws)

        # Add filters
        ws.auto_filter.ref = ws.dimensions

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

    def _apply_conditional_formatting(self, ws, df: pd.DataFrame):
        """Apply conditional formatting to metrics."""
        # Find difficulty and discrimination columns
        for col_idx, col_name in enumerate(df.columns, 1):
            col_letter = ws.cell(row=1, column=col_idx).column_letter

            if "difficulty" in col_name.lower():
                # Color scale for difficulty (0.3-0.7 is ideal)
                ws.conditional_formatting.add(
                    f"{col_letter}2:{col_letter}{len(df) + 1}",
                    ColorScaleRule(
                        start_type="num", start_value=0, start_color="FF0000",
                        mid_type="num", mid_value=0.5, mid_color="00FF00",
                        end_type="num", end_value=1, end_color="FF0000"
                    )
                )

            elif "discrimination" in col_name.lower():
                # Color scale for discrimination (higher is better)
                ws.conditional_formatting.add(
                    f"{col_letter}2:{col_letter}{len(df) + 1}",
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
        std_dev = test_stats.get("std_deviation", "N/A")
        reliability = test_stats.get("cronbach_alpha", "N/A")

        # Format numeric values
        if isinstance(mean_score, (int, float)):
            mean_score = f"{mean_score:.2f}%"
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
        std_dev = test_stats.get("std_deviation", "N/A")
        reliability = test_stats.get("cronbach_alpha", "N/A")

        # Format values
        if isinstance(mean_score, (int, float)):
            mean_score_str = f"{mean_score:.2f}%"
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
        if isinstance(mean_score, (int, float)):
            print(f"Mean Score: {mean_score:.2f}%")
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
