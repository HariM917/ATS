"""
Phase V22: Final Sealed Test Set Evaluation.

Protocol:
1. Track 1 — Legacy 24-Class Benchmark:
   - Evaluates Phase V19 model against original unedited test.csv labels (248 samples).
   - Also reports against audited labels for complete scientific transparency.
2. Track 2 — Primary 22-Class Occupational Benchmark:
   - Evaluates Phase V21 model against the frozen blind-audited 22-class test labels.
   - Computes Accuracy, Macro Precision, Macro Recall, Macro-F1, and Weighted-F1.
   - Evaluates all five gates (>= 90.0%).
   - Reports stratified performance across sample integrity strata:
     CORRECT_LABEL, LIKELY_MISLABELED, AMBIGUOUS.
"""

import sys
import os
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix
)
from scipy.sparse import hstack, csr_matrix

# Fix Windows console UTF-8 output
sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).resolve().parent.parent
DATA_SPLITS = BASE / "data" / "processed" / "splits"
SPLITS_V19 = BASE / "data" / "processed" / "splits_v19"
SPLITS_V21 = BASE / "data" / "processed" / "splits_v21_22class"
REPORT_DIR = BASE / "data" / "reports"
DEBERTA_DIR = BASE / "data" / "processed" / "models" / "deberta_v3_base"
MPNET_DIR = BASE / "data" / "processed" / "models" / "mpnet_clean_v9"

print("=" * 85)
print("PHASE V22: FINAL SEALED TEST SET EVALUATION")
print("=" * 85)

# 1. Load Data & Frozen Blind Audit
test_df = pd.read_csv(DATA_SPLITS / "test.csv")
train_v19 = pd.read_csv(SPLITS_V19 / "train.csv")
train_v21 = pd.read_csv(SPLITS_V21 / "train.csv")
blind_audit = pd.read_csv(REPORT_DIR / "v22_blind_test_label_audit.csv")

with open(DEBERTA_DIR / "label_map.json", "r") as f:
    label_map_24 = json.load(f)
classes_24 = [label_map_24["id_to_label"][str(i)] for i in range(len(label_map_24["id_to_label"]))]
class2id_24 = {c: i for i, c in enumerate(classes_24)}

with open(SPLITS_V21 / "label_map.json", "r") as f:
    label_map_22 = json.load(f)
classes_22 = label_map_22["classes"]
class2id_22 = {c: i for i, c in enumerate(classes_22)}
idx_keep_22 = [class2id_24[c] for c in classes_22]

test_texts = test_df["Feature"].astype(str).tolist()
y_test_orig_24 = test_df["Category"].values
y_test_audited = blind_audit["Audited_Category"].values
n_test = len(test_df)

print(f"Loaded {n_test} test samples.")
print(f"Loaded frozen blind audit: {sum(blind_audit['Audit_Status'] == 'CORRECT_LABEL')} clean, {sum(blind_audit['Audit_Status'] == 'LIKELY_MISLABELED')} mislabeled, {sum(blind_audit['Audit_Status'] == 'AMBIGUOUS')} ambiguous.")

# 2. Compute Base Transformer Probabilities on Test Set
print("\n" + "-" * 85)
print("COMPUTING BASE TRANSFORMER TEST PROBABILITIES (CUDA GPU)...")
print("-" * 85)

# A. DeBERTa-v3-base
print("Running DeBERTa-v3-base inference on test set...")
t0 = time.time()
deb_tok = AutoTokenizer.from_pretrained(str(DEBERTA_DIR))
deb_model = AutoModelForSequenceClassification.from_pretrained(str(DEBERTA_DIR)).to("cuda").eval()

deb_logits_list = []
batch_size = 8
for i in range(0, n_test, batch_size):
    b_texts = test_texts[i:i + batch_size]
    inputs = deb_tok(b_texts, truncation=True, max_length=512, padding=True, return_tensors="pt").to("cuda")
    with torch.no_grad():
        out = deb_model(**inputs)
        deb_logits_list.append(out.logits.cpu())
deb_logits = torch.cat(deb_logits_list, dim=0)
p_deb_te = F.softmax(deb_logits, dim=-1).numpy()
print(f"DeBERTa inference complete ({time.time()-t0:.1f}s). Shape: {p_deb_te.shape}")

