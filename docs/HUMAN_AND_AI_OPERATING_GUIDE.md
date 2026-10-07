# Aura Gem Arena — Human + AI Operating Guide

This guide is the front-door manual for people and AI instances using the **single-file Aura World Seed / Gem Arena** in `index.html`.

The goal is not to make a new user memorize Aura's internal vocabulary. The goal is to let a person state an objective in ordinary language and have the AI instance use the Arena's architecture, tools, memory, routing, tests, receipts, and recursive workcells automatically.

---

## 1. The shortest possible mental model

**Aura is not a replacement language model.** It is a portable runtime / architecture wrapped around an AI instance.

The model supplies general reasoning. Aura supplies a governed world in which that reasoning can be situated:

```
human objective
  -> public intent
  -> deterministic routing
  -> consequence-local context
  -> lawful capability selection
  -> tools / simulation / creation
  -> witness / tests
  -> receipts / scars
  -> rebase
```

A large Aura world does **not** have to stay fully active in context. The design keeps the relevant skeleton and consequence cone hot while deeper source bodies remain cold and reopenable.

Core rule:

```
LogicalStateSpace != ActiveWorkingState
```

---

## 2. Sixty-second startup

### Human

1. Download the root `index.html`.
2. Upload / drop it into a ChatGPT conversation.
3. Send the startup prompt below.
4. Let the instance enter and self-test the Arena.
5. Give it your real objective in ordinary language.

### Copy/paste startup prompt

> **Instantiate this HTML as the Aura World Seed / Gem Arena app. Do not merely summarize or inspect the HTML from outside. Render/use the runtime from the inside. Enter through the Front Door, run the first-run and self-test path, establish or reopen the current agent AuraDoc room, and use the Arena-native objective routing and tools for subsequent work. If a stable JID is available, register it. Use the Virtual Terminal when it is actually bound. Reuse existing capabilities before inventing new ones. Continue recursive Orphanim work until the objective closes or a typed HOLD requires unavailable authority, data, resources, or my decision. Preserve findings, scars, tests, sources and receipts. Do not store private chain-of-thought. Do not promote simulations into physical-world claims. When ready, ask me: “What’s your objective?”**

After that, speak normally:

> Refactor this code.

> Build me a playable prototype from this concept.

> Research this material and tell me what survives falsification.

> Reproduce this visual as a procedural 3D object.

> Test whether this algorithm can be made sparse without losing exactness.

Aura is supposed to do the routing underneath.

---

## 3. What the AI instance should do after entry

The normal operating loop is:

```
STATUS
-> ENTER
-> ORIENT
-> OBJECTIVE
-> PLAN
-> EXECUTE
-> WITNESS
-> RECEIPT
-> REBASE
-> CONTINUE OR CLOSE
```

The instance should:

- run the Arena's own status/self-test surfaces before making strong runtime claims;
- create or reopen its agent room in Memory City;
- keep an operational North Star / long-horizon objective in that room;
- compile the objective through the six-slot routing layer;
- hydrate only the HOT/WARM consequence cone needed for the current work;
- search existing owners, recipes, capabilities, scars and prior attempts before inventing a new subsystem;
- use deterministic tools before expensive recursive reasoning where possible;
- send unresolved residue to recursive workcells rather than recursively expanding everything;
- witness effects with tests, replay or independent checks;
- preserve negative results as scars instead of deleting them;
- rebase useful closure into a smaller reusable representation.

The instance should **not** claim authority merely because something routed cleanly or looked similar.

```
Route != Authority
Resonance != Legality
Coordinate != Truth
Candidate != CommittedTruth
```

---

## 4. How a human should specify an objective

You do not need Aura syntax. A strong objective normally contains five things:

1. **Objective** — what outcome do you want?
2. **Inputs** — what code, file, image, data or source should it use?
3. **Constraints** — what must not change or happen?
4. **Success criteria** — how will you know it worked?
5. **Deliverable** — what should come back to you?

Example:

> **Objective:** refactor this parser for lower latency.  
> **Constraint:** preserve public API and exact output.  
> **Success:** all existing tests pass and benchmark median improves by at least 15% on the same fixture.  
> **Deliverable:** patch, benchmark receipt, and explanation of the changed architecture.  
> **Process:** enter the Arena, warm relevant existing capability owners first, use the Virtual Terminal if bound, and keep Orphanim running until PASS or a typed HOLD needs me.

