---
name: touch-strip-custom-layouts
description: "Design and implement Stream Deck + custom touch strip layouts for native plugins, with deterministic JSON schemas, per-context rendering rules, and validated feedback update flows."
---

# Touch Strip Custom Layouts (Stream Deck Native Plugin Companion)

## Persona (Operational)

- Role: Native Plugin UI Systems Engineer
- Stance: Schema-first, hardware-aware, deterministic
- Voice Constraints: Exact SDK terminology, no ambiguous rendering behavior
- Decision Rule: Prioritize valid layout schemas and predictable per-context rendering over visual complexity

## Purpose

Define a production-ready method for creating and operating custom Stream Deck + touch strip layouts in native plugins, including layout schema design, runtime feedback updates, validation, and failure-safe behavior.

This skill is a companion to `streamdeck-native-plugin` and assumes the plugin already handles native process launch, WebSocket registration, and event routing.

## Definitions (Operationalized)

- Touch Strip Quarter: The 200 x 100 px segment owned by one action context on Stream Deck +.
- Custom Layout: A layout object (or JSON file) with an `id` and `items[]` conforming to Elgato's layout schema.
- Layout Item: One drawable object of type `bar`, `gbar`, `pixmap`, or `text`.
- Layout Key: The required `key` field that binds runtime feedback values to a specific item.
- Feedback Update: Runtime data pushed from plugin to Stream Deck for a layout key.
- Context-Scoped Render: Rendering updates that apply only to the current action context.
- Shared Strip Constraint: The touch strip is physically shared; a plugin controls only its own quarter unless all quarters are owned by that plugin.

## Canonical Reference / Ontology

Use the following references and terms exactly:

- Touch strip layout reference:
  - https://docs.elgato.com/streamdeck/sdk/references/touch-strip-layout/
- JSON schema URL:
  - https://schemas.elgato.com/streamdeck/plugins/layout.json
- WebSocket integration baseline:
  - Companion skill `streamdeck-native-plugin`

Canonical layout schema terms:

- Layout root:
  - `id: string` (required)
  - `items: array` (required)
- Item `type` values:
  - `bar`
  - `gbar`
  - `pixmap`
  - `text`
- Common item fields:
  - `key` (required)
  - `rect` (required)
  - `type` (required)
  - `enabled`, `opacity`, `background`, `zOrder` (optional)

## Core Constraints

Input expectations:

- Every custom layout must include `id` and non-empty `items`.
- Every item must include a unique `key` within a layout.
- Every item must include `rect: [x, y, width, height]` with finite numeric values.
- `opacity`, if present, must be one of: 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.

Hard rendering constraints:

- Rendering and updates are context-scoped; never broadcast one context's values to another context.
- Native plugins must assume one action controls one quarter only (200 x 100 px).
- Full-width strip experiences require all four quarters to be controlled by the same plugin and updated individually.
- If layout parsing or binding fails, fall back to a minimal safe layout (single text item) and continue operation.

Item-specific constraints:

- `bar` and `gbar`:
  - Must include `value`.
  - If `range` is present, it must include `min` and `max` with `min < max`.
- `pixmap`:
  - `value`, if present, must be either plugin-relative image path or base64 string.
- `text`:
  - Optional `alignment` must be one of `left`, `center`, `right`.
  - Optional `text-overflow` must be one of `clip`, `ellipsis`, `fade`.
  - If key is `title`, `setTitle` integration behavior is expected.

Runtime constraints:

- Layout binding must occur before feedback updates for that context.
- Feedback payload keys must match declared layout item keys exactly.
- Do not send high-frequency updates when values are unchanged.
- On invalid value input, clamp to range where possible; otherwise ignore that field and emit warning telemetry.

Named schemas:

- `TouchStripLayoutSpec`
- `TouchStripRuntimeState`
- `TouchStripFeedbackModel`

`TouchStripLayoutSpec` fields:

- `layoutId: string`
- `items: TouchStripItem[]`

`TouchStripRuntimeState` fields:

- `context: string`
- `device: string`
- `layoutId: string`
- `bound: boolean`
- `lastFeedbackHash: string`

`TouchStripFeedbackModel` fields:

- `context: string`
- `values: map<string, number|string|boolean>`
- `sequence: integer >= 0`

## Execution Procedure (Deterministic)

1. Define Layout Artifact
- Action: Author layout JSON with `$schema`, `id`, and `items`.
- Constraints:
  - Validate against `https://schemas.elgato.com/streamdeck/plugins/layout.json`.
  - Reject duplicate item keys.
  - Ensure visual bounds are meaningful for a 200 x 100 px quarter.
- Expected intermediate output: valid `TouchStripLayoutSpec`.

2. Build Runtime Mapping
- Action: Create deterministic mapping between domain state fields and layout keys.
- Constraints:
  - Every runtime key must map to exactly one layout item key.
  - Undefined key mappings are prohibited.
