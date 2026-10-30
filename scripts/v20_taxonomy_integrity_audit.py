"""
Phase V20: Full 24-Class Taxonomy & Split Integrity Audit.

Analyzes the occupational validity, noise profile, and split distribution across all 2,480 records:
1. Audits every one of the 24 classes:
   - Original count (Train, Val, Test)
   - Audited count (Train, Val)
   - Relabeled OUT (count and top destination classes)
   - Relabeled IN (count and top origin classes)
   - Genuine occupational examples
   - Ambiguous examples
   - Noisy examples
   - Audit Confidence / Occupational Purity Score
2. Deep dive into the 7 fragile classes:
   - AUTOMOBILE, BPO, AGRICULTURE, APPAREL, ARTS, FITNESS, BANKING.
3. Rigorous empirical answer to the core question:
   Are AUTOMOBILE and BPO legitimate occupational classes, or are they industry tags masquerading as occupations?
"""

import sys
import os
import json
from pathlib import Path
import numpy as np
import pandas as pd

# Fix Windows console UTF-8 output
sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).resolve().parent.parent
DATA_SPLITS = BASE / "data" / "processed" / "splits"
REPORT_DIR = BASE / "data" / "reports"
DEBERTA_DIR = BASE / "data" / "processed" / "models" / "deberta_v3_base"

print("=" * 85)
print("PHASE V20: FULL 24-CLASS TAXONOMY & SPLIT INTEGRITY AUDIT")
print("=" * 85)

# 1. Load Data
dedup_df = pd.read_csv(BASE / "data" / "processed" / "cleaned_resume_data_deduplicated.csv")
train_df = pd.read_csv(DATA_SPLITS / "train.csv")
val_df = pd.read_csv(DATA_SPLITS / "validation.csv")
v19_audit = pd.read_csv(REPORT_DIR / "v19_full_dataset_audit.csv")

with open(DEBERTA_DIR / "label_map.json", "r") as f:
    label_map = json.load(f)
classes = [label_map["id_to_label"][str(i)] for i in range(len(label_map["id_to_label"]))]

train_ids = set(train_df["ID"])
val_ids = set(val_df["ID"])
test_ids = set(dedup_df["ID"]) - train_ids - val_ids

test_df = dedup_df[dedup_df["ID"].isin(test_ids)]

print(f"Total deduplicated corpus: {len(dedup_df)} resumes.")
print(f"Split breakdown: Train = {len(train_ids)}, Validation = {len(val_ids)}, Test = {len(test_ids)}")

# 2. Compute 24-Class Audit Matrix
matrix_records = []

for c in sorted(classes):
    # Original counts
    orig_tr = int(sum(train_df["Category"] == c))
    orig_va = int(sum(val_df["Category"] == c))
    orig_te = int(sum(test_df["Category"] == c))
    orig_total = orig_tr + orig_va + orig_te
    
    # Audit subset (Train + Val: 2,232 samples)
    c_audit_sub = v19_audit[v19_audit["Original_Category"] == c]
    
    genuine_count = int(sum(c_audit_sub["Audit_Status"] == "CORRECT_LABEL"))
    relabeled_out = int(sum(c_audit_sub["Audit_Status"] == "LIKELY_MISLABELED"))
    ambiguous_count = int(sum(c_audit_sub["Audit_Status"] == "AMBIGUOUS"))
    noisy_count = int(sum(c_audit_sub["Audit_Status"] == "POSSIBLY_NOISY"))
    
    # Samples relabeled IN from other categories
    relabeled_in_sub = v19_audit[(v19_audit["Category"] == c) & (v19_audit["Original_Category"] != c)]
    relabeled_in = len(relabeled_in_sub)
    
    # Audited counts in Train and Val
    aud_tr = int(sum((v19_audit["Split"] == "train") & (v19_audit["Category"] == c)))
    aud_va = int(sum((v19_audit["Split"] == "validation") & (v19_audit["Category"] == c)))
    aud_total_known = aud_tr + aud_va
    
    # Audit confidence / Occupational Purity (% of original samples that were genuine occupational matches)
    audit_confidence = genuine_count / len(c_audit_sub) if len(c_audit_sub) > 0 else 0.0
    
    # Destinations of relabeled OUT samples
    dest_counts = c_audit_sub[c_audit_sub["Audit_Status"] == "LIKELY_MISLABELED"]["Category"].value_counts().to_dict()
    top_destinations = ", ".join([f"{k} ({v})" for k, v in list(dest_counts.items())[:3]]) if dest_counts else "None"
    
    # Origins of relabeled IN samples
    origin_counts = relabeled_in_sub["Original_Category"].value_counts().to_dict()
    top_origins = ", ".join([f"{k} ({v})" for k, v in list(origin_counts.items())[:3]]) if origin_counts else "None"
    
    matrix_records.append({
        "Class": c,
        "Original_Total": orig_total,
        "Train_Orig": orig_tr,
        "Val_Orig": orig_va,
        "Test_Orig": orig_te,
        "Audited_Total_Known": aud_total_known,
        "Train_Audited": aud_tr,
        "Val_Audited": aud_va,
        "Genuine_Count": genuine_count,
        "Relabeled_Out": relabeled_out,
        "Relabeled_In": relabeled_in,
        "Ambiguous_Count": ambiguous_count,
        "Noisy_Count": noisy_count,
        "Purity_Score": round(audit_confidence, 4),
        "Top_Destinations": top_destinations,
        "Top_Origins": top_origins
    })

