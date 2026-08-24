# Priority 6 Issue 3.2 — Prediction Interpretation and Transparency

## Scope
This fix keeps the existing Random Forest model and its trained vocabulary unchanged. It does not retrain the model or alter the saved feature contract. The work is limited to making the prediction output clearer, safer, and more useful to teachers and advisers.

## Actual current behavior inspected
The live implementation already behaves as follows:

- `PredictionService.predict_for_student()` builds a feature frame from the student’s current academic, attendance, and behavior data.
- It validates that frame against `model.feature_names_in_` before predicting.
- It uses `model.predict_proba()` to compute the confidence for the selected class.
- The saved label map converts the tree prediction to `At Risk` or `Not At Risk`.
- `save_prediction()` stores a single risk level (`High` when `At Risk`, otherwise `Low`) and saves the top model-driving factors.
- The explanation text is model-importance based and is not a causal diagnosis of personal failure or misconduct.

This means the system is a decision-support estimator rather than a confirmed diagnosis. The UI and summary text must reflect that accurately.

## What changed
### Backend
- Updated the explanation summary in `BACKEND/predictions/services/explanation_service.py` to:
  - state that the result is an “AI risk estimate”;
  - describe it as model-based and based on current academic, attendance, and behavior indicators;
  - explicitly say it is not a confirmed diagnosis;
  - instruct teacher review before formal intervention decisions.
- Kept the prediction label format and model summary structure compatible with the existing tests and API consumers.

### Frontend
- Updated the guidance in `FRONTEND/src/pages/students/StudentDetailPage.jsx` so it describes the prediction as decision support, not a definitive diagnosis.
- The wording now focuses on:
  - current evidence review;
  - top contributing factors;
  - teacher judgment and live academic records as the final decision basis.

## Evidence and validation
Verified with:

```bash
Set-Location -Path 'f:\edu_new\BACKEND'; python manage.py test predictions.tests --keepdb
```

Result:

- 23 tests run
- all passed
- exit status successful

This confirms the updated explanation language remains compatible with the prediction flow and the existing tests for generation, persistence, and authorization.

## Result
The prediction now communicates the real behavior of the model without inventing unsupported claims or creating interventions automatically. Teachers receive an understandable, evidence-based summary that is transparent about model limitations and encourages live review of actual academic and support data.
