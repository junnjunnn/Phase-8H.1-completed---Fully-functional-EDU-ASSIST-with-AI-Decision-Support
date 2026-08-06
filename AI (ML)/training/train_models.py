import json
import pickle
import time
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, classification_report

BASE_DIR = Path(r'f:\edu_new\AI (ML)')
PREPROCESSING_DIR = BASE_DIR / 'preprocessing'
EVALUATION_DIR = BASE_DIR / 'evaluation'
MODELS_DIR = BASE_DIR / 'models'

X_TRAIN_PATH = PREPROCESSING_DIR / 'X_train.csv'
X_TEST_PATH = PREPROCESSING_DIR / 'X_test.csv'
Y_TRAIN_PATH = PREPROCESSING_DIR / 'y_train.csv'
Y_TEST_PATH = PREPROCESSING_DIR / 'y_test.csv'
MAPPING_PATH = PREPROCESSING_DIR / 'feature_mapping.json'


def load_datasets() -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    X_train = pd.read_csv(X_TRAIN_PATH)
    X_test = pd.read_csv(X_TEST_PATH)
    y_train = pd.read_csv(Y_TRAIN_PATH).squeeze('columns')
    y_test = pd.read_csv(Y_TEST_PATH).squeeze('columns')

    if X_train.shape[0] != y_train.shape[0]:
        raise ValueError('Training features and labels have inconsistent dimensions')
    if X_test.shape[0] != y_test.shape[0]:
        raise ValueError('Test features and labels have inconsistent dimensions')
    if list(X_train.columns) != list(X_test.columns):
        raise ValueError('Train and test features are inconsistent')

    return X_train, X_test, y_train, y_test


def train_and_evaluate(X_train, X_test, y_train, y_test):
    models = {
        'Decision Tree': DecisionTreeClassifier(random_state=42),
        'Random Forest': RandomForestClassifier(random_state=42, n_estimators=200),
        'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
    }

    results = []
    for name, model in models.items():
        start = time.time()
        model.fit(X_train, y_train)
        train_time = time.time() - start

        pred_start = time.time()
        y_pred = model.predict(X_test)
        pred_time = time.time() - pred_start

        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, pos_label=1, zero_division=0)
        recall = recall_score(y_test, y_pred, pos_label=1, zero_division=0)
        f1 = f1_score(y_test, y_pred, pos_label=1, zero_division=0)
        roc_auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
        cm = confusion_matrix(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

        results.append({
            'Algorithm': name,
            'Accuracy': round(accuracy, 4),
            'Precision': round(precision, 4),
            'Recall': round(recall, 4),
            'F1': round(f1, 4),
            'ROC-AUC': round(roc_auc, 4),
            'Training Time': round(train_time, 4),
            'Prediction Time': round(pred_time, 4),
            'Confusion Matrix': cm.tolist(),
            'Classification Report': report,
            'Model': model,
        })

    return results


def save_comparison(results, feature_names):
    comparison_df = pd.DataFrame([
        {
            'Algorithm': r['Algorithm'],
            'Accuracy': r['Accuracy'],
            'Precision': r['Precision'],
            'Recall': r['Recall'],
            'F1': r['F1'],
            'ROC-AUC': r['ROC-AUC'],
            'Training Time': r['Training Time'],
            'Prediction Time': r['Prediction Time'],
        }
        for r in results
    ])
    comparison_path = EVALUATION_DIR / 'model_comparison.csv'
    comparison_df.to_csv(comparison_path, index=False)

    best_result = max(results, key=lambda r: r['ROC-AUC'])
    best_model = best_result['Model']

    with (MODELS_DIR / 'risk_model.pkl').open('wb') as fh:
        pickle.dump(best_model, fh)

    with (MODELS_DIR / 'label_encoder.pkl').open('wb') as fh:
        pickle.dump({'target_map': {1: 'At Risk', 0: 'Not At Risk'}}, fh)

    with (MODELS_DIR / 'feature_mapping.json').open('w', encoding='utf-8') as fh:
        json.dump(json.loads(MAPPING_PATH.read_text(encoding='utf-8')), fh, indent=2)

    if hasattr(best_model, 'feature_importances_'):
        importances = pd.Series(best_model.feature_importances_, index=feature_names)
        top_features = importances.sort_values(ascending=False).head(20)
        top_features.to_frame(name='importance').to_csv(EVALUATION_DIR / 'feature_importance.csv')

        plt.figure(figsize=(10, 8))
        top_features.plot(kind='barh')
        plt.title('Top 20 Feature Importances - Random Forest')
        plt.tight_layout()
        plt.savefig(EVALUATION_DIR / 'feature_importance.png', dpi=300)
        plt.close()

    return best_result


def write_evaluation_report(results, best_result, feature_names):
    report_lines = [
        '# Model Evaluation Report',
        '',
        '## Dataset Summary',
        f'- Training size: {len(pd.read_csv(X_TRAIN_PATH))}',
        f'- Testing size: {len(pd.read_csv(X_TEST_PATH))}',
        '- Source: processed synthetic student dataset',
        '',
        '## Algorithms Compared',
    ]
    for r in results:
        report_lines.append(f"- {r['Algorithm']}: Accuracy {r['Accuracy']}, Precision {r['Precision']}, Recall {r['Recall']}, F1 {r['F1']}, ROC-AUC {r['ROC-AUC']}")

    report_lines.extend([
        '',
        '## Best Algorithm',
        f"- {best_result['Algorithm']}",
        f"- Reason: highest ROC-AUC and strong balance across precision and recall for EDU ASSIST risk prediction.",
        '',
        '## Feature Importance Summary',
    ])

    if hasattr(best_result['Model'], 'feature_importances_'):
        importances = pd.Series(best_result['Model'].feature_importances_, index=feature_names)
        top_features = importances.sort_values(ascending=False).head(10)
        for name, value in top_features.items():
            report_lines.append(f'- {name}: {value:.4f}')

    report_lines.extend([
        '',
        '## Known Limitations',
        '- This is a synthetic dataset and may not reflect all real-world school patterns.',
        '- The current model uses default hyperparameters and has not been tuned.',
        '- The model should be retrained when real school data becomes available.',
    ])

    (EVALUATION_DIR / 'model_evaluation.md').write_text('\n'.join(report_lines), encoding='utf-8')


def main():
    X_train, X_test, y_train, y_test = load_datasets()
    results = train_and_evaluate(X_train, X_test, y_train, y_test)
    best_result = save_comparison(results, X_train.columns.tolist())
    write_evaluation_report(results, best_result, X_train.columns.tolist())

    print('Training completed.')
    print('Comparison table saved to', EVALUATION_DIR / 'model_comparison.csv')
    print('Feature importance saved to', EVALUATION_DIR / 'feature_importance.csv')
    print('Evaluation report saved to', EVALUATION_DIR / 'model_evaluation.md')
    print('Best model saved to', MODELS_DIR / 'risk_model.pkl')

    print('Best model predictions:')
    y_pred = best_result['Model'].predict(X_test)
    for idx, pred in enumerate(y_pred[:10]):
        label = 'At Risk' if pred == 1 else 'Not At Risk'
        print(idx, label)


if __name__ == '__main__':
    main()
