# Test Analysis Orchestration System

A comprehensive system for analyzing student test performance data using a multi-agent architecture with parallel processing and automated report generation.

## Overview

This system provides automated analysis of educational test data including:
- Statistical metrics calculation (difficulty, discrimination, reliability)
- Quality assessment of test questions
- Weight optimization using discrimination, difficulty, and variance metrics
- Visual reports with static and interactive charts
- Automated recommendations for test improvement

## Architecture

The system uses a unified orchestrator pattern that coordinates specialized agents running in parallel:

```
┌─────────────────────────────────┐
│   TestAnalysisOrchestrator      │
│   (Main Coordinator)            │
└─────────┬───────────────────────┘
          │
    ┌─────┴─────┐
    │   Data    │
    │  Loader   │
    └─────┬─────┘
          │
    ┌─────┴──────────────────┐
    │   Parallel Execution    │
    │                         │
    ├─────┬─────┬────────────┤
    │     │     │            │
┌───▼──┐ ┌▼────┐ ┌▼──────────┐
│Agent1│ │Agent2│ │Agent3     │
│      │ │      │ │           │
│Metrics │Visual│ │Recommend- │
│Calc    │Gen   │ │ation      │
└───┬──┘ └┬────┘ └┬──────────┘
    │     │       │
    └─────┴───┬───┘
              │
        ┌─────▼─────┐
        │ Assembly  │
        │   Agent   │
        └─────┬─────┘
              │
        ┌─────▼─────┐
        │  Final    │
        │ Outputs   │
        │ (Excel,   │
        │  HTML,    │
        │  Text)    │
        └───────────┘
```

**Core Components:**

1. **TestAnalysisOrchestrator** (`orchestrator.py`): Main coordinator that:
   - Loads and validates input Excel/CSV data
   - Parses student performance data into clean pandas DataFrame
   - Calculates basic statistics (max points, student count, etc.)
   - Dispatches work to three specialized agents running in parallel
   - Collects results and coordinates final assembly

2. **Agent 1 - Metrics Calculator** (`agents/metrics_agent.py`): Computes statistical metrics
3. **Agent 2 - Visualization Generator** (`agents/visualization_agent.py`): Creates visualizations
4. **Agent 3 - Recommendation Engine** (`agents/recommendations_agent.py`): Generates recommendations
5. **Assembly Agent** (`agents/assembly_agent.py`): Combines outputs into final deliverables

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
from orchestrator import TestAnalysisOrchestrator

# Initialize with Excel file path
orchestrator = TestAnalysisOrchestrator("student_scores.xlsx")

# Run complete analysis pipeline
results = orchestrator.run()

print(f"Analysis complete: {results['success']}")
print(f"Output files: {results['output_files']}")
print(f"Execution time: {results['execution_time_seconds']:.2f} seconds")

# Access individual agent results
print(f"Metrics: {results['metrics_results']}")
print(f"Recommendations: {results['recommendation_results']}")
```

### With Custom Output Directory

```python
orchestrator = TestAnalysisOrchestrator(
    "student_scores.xlsx",
    output_dir="./my_reports"
)
results = orchestrator.run()
```

### With Optional Weights File

```python
orchestrator = TestAnalysisOrchestrator(
    "student_scores.xlsx",
    weights_path="current_weights.csv",
    output_dir="./results"
)
results = orchestrator.run()
```

### Sequential vs Parallel Execution

```python
# Run agents in parallel (default, faster)
results = orchestrator.run(parallel=True)

# Run agents sequentially (useful for debugging)
results = orchestrator.run(parallel=False)
```

### Using the Weight Optimizer Directly

```python
from weight_optimizer import WeightOptimizer, WeightOptimizerConfig
import pandas as pd