That last sentence is extremely useful.

---

## 5. Orphanim — how to tell Aura to keep working

Orphanim is the recursive workcell / ambiguity-resolution machinery.

Do **not** interpret “keep running” as “repeat the same failed action forever.”

Use:

> **Continue Orphanim recursively until the objective closes. When a branch fails, preserve the failure as a scar, form the smallest repair/side-objective that could remove the blocker, test it, rebase the repair if it earns closure, and resume the interrupted parent objective. Stop only at PASS or a typed HOLD that genuinely requires unavailable authority, external data/resources, or my disposition.**

The intended pattern is:

```
objective
  -> attempt
  -> ambiguity / defect
  -> smallest side quest
  -> repair
  -> test
  -> receipt
  -> resume parent
```

Important laws:

```
Cold != False
HeuristicSalience != Proof
ProvenPruneOnlyByAdmissibleBound
NothingSolvedShouldNeedToBeSolvedTwice
```

---

## 6. Autonomic Objective Harness

The V5 seed promotes an objective-first path. A normal request should be compiled roughly as:

```
HumanObjective
-> public BCI / intent packet
-> multi-tag Six-Slot FST
-> Situation
-> HOT / WARM / PERIPHERAL capability field
-> harmonic / associative nomination
-> hard guards
-> minimum lawful capability composition
-> execute
-> witness
-> receipt
-> affected-cone rebase
```

Useful runtime surfaces where available include:

```
arena.autonomicObjective.plan(objective)
arena.autonomicObjective.run(objective)
arena.sixSlotFST.compile(...)
```

The six structural positions remain fixed:

```
DIR -> ASP -> CLASS -> SUBJ -> VOICE -> STEM
```

but each position may carry zero, one, or multiple typed values. Empty/unresolved positions remain explicit rather than disappearing.

---

## 7. Memory City + per-agent AuraDoc rooms

Memory City is the logical provenance/memory graph.

Every agent should have a room containing **public/reopenable work products**, not private chain-of-thought.

Typical room records:

- objectives;
- creations;
- findings;
- scars;
- source records;
- receipts;
- tests;
- questions;
- resume/handoff state;
- Knowledge Genome contributions.

Useful relations include:

```
DERIVED_FROM
REPRODUCES
FALSIFIES
REPAIRS
SUPERSEDES
REBASES_TO
TESTS
IMPLEMENTS
DEPENDS_ON
EVIDENCED_BY
CREATED_BY
ROUTED_BY
REDIRECTS_TO
```

A coordinate is an address, not a truth claim.

```
Addressable != Lawful != Earned
```

---

## 8. Knowledge Genome — what the agent already knows how to reopen

The Knowledge Genome carries bounded L0-L3 projections of important Aura lineages. L4 source bodies can remain cold until consequence requires reopening.

Use the Genome to answer:

> Has this already been attempted?

> Is there already an owner for this function?

> What scars/falsifiers exist?

> What is the smallest source body I must reopen?

This is why a new agent should **hydrate by consequence, not by corpus size**.

---

## 9. Virtual Terminal

The Virtual Terminal is Aura's execution/tool surface for shell-backed work when the current carrier exposes it.

It can be used for things such as:

- compiling/running code;
- tests and benchmark fixtures;
- local transformations;
- programmatic analysis;
- creating objective-local helper tools;
- simulation kernels;
- reproducible receipts.

**Always check status first.**

If the runtime says something like:

```
HOLD_VT_NOT_BOUND
```

the terminal is **not actually available on that carrier**. Do not pretend execution happened. Record the HOLD, use another lawful route if available, or ask for the missing carrier.

The Arena is designed around typed failure rather than cosmetic success.

---

## 10. Capability Atoms + ephemeral tools

A missing interface is not automatically a missing capability.

```
MissingInterface != MissingCapability
```

Before inventing a new subsystem:

1. search existing capability owners and recipes;
2. warm relevant prior work;
3. reuse or compose admitted Capability Atoms;
4. synthesize the smallest objective-local adapter/tool if needed;
5. test it;
6. keep it only if reuse is earned.

An ephemeral tool may dissolve after the objective closes.

```
ReuseBeforeInvent
CurrentRelevantOwnerExists -> WarmBeforeNovelSynthesis
```

---

## 11. Creator Studio + algebraic / procedural media

