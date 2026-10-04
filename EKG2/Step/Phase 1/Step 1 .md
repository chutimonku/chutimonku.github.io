# Step 1.2 — Define the Unit of Analysis (Data Grain)

> **Parent Phase:** Phase 1 — Problem Governance and Data Foundation  
> **Target Execution:** Data Architecture, Schema Setup & Data Splitting Guardrails

---

## 1. Grain Definition
State clearly what one record represents in the analytical dataset across modalities:
- **Entity Level:** 1 record = 1 individual/patient/customer.
- **Encounter / Event Level:** 1 record = 1 test visit, transaction, or study episode.
- **Windowed Signal Level:** 1 record = 10-second ECG snippet or video segment.

---

## 2. Repeated Observations and Longitudinal Entities Guardrail
Do not assume one entity has only one record. An entity may legitimately have many observations, visits, studies, transactions, images, signal segments, or measurements.

### Key Operational Rules:
1. **Preserve Repeated Records:** Do not drop valid repeated observations merely to force one row per entity.
2. **Primary Key Construction:** Define composite keys combining `Entity_ID` + `Event_ID` / `Timestamp` to avoid grain mismatch and duplicate counting.
3. **Target Scope:** Explicitly state whether the target applies to an observation, episode, encounter, entity, or future time window.
4. **Group Splitting Guardrail:** Observations from the same entity must not appear across independent train, validation, and test partitions (must use `GroupKFold` anchored on `Entity_ID`).
5. **Dashboard Timeline View:** Display repeated predictions for the same entity as a longitudinal timeline rather than averaging values across visits.

---

## 3. Checkpoint Verification
- [ ] Primary composite key defined (`Entity_ID` + `Event_ID`).
- [ ] Longitudinal relationship mapped.
- [ ] Splitting rule assigned to `GroupKFold`.