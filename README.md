# Test Weight Optimization Specialist

A Python library for analyzing test question metrics and generating optimal weight recommendations for educational assessments.

## Features

- **Weight Optimization**: Calculates recommended question weights using discrimination, difficulty, and variance metrics
- **Question Analysis**: Provides actionable recommendations for each test question
- **Test-Level Insights**: Generates overall test improvement suggestions
- **Priority Identification**: Highlights top 5 questions needing immediate attention
- **Excel Export**: Creates detailed spreadsheets with multiple analysis views

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

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

## Weight Calculation Formula

```
Recommended_Weight = (Discrimination_Index × α) + (Difficulty_Penalty × β) + (Variance_Factor × γ)
```

Default parameters: α=0.5, β=0.3, γ=0.2

### Components

1. **Discrimination Index**: Raw discrimination value (0-1)
2. **Difficulty Penalty**: Gaussian curve centered at 0.55
   - `exp(-((difficulty - 0.55)² / (2 × 0.15²))`
3. **Variance Factor**: Normalized standard deviation

## Output Structure

```python
{
    'recommended_weights': Dict[str, float],      # question_id: weight (%)
    'weight_changes': DataFrame,                   # Current vs recommended
    'question_recommendations': DataFrame,         # Per-question actions
    'test_recommendations': List[str],            # Overall insights
    'priority_items': DataFrame,                   # Top 5 urgent issues
    'excel_sheets': {
        'question_analysis': DataFrame,
        'question_rankings': DataFrame,
        'distribution_details': DataFrame,
        'recommendations': DataFrame
    }
}
```

## Recommendation Actions

- **Keep as-is**: Metrics within acceptable range
- **Adjust weight**: Good metrics but weight mismatch
- **Review carefully**: Question has concerning metrics
- **Consider removing**: Severe issues (negative/very poor discrimination)

## Running Examples

```bash
python example_usage.py
```

## Running Tests

```bash
python -m pytest test_optimizer.py -v
# or
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

## Input Data Requirements

The `question_metrics` DataFrame must contain:
- `question_id`: Unique identifier for each question
- `difficulty`: Proportion of students answering correctly (0-1)
- `discrimination`: Discrimination index (typically -1 to 1)
- `std_dev`: Standard deviation of responses

Optional columns:
- `upper_group_correct`: Proportion correct in upper 27%
- `lower_group_correct`: Proportion correct in lower 27%

## License

MIT License