# Prepare your question metrics
question_metrics = pd.DataFrame({
    'question_id': ['Q1', 'Q2', 'Q3'],
    'difficulty': [0.55, 0.80, 0.20],
    'discrimination': [0.40, 0.10, 0.35],
    'std_dev': [0.50, 0.40, 0.45],
    'upper_group_correct': [0.75, 0.85, 0.45],
    'lower_group_correct': [0.35, 0.75, 0.10]
})

# Test statistics
test_stats = {
    'cronbach_alpha': 0.78,
    'mean_score': 70,
    'total_students': 150
}

# Current weights (optional)
current_weights = {'Q1': 33.3, 'Q2': 33.3, 'Q3': 33.4}

# Initialize optimizer
optimizer = WeightOptimizer()

# Run optimization
results = optimizer.optimize(
    question_metrics=question_metrics,
    test_statistics=test_stats,
    current_weights=current_weights
)

# Access results
print(results['recommended_weights'])
print(results['test_recommendations'])

# Save to Excel
optimizer.save_to_excel(results, 'output.xlsx')
```

### Command Line Interface

```bash
# Basic usage
python main.py input_data.xlsx

# With optional weights and custom output directory
python main.py input_data.xlsx --weights current_weights.csv --output-dir results/

# Run agents sequentially (for debugging)
python main.py input_data.xlsx --sequential
```

#### CLI Arguments

- `input_data`: Path to input Excel (.xlsx/.xls) or CSV (.csv) file containing test responses
- `--weights`: Optional path to question weights CSV file
- `--output-dir`: Directory for output files (default: `results/`)
- `--sequential`: Run agents sequentially instead of in parallel (useful for debugging)

#### Example Output

```
============================================================
TEST ANALYSIS ORCHESTRATOR
============================================================

[Step 1/3] Loading and validating data...
Loading data from: student_scores.xlsx
  ✓ Loaded 100 rows, 11 columns
  ✓ Data structure validated: Data structure is valid
  ✓ Data cleaned and standardized

Basic Statistics:
  - Students: 100
  - Questions: 10
  - Mean Total Score: 72.45
  - Std Dev: 15.32

[Step 2/3] Running analysis agents...
Starting analysis agents...
  ✓ Agent Metrics completed
  ✓ Agent Visualization completed
  ✓ Agent Recommendations completed

[Step 3/3] Assembling final outputs...
Assembling final reports...

============================================================
✓ Analysis completed successfully!
Total execution time: 2.45 seconds

Generated files:
  - Excel: results/student_scores_analysis.xlsx
  - Html: results/student_scores_report.html
  - Summary: results/student_scores_summary.txt
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

The system generates three output files:

1. **Excel Workbook** (`test_analysis_TIMESTAMP.xlsx`)
   - Raw_Scores sheet
   - Question_Metrics sheet
   - Test_Statistics sheet
   - Quality_Flags sheet
   - Visualizations sheet (embedded images)
   - **Recommended_Weights sheet**
   - **Priority_Items sheet**

2. **HTML Report** (`test_analysis_TIMESTAMP.html`)
   - Interactive Plotly charts
   - Question quality summary
   - Test statistics overview
   - Prioritized recommendations

3. **Text Summary** (`test_analysis_TIMESTAMP.txt`)
   - Quick overview of key findings
   - Quality distribution
   - Reliability metrics

## Weight Optimization

### Formula
```
Recommended_Weight = (Discrimination_Index × α) + (Difficulty_Penalty × β) + (Variance_Factor × γ)
```

Default parameters: α=0.5, β=0.3, γ=0.2

### Components

1. **Discrimination Index**: Raw discrimination value (0-1)
2. **Difficulty Penalty**: Gaussian curve centered at 0.55
   - `exp(-((difficulty - 0.55)² / (2 × 0.15²))`
3. **Variance Factor**: Normalized standard deviation

### Recommendation Actions

- **Keep as-is**: Metrics within acceptable range
- **Adjust weight**: Good metrics but weight mismatch
- **Review carefully**: Question has concerning metrics
- **Consider removing**: Severe issues (negative/very poor discrimination)

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

