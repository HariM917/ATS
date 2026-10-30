# TalentFlow AI Dataset Card: Resume Classification & ATS Dataset

## 1. Dataset Summary
- **Source File**: `clean_resume_data.csv`
- **Source SHA-256**: `bb408fd0f5b5078361c2b086991b540161d4876e0832ea9c86e37b60de8dfb64`
- **Total Raw Records**: `2,484`
- **Clean Production Records**: `2,481`
- **Flagged for Manual Review**: `15`
- **Exact Duplicates Removed**: `2`
- **Near-Duplicate Clusters**: `9`
- **Train / Validation / Test Split**: `1,740` / `371` / `370` (70% / 15% / 15%)
- **Preprocessing Pipeline Version**: `1.0.0`
- **Split Random Seed**: `42`
- **Generated At**: `2026-09-10 04:36:42 UTC`

---

## 2. Provenance & Attribution
- **Dataset Title**: Cleaned Multi-Category Resume Corpus (`clean_resume_data.csv`)
- **Origin**: Curated English professional resume dataset spanning 24 primary career domains.
- **Data Anonymization**: The source dataset has pre-scrubbed identifiable entities with standardized placeholders (`company name`, `city state`). Zero direct email or phone numbers were detected in the raw input text.

---

## 3. Canonical Schema Specification
The raw dataset contains 3 primary columns: `ID`, `Category`, `Feature`.
The cleaning pipeline maps this into the canonical ATS dataset format:

| Field Name | Type | Source / Derivation | Description |
|---|---|---|---|
| `resume_id` | Integer / String | Source `ID` | Unique identifier for each candidate resume record |
| `resume_text` | String | Source `Feature` (Cleaned) | Unicode-normalized, artifact-cleaned resume text |
| `role` | String | Source `Category` (Canonical) | Standardized profession / category label (24 classes) |
| `skills` | String | ATS Parser (Runtime) | Explicitly unpopulated at preprocessing to prevent synthetic fabrication |
| `education` | String | ATS Parser (Runtime) | Derived at runtime by parser |
| `experience_years` | Float | ATS Parser (Runtime) | Derived at runtime |
| `projects` | String | ATS Parser (Runtime) | Derived at runtime |
| `certifications` | String | ATS Parser (Runtime) | Derived at runtime |
| `source` | String | Constant | Identifier of the data source (`clean_resume_data.csv`) |
| `quality_score` | Float | Computed (0.0 to 1.0) | Automated text length and format quality score |

---

## 4. Class Distribution (24 Categories)

| Category | Sample Count | % of Dataset |
|---|---|---|
| `INFORMATION-TECHNOLOGY` | `120` | `4.83%` |
| `BUSINESS-DEVELOPMENT` | `120` | `4.83%` |
| `ADVOCATE` | `118` | `4.75%` |
| `CHEF` | `118` | `4.75%` |
| `FINANCE` | `118` | `4.75%` |
| `ENGINEERING` | `118` | `4.75%` |
| `ACCOUNTANT` | `118` | `4.75%` |
| `FITNESS` | `117` | `4.71%` |
| `AVIATION` | `117` | `4.71%` |
| `SALES` | `116` | `4.67%` |
| `HEALTHCARE` | `115` | `4.63%` |
| `CONSULTANT` | `115` | `4.63%` |
| `BANKING` | `115` | `4.63%` |
| `CONSTRUCTION` | `112` | `4.51%` |
| `PUBLIC-RELATIONS` | `111` | `4.47%` |
| `HR` | `110` | `4.43%` |
| `DESIGNER` | `107` | `4.31%` |
| `ARTS` | `103` | `4.15%` |
| `TEACHER` | `102` | `4.11%` |
| `APPAREL` | `97` | `3.90%` |
| `DIGITAL-MEDIA` | `96` | `3.86%` |
| `AGRICULTURE` | `63` | `2.54%` |
| `AUTOMOBILE` | `36` | `1.45%` |
| `BPO` | `22` | `0.89%` |

---

## 5. Preprocessing & Quality Filtering
1. **Text Normalization**: Unicode NFC normalization, replacement of non-standard dashes/quotes/BOM, removal of OCR/PDF artifacts, whitespace collapsing while strictly preserving programming languages (`C++`, `C#`, `Node.js`, `scikit-learn`, `PyTorch`).
2. **Duplicate Detection**:
   - Exact duplicates detected via normalized MD5 text hashing.
   - Near-duplicates detected via TF-IDF cosine similarity (threshold >= 0.95).
   - Duplicate records logged to `data/reports/duplicates.csv`.
3. **Manual Review Queue**: Questionable records (empty, exact duplicate, near duplicate, short text) are directed to `data/reports/manual_review.csv` for human review (`KEEP`, `REMOVE`, `REVIEW`).
4. **Leakage Prevention**: Stratified splitting with duplicate group clustering to ensure no identical or near-duplicate resumes cross the Train/Validation/Test boundary.

---

## 6. Known Limitations & Potential Biases
- **Class Imbalance**: Categories range from INFORMATION-TECHNOLOGY (120 samples) to BPO (22 samples). Minor classes have fewer samples and should be monitored during classifier evaluation.
- **Structured Fields**: Structured skills and experience are not fabricated in the dataset and rely on the production ATS parser.
- **Language**: Dataset is entirely in English.