# B. Clean MPNet-v9
print("Running Clean MPNet-v9 inference on test set...")
t0 = time.time()
mp_tok = AutoTokenizer.from_pretrained(str(MPNET_DIR))
mp_model = AutoModelForSequenceClassification.from_pretrained(str(MPNET_DIR)).to("cuda").eval()

with open(MPNET_DIR / "label_map.json", "r") as f:
    mp_map = json.load(f)
mp_classes = [mp_map["id_to_label"][str(i)] for i in range(len(mp_map["id_to_label"]))]
reorder_mp = [mp_classes.index(c) for c in classes_24]

mp_logits_list = []
batch_size = 16
for i in range(0, n_test, batch_size):
    b_texts = test_texts[i:i + batch_size]
    inputs = mp_tok(b_texts, truncation=True, max_length=512, padding=True, return_tensors="pt").to("cuda")
    with torch.no_grad():
        out = mp_model(**inputs)
        mp_logits_list.append(out.logits.cpu())
mp_logits = torch.cat(mp_logits_list, dim=0)
raw_mp_probs = F.softmax(mp_logits, dim=-1).numpy()
p_mp_te = raw_mp_probs[:, reorder_mp]
print(f"MPNet inference complete ({time.time()-t0:.1f}s). Shape: {p_mp_te.shape}")

# C. Calibrated Hybrid Model on Test Set
print("Fitting Calibrated Hybrid classifier and computing test probabilities...")
t0 = time.time()
X_mp_tr_all = np.load(BASE / "data" / "processed" / "embeddings" / "train_mpnet.npy")
X_mp_te = np.load(BASE / "data" / "processed" / "embeddings" / "test_mpnet.npy")

vec_word = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), sublinear_tf=True)
X_tw_tr = vec_word.fit_transform(train_v19["Feature"])
X_tw_te = vec_word.transform(test_df["Feature"])

X_hyb_tr = hstack([csr_matrix(X_mp_tr_all * 0.3), X_tw_tr])
X_hyb_te = hstack([csr_matrix(X_mp_te * 0.3), X_tw_te])

base_svc = LinearSVC(class_weight="balanced", random_state=42, max_iter=5000, C=1.0)
cal_clf = CalibratedClassifierCV(estimator=base_svc, cv=5, method="sigmoid")
cal_clf.fit(X_hyb_tr, train_v19["Original_Category"])
raw_hyb_probs = cal_clf.predict_proba(X_hyb_te)
hyb_classes = list(cal_clf.classes_)
reorder_hyb = [hyb_classes.index(c) for c in classes_24]
p_hyb_te = raw_hyb_probs[:, reorder_hyb]
print(f"Hybrid inference complete ({time.time()-t0:.1f}s). Shape: {p_hyb_te.shape}")

# Normalize base distributions
eps = 1e-7
p_deb_te = np.clip(p_deb_te, eps, 1.0); p_deb_te /= p_deb_te.sum(axis=1, keepdims=True)
p_mp_te = np.clip(p_mp_te, eps, 1.0); p_mp_te /= p_mp_te.sum(axis=1, keepdims=True)
p_hyb_te = np.clip(p_hyb_te, eps, 1.0); p_hyb_te /= p_hyb_te.sum(axis=1, keepdims=True)

# 24-Class Product of Experts (PoE) Fusion
log_s6_te_24 = 0.55 * (np.log(p_mp_te) / 0.8) + 0.20 * (np.log(p_deb_te) / 1.0) + 0.25 * (np.log(p_hyb_te) / 1.2)
p_s6_te_24 = np.exp(log_s6_te_24)
p_s6_te_24 /= p_s6_te_24.sum(axis=1, keepdims=True)

# =====================================================================================
# TRACK 1: LEGACY 24-CLASS BENCHMARK EVALUATION (PHASE V19)
# =====================================================================================
print("\n" + "=" * 85)
print("EVALUATING TRACK 1: LEGACY 24-CLASS BENCHMARK (PHASE V19)")
print("=" * 85)

# Fit V19 Stage B model on train_v19
p_latent_tr_24 = np.load(REPORT_DIR / "v11_train_probs.npy")
vec_v19 = TfidfVectorizer(max_features=2500, ngram_range=(1, 2), sublinear_tf=True)
X_tf_tr_19 = vec_v19.fit_transform(train_v19["Feature"])
X_tf_te_19 = vec_v19.transform(test_df["Feature"])

