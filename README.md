# Test Evaluations - Multi-Agent Analysis System

A comprehensive test evaluation system using a multi-agent architecture for psychometric analysis and visualization of educational assessments.

## Overview

This system uses a pipeline of specialized agents to analyze test results:

- **Agent 1: Metrics Calculator** - Computes psychometric metrics (difficulty, discrimination, reliability)
- **Agent 2: Visualization Generator** - Creates static and interactive visualizations
- **Agent 3: Report Generator** - Compiles findings into Excel and HTML reports

## Agent 2: Visualization Generator

The Visualization Generator is the second agent in the pipeline. It receives calculated metrics from Agent 1 and produces comprehensive visualizations for both Excel (static) and HTML (interactive) outputs.

### Features

#### Excel Static Visualizations (matplotlib/seaborn)
- **Difficulty Curve Chart** - Line plot showing question difficulty progression with outlier detection
- **Discrimination vs. Difficulty Scatter** - 4-quadrant plot color-coded by question quality
- **Weights Comparison Bar Chart** - Current vs. recommended question weights
- **Quality Distribution** - Pie and bar charts of good/review/poor question counts

#### Interactive HTML Visualizations (Plotly)
- **Individual Question Analysis** - Scrollable section with score distributions and metrics for each question
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
```

## Quick Start

```python
from src.agents.visualization_generator import VisualizationGenerator
from src.models.metrics import QuestionMetrics, TestStatistics, QualityCategory

# 1. Prepare your data (from Agent 1)
question_metrics = [...]  # List of QuestionMetrics from Agent 1
test_statistics = TestStatistics(...)  # From Agent 1

# 2. Initialize the generator
generator = VisualizationGenerator(output_dir="output")

# 3. Generate all visualizations
output = generator.generate(
    question_metrics=question_metrics,
    test_statistics=test_statistics,
)

# 4. Access the results
print("Excel images:", output.excel_images)
print("Plotly figures:", output.plotly_figures)

# 5. Save interactive HTML report
html_path = generator.save_plotly_html(output, "report.html")
```

## Example

Run the complete example to see the agent in action:

```bash
cd TestEvaluations
python examples/example_usage.py
```

This will:
1. Generate sample data simulating Agent 1 output
2. Create all static Excel images in `output/`
3. Generate all interactive Plotly figures
4. Save a complete HTML report to `output/test_evaluation_report.html`

## Project Structure

```
TestEvaluations/
├── src/
│   ├── agents/
│   │   ├── visualization_generator.py    # Main Agent 2 orchestrator
│   │   ├── excel_visualizations.py       # Static chart generator
│   │   └── plotly_visualizations.py      # Interactive chart generator
│   ├── models/
│   │   └── metrics.py                     # Data models and types
│   └── utils/
│       └── colors.py                      # Colorblind-friendly palettes
├── examples/
│   └── example_usage.py                   # Complete usage example
├── output/                                # Generated visualizations
├── tests/                                 # Unit tests
├── requirements.txt                       # Python dependencies
├── pyproject.toml                         # Project configuration
└── README.md                              # This file
```

## Input Format

The Visualization Generator expects the following inputs from Agent 1:

### QuestionMetrics (per question)
```python
{
    'question_id': str,
    'question_number': int,
    'mean_score': float,
    'median_score': float,
    'std_dev': float,
    'min_score': float,
    'max_score': float,
    'difficulty_index': float,      # P-value (0-1)
    'discrimination_index': float,  # Point-biserial or upper-lower 27%
    'current_weight': float,
    'recommended_weight': float,
    'max_possible_score': float,
    'quality_category': str,        # 'good', 'review', or 'poor'
    'is_curve_breaker': bool,
    'quality_notes': List[str],
    'score_distribution': np.ndarray  # Optional: raw scores
}
```

### TestStatistics (overall)
```python
{
    'total_questions': int,
    'total_students': int,
    'max_possible_score': float,
    'mean_total_score': float,
    'median_total_score': float,
    'std_dev_total_score': float,
    'min_total_score': float,
    'max_total_score': float,
    'cronbach_alpha': float,
    'sem': float,
    'skewness': float,
    'kurtosis': float,
    'good_questions_count': int,
    'review_questions_count': int,
    'poor_questions_count': int,
    'upper_27_cutoff': float,
    'lower_27_cutoff': float,
    'student_total_scores': np.ndarray  # Optional: all student totals
}
```

## Output Format

The agent returns a `VisualizationOutput` object:

```python
{
    'excel_images': {
        'difficulty_curve': 'output/difficulty_curve.png',
        'scatter': 'output/discrimination_difficulty_scatter.png',
        'weights': 'output/weights_comparison.png',
        'quality': 'output/quality_distribution.png'
    },
    'plotly_figures': {
        'question_details': <plotly.graph_objects.Figure>,
        'difficulty_curve': <plotly.graph_objects.Figure>,
        'scatter': <plotly.graph_objects.Figure>,
        'weights': <plotly.graph_objects.Figure>,
        'heatmap': <plotly.graph_objects.Figure>,
        'distribution': <plotly.graph_objects.Figure>
    }
}
```

## Dependencies

- **pandas** >= 1.5.0 - Data manipulation
- **numpy** >= 1.21.0 - Numerical operations
- **matplotlib** >= 3.5.0 - Static visualizations
- **seaborn** >= 0.12.0 - Statistical plotting
- **plotly** >= 5.10.0 - Interactive visualizations
- **openpyxl** >= 3.0.0 - Excel support
- **Pillow** >= 9.0.0 - Image processing

## Colorblind Accessibility

All visualizations use the Wong (2011) colorblind-friendly palette:
- Blue: #0072B2
- Orange: #E69F00
- Bluish Green: #009E73
- Yellow: #F0E442
- Sky Blue: #56B4E9
- Vermillion: #D55E00
- Reddish Purple: #CC79A7

This ensures that charts are distinguishable for people with:
- Deuteranopia (red-green color blindness)
- Protanopia (red color blindness)
- Tritanopia (blue-yellow color blindness)

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
