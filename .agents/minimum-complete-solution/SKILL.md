---
name: minimum-complete-solution
description: Design the least complicated implementation that completely satisfies the task, and prevent architecture from growing beyond what was asked. Use before starting any new feature, tool, app, screen, integration, pipeline or greenfield build, and whenever a plan involves several components, services or dependencies. Use it when adding a new dependency, abstraction or build step mid-task, and whenever the implementation appears to be growing without the requirements having changed.
---

# Minimum complete solution

## The objective

**Minimum complexity consistent with complete, stable fulfilment of the requested
outcome.**

Not fewest lines. Not smallest package at any cost. Not the quickest hack. Each of
those optimises a proxy and pays for it somewhere the user actually feels.

**Completeness before cleverness. Simplicity after completeness.**

## Procedure

### 1. Extract only real requirements

List mandatory behaviours, mandatory artefacts, constraints and required evidence.
Keep optional ideas in a separate list. Do not design for hypothetical future work
unless extensibility was explicitly requested — speculative generality is the most
expensive habit in this list, because it is invisible until someone has to change it.

### 2. Propose the smallest viable architecture

For every component ask: **which explicit requirement requires this?**

If there is no clear answer, the component is a candidate for removal. Components
include services, APIs, dependencies, abstraction layers, queues, workers,
databases, caches, frameworks, helper modules, build steps, external processes and
configuration systems.

### 3. Apply the reduction tests

- **Dependency** — can this dependency disappear without losing a requirement?
- **Service** — can one upstream service replace two?
- **Abstraction** — is this needed now, or only for hypothetical future work?
- **File** — does splitting this out materially improve clarity, or only tidiness?
- **Process** — can an external process be replaced by a native capability?
- **Failure surface** — can the outcome be reached with fewer network calls, moving
  parts or state transitions?
- **State** — is persistent state actually required?
- **Stop** — once acceptance is demonstrated, is more architecture needed at all?
- **Diagnostic sweep** — before editing, have all observable defects in the current stable state been collected?
- **Verification** — can the next run validate several unresolved requirements or fixes at once?

## Guardrail

Do not optimise for smallness at the expense of clarity, stability, maintainability
appropriate to scope, execution friction, platform compatibility, user experience,
or the explicit acceptance criteria.

A larger self-contained executable can be a better minimum complete solution than a
tiny source package, if instant execution without an installed runtime is what was
asked for. The measure is the recipient's outcome, not the artefact's size.

## Visual and product work

For UI, web, mobile, game and visual tools:
- prefer direct component structures over a premature design system;
- use the smallest state model the interaction actually needs;
- avoid speculative screens and settings;
- avoid visual flourish that adds failure modes;
- preserve platform-native behaviour where it reduces complexity and friction.

For image and 3D pipelines:
- prefer the simplest path that produces the required visual result;
- do not build a procedural system where direct construction is adequate;
- do not add fine detail before silhouette and proportion are accepted — detail on
  an unaccepted base is work that will be thrown away.

## Decision record

Before implementing, write this. It is short by design; it exists to make later
scope creep visible, not to be ceremony.

```
REQUIREMENTS
- ...
MINIMUM COMPONENTS
- ...
REJECTED AS UNNECESSARY
- ...
PRIMARY RISKS
- ...
```


## Iteration economy

Minimum complexity includes the work loop, not just the architecture.

- Fix true blockers immediately because they prevent useful downstream evidence.
- Once the system reaches a stable inspectable state, finish the diagnostic sweep
  before editing.
- Batch compatible low-risk corrections that come from the same evidence state.
- Prefer one verification boundary that settles several fixes or criteria.
- Do not create temporary diagnostics, captures or instrumentation repeatedly when
  one bounded diagnostic pass can answer the outstanding questions.
- If two consecutive fix/recheck cycles occur on the same feature, stop local
  patching and perform a fresh whole-state sweep before another change.

Optimising verification cycles must never mean skipping evidence required for
acceptance; it means gathering more useful evidence per run.

## During implementation

When a new component appears, ask: **did the task change, or did the implementation
drift?** Both are legitimate answers, but they have different consequences — a
changed task needs the record updating; drift needs reverting. Prefer targeted fixes
over architectural expansion.

## Stop condition

Stop when all explicit criteria are met or ready for direct verification, no
requirement-level defect remains, and further architecture would serve only
hypothetical future work or optional polish.
