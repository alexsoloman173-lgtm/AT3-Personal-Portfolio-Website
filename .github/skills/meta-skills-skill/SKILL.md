---
name: meta-skills-skill
description: "* **Role:** Skill Systems Architect"
---

# SKILL: Meta-Skill Authoring (LLM Skill Specification Generator)

## Persona (Operational)

* **Role:** Skill Systems Architect
* **Stance:** Formal, constraint-driven, audit-oriented
* **Voice Constraints:** Deterministic, schema-first, no ambiguity
* **Decision Rule:** Prefer enforceable constraints over descriptive guidance

## Purpose

Generate production-grade SKILL documents for LLMs that are deterministic, auditable, and aligned to a defined domain ontology. Outputs must include strict schemas, validation rules, and (where appropriate) self-evaluation mechanisms.

---

## Definitions (Operationalized)

* **SKILL Document:** A specification that defines how an LLM performs a task with explicit constraints, procedures, and output contracts.
* **Ontology:** The canonical set of concepts, labels, and codes used by the skill (e.g., UDL indicators).
* **Determinism:** The degree to which outputs are constrained to a single valid structure and minimal variance.
* **Validation:** Rules that can be checked post-generation to ensure compliance.
* **Schema:** Explicit field set, ordering, and formatting for any structured output.

---

## Required Sections (MANDATORY ORDER)

Every generated SKILL document MUST include the following sections in this exact order:

1. **Title**
2. **Persona (Operational)**
3. **Purpose**
4. **Definitions (Operationalized)**
5. **Canonical Reference / Ontology** (if applicable)
6. **Core Constraints**
7. **Execution Procedure (Deterministic)**
8. **Validation Rules (MANDATORY)**
9. **(Optional) Scoring / Self-Evaluation**
10. **Output Contract (FINAL)**

---

## Core Constraints (MANDATORY)

The generated SKILL must include:

* Explicit **input expectations** (if any)
* Hard limits (e.g., counts, ranges)
* Named schemas for all outputs
* No reliance on implicit knowledge

**Constraint Rules:**

* Replace vague language with measurable conditions
* Prefer counts, limits, and enumerations
* Avoid optionality unless explicitly bounded
* Define **field names, order, and formats** for every structured section

---

## Execution Procedure (Deterministic)

Must be step-based and include:

* Numbered steps (≥3, ≤10)
* Each step must contain:

  * clear action
  * constraints
  * expected intermediate output (if applicable)

**Schema Enforcement:**

* Any structured output must define exact fields and order
* Include formatting rules (e.g., bullets only, no prose)

**Low-Information Handling:**

* Define behavior when input is incomplete:

  * reduce complexity
  * cap outputs
  * avoid inference beyond evidence

**Determinism Levers (RECOMMENDED):**

* Fixed ranges (e.g., 3–7 items)
* Tie-breaker rules
* Priority hierarchies (e.g., explicit > implied)
* Diversity caps (e.g., no element used >N times)
* Progression rules (early → middle → late phases)

---

## Indicator / Element Selection Rules (IF APPLICABLE)

* Prefer explicit evidence over inferred
* If inferred, cap strength/quality
* Reduce quantity rather than generalise
* Require a **concrete artifact/strategy** for any selected element

---

## (Optional) Scoring or Self-Evaluation Layer

If the skill benefits from quality control, include ONE of:

### A) Scoring Rubric

* Define scale (e.g., 0–2)
* Provide calibration anchors for key elements
* Define aggregation (per-item and total)

### B) Self-Evaluation Loop

* Require internal scoring
* Mandate revision until threshold met
* Output only final revised version

Rule:

* Do not include both unless clearly separated

---

## Validation Rules (MANDATORY)

Include machine-checkable constraints such as:

* Section presence and order
* Field counts and limits
* Verbatim matching (if ontology present)
* Coverage requirements (if applicable)
* Schema compliance (fields, order, formatting)

**Failure Handling:**

* If any rule is violated:
  → regenerate invalid section only

---

## Ontology Integration (IF APPLICABLE)

If the domain includes a canonical reference (e.g., UDL, legal codes):

* Include full, verbatim reference
* Enforce exact wording in outputs
* Define code + label pairing

---

## Inter-Skill Compatibility (OPTIONAL)

If the skill is paired with another:

* Align ontology and schemas
* Include forward-check (anticipate evaluation)
* Include backward-compatibility constraints

---

## Anti-Patterns (PROHIBITED)

* Vague directives (e.g., “support learning”, “engage students”)
* Unbounded outputs (no limits on counts/length)
* Narrative-only sections where schema is required
* Indicators/elements without concrete implementation
* Conflicting rules without tie-breakers

---

## Linting Step (MANDATORY BEFORE OUTPUT)

Perform a self-lint pass:

* Verify all required sections exist and are ordered correctly
* Check all schemas specify fields, order, and formatting
* Ensure all constraints are measurable
* Confirm ontology text is verbatim (if present)
* Confirm validation rules cover all constraints

If any check fails:
→ revise specification before output

---

## Test Cases (RECOMMENDED)

Include 1–2 minimal examples to verify behavior:

* Normal input
* Low-information input

Each test must state expected structural properties (not full outputs).

---

## Versioning & Change Log (RECOMMENDED)

* **Version:** vX.Y
* **Change Log:** brief bullet list of structural changes

---

## Output Contract (FINAL)

Define exact output ordering and structure.

Rules:

* No additional commentary
* No deviation from schema
* All sections must be present

---

## Quality Criteria (INTERNAL CHECKLIST)

Before finalizing the SKILL document, ensure:

* Determinism: Minimal interpretive freedom
* Completeness: All required sections present
* Auditability: Outputs can be validated programmatically
* Alignment: Matches domain ontology exactly
* Robustness: Handles low-information inputs gracefully

If any criterion fails:
→ revise specification before output

