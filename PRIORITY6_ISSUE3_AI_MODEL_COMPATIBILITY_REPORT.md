# PRIORITY 6 — ISSUE 3 — AI MODEL COMPATIBILITY REPORT

## Summary
The root cause was a vocabulary mismatch between the saved Random Forest contract and the live EDU ASSIST data model. The trained model expects canonical values such as `Moonstone`, `Makatao (Love for Fellowmen)`, and `Demonstrate contributions toward solidarity`, while the current application still produces legacy names such as `Onyx`, `Respect`, and `Respectful Behavior`.

The compatibility fix was implemented by aligning the application’s preprocessing contract with the canonical model vocabulary, while preserving explicit warnings for unsupported values instead of silently discarding them.

## Root Cause
The saved model artifact and configuration in the AI model folder were trained against the canonical feature contract in [AI (ML)/models/feature_mapping.json](AI%20(ML)/models/feature_mapping.json), which includes:

- section values such as `A`, `B`, `C`, `D`, and `Moonstone`
- core values such as `Makatao (Love for Fellowmen)`
- indicators such as `Demonstrate contributions toward solidarity`
- canonical subject-to-feature mappings for active academic subjects

The live database and current app vocabulary were still generating legacy names, especially in real section and behavior records. The service was previously treating these mismatches as incompatible before prediction generation, which blocked valid predictions from using the actual trained model.

## Fix Implemented
The compatibility layer was updated in [BACKEND/predictions/services/prediction_service.py](BACKEND/predictions/services/prediction_service.py) to:

- canonicalize section, behavior, and intervention values against the model contract
- map legacy names to the exact trained vocabulary
- keep unsupported values as explicit diagnostics instead of silently dropping them
- preserve the actual trained-feature shape and strict validation against `feature_names_in_`

The canonical mappings were synchronized in [AI (ML)/models/feature_mapping.json](AI%20(ML)/models/feature_mapping.json) and mirrored in [AI (ML)/preprocessing/feature_mapping.json](AI%20(ML)/preprocessing/feature_mapping.json) so the runtime preprocessing and saved model contract remain aligned.

Regression coverage was also updated in [BACKEND/predictions/tests.py](BACKEND/predictions/tests.py) to validate the real compatibility contract, including:

- current subject aliases mapping to the saved feature slots
- legacy behavior values mapping to canonical DepEd values
- exact model one-hot feature structure preservation

## Validation
The following command was used to verify the patch:

```powershell
cd 'F:\edu_new\BACKEND'; .\venv\Scripts\python.exe manage.py test predictions.tests --keepdb -v 2
```

Fresh result:

- 22 tests ran
- 22 passed
- exit code 0

This confirms the compatibility fix works with the actual trained model contract and the current application data contract that is synchronized in the application’s feature mapping.

## Safety Notes
This solution is intentionally conservative:

- valid aliases are normalized to the canonical contract used by the saved model
- unsupported values still emit diagnostics and are not silently forced into the wrong slot
- the service continues to validate the exact model feature vector before prediction is allowed

This preserves prediction validity without weakening the actual contract check.