matrix_df = pd.DataFrame(matrix_records)
matrix_df = matrix_df.sort_values(by="Purity_Score", ascending=True)

# Save Matrix
matrix_df.to_csv(REPORT_DIR / "v20_taxonomy_audit_matrix.csv", index=False)

print("\n" + "=" * 85)
print("FULL 24-CLASS TAXONOMY PURITY & INTEGRITY MATRIX (SORTED BY PURITY):")
print("=" * 85)
cols_to_print = ["Class", "Original_Total", "Purity_Score", "Genuine_Count", "Relabeled_Out", "Relabeled_In", "Val_Orig", "Val_Audited"]
print(matrix_df[cols_to_print].to_string(index=False))

# 3. Deep Dive into the Fragile Classes
fragile_classes = ["AUTOMOBILE", "BPO", "AGRICULTURE", "APPAREL", "ARTS", "FITNESS", "BANKING"]

fragile_analysis = {}

for fc in fragile_classes:
    fc_sub = v19_audit[v19_audit["Original_Category"] == fc]
    fc_reassigned = fc_sub[fc_sub["Audit_Status"] == "LIKELY_MISLABELED"]
    
    fragile_analysis[fc] = {
        "original_total": int(sum(dedup_df["Category"] == fc)),
        "train_orig": int(sum(train_df["Category"] == fc)),
        "val_orig": int(sum(val_df["Category"] == fc)),
        "val_audited": int(sum((v19_audit["Split"] == "validation") & (v19_audit["Category"] == fc))),
        "purity_score": round(float(sum(fc_sub["Audit_Status"] == "CORRECT_LABEL") / len(fc_sub)), 4),
        "relabeled_out_count": len(fc_reassigned),
        "relabeled_out_breakdown": fc_reassigned["Category"].value_counts().to_dict(),
        "sample_reasons": fc_reassigned["Audit_Reason"].head(5).tolist()
    }

with open(REPORT_DIR / "v20_taxonomy_audit_report.json", "w") as f:
    json.dump({
        "audit_matrix": matrix_records,
        "fragile_classes_deep_dive": fragile_analysis
    }, f, indent=2)

print("\n" + "=" * 85)
print("DEEP DIVE: OCCUPATIONAL PURITY OF FRAGILE CLASSES")
print("=" * 85)
for fc in fragile_classes:
    fa = fragile_analysis[fc]
    print(f"\n--- {fc} ---")
    print(f"  Original Count: {fa['original_total']} (Train: {fa['train_orig']}, Val: {fa['val_orig']})")
    print(f"  Audited Val Support: {fa['val_audited']}")
    print(f"  Occupational Purity: {fa['purity_score']*100:.2f}% (Relabeled Out: {fa['relabeled_out_count']})")
    print(f"  Where did they go? {fa['relabeled_out_breakdown']}")

print("\nV20 Taxonomy Audit Complete. Artifacts saved in data/reports/.")
