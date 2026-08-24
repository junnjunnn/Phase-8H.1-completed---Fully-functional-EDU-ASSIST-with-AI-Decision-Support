# Priority 6 Issue 3.4 — AI Risk Decision Alignment and Teacher-Readable Risk Assessment

## Objective

This issue focused on making the existing AI prediction understandable and useful to teachers and advisers without modifying the Random Forest model, altering its feature vocabulary, fabricating accuracy, or creating automatic interventions. The goal was to clearly separate:

1. academic concern indicators
2. AI risk prediction
3. teacher/adviser interpretation

## Current model behavior

The live model remains a binary Random Forest classifier:

- 0 = Not At Risk
- 1 = At Risk

The backend continues to use the trained model artifact and the saved model contract. The model was trained on a synthetic composite risk-labeling process using multiple indicators, including general average, failed subjects, attendance, lateness, behavior, interventions, and academic context. The issue was not to retrain the model or change the label definitions.

## Changes made

### Backend

- Updated the explanation summary wording so it uses teacher-friendly language such as "AI risk prediction" and "This means the model found patterns...".
- Kept the explanation grounded in model-based evidence without claiming causality.
- Ensured factor explanations say the information was considered by the model rather than saying it caused the prediction.

### Frontend

- Added a clear academic-concern section showing:
  - General Average
  - Academic Concern: YES/NO
  - Reason: General Average below 75 or not
- Added a separate AI risk section showing:
  - AI Risk: AT RISK / NOT AT RISK
  - Probability
  - Model: Random Forest
- Added transparency notices when academic concern and AI risk differ.
- Kept the prediction factors visible in teacher-readable form with:
  - Factor
  - Current student value
  - Why it matters
- Kept prediction generation available in the prediction area and ensured the latest prediction remains displayed after generation.

## Academic concern vs AI risk distinction

The interface now explicitly separates:

- Academic Concern: a school monitoring rule based on General Average < 75
- AI Risk Prediction: the current Random Forest estimate based on multiple student indicators

This avoids implying that General Average < 75 automatically determines the AI result.

## Probability explanation

The UI now explains probability as a model estimate, not a guarantee of failure. The wording is kept to the form:

- Model probability: 76.5%
- Based on the current student data, the model estimates a 76.5% probability for the predicted At Risk class.

No claim is made that the student will fail or that the model has identified a guaranteed real-world outcome.

## Factor explanation

Prediction factors continue to display the current student value and explain in plain language that the information was considered by the model.

Examples include:

- This was one of the indicators considered by the model.
- The student’s current general average is 71.86, which is below the school’s academic concern threshold of 75.

No factor text claims direct causality.

## Intervention suggestion design

The UI does not automatically create interventions or automatically notify parents. It provides a non-automatic advisory section labeled as decision support only.

This issue keeps intervention suggestions as teacher review guidance only when:

- AI risk is At Risk, or
- academic concern is YES

## Authorization verification

Authorization rules were preserved. The existing backend access model remains in place for:

- adviser-scoped student access
- subject-scoped academic access
- admin/guidance/registrar access behavior remained unchanged

## Tests performed

### Backend

Executed:

```bash
Set-Location 'F:\edu_new\BACKEND'; .\venv\Scripts\python.exe manage.py test predictions.tests --keepdb -v 2
```

Result: 25 tests passed.

### Frontend compile check

Executed:

```bash
Set-Location 'F:\edu_new\FRONTEND'; npm run build
```

Result: build completed successfully.

## Manual validation status

The issue requirements include a manual checklist for Edizon and responsive layout checks. In this session, the relevant automated validation was completed and the frontend project build succeeded. A full browser-driven manual walkthrough was not executed in the VS Code browser session in this pass, so browser validation remains a manual follow-up item if required by the project team.

## Known limitations

- The model is still synthetic and not a real-world production risk model.
- The probability remains a model output, not a guaranteed real-world likelihood of failure.
- Academic concern and AI risk are intentionally separate indicators and may legitimately differ.
- Teacher judgment remains the final decision layer.

## Confirmation

The Random Forest model itself was not retrained, replaced, or modified in this issue. The model artifact and trained feature vocabulary remain intact.

## Files changed

- [FRONTEND/src/pages/students/StudentDetailPage.jsx](FRONTEND/src/pages/students/StudentDetailPage.jsx)
- [BACKEND/predictions/services/explanation_service.py](BACKEND/predictions/services/explanation_service.py)
- [BACKEND/predictions/services/prediction_service.py](BACKEND/predictions/services/prediction_service.py)
- [BACKEND/predictions/tests.py](BACKEND/predictions/tests.py)
- [PRIORITY6_ISSUE3_4_AI_RISK_DECISION_ALIGNMENT_REPORT.md](PRIORITY6_ISSUE3_4_AI_RISK_DECISION_ALIGNMENT_REPORT.md)

## Summary

This issue was completed as a transparency and decision-support update: the UI now separates academic concern from AI risk, explains the label in teacher-friendly terms, keeps the model’s binary behavior intact, avoids causal over-claims, and leaves the underlying Random Forest unchanged.
