# Test Evaluation Analysis System

A comprehensive test analysis system that uses parallel processing agents to analyze test performance and generate detailed reports.

## Features

- **Parallel Agent Processing**: Three specialized agents work concurrently to analyze metrics, generate visualizations, and create recommendations
- **Multi-format Output**: Generates Excel workbooks, interactive HTML reports, and text summaries
- **Psychometric Analysis**: Calculates difficulty, discrimination, and reliability metrics
- **Quality Assessment**: Automatically classifies questions and provides actionable recommendations

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py input_data.xlsx --weights current_weights.csv --output-dir results/
```

### Arguments

- `input_data`: Path to input Excel or CSV file containing test responses
- `--weights`: Optional path to question weights CSV file
- `--output-dir`: Directory for output files (default: `results/`)

### Input Data Format

The input file should contain:
- First column: Student identifiers
- Remaining columns: Question responses (1 for correct, 0 for incorrect)

## Output Files

1. **`{filename}_analysis.xlsx`**: Multi-sheet Excel workbook with:
   - Question Analysis
   - Question Rankings
   - Distribution Details
   - Recommendations
   - Visualizations (embedded images)

2. **`{filename}_report.html`**: Interactive HTML report with:
   - Summary statistics
   - Interactive Plotly charts
   - Detailed recommendations

3. **`{filename}_summary.txt`**: Plain text summary suitable for reports

## Architecture

The system uses an orchestrator pattern with four specialized agents:

1. **Metrics Agent**: Calculates test statistics and question-level metrics
2. **Visualization Agent**: Generates interactive and static visualizations
3. **Recommendations Agent**: Analyzes data and generates prioritized recommendations
4. **Assembly Agent**: Combines all outputs into final deliverables

## Dependencies

- openpyxl: Excel file creation
- pandas: Data manipulation
- plotly: Interactive visualizations
- matplotlib: Static visualizations
- numpy: Numerical computations
- kaleido: Plotly image export