## Dependencies

- openpyxl: Excel file creation and reading
- pandas: Data manipulation
- numpy: Numerical computations
- scipy: Statistical computations (weight optimization)
- plotly: Interactive visualizations
- matplotlib: Static visualizations
- seaborn: Statistical visualizations
- kaleido: Plotly image export
- xlrd: Legacy Excel format support
- Pillow: Image processing

## Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=test_analysis --cov-report=html

# Run specific test file
pytest tests/test_metrics_calculator.py -v

# Run weight optimizer tests
python test_optimizer.py
```

## Configuration

Customize the optimizer with your own parameters:

```python
from weight_optimizer import WeightOptimizerConfig

config = WeightOptimizerConfig(
    alpha=0.6,              # Discrimination weight
    beta=0.3,               # Difficulty penalty weight
    gamma=0.1,              # Variance factor weight
    optimal_difficulty=0.60, # Center of difficulty curve
    difficulty_sigma=0.20    # Spread of difficulty curve
)

optimizer = WeightOptimizer(config)
```

## Running Examples

```bash
# Run the visualization generator example
python examples/example_usage.py

# Run weight optimizer standalone example
python example_usage.py
```

This will generate sample data, create all visualizations, and save an HTML report.

## Project Structure

```
TestEvaluations/
├── orchestrator.py                          # Main unified orchestrator (primary entry point)
├── main.py                                  # CLI entry point (imports from orchestrator)
├── agents/                                  # Specialized analysis agents
│   ├── __init__.py
│   ├── metrics_agent.py                     # Agent 1: Statistical metrics calculation
│   ├── visualization_agent.py              # Agent 2: Visualization generation
│   ├── recommendations_agent.py            # Agent 3: Recommendation engine
│   └── assembly_agent.py                    # Final report assembly agent
├── test_analysis/                          # Legacy orchestrator (being phased out)
│   ├── __init__.py
│   ├── orchestrator.py                     # Old coordinator (deprecated)
│   ├── data_loader.py                      # Data loading utilities
│   ├── metrics_calculator.py               # Alternative metrics implementation
│   ├── visualization_generator.py          # Stub implementation
│   └── recommendation_engine.py            # Alternative recommendation engine
├── src/                                    # Advanced visualization modules
│   ├── agents/
│   │   ├── visualization_generator.py      # Enhanced visualization orchestrator
│   │   ├── excel_visualizations.py         # Static chart generator
│   │   └── plotly_visualizations.py        # Interactive chart generator
│   ├── models/
│   │   └── metrics.py                       # Data models and types
│   └── utils/
│       └── colors.py                        # Colorblind-friendly palettes
├── tests/
│   ├── test_orchestrator.py                 # Orchestrator unit tests
│   └── test_metrics_calculator.py           # Metrics calculator tests
├── examples/
│   └── example_usage.py                     # Complete visualization example
├── weight_optimizer.py                      # Standalone weight optimization module
├── example_usage.py                         # Weight optimizer demo script
├── test_optimizer.py                        # Weight optimizer unit tests
├── requirements.txt                         # Python dependencies
├── requirements-dev.txt                     # Dev dependencies
├── setup.py                                 # Package setup
├── pyproject.toml                           # Project metadata
└── README.md                                # This file
```

**Key Files:**
- `orchestrator.py`: Main unified orchestrator - the single source of truth
- `main.py`: Simple CLI entry point
- `agents/`: Directory containing all specialized agent implementations
- `tests/test_orchestrator.py`: Comprehensive tests for the orchestrator

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

- ~~Full integration of Assembly Agent with orchestrator pipeline~~ ✅ Complete
- ~~Consolidate parallel orchestrator implementations~~ ✅ Complete
- Enhanced visualization integration with advanced Plotly features
- Dashboard web interface
- Additional export formats (PDF, PowerPoint)
- Batch processing for multiple tests
- API endpoint for programmatic access
- Database integration for historical analysis

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
