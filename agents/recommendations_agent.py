"""
Recommendations Generation Agent (Agent 3)

Analyzes test data and generates actionable recommendations.
"""

from typing import Any, Dict, List

import numpy as np
import pandas as pd


class RecommendationsAgent:
    """Agent responsible for generating recommendations."""

    def generate_recommendations(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate recommendations based on test analysis.

        Args:
            data: DataFrame with student responses

        Returns:
            Dictionary containing analysis, rankings, and recommendations
        """
        if data.empty:
            return self._empty_recommendations()

        # Extract question columns
        question_cols = data.columns[1:]
        scores = data[question_cols].values

        # Analyze each question
        question_analysis = self._analyze_questions(scores, question_cols)

        # Generate rankings
        question_rankings = self._generate_rankings(question_analysis)

        # Calculate quality distribution
        quality_distribution = self._calculate_quality_distribution(question_analysis)

        # Generate distribution details
        distribution_details = self._generate_distribution_details(scores, question_analysis)

        # Generate recommendations
        recommendations = self._generate_priority_recommendations(question_analysis)

        # Generate key insights
        key_insights = self._generate_key_insights(scores, question_analysis)

        return {
            "question_analysis": question_analysis,
            "question_rankings": question_rankings,
            "distribution_details": distribution_details,
            "quality_distribution": quality_distribution,
            "recommendations": recommendations,
            "key_insights": key_insights
        }

    def _analyze_questions(
        self,
        scores: np.ndarray,
        question_cols: pd.Index
    ) -> List[Dict[str, Any]]:
        """Analyze each question and classify quality."""
        total_scores = scores.sum(axis=1)
        analysis = []

        for idx, col in enumerate(question_cols):
            q_scores = scores[:, idx]

            # Get max possible score for this question
            max_score = np.max(q_scores)
            if max_score == 0:
                max_score = 1  # Avoid division by zero

            # Calculate metrics
            # Difficulty (inverted proportion correct) - normalized to 0-1 range
            # High value = hard question, Low value = easy question
            difficulty = 1 - (np.mean(q_scores) / max_score)

            if np.std(q_scores) == 0:
                discrimination = 0.0
            else:
                corr = np.corrcoef(q_scores, total_scores)[0, 1]
                discrimination = float(corr) if not np.isnan(corr) else 0.0

            # Classify quality
            quality = self._classify_question_quality(difficulty, discrimination)

            # Generate specific issues
            issues = self._identify_issues(difficulty, discrimination)

            # Generate classification explanation
            classification_reason = self._explain_classification(difficulty, discrimination, quality)

            analysis.append({
                "question_id": str(col),
                "difficulty": round(difficulty, 3),
                "discrimination": round(discrimination, 3),
                "quality": quality,
                "issues": issues,
                "classification_reason": classification_reason,
                "variance": round(np.var(q_scores), 3)
            })

        return analysis

    def _classify_question_quality(self, difficulty: float, discrimination: float) -> str:
        """Classify question quality based on psychometric standards."""
        if discrimination < 0.15:
            return "Poor"
        elif discrimination < 0.3:
            if difficulty < 0.2 or difficulty > 0.8:
                return "Poor"
            else:
                return "Review"
        else:
            if 0.3 <= difficulty <= 0.7:
                return "Good"
            elif 0.2 <= difficulty <= 0.8:
                return "Review"
            else:
                return "Poor"

    def _explain_classification(self, difficulty: float, discrimination: float, quality: str) -> str:
        """Explain why a question received its quality classification.

        Returns a step-by-step explanation of the decision logic.
        """
        explanation_parts = []

        # Step 1: Check discrimination
        if discrimination < 0:
            explanation_parts.append(f"FAIL: Discrimination={discrimination:.3f} (NEGATIVE - question confuses high performers)")
        elif discrimination < 0.15:
            explanation_parts.append(f"FAIL: Discrimination={discrimination:.3f} < 0.15 (VERY POOR - fails to differentiate students)")
        elif discrimination < 0.3:
            explanation_parts.append(f"WARN: Discrimination={discrimination:.3f} is 0.15-0.30 (LOW - weak differentiation)")
        else:
            explanation_parts.append(f"PASS: Discrimination={discrimination:.3f} >= 0.30 (GOOD differentiation)")

        # Step 2: Check difficulty (inverted: high = hard, low = easy)
        if difficulty < 0.2:
            explanation_parts.append(f"FAIL: Difficulty={difficulty:.3f} < 0.20 (TOO EASY - most students succeed)")
        elif difficulty > 0.8:
            explanation_parts.append(f"FAIL: Difficulty={difficulty:.3f} > 0.80 (TOO HARD - most students fail)")
        elif 0.3 <= difficulty <= 0.7:
            explanation_parts.append(f"PASS: Difficulty={difficulty:.3f} in ideal range 0.30-0.70")
        elif 0.2 <= difficulty <= 0.8:
            explanation_parts.append(f"WARN: Difficulty={difficulty:.3f} in acceptable range 0.20-0.80")
        else:
            explanation_parts.append(f"FAIL: Difficulty={difficulty:.3f} outside acceptable range")

        # Step 3: Final decision
        if quality == "Good":
            explanation_parts.append(f"PASS: RESULT: GOOD - Both metrics in ideal ranges")
        elif quality == "Review":
            explanation_parts.append(f"WARN: RESULT: NEEDS REVIEW - Metrics marginally acceptable")
        else:
            explanation_parts.append(f"FAIL: RESULT: POOR - One or more metrics below standards")

        return " | ".join(explanation_parts)

    def _identify_issues(self, difficulty: float, discrimination: float) -> List[str]:
        """Identify specific issues with a question."""
        issues = []

        if difficulty < 0.2:
            issues.append("Too easy")
        elif difficulty > 0.8:
            issues.append("Too difficult")

        if discrimination < 0:
            issues.append("Negative discrimination - consider removing")
        elif discrimination < 0.15:
            issues.append("Very poor discrimination")
        elif discrimination < 0.3:
            issues.append("Low discrimination")

        if not issues:
            issues.append("No major issues")

        return issues

    def _generate_rankings(self, question_analysis: List[Dict]) -> Dict[str, Any]:
        """Generate question rankings by various criteria."""
        if not question_analysis:
            return {}

        # Sort by discrimination (best questions)
        by_discrimination = sorted(
            question_analysis,
            key=lambda x: x["discrimination"],
            reverse=True
        )

        # Sort by difficulty deviation from 0.5 (ideal difficulty)
        by_difficulty_ideal = sorted(
            question_analysis,
            key=lambda x: abs(x["difficulty"] - 0.5)
        )

        # Problem questions (poor quality first)
        problem_questions = [
            q for q in question_analysis
            if q["quality"] in ["Poor", "Review"]
        ]
        problem_questions.sort(key=lambda x: (
            0 if x["quality"] == "Poor" else 1,
            x["discrimination"]
        ))

        return {
            "best_discriminating": by_discrimination[:10],
            "worst_discriminating": by_discrimination[-10:],
            "ideal_difficulty": by_difficulty_ideal[:10],
            "problem_questions": problem_questions[:10]
        }

    def _calculate_quality_distribution(self, question_analysis: List[Dict]) -> Dict[str, int]:
        """Calculate distribution of question quality."""
        distribution = {"good": 0, "review": 0, "poor": 0}

        for q in question_analysis:
            quality = q.get("quality", "").lower()
            if quality == "good":
                distribution["good"] += 1
            elif quality == "review":
                distribution["review"] += 1
            elif quality == "poor":
                distribution["poor"] += 1

        return distribution

    def _generate_distribution_details(
        self,
        scores: np.ndarray,
        question_analysis: List[Dict]
    ) -> Dict[str, Any]:
        """Generate detailed distribution statistics."""
        difficulties = [q["difficulty"] for q in question_analysis]
        discriminations = [q["discrimination"] for q in question_analysis]

        return {
            "difficulty": {
                "mean": round(np.mean(difficulties), 3),
                "std": round(np.std(difficulties), 3),
                "min": round(np.min(difficulties), 3),
                "max": round(np.max(difficulties), 3),
                "very_easy (>0.8)": sum(1 for d in difficulties if d > 0.8),
                "easy (0.6-0.8)": sum(1 for d in difficulties if 0.6 <= d <= 0.8),
                "moderate (0.4-0.6)": sum(1 for d in difficulties if 0.4 <= d <= 0.6),
                "difficult (0.2-0.4)": sum(1 for d in difficulties if 0.2 <= d <= 0.4),
                "very_difficult (<0.2)": sum(1 for d in difficulties if d < 0.2)
            },
            "discrimination": {
                "mean": round(np.mean(discriminations), 3),
                "std": round(np.std(discriminations), 3),
                "min": round(np.min(discriminations), 3),
                "max": round(np.max(discriminations), 3),
                "excellent (>0.4)": sum(1 for d in discriminations if d > 0.4),
                "good (0.3-0.4)": sum(1 for d in discriminations if 0.3 <= d <= 0.4),
                "acceptable (0.2-0.3)": sum(1 for d in discriminations if 0.2 <= d <= 0.3),
                "poor (<0.2)": sum(1 for d in discriminations if d < 0.2)
            },
            "score_distribution": {
                "total_students": scores.shape[0],
                "mean_total": round(np.mean(scores.sum(axis=1)), 2),
                "std_total": round(np.std(scores.sum(axis=1)), 2)
            }
        }

    def _generate_priority_recommendations(
        self,
        question_analysis: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations."""
        recommendations = []

        # Check for poor questions
        poor_questions = [q for q in question_analysis if q["quality"] == "Poor"]
        if poor_questions:
            recommendations.append({
                "priority": "High",
                "recommendation": f"Review and revise {len(poor_questions)} poor quality questions that may be reducing test validity",
                "question_ids": [q["question_id"] for q in poor_questions]
            })

        # Check for negative discrimination
        negative_disc = [q for q in question_analysis if q["discrimination"] < 0]
        if negative_disc:
            recommendations.append({
                "priority": "High",
                "recommendation": "Remove or rewrite questions with negative discrimination as they may be confusing high-performing students",
                "question_ids": [q["question_id"] for q in negative_disc]
            })

        # Check for too hard questions (high difficulty score = hard)
        too_hard = [q for q in question_analysis if q["difficulty"] > 0.85]
        if too_hard:
            recommendations.append({
                "priority": "Medium",
                "recommendation": f"Review {len(too_hard)} questions that may be too difficult (<15% correct)",
                "question_ids": [q["question_id"] for q in too_hard]
            })

        # Check for too easy questions (low difficulty score = easy)
        too_easy = [q for q in question_analysis if q["difficulty"] < 0.15]
        if too_easy:
            recommendations.append({
                "priority": "Medium",
                "recommendation": f"Consider increasing difficulty of {len(too_easy)} questions that are too easy (>85% correct)",
                "question_ids": [q["question_id"] for q in too_easy]
            })

        # Check for low discrimination
        low_disc = [
            q for q in question_analysis
            if 0 <= q["discrimination"] < 0.2 and q["quality"] != "Poor"
        ]
        if low_disc:
            recommendations.append({
                "priority": "Medium",
                "recommendation": f"Improve discrimination of {len(low_disc)} questions through better distractors or clearer wording",
                "question_ids": [q["question_id"] for q in low_disc]
            })

        # Check for weight imbalances
        max_scores = [q["max_score"] for q in question_analysis]
        if len(max_scores) > 1:
            max_weight = max(max_scores)
            min_weight = min(max_scores)
            mean_weight = np.mean(max_scores)
            std_weight = np.std(max_scores)

            # Check if weights are highly imbalanced (coefficient of variation > 0.5)
            if std_weight > 0 and (std_weight / mean_weight) > 0.5:
                recommendations.append({
                    "priority": "Medium",
                    "recommendation": f"Question weights are imbalanced (range: {min_weight}-{max_weight} points). Consider balancing weights to ensure fair assessment.",
                    "details": f"Weight distribution - Min: {min_weight}, Max: {max_weight}, Mean: {mean_weight:.1f}, Std: {std_weight:.1f}"
                })

            # Check if any single question dominates the test (>40% of total)
            total_weight = sum(max_scores)
            high_weight_questions = [(q["question_id"], q["max_score"])
                                    for q in question_analysis
                                    if q["max_score"] / total_weight > 0.4]
            if high_weight_questions:
                for qid, weight in high_weight_questions:
                    recommendations.append({
                        "priority": "Medium",
                        "recommendation": f"Question {qid} accounts for {weight/total_weight*100:.1f}% of total points - consider redistributing weights for better balance",
                        "question_ids": [qid]
                    })

        # General recommendations
        review_questions = [q for q in question_analysis if q["quality"] == "Review"]
        if len(review_questions) > len(question_analysis) * 0.3:
            recommendations.append({
                "priority": "Low",
                "recommendation": "Consider a comprehensive review of test items as many questions need improvement"
            })

        good_questions = [q for q in question_analysis if q["quality"] == "Good"]
        if len(good_questions) < len(question_analysis) * 0.5:
            recommendations.append({
                "priority": "Low",
                "recommendation": "Less than half of questions meet quality standards - consider test revision"
            })

        return recommendations

    def _generate_key_insights(
        self,
        scores: np.ndarray,
        question_analysis: List[Dict]
    ) -> List[str]:
        """Generate key insights from the analysis."""
        insights = []

        # Quality insights
        good_pct = sum(1 for q in question_analysis if q["quality"] == "Good") / len(question_analysis) * 100
        insights.append(f"{good_pct:.1f}% of questions meet quality standards")

        # Difficulty insights (inverted: high = hard, low = easy)
        avg_difficulty = np.mean([q["difficulty"] for q in question_analysis])
        if avg_difficulty < 0.4:
            insights.append("Test is generally easy with high average success rate")
        elif avg_difficulty > 0.7:
            insights.append("Test is generally difficult with low average success rate")
        else:
            insights.append("Test difficulty is well-balanced overall")

        # Discrimination insights
        avg_disc = np.mean([q["discrimination"] for q in question_analysis])
        if avg_disc > 0.3:
            insights.append("Questions effectively discriminate between high and low performers")
        elif avg_disc < 0.2:
            insights.append("Overall discrimination is poor - test may not effectively differentiate student abilities")

        # Score distribution
        total_scores = scores.sum(axis=1)
        cv = np.std(total_scores) / np.mean(total_scores)
        if cv > 0.3:
            insights.append("Wide variation in student scores indicates diverse ability levels")
        else:
            insights.append("Relatively narrow score distribution")

        # Weight insights (auto-detected from student responses)
        max_scores = [q["max_score"] for q in question_analysis]
        total_weight = sum(max_scores)
        mean_weight = np.mean(max_scores)
        unique_weights = len(set(max_scores))

        if unique_weights == 1:
            insights.append(f"All questions equally weighted ({int(max_scores[0])} point{'s' if max_scores[0] > 1 else ''} each)")
        else:
            weight_range = f"{int(min(max_scores))}-{int(max(max_scores))}"
            insights.append(f"Question weights vary from {weight_range} points (total: {int(total_weight)} points)")

        return insights

    def _empty_recommendations(self) -> Dict[str, Any]:
        """Return empty recommendations structure."""
        return {
            "question_analysis": [],
            "question_rankings": {},
            "distribution_details": {},
            "quality_distribution": {"good": 0, "review": 0, "poor": 0},
            "recommendations": [],
            "key_insights": []
        }
