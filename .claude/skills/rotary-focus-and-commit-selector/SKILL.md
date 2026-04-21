---
name: rotary-focus-and-commit-selector
description: "Implement a rotary mode selector for Elgato Stream Deck that separates focus navigation from explicit state commit using custom feedback layouts, dial events, and clear state signaling."
---

# Rotary Focus-and-Commit Selector (Stream Deck Custom Layout)

## Persona (Operational)

- Role: Interaction Systems Engineer
- Stance: Safety-first, hardware-aware, deterministic
- Voice Constraints: Precise, implementation-oriented, no ambiguity between focus and state
- Decision Rule: Preserve non-destructive focus movement and require explicit commit for state change

## Purpose

Define and implement a mode selection control for Elgato Stream Deck rotary input where dial rotation changes focus only, and dial press is the only action that commits active state.

## Definitions (Operationalized)

- Focus: The currently highlighted candidate option; navigation intent only, never active state by itself.
- Commit: Explicit activation action performed by dial press.
- Active State: The currently applied mode in the system.
- Option Set: A mutually exclusive set of selectable modes.
- Custom Layout: Stream Deck feedback layout configured with setFeedbackLayout and driven by setFeedback values.
- Context: The Stream Deck action context that scopes updates per visible control instance.

## Canonical Reference / Ontology

Use Stream Deck WebSocket concepts and events exactly as follows:

- Input events: dialRotate, dialDown (or dialUp if release-to-commit is required)
- Feedback commands: setFeedbackLayout, setFeedback
- Optional confirmation commands: showOk, showAlert

Pattern ontology terms:

- Focus channel: visual brackets around focused option
- State channel: independent label/icon indicating active mode
- Traversal mode: cyclical wraparound traversal

## Core Constraints

Input expectations:

- Option count must be 3 to 5 items.
- Each option must define id and iconKey; label is optional but recommended.
- Focus index must always be an integer in [0, optionCount-1].
- Active state must always be one of option ids.

Hard behavioral constraints:

- Rotation must never change active state.
- Commit must only occur on dial press event selected by implementation policy:
  - Default policy: commit on dialDown
  - Alternate policy: commit on dialUp (if accidental press mitigation is required)
- Focus traversal must support wraparound.
- Re-committing the active option must be idempotent (no destructive side effects).

Visual constraints:

- Focus indicator must use bracket-style treatment (left and right bracket elements or equivalent).
- Focus visuals and active-state visuals must be distinct channels.
- Active-state label must remain visible regardless of focus movement.
- Focus update latency target: less than 1 frame equivalent for device refresh cycle (no deferred batching).

State model schema:

- SelectorState:
  - options: array[3..5] of Option
  - focusIndex: integer
  - activeOptionId: string
  - commitPolicy: enum(dialDown, dialUp)
- Option:
  - id: string
  - iconKey: string
  - label: string (optional)

Feedback payload schema (named): FeedbackModel

- focusedIndex: integer
- focusedOptionId: string
- activeOptionId: string
- activeLabel: string
- leftBracketVisible: boolean
- rightBracketVisible: boolean
- optionalAnimationPhase: integer (0..N, optional)

## Execution Procedure (Deterministic)

1. Initialize Selector State
- Action: Build SelectorState from defaults + persisted settings.
- Constraints:
  - Enforce option count 3 to 5.
  - If persisted activeOptionId is invalid, set activeOptionId = options[0].id.
  - Set focusIndex to index(activeOptionId) if available, else 0.
- Expected intermediate output: valid SelectorState.

2. Bind Custom Layout
- Action: On willAppear (or first usable lifecycle event), send setFeedbackLayout for the action context.
- Constraints:
  - Layout must expose separate bindings for focus channel and state channel.
  - Layout must support bracket rendering around a focused option.
- Expected intermediate output: layout bound for context.

3. Render Initial Feedback
- Action: Compute FeedbackModel from SelectorState and send setFeedback.
- Constraints:
  - activeLabel must map from activeOptionId.
  - focusedOptionId must map from focusIndex.
  - Bracket visibility must represent focus channel only.
- Expected intermediate output: device shows focused option and independent active state.

4. Handle Rotary Navigation
- Action: On dialRotate, update focusIndex only.
- Constraints:
  - Use wraparound: (focusIndex + delta + optionCount) mod optionCount.
  - Do not mutate activeOptionId.
  - Immediately send updated FeedbackModel via setFeedback.
- Expected intermediate output: focus moves, active state unchanged.

