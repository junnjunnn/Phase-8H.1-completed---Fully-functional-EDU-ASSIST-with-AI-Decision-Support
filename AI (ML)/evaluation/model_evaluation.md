# Model Evaluation Report

## Dataset Summary
- Training size: 800
- Testing size: 200
- Source: processed synthetic student dataset

## Algorithms Compared
- Decision Tree: Accuracy 0.985, Precision 0.978, Recall 0.9889, F1 0.9834, ROC-AUC 0.9854
- Random Forest: Accuracy 0.985, Precision 1.0, Recall 0.9667, F1 0.9831, ROC-AUC 0.9995
- Logistic Regression: Accuracy 0.94, Precision 0.9535, Recall 0.9111, F1 0.9318, ROC-AUC 0.9923

## Best Algorithm
- Random Forest
- Reason: highest ROC-AUC and strong balance across precision and recall for EDU ASSIST risk prediction.

## Feature Importance Summary
- general_average: 0.1709
- failed_subjects: 0.1170
- behavior_teacher_rating_AO: 0.0818
- high_grade_count: 0.0578
- attendance_rate: 0.0476
- absent_percentage: 0.0400
- present_days: 0.0391
- absent_days: 0.0376
- mapeh_grade: 0.0339
- education_grade: 0.0334

## Known Limitations
- This is a synthetic dataset and may not reflect all real-world school patterns.
- The current model uses default hyperparameters and has not been tuned.
- The model should be retrained when real school data becomes available.