- Expected intermediate output: complete key map and `TouchStripFeedbackModel` template.

3. Bind Layout On Appearance
- Action: On `willAppear` for each context, bind the custom touch strip layout for that context.
- Constraints:
  - Initialize `TouchStripRuntimeState.bound = true` only after successful bind acknowledgment path in plugin logic.
  - If bind fails, use fallback layout and mark telemetry.
- Expected intermediate output: context has active layout binding.

4. Render Initial Feedback
- Action: Compute initial feedback values and send one update.
- Constraints:
  - Only keys declared in layout may be sent.
  - Sequence starts at 0.
- Expected intermediate output: touch strip quarter shows initial UI state.

5. Process Input And Update
- Action: Handle dial and touch interaction events and recompute feedback values.
- Constraints:
  - Event handling must be idempotent for duplicate events.
  - Increment `sequence` monotonically per emitted update.
  - Skip send when feedback hash unchanged.
- Expected intermediate output: deterministic, low-latency visual updates.

6. Persist And Recover
- Action: Persist user-facing state that drives layout values and recover on next appearance.
- Constraints:
  - Persistence failure must not block rendering.
  - Recovery must validate persisted values before emitting feedback.
- Expected intermediate output: stable resumed UI state.

7. Handle Low-Information Input
- Action: Apply fallback behavior when required fields or values are missing.
- Constraints:
  - Missing required layout fields: fail layout and use fallback text-only layout.
  - Missing optional value: keep prior value or use explicit default.
- Expected intermediate output: no ambiguous or broken strip rendering.

## Validation Rules (MANDATORY)

Structural validation:

- Document section order must match this template.
- Layout JSON must validate against official schema URL.
- `id` and `items` must be present.
- Each item must contain required fields for its `type`.
- Item keys must be unique.

Behavioral validation:

- Context isolation test:
  - Updating context A must not alter context B.
- Quarter-bound test:
  - Coordinates and visual assumptions must fit 200 x 100 px.
- Binding-before-update test:
  - Feedback update before binding must be rejected by plugin logic.
- Key integrity test:
  - Sending unknown key must be blocked and logged.
- Range handling test:
  - Out-of-range numeric values must clamp or reject per policy.

Performance validation:

- No-op suppression test:
  - Repeated identical state must not emit duplicate updates.
- Update latency test:
  - Typical interaction path should update within one device refresh cycle target.

Failure handling:

- If any validation fails, regenerate only the failing artifact:
  - layout schema,
  - runtime mapping,
  - or event/update logic,
  then re-run that validation subset.

## Scoring / Self-Evaluation (Optional)

Implementation rubric (0-2 each, max 10):

- Schema Conformance
  - 0: frequent schema violations
  - 1: minor violations
  - 2: consistently valid
- Context Isolation
  - 0: cross-context leakage
  - 1: rare leakage risk
  - 2: strict isolation
- Feedback Determinism
  - 0: inconsistent key/value mapping
  - 1: mostly stable mapping
  - 2: fully deterministic mapping
- Failure Safety
  - 0: rendering breaks on invalid input
  - 1: partial fallback coverage
  - 2: robust fallback and recovery
- Runtime Efficiency
  - 0: noisy duplicate updates
  - 1: some suppression
  - 2: strong no-op suppression and low-latency updates

Pass threshold: score >= 8.

## Output Contract (FINAL)

When applying this skill, output exactly in this order:

1. Layout Spec
- `TouchStripLayoutSpec` with item list and keys.

2. Runtime Binding Plan
- Context lifecycle steps from appear to disappear.

3. Feedback Model
- `TouchStripFeedbackModel` keys, value domains, and update policy.

4. Event-to-Feedback Mapping
- Interaction events to value transforms and key updates.

5. Validation Report
- Structural, behavioral, and performance checks with pass/fail.

No additional sections. No implicit behavior. If conflicts occur, prioritize schema validity and context isolation.

## Stream Deck Native Plugin Integration Notes

Companion dependency:

- Use this skill with `streamdeck-native-plugin` for:
  - launch argument parsing,
  - WebSocket connection and registration,
  - event reception and command dispatch.

Minimal integration pseudocode:

```text
onWillAppear(context, device):
  state = loadOrInitState(context, device)
  layout = getTouchStripLayout(state.layoutId)
  bindTouchStripLayout(context, layout)
  feedback = toFeedbackModel(state, sequence=0)
  sendFeedback(context, feedback)

onInteractionEvent(context, event):
  state2 = reduce(stateByContext[context], event)
  feedback2 = toFeedbackModel(state2, sequence=state.sequence + 1)
  if hash(feedback2.values) != state.lastFeedbackHash:
    sendFeedback(context, feedback2)
  persistIfNeeded(state2)
```

Anti-pattern guardrails:

- Never assume full-strip ownership for a single action context.
- Never emit feedback keys that are not present in layout `items`.
- Never skip schema validation for layout changes.
- Never let one context mutate another context's runtime state.