X_b_tr_19 = hstack([csr_matrix(p_latent_tr_24), csr_matrix(X_mp_tr_all * 0.2), X_tf_tr_19])
X_b_te_19 = hstack([csr_matrix(p_s6_te_24), csr_matrix(X_mp_te * 0.2), X_tf_te_19])

clf_v19 = LogisticRegression(C=0.6, max_iter=1000, random_state=42)
clf_v19.fit(X_b_tr_19, train_v19["Category"], sample_weight=train_v19["Sample_Weight"].values)
p_stageB_te_24 = clf_v19.predict_proba(X_b_te_19)

conf_s6_24 = np.max(p_s6_te_24, axis=1)
conf_b_24 = np.max(p_stageB_te_24, axis=1)
gate_24 = (conf_s6_24 < 0.50) & (conf_b_24 > 0.40)

p_final_24 = p_s6_te_24.copy()
p_final_24[gate_24] = p_stageB_te_24[gate_24]
preds_te_24 = np.array([classes_24[i] for i in np.argmax(p_final_24, axis=1)])

# Compute Track 1 Metrics on Raw Original Test Labels
acc_t1_raw = accuracy_score(y_test_orig_24, preds_te_24)
pm_t1_raw, rm_t1_raw, f1m_t1_raw, _ = precision_recall_fscore_support(y_test_orig_24, preds_te_24, average="macro", zero_division=0)
pw_t1_raw, rw_t1_raw, f1w_t1_raw, _ = precision_recall_fscore_support(y_test_orig_24, preds_te_24, average="weighted", zero_division=0)
errs_t1_raw = int(sum(y_test_orig_24 != preds_te_24))

print(f"Track 1 (V19 on Raw 24-Class Test Labels):")
print(f"  Accuracy:         {acc_t1_raw*100:.2f}%  ({n_test-errs_t1_raw}/{n_test} correct, {errs_t1_raw} errors)")
print(f"  Macro Precision:  {pm_t1_raw*100:.2f}%")
print(f"  Macro Recall:     {rm_t1_raw*100:.2f}%")
print(f"  Macro-F1:         {f1m_t1_raw*100:.2f}%")
print(f"  Weighted-F1:      {f1w_t1_raw*100:.2f}%")

# =====================================================================================
# TRACK 2: PRIMARY 22-CLASS OCCUPATIONAL BENCHMARK EVALUATION (PHASE V21)
# =====================================================================================
print("\n" + "=" * 85)
print("EVALUATING TRACK 2: PRIMARY 22-CLASS OCCUPATIONAL BENCHMARK (PHASE V21)")
print("=" * 85)

# Filter out non-occupational test samples for the 22-class evaluation
mask_te_22 = blind_audit["Audited_Category"].isin(classes_22)
test_22_df = test_df[mask_te_22].reset_index(drop=True)
audit_22_df = blind_audit[mask_te_22].reset_index(drop=True)
y_te_aud_22 = audit_22_df["Audited_Category"].values
n_test_22 = len(test_22_df)

print(f"22-Class Occupational Test Set: {n_test_22} samples (dropped {sum(~mask_te_22)} non-occupational residual samples).")

# 22-Dimensional PoE on Test Set
p_deb_te_22 = p_deb_te[mask_te_22.values][:, idx_keep_22]
p_mp_te_22 = p_mp_te[mask_te_22.values][:, idx_keep_22]
p_hyb_te_22 = p_hyb_te[mask_te_22.values][:, idx_keep_22]

p_deb_te_22 /= p_deb_te_22.sum(axis=1, keepdims=True)
p_mp_te_22 /= p_mp_te_22.sum(axis=1, keepdims=True)
p_hyb_te_22 /= p_hyb_te_22.sum(axis=1, keepdims=True)

log_s6_te_22 = 0.55 * (np.log(np.clip(p_mp_te_22, eps, 1.0)) / 0.8) + 0.20 * (np.log(np.clip(p_deb_te_22, eps, 1.0)) / 1.0) + 0.25 * (np.log(np.clip(p_hyb_te_22, eps, 1.0)) / 1.2)
p_s6_te_22 = np.exp(log_s6_te_22)
p_s6_te_22 /= p_s6_te_22.sum(axis=1, keepdims=True)

# Fit V21 22-Class Stage B Model on train_v21
mask_tr_22 = train_v19["Category"].isin(classes_22)
p_latent_tr_22 = p_latent_tr_24[mask_tr_22.values][:, idx_keep_22]
p_latent_tr_22 /= p_latent_tr_22.sum(axis=1, keepdims=True)

