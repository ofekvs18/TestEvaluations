# Test Analysis Orchestration System

A comprehensive system for analyzing student test performance data using parallel agent processing.

## Overview

This system provides automated analysis of educational test data including:
- Statistical metrics calculation (difficulty, discrimination, reliability)
- Quality assessment of test questions
- Automated recommendations for test improvement
- Visual reports and data exports
- Interactive HTML dashboards with Plotly visualizations

## Architecture

The system uses an orchestrator pattern with specialized agents:

1. **Orchestrator**: Coordinates data loading, validation, and agent execution
2. **Agent 1 (Metrics Calculator)**: Computes statistical metrics for questions and tests
3. **Agent 2 (Visualization Generator)**: Creates charts and visual reports
4. **Agent 3 (Recommendation Engine)**: Generates actionable recommendations
5. **Assembly Agent**: Combines all outputs into final deliverables (Excel, HTML, text)

## Installation

```bash
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

## Usage

### Python API

```python
from test_analysis import TestAnalysisOrchestrator

# Initialize with Excel file path
orchestrator = TestAnalysisOrchestrator("student_scores.xlsx")

# Run complete analysis
results = orchestrator.run(output_dir="./output")

print(f"Analysis complete: {results['success']}")
print(f"Output files: {results['output_files']}")
```

### With Custom Weights

```python
weights = {
    'Q1': 2.0,  # Double weight for Q1
    'Q2': 1.5,
    'Q3': 1.0,
    'Q4': 1.0,
    'Q5': 0.5
}

orchestrator = TestAnalysisOrchestrator(
    "student_scores.xlsx",
    current_weights=weights
)
results = orchestrator.run()
```

### Command Line Interface

```bash
python main.py input_data.xlsx --weights current_weights.csv --output-dir results/
```

#### CLI Arguments

- `input_data`: Path to input Excel or CSV file containing test responses
- `--weights`: Optional path to question weights CSV file
- `--output-dir`: Directory for output files (default: `results/`)

### Using Individual Agents

```python
from test_analysis import MetricsCalculator
import pandas as pd

# Load your own data
scores_df = pd.read_excel("scores.xlsx")

# Run just the metrics calculator
calculator = MetricsCalculator(scores_df)
metrics = calculator.run()

# Access specific metrics
print(metrics['question_metrics'])
print(metrics['test_statistics'])
```

## Input Format

The Excel file should have:
- First column: Student identifiers (ID, name, etc.)
- Remaining columns: Question scores (numeric)

Example:
```
Student_ID | Q1  | Q2  | Q3  | Q4  | Q5
S001       | 10  | 8   | 7   | 9   | 6
S002       | 9   | 7   | 8   | 8   | 7
...
```

## Output Files

The system generates three output files:

1. **Excel Workbook** (`test_analysis_TIMESTAMP.xlsx`)
   - Raw_Scores sheet
   - Question_Metrics sheet
   - Test_Statistics sheet
   - Quality_Flags sheet
   - Visualizations sheet (embedded images)

2. **HTML Report** (`test_analysis_TIMESTAMP.html`)
   - Interactive Plotly charts
   - Question quality summary
   - Test statistics overview
   - Prioritized recommendations

3. **Text Summary** (`test_analysis_TIMESTAMP.txt`)
   - Quick overview of key findings
   - Quality distribution
   - Reliability metrics

## Metrics Calculated

### Per-Question Metrics
- **Difficulty Index**: Mean score / max points (0 = hard, 1 = easy)
- **Discrimination Index**: Difference in performance between top and bottom 27%
- **Item-Total Correlation**: Correlation with total score (minus the item)
- **Predictive Power**: How well the question predicts overall performance

### Quality Flags
- **Good**: High discrimination (>0.3), moderate difficulty (0.3-0.8)
- **Review**: Marginal metrics that may need adjustment
- **Poor**: Low or negative discrimination

### Test-Level Metrics
- Cronbach's Alpha (reliability)
- Score distribution statistics
- Upper/Lower group cutoffs

## Dependencies

- openpyxl: Excel file creation and reading
- pandas: Data manipulation
- numpy: Numerical computations
- plotly: Interactive visualizations
- matplotlib: Static visualizations
- kaleido: Plotly image export
- xlrd: Legacy Excel format support

## Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=test_analysis --cov-report=html

# Run specific test file
pytest tests/test_metrics_calculator.py -v
```

## Project Structure

```
TestEvaluations/
├── test_analysis/
│   ├── __init__.py
│   ├── orchestrator.py          # Main coordinator
│   ├── data_loader.py           # Data loading utilities
│   ├── metrics_calculator.py    # Agent 1: Statistical analysis
│   ├── visualization_generator.py  # Agent 2: Charts
│   └── recommendation_engine.py    # Agent 3: Recommendations
├── agents/
│   ├── __init__.py
│   ├── assembly_agent.py        # Final report assembly
│   ├── metrics_agent.py         # Alternative metrics implementation
│   ├── visualization_agent.py   # Alternative visualization implementation
│   └── recommendations_agent.py # Alternative recommendations implementation
├── tests/
│   ├── __init__.py
│   ├── test_orchestrator.py
│   └── test_metrics_calculator.py
├── main.py                      # CLI entry point
├── requirements.txt
├── requirements-dev.txt
├── setup.py
└── README.md
```

## Future Development

The system supports both the core `test_analysis` package and the `agents` package implementations. These can be integrated to provide maximum flexibility in test analysis workflows.
