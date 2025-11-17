# Test Analysis Orchestration System

A comprehensive system for analyzing student test performance data using a multi-agent architecture with parallel processing.

## Overview

This system provides automated analysis of educational test data including:
- Statistical metrics calculation (difficulty, discrimination, reliability)
- Quality assessment of test questions
- Visual reports with static and interactive charts
- Automated recommendations for test improvement

## Architecture

The system uses an orchestrator pattern with specialized agents:

1. **Orchestrator**: Coordinates data loading, validation, and agent execution
2. **Agent 1 (Metrics Calculator)**: Computes statistical metrics for questions and tests
3. **Agent 2 (Visualization Generator)**: Creates static and interactive visualizations
4. **Agent 3 (Recommendation Engine)**: Generates actionable recommendations (stub)

## Agent 2: Visualization Generator

The Visualization Generator creates comprehensive visualizations for both Excel (static) and HTML (interactive) outputs.

### Features

#### Excel Static Visualizations (matplotlib/seaborn)
- **Difficulty Curve Chart** - Line plot showing question difficulty progression with outlier detection
- **Discrimination vs. Difficulty Scatter** - 4-quadrant plot color-coded by question quality
- **Weights Comparison Bar Chart** - Current vs. recommended question weights
- **Quality Distribution** - Pie and bar charts of good/review/poor question counts

#### Interactive HTML Visualizations (Plotly)
- **Individual Question Analysis** - Scrollable section with score distributions and metrics
- **Interactive Difficulty Curve** - Toggle between original/sorted order with hover tooltips
- **Discrimination-Difficulty Bubble Chart** - Size represents weight, rich hover information
- **Sortable Weight Comparison** - Multiple sorting criteria with change indicators
- **Correlation Heatmap** - Inter-question correlation matrix to identify redundant questions
- **Student Distribution** - Overall score histogram with percentile markers

### Design Principles

- **Colorblind-friendly** - Uses Wong (2011) palette distinguishable for all color vision types
- **Publication-ready** - High DPI static images with professional styling
- **Interactive** - Rich tooltips, sorting, filtering for HTML output
- **Professional** - Clean, consistent styling across all visualizations

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd TestEvaluations

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

## Usage

### Basic Usage with Orchestrator

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

### Using the Visualization Generator (Agent 2)

```python
from src.agents.visualization_generator import VisualizationGenerator
from src.models.metrics import QuestionMetrics, TestStatistics

# Prepare data from Agent 1
question_metrics = [...]  # List of QuestionMetrics
test_statistics = TestStatistics(...)

# Initialize the generator
generator = VisualizationGenerator(output_dir="output")

# Generate all visualizations
output = generator.generate(
    question_metrics=question_metrics,
    test_statistics=test_statistics,
)

# Access the results
print("Excel images:", output.excel_images)
print("Plotly figures:", output.plotly_figures)

# Save interactive HTML report
html_path = generator.save_plotly_html(output, "report.html")
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

The orchestrator generates three output files:

1. **Excel Workbook** (`test_analysis_TIMESTAMP.xlsx`)
   - Raw_Scores sheet
   - Question_Metrics sheet
   - Test_Statistics sheet
   - Quality_Flags sheet

2. **HTML Report** (`test_analysis_TIMESTAMP.html`)
   - Interactive report with tables and visualizations
   - Question quality summary
   - Test statistics overview

3. **Text Summary** (`test_analysis_TIMESTAMP.txt`)
   - Quick overview of key findings
   - Quality distribution
   - Reliability metrics

## Metrics Calculated

### Per-Question Metrics (Agent 1)
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
- Score distribution statistics (mean, median, std dev, skewness, kurtosis)
- Upper/Lower group cutoffs (27th and 73rd percentiles)
- Standard Error of Measurement (SEM)

## Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=test_analysis --cov-report=html

# Run specific test file
pytest tests/test_metrics_calculator.py -v
```

## Running Examples

```bash
# Run the visualization generator example
python examples/example_usage.py
```

This will generate sample data, create all visualizations, and save an HTML report.

## Project Structure

```
TestEvaluations/
├── test_analysis/                          # Core orchestrator and Agent 1
│   ├── __init__.py
│   ├── orchestrator.py                     # Main coordinator
│   ├── data_loader.py                      # Data loading utilities
│   ├── metrics_calculator.py               # Agent 1: Statistical analysis
│   ├── visualization_generator.py          # Agent 2 stub (to be integrated)
│   └── recommendation_engine.py            # Agent 3: Recommendations (stub)
├── src/                                    # Agent 2: Visualization Generator
│   ├── agents/
│   │   ├── visualization_generator.py      # Main visualization orchestrator
│   │   ├── excel_visualizations.py         # Static chart generator
│   │   └── plotly_visualizations.py        # Interactive chart generator
│   ├── models/
│   │   └── metrics.py                       # Data models and types
│   └── utils/
│       └── colors.py                        # Colorblind-friendly palettes
├── examples/
│   └── example_usage.py                     # Complete visualization example
├── tests/
│   ├── test_orchestrator.py
│   └── test_metrics_calculator.py
├── output/                                  # Generated visualizations
├── requirements.txt                         # Python dependencies
├── requirements-dev.txt                     # Dev dependencies
├── setup.py                                 # Package setup
└── README.md                                # This file
```

## Colorblind Accessibility

All visualizations use the Wong (2011) colorblind-friendly palette:
- Blue: #0072B2
- Orange: #E69F00
- Bluish Green: #009E73
- Yellow: #F0E442
- Sky Blue: #56B4E9
- Vermillion: #D55E00
- Reddish Purple: #CC79A7

This ensures charts are distinguishable for people with:
- Deuteranopia (red-green color blindness)
- Protanopia (red color blindness)
- Tritanopia (blue-yellow color blindness)

## Future Development

- Full integration of Agent 2 visualizations with orchestrator
- Complete implementation of Agent 3 (Recommendation Engine)
- Dashboard web interface
- Additional export formats (PDF, PowerPoint)
- Batch processing for multiple tests

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details.

## References

- Wong, B. (2011). Points of view: Color blindness. Nature Methods, 8(6), 441.
- Classical Test Theory psychometric analysis standards
- Plotly.js for interactive visualization
- Matplotlib/Seaborn for publication-quality static charts