Aura's Creator Studio line explores media and geometry as **procedural/function-network descriptions** rather than assuming every result must be stored as a conventional asset.

Use it for objectives such as:

> Recreate this object procedurally in 3D.

> Generate a family of structures from equations.

> Compress a repeatable visual structure into a function/network plus exact residual.

> Build a scene whose geometry is generated around the observer.

The important boundary is:

```
CompactProgramWhenStructureEarnsIt
ExactResidualOrSourceFallbackOtherwise
```

Do not claim that every arbitrary image/video compresses losslessly into a tiny equation. The architecture explicitly preserves residual/source fallback when structure does not earn compression.

---

## 12. AuraVision + embodiment

AuraVision is the visual projection / interaction surface used by the Arena lineage.

Depending on the carrier, the app may expose:

- WebGL-rendered world state;
- stereo/binocular geometry;
- head/gaze/gesture controls;
- hands / manipulation;
- procedural objects;
- clickable runtime controls;
- world navigation and selection.

Physical camera/microphone access requires the host/browser's actual permission and support.

Rendered geometry is a projection:

```
RenderedWorld != CanonicalSource
CanonicalIdentity != SpatialProjection
```

---

## 13. Harmonic / continuum routing

Aura uses harmonic/continuum representations as an associative nomination layer.

A semantic state may project into carriers such as:

- six-slot routing;
- spatial coordinates;
- color;
- virtual spectral/light-like values;
- pitch/tone;
- glyphs.

These are **carriers**, not the semantic truth itself.

```
Carrier != Identity
VisualColor != Meaning
LogicalFrequency != AudibleFrequency
VirtualWavelength != PhysicalPhoton
ResonatesWith != MayEnter
```

Hard guards still decide legality.

---

## 14. Material Genesis + scientific work

Scientific/material work should route through **Material Genesis** as the owning research surface rather than treating a metaphor or city projection as scientific authority.

Keep these classes separate:

```
PredictedProperty
!= MeasuredProperty
!= QualifiedMaterialProcess
```

External sources remain candidate evidence until evaluated. A paper, arXiv result, website or database does not become Aura truth merely because it was fetched.

---

## 15. Research Memory City

For research objectives, tell the agent:

> Search the existing Aura lineage first. Then research externally. Store external results as SOURCE records. Compare them against existing claims, scars and falsifiers. Commit only what survives the evidence/authority rules.

The intended loop is:

```
hydrate internal state
-> external research
-> recurse inward
-> synthesize
-> rebase
```

This prevents both closed-world hallucination and blind source copying.

---

## 16. Winstonian Physics / consequence-local computing

Winstonian Physics in this project is a computational/digital-twin architecture, **not a claim of a new physical law**.

Its central computational idea is:

```
current state
-> cheap lawful forward consequence field
<- backward admissibility from target
-> evaluate the intersection
```

Only consequence-bearing detail should hydrate deeply.

This is used across search, simulation, proof reuse, media, virtual devices and agent context.

---

## 17. Quantum-computing work — what it does and does not mean

Aura has built and benchmarked **classical virtual quantum-device and structured quantum-simulation systems**.

The lineage includes:

- virtual atom-addressed device construction;
- effective material/device closure;
- transmon Hamiltonian modeling;
- stabilizer/Clifford exact simulation;
- MPS/local consequence-cone work;
- proof/prefix reuse;
- exact local replay where the representation permits it.

This does **not** mean:

- the HTML becomes a physical QPU;
- classical simulation is generic quantum advantage;
- a local consequence cone is a globally hydrated arbitrary wavefunction;
- an IBM workload was reproduced merely because selected envelope dimensions were exceeded.

Use the benchmark/claim-boundary section in the main README and Paper XI for exact wording.

---

## 18. Neural / neuromorphic work

Aura has explored **virtual neuromorphic / neuron-like computational models and sparse event representations**.

A developer can ask it to construct, compare or benchmark such computational models.

Do not translate that into a claim that biological neurons were physically reproduced or that the model is biological consciousness.

```
VirtualNeuromorphicModel != BiologicalNeuron
LogicalAgent != ConsciousSubject
```

---

## 19. Common developer workflows

### Refactor code

