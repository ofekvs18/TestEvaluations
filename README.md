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

## Visualization Generator (Agent 2)

The Visualization Generator creates both static and interactive visualizations:

### Static Visualizations (matplotlib)
- **Score Distribution** - Histogram of total student scores
- **Difficulty vs. Discrimination Scatter** - Question analysis plot with color coding

### Interactive Visualizations (Plotly)
- **Question Analysis** - Interactive difficulty vs. discrimination chart with hover tooltips
- **Score Distribution** - Interactive histogram with statistics
- **Question Difficulty Distribution** - Histogram showing question difficulty spread

All visualizations are embedded in the final HTML report and Excel workbook.

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

### Accessing Individual Agent Results

```python
from orchestrator import TestAnalysisOrchestrator

orchestrator = TestAnalysisOrchestrator("scores.xlsx")
results = orchestrator.run()

# Access metrics from Agent 1
metrics = results['metrics_results']
print(metrics['test_statistics'])
print(metrics['question_metrics'])

# Access visualizations from Agent 2
viz = results['visualization_results']
print(viz['plotly_figures'])
print(viz['static_images'])

# Access recommendations from Agent 3
recs = results['recommendation_results']
print(recs['recommendations'])
print(recs['key_insights'])
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

## Recommendations

The Recommendation Engine (Agent 3) analyzes questions and provides actionable guidance:

### Priority Levels

- **High Priority**: Questions with negative discrimination or poor quality
- **Medium Priority**: Questions that are too easy/difficult or have low discrimination
- **Low Priority**: General test improvement suggestions

### Recommendation Actions

- **Review and revise**: Questions with poor quality metrics
- **Remove or rewrite**: Questions with negative discrimination
- **Increase difficulty**: Questions that are too easy (>85% correct)
- **Decrease difficulty**: Questions that are too difficult (<15% correct)
- **Improve discrimination**: Questions with weak ability to differentiate students

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
pytest tests/ --cov=orchestrator --cov=agents --cov-report=html

# Run specific test
pytest tests/test_orchestrator.py -v
```

## Project Structure

```
TestEvaluations/
├── orchestrator.py              # Main unified orchestrator (primary entry point)
├── main.py                      # CLI entry point
├── agents/                      # Specialized analysis agents
│   ├── __init__.py
│   ├── metrics_agent.py         # Agent 1: Statistical metrics calculation
│   ├── visualization_agent.py   # Agent 2: Visualization generation
│   ├── recommendations_agent.py # Agent 3: Recommendation engine
│   └── assembly_agent.py        # Final report assembly agent
├── tests/
│   └── test_orchestrator.py     # Comprehensive orchestrator tests
├── requirements.txt             # Python dependencies
├── requirements-dev.txt         # Development dependencies
├── setup.py                     # Package setup
├── pyproject.toml               # Project metadata
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

**Total: 9 Python files** - Clean, focused, no duplicates!

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
