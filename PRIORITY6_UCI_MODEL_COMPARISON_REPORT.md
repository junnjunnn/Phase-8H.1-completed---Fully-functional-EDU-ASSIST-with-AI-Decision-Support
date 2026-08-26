# PRIORITY 6 — UCI Model Comparison Report

## Summary

A comparison was not carried forward into a trained UCI model because the dataset does not satisfy the requirement for a defensible At Risk / Not At Risk target and the field structure is not compatible with the live EDU ASSIST risk feature contract.

## Comparison status

The UCI dataset did not pass the gate for safe training in the current risk system. Therefore:

- no UCI model was trained
- no UCI model artifact was created
- no production prediction behavior was changed
- the existing synthetic EDU ASSIST model remained preserved

## Old model

- Source: synthetic EDU ASSIST training data
- Target: `risk_status` with values `At Risk` and `Not At Risk`
- Feature contract: academic, attendance, behavior, intervention, enrollment, and school context
- Model artifact: `AI (ML)/models/risk_model.pkl`
- Operational purpose: live risk classification aligned to EDU ASSIST semantics

## UCI dataset

- Source: academic performance dataset for Math and Portuguese courses
- Target: no valid `At Risk` / `Not At Risk` label
- Feature contract: demographics, family background, study habits, absences, course grades
- Missing operational fields: section, grade level, enrollment, behavior, intervention, risk label, student ID
- Compatibility: not suitable for the current model

## Decision

The UCI dataset is rejected for the current risk model and no direct replacement is justified.

This is a safe stop, not a failed experiment. The correct requirement is that the dataset must be proven compatible before retraining or production integration. It was not.