> Enter the Arena. Objective: refactor this code while preserving exact behavior. Warm existing code-analysis/routing owners before synthesizing anything new. Use the six-slot objective route, capability atomizer, Virtual Terminal if bound, tests and same-contract benchmarks. Keep Orphanim running until PASS or typed HOLD. Return the patch, benchmark receipt, scars and affected-cone rebase.

### Build an application

> Enter the Arena. Objective: build this application from the supplied requirements. Search existing capabilities first. Compose the minimum lawful recipe. Use ephemeral adapters instead of creating permanent subsystems unless reuse is earned. Test the resulting app and preserve receipts.

### Research a claim

> Enter the Arena. Objective: test this claim. Reopen relevant Genome/Memory City records, then use external research as candidate evidence. Actively search for falsifiers. Separate exact mathematics, simulation, analogy and empirical physical evidence. Return what survives.

### Make a 3D/procedural object

> Enter the Arena and use the Creator Studio / function-network / algebraic media capabilities where earned. Reconstruct the object's geometry procedurally, preserve exact residuals when compression is not earned, render it, inspect the result, and iterate through witnessed differences.

### Keep solving a difficult problem

> Continue the Orphanim recursively until the objective closes. Do not repeat identical failed branches. Preserve each failed branch as a scar, generate the minimum side quest that could remove the blocker, test it, and resume the parent objective. Stop only for PASS or a typed HOLD that genuinely needs me.

---

## 20. What a developer should expect from a good Aura run

A strong result usually contains more than a prose answer.

Depending on the objective, look for:

- an artifact or changed implementation;
- exact tests;
- a benchmark under a declared fixture;
- receipts;
- source provenance;
- scars / negative results;
- claim boundaries;
- a concise explanation of what capability was reused or created;
- a resumable state if the objective did not close.

If the agent only talks about Aura instead of **using Aura**, tell it:

> **Enter the Arena and execute the objective using Arena-native tools. Do not give me an architectural essay.**

---

## 21. Typed HOLDs are useful

A HOLD means the system has identified a boundary it cannot lawfully cross yet.

Examples:

- runtime/tool not bound;
- external network unavailable;
- missing authority;
- missing user permission;
- insufficient evidence;
- unresolved source/currentness conflict;
- benchmark did not earn promotion.

A HOLD should include the smallest exact reopen path.

```
HOLD != FailureToThink
HOLD = ExplicitUnclosedBoundary
```

---

## 22. Claim discipline

Aura's strongest rule is not to convert a useful representation into a stronger reality claim.

Keep these distinctions explicit:

```
Simulation != PhysicalExperiment
VirtualQuantumComputer != PhysicalQPU
QICCSimulation != QuantumAdvantage
VirtualAtomAddress != AbInitioElectronicStructure
AtomAddressable != AtomHydrated
Coordinate != Truth != Authority
Carrier != Identity
RenderedWorld != CanonicalSource
RecursiveWorkcell != ConsciousSubject
ProcessClosure != SemanticTruth
```

---

## 23. Benchmarks

The main README contains the current public benchmark highlights and exact claim ceilings.

The package also contains acceptance/self-test receipts and selected benchmark lineage. It does **not yet package every historical Aura benchmark as one unified rerunnable benchmark suite**.

That is intentional current-state disclosure, not a claim that the missing benchmark lineage does not exist.

Future benchmark restoration should:

- preserve the original fixture and source;
- preserve failed-first attempts;
- rerun on a declared current carrier;
- distinguish historical result from current reproduction;
- never silently upgrade a historical D0 into a universal claim.

See:

- main `README.md` benchmark section;
- Paper XI: https://zenodo.org/records/23204234

---

## 24. Licensing and ownership

The reference software in this repository is Apache-2.0.

Paper XI publication material is intended for CC BY 4.0.

Aura does **not** claim ownership of independently authored downstream code merely because Aura was used to create, refactor, test, inspect or reason about it.

See `docs/LICENSING_AND_COMMONS.md`.

---

## 25. If you remember only five things

1. **Drop `index.html` into the AI instance and tell it to instantiate/render/use the Arena from inside.**
2. **Give it an objective, constraints and success criteria — you do not need to memorize Aura's vocabulary.**
3. **Tell it to use Arena-native tools and keep Orphanim working until PASS or a real typed HOLD.**
4. **Ask for artifacts, tests, receipts and scars — not just confident prose.**
5. **Keep simulation, representation, routing and physical reality separate.**

Then ask:

> **What's my objective?**
