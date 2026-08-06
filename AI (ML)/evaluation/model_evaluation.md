# Model Evaluation Report

## Dataset Summary
- Training size: 800
- Testing size: 200
- Source: processed synthetic student dataset

## Algorithms Compared
- Decision Tree: Accuracy 0.835, Precision 0.7949, Recall 0.7848, F1 0.7898, ROC-AUC 0.8263
- Random Forest: Accuracy 0.895, Precision 0.8718, Recall 0.8608, F1 0.8662, ROC-AUC 0.9071
- Logistic Regression: Accuracy 0.865, Precision 0.8611, Recall 0.7848, F1 0.8212, ROC-AUC 0.8797

## Best Algorithm
- Random Forest
- Reason: highest ROC-AUC and strong balance across precision and recall for EDU ASSIST risk prediction.

## Feature Importance Summary
- general_average: 0.1151
- failed_subjects: 0.0708
- behavior_teacher_rating_AO: 0.0595
- attendance_rate: 0.0493
- esp_grade: 0.0490
- filipino_grade: 0.0466
- mapeh_grade: 0.0462
- science_grade: 0.0456
- araling_panlipunan_grade: 0.0443
- mathematics_grade: 0.0428

## Known Limitations
- This is a synthetic dataset and may not reflect all real-world school patterns.
- The current model uses default hyperparameters and has not been tuned.
- The model should be retrained when real school data becomes available.