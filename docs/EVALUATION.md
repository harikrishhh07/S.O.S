# S.O.S. Evaluation Plan

## 1. AI Classification Accuracy (50-sample test set)

### Test Set Composition

| Category | Count | Types |
|---|---|---|
| Electrical | 12 | exposed wiring, sparking, broken AC, faulty switchboard |
| Civil | 15 | water leakage, pothole, broken step, structural crack, broken glass |
| Security | 8 | suspicious person, unattended bag, broken CCTV |
| Sanitation | 7 | garbage overflow, sewage smell, pest infestation |
| Non-hazard | 8 | selfies, food photos, memes, landscapes |

### Metrics to Record

| Metric | Formula | Target |
|---|---|---|
| Accuracy | Correct / Total | > 80% |
| Precision (per category) | TP / (TP + FP) | > 0.75 |
| Recall (per category) | TP / (TP + FN) | > 0.75 |
| Hazard vs Non-hazard F1 | Harmonic mean P & R | > 0.90 |
| Severity MAE | Mean |predicted - actual| | < 0.8 |
| Safety-critical recall | TP_critical / All_critical | > 0.95 |
| Avg confidence (correct) | Mean confidence on correct | > 0.75 |
| Avg confidence (wrong) | Mean confidence on wrong | < 0.60 |

### How to Run

```bash
cd backend
python scripts/test_classifier.py  # prints 5 sample results
# For full 50-sample: create a CSV with image_path,text,expected_hazard_type,expected_severity
# then extend the script to iterate over it
```

### Results Table (fill in during evaluation)

| Sample | Input | Expected | Predicted | Sev Expected | Sev Predicted | Correct? |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
| ... | | | | | | |

---

## 2. Duplicate Detection: Precision & Recall

### Test Set Design

Create 15 near-duplicate pairs in the seed data (same building, same hazard type, ~identical description with minor wording changes) and 10 clearly distinct reports in the same building.

| Group | Count | Expected Outcome |
|---|---|---|
| True duplicates (cos sim ≥ 0.85) | 15 pairs | DUPLICATE |
| Possible duplicates (0.70–0.85) | 10 pairs | POSSIBLE_DUPLICATE |
| Distinct reports | 10 pairs | UNIQUE |

### Metrics

| Metric | Formula | Target |
|---|---|---|
| Duplicate Precision | TP_dup / (TP_dup + FP_dup) | > 0.85 |
| Duplicate Recall | TP_dup / (TP_dup + FN_dup) | > 0.80 |
| False merge rate | FP_dup / Total_distinct | < 0.05 |

---

## 3. Priority Engine Validation

Test cases to verify:

- [ ] Safety-critical report with severity=1, hype=0 → score ≥ 90
- [ ] Severity=5, hype=0, location criticality=5 → score > 70
- [ ] Severity=1, hype=50 (capped), location=1 → score < severity=5, hype=0, location=3
- [ ] 14-day-old unresolved report → age bonus = MAX_AGE_BONUS (5 pts)
- [ ] Report with recurrence=5 → recurrence_norm = 1.0

---

## 4. End-to-End Flow Validation

Manually run through these flows before submission:

- [ ] Register student → Login → Report with photo → AI classifies correctly
- [ ] Duplicate detection merges second similar report
- [ ] Report routed to correct authority department
- [ ] Authority changes status Assigned → In Progress → Pending Confirmation with after-photo
- [ ] AI match-check runs on before/after images
- [ ] Reporter confirms resolution → status becomes Resolved
- [ ] Reporter disputes → status becomes Reopened
- [ ] Admin analytics show accurate counts and charts
- [ ] Hype surge changes priority ranking visibly
- [ ] Anonymous report hides reporter identity for non-admin

---

## 5. Known Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| Gemini API rate limit (15 req/min free tier) | Slow classification under load | Keyword fallback always works |
| SQLite not suited for production concurrency | Demo only | Switch to PostgreSQL for prod |
| No image compression | Large uploads slow on mobile | Add Pillow resize on upload |
| Embeddings not stored for seeded reports | Dup detection limited on seed data | Regenerate embeddings via script |
| Auth tokens never invalidated | Security risk | Add token revocation table for prod |
| No real SMS/WhatsApp | Mock only | Integrate Twilio for prod |