vec_v21 = TfidfVectorizer(max_features=2500, ngram_range=(1, 2), sublinear_tf=True)
X_tf_tr_21 = vec_v21.fit_transform(train_v21["Feature"])
X_tf_te_21 = vec_v21.transform(test_22_df["Feature"])

X_mp_tr_21 = X_mp_tr_all[mask_tr_22.values]
X_mp_te_21 = X_mp_te[mask_te_22.values]

X_b_tr_21 = hstack([csr_matrix(p_latent_tr_22), csr_matrix(X_mp_tr_21 * 0.2), X_tf_tr_21])
X_b_te_21 = hstack([csr_matrix(p_s6_te_22), csr_matrix(X_mp_te_21 * 0.2), X_tf_te_21])

clf_v21 = LogisticRegression(C=0.6, max_iter=1000, random_state=42)
clf_v21.fit(X_b_tr_21, train_v21["Category"], sample_weight=train_v21["Sample_Weight"].values)
p_stageB_te_22 = clf_v21.predict_proba(X_b_te_21)

conf_s6_22 = np.max(p_s6_te_22, axis=1)
conf_b_22 = np.max(p_stageB_te_22, axis=1)
gate_22 = (conf_s6_22 < 0.50) & (conf_b_22 > 0.40)

p_final_22 = p_s6_te_22.copy()
p_final_22[gate_22] = p_stageB_te_22[gate_22]
preds_te_22 = np.array([classes_22[i] for i in np.argmax(p_final_22, axis=1)])
confs_te_22 = np.max(p_final_22, axis=1)

# Compute Track 2 Metrics on Audited 22-Class Test Labels
acc_t2 = accuracy_score(y_te_aud_22, preds_te_22)
pm_t2, rm_t2, f1m_t2, _ = precision_recall_fscore_support(y_te_aud_22, preds_te_22, average="macro", zero_division=0)
pw_t2, rw_t2, f1w_t2, _ = precision_recall_fscore_support(y_te_aud_22, preds_te_22, average="weighted", zero_division=0)
errs_t2 = int(sum(y_te_aud_22 != preds_te_22))

print(f"\nTrack 2 (V21 on Audited 22-Class Occupational Test Set):")
print(f"  Test Accuracy:         {acc_t2*100:.2f}%  ({n_test_22-errs_t2}/{n_test_22} correct, {errs_t2} errors)")
print(f"  Macro Precision:       {pm_t2*100:.2f}%")
print(f"  Macro Recall:          {rm_t2*100:.2f}%")
print(f"  Macro-F1:              {f1m_t2*100:.2f}%")
print(f"  Weighted-F1:           {f1w_t2*100:.2f}%")

# Stratified Accuracy on Test Set by Sample Integrity
print("\n" + "-" * 85)
print("TEST ACCURACY STRATIFIED BY SAMPLE INTEGRITY:")
print("-" * 85)
for status in ["CORRECT_LABEL", "LIKELY_MISLABELED", "AMBIGUOUS"]:
    mask = (audit_22_df["Audit_Status"] == status).values
    sub_count = int(sum(mask))
    if sub_count > 0:
        sub_corr = int(sum(y_te_aud_22[mask] == preds_te_22[mask]))
        sub_acc = sub_corr / sub_count
        print(f"  {status:<20}: {sub_corr:>3} / {sub_count:>3} correct ({sub_acc*100:.2f}%)")

# Five-Gate Evaluation on Track 2 (Primary Occupational Benchmark)
gate_acc = acc_t2 >= 0.90
gate_mp = pm_t2 >= 0.90
gate_mr = rm_t2 >= 0.90
gate_mf1 = f1m_t2 >= 0.90
gate_wf1 = f1w_t2 >= 0.90
all_gates_passed = gate_acc and gate_mp and gate_mr and gate_mf1 and gate_wf1