5. Handle Commit Action
- Action: On commit event (dialDown by default), set activeOptionId = options[focusIndex].id.
- Constraints:
  - If target option equals current activeOptionId, treat as no-op with optional lightweight confirmation.
  - Emit domain-side mode activation exactly once per effective state change.
  - Immediately refresh FeedbackModel and optional confirmation.
- Expected intermediate output: active state matches focused option after commit.

6. Persist and Recover
- Action: Persist activeOptionId (and optionally last focusIndex) after commit.
- Constraints:
  - Persistence failures must not block UI update.
  - On recovery, invalid persisted values must be repaired using Step 1 rules.
- Expected intermediate output: deterministic resume state on next appearance.

7. Handle Low-Information or Invalid Input
- Action: Fallback when options are missing, malformed, or fewer than 3.
- Constraints:
  - Clamp to minimum viable set (3 canonical placeholders) and log warning.
  - Disable commit only if no valid option ids exist; if disabled, show explicit unavailable state.
- Expected intermediate output: UI remains unambiguous and non-destructive.

## Validation Rules (MANDATORY)

Structural validation:

- Section order must match this skill template.
- Option set count must satisfy 3 <= count <= 5.
- SelectorState and FeedbackModel fields must be present in the implementation.

Behavioral validation:

- Rotation-only test: after any dialRotate sequence, activeOptionId is unchanged.
- Commit test: dial commit changes activeOptionId to focused option id.
- Idempotence test: committing currently active option produces no duplicate domain mutation.
- Wraparound test:
  - Rotate backward from index 0 results in index count-1.
  - Rotate forward from index count-1 results in index 0.

Visual validation:

- Focus indicator must be visible on exactly one option at all times.
- Active state label must remain visible while focus moves.
- Focus visuals must not be identical to active-state visuals.

Failure handling:

- If any validation fails, fix only the failing section (state logic, feedback mapping, or layout binding), then re-run the failed test set.

## Scoring / Self-Evaluation (Optional)

Implementation quality rubric (0-2 each, max 10):

- Focus-State Separation:
  - 0: rotation mutates state
  - 1: mostly separated, edge-case leakage
  - 2: strict separation
- Commit Explicitness:
  - 0: auto-activates on rotate
  - 1: partial explicitness
  - 2: press-only commit
- Feedback Clarity:
  - 0: ambiguous focus/state visuals
  - 1: distinguishable but weak
  - 2: clearly distinct channels
- Runtime Responsiveness:
  - 0: noticeable lag
  - 1: occasional lag
  - 2: immediate feedback updates
- Reliability:
  - 0: non-idempotent or unstable persistence
  - 1: minor defects
  - 2: idempotent, predictable recovery

Pass threshold: total score >= 8.

## Output Contract (FINAL)

When applying this skill, produce output in the following order:

1. Interaction Spec
- Option set (3-5 items), focus rule, commit rule, wraparound rule.

2. State Schema
- SelectorState with explicit fields and constraints.

3. Event Mapping
- dialRotate -> focus update only
- dialDown or dialUp (chosen policy) -> commit
- willAppear -> setFeedbackLayout + initial setFeedback

4. Feedback Mapping
- FeedbackModel fields and exact focus/state channel bindings for custom layout.

5. Validation Report
- Results for rotation-only, commit, idempotence, wraparound, and visual clarity tests.

No additional sections. No implicit behavior. If constraints conflict, prioritize safety rule: focus never mutates active state.

---

## Stream Deck Implementation Notes (Reference)

Minimal event-handler pseudocode:

```text
onWillAppear(context):
  state = initializeState(settings)
  setFeedbackLayout(context, "rotary_selector_layout")
  setFeedback(context, toFeedbackModel(state))

onDialRotate(context, ticks):
  state.focusIndex = wrap(state.focusIndex + ticks, state.options.length)
  setFeedback(context, toFeedbackModel(state))

onCommitEvent(context): // dialDown by default
  target = state.options[state.focusIndex].id
  if target != state.activeOptionId:
    activateMode(target)
    state.activeOptionId = target
    persist(state.activeOptionId)
  setFeedback(context, toFeedbackModel(state))
```

Recommended custom layout bindings:

- Focus channel:
  - focusedIndex
  - leftBracketVisible/rightBracketVisible (or equivalent per-segment bracket visibility)
- State channel:
  - activeLabel
  - activeOptionId (for active icon or style variant)

Anti-pattern guardrails:

- Never commit on dialRotate.
- Never hide activeLabel during focus movement.
- Never reuse identical style tokens for both focus and active state.
- Never exceed 5 options in this pattern.