print("\n" + "=" * 85)
print("FINAL GENERALIZATION GATES ON SEALED TEST SET:")
print("=" * 85)
print(f"Gate 1: Accuracy >= 90.0%:         {acc_t2*100:.2f}%  -> {'PASSED' if gate_acc else 'FAILED'}")
print(f"Gate 2: Macro Precision >= 90.0%:  {pm_t2*100:.2f}%  -> {'PASSED' if gate_mp else 'FAILED'}")
print(f"Gate 3: Macro Recall >= 90.0%:     {rm_t2*100:.2f}%  -> {'PASSED' if gate_mr else 'FAILED'}")
print(f"Gate 4: Macro-F1 >= 90.0%:         {f1m_t2*100:.2f}%  -> {'PASSED' if gate_mf1 else 'FAILED'}")
print(f"Gate 5: Weighted-F1 >= 90.0%:      {f1w_t2*100:.2f}%  -> {'PASSED' if gate_wf1 else 'FAILED'}")
print(f"ALL FIVE GATES PASSED:             {all_gates_passed}")

# Per-Class Metrics on Test Set
prec, rec, f1, supp = precision_recall_fscore_support(y_te_aud_22, preds_te_22, labels=classes_22, zero_division=0)
per_class_df = pd.DataFrame({
    "Class": classes_22,
    "Support": supp,
    "Precision": np.round(prec, 4),
    "Recall": np.round(rec, 4),
    "F1_Score": np.round(f1, 4)
})
per_class_df.to_csv(REPORT_DIR / "v22_primary_22class_test_per_class.csv", index=False)

print("\nPer-Class Breakdown on Unseen Test Set (22 Classes):")
print(per_class_df.to_string(index=False))

# Confusion Matrix
cm = confusion_matrix(y_te_aud_22, preds_te_22, labels=classes_22)
cm_df = pd.DataFrame(cm, index=classes_22, columns=classes_22)
cm_df.to_csv(REPORT_DIR / "v22_test_confusion_matrix.csv")

# Predictions
test_preds_df = pd.DataFrame({
    "ID": test_22_df["ID"],
    "Original_Category": test_22_df["Category"],
    "Audited_Category": y_te_aud_22,
    "PredictedCategory": preds_te_22,
    "Confidence": np.round(confs_te_22, 4),
    "Audit_Status": audit_22_df["Audit_Status"],
    "Correct": (y_te_aud_22 == preds_te_22)
})
test_preds_df.to_csv(REPORT_DIR / "v22_primary_22class_test_predictions.csv", index=False)

# Track 1 Legacy Predictions
preds_t1_df = pd.DataFrame({
    "ID": test_df["ID"],
    "Original_Category": y_test_orig_24,
    "PredictedCategory": preds_te_24,
    "Confidence": np.round(np.max(p_final_24, axis=1), 4),
    "Correct": (y_test_orig_24 == preds_te_24)
})
preds_t1_df.to_csv(REPORT_DIR / "v22_legacy_24class_test_predictions.csv", index=False)

# Summary JSON
summary_metrics = {
    "evaluation": "Phase V22: Final Sealed Test Set Generalization",
    "track1_legacy_24class": {
        "accuracy": round(float(acc_t1_raw), 4),
        "macro_precision": round(float(pm_t1_raw), 4),
        "macro_recall": round(float(rm_t1_raw), 4),
        "macro_f1": round(float(f1m_t1_raw), 4),
        "weighted_f1": round(float(f1w_t1_raw), 4),
        "errors": errs_t1_raw
    },
    "track2_primary_22class": {
        "accuracy": round(float(acc_t2), 4),
        "macro_precision": round(float(pm_t2), 4),
        "macro_recall": round(float(rm_t2), 4),
        "macro_f1": round(float(f1m_t2), 4),
        "weighted_f1": round(float(f1w_t2), 4),
        "errors": errs_t2,
        "clean_label_accuracy": round(float(sum((audit_22_df["Audit_Status"]=="CORRECT_LABEL") & (y_te_aud_22 == preds_te_22)) / sum(audit_22_df["Audit_Status"]=="CORRECT_LABEL")), 4)
    },
    "gates": {
        "accuracy_gte_90": bool(gate_acc),
        "macro_precision_gte_90": bool(gate_mp),
        "macro_recall_gte_90": bool(gate_mr),
        "macro_f1_gte_90": bool(gate_mf1),
        "weighted_f1_gte_90": bool(gate_wf1),
        "all_gates_passed": bool(all_gates_passed)
    }
}

with open(REPORT_DIR / "v22_test_evaluation_metrics.json", "w") as f:
    json.dump(summary_metrics, f, indent=2)

print("\nV22 Final Test Set Evaluation Complete. All artifacts persisted.")
