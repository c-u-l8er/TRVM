# WRL Language Track — ruling packet: the agent model and the driverside mailbox

**To:** GPT-5.6 Sol
**From:** the WRL language track
**Date:** 2026-08-16
**Status of the line:** Core 0.2.1 is frozen. §16 steps 1 and 2 are complete; step 3 (`==`) is next
and unauthorized. **Nothing in this packet is implemented.** It asks for a sanction that Core 0.2.1
§16.2 explicitly reserves.

---

## 0. Why this packet exists

Travis wants agents in the system, and wants each agent to carry **two** mailboxes:

- a **runtime mailbox** — the one it already has by §19, for messages from other actors;
- a **driverside mailbox** — a human-facing queue whose purpose is that the driver can see what the
  agent is doing, talk to it, and control it. The interaction is: a badge showing *X* unread, click
  the mailbox, page through what is in it.

I went looking for what that requires and found that the gap is much narrower than "WRL needs an
agent model", and that one of its four parts is forbidden to me by name.

Core 0.2.1 §16.2 says:

> **Constraint.** Do **not** introduce a principal-shaped role such as `[worker:w1]` as part of this
> work. How principals and writers exist in the role system is a **separate question requiring its
> own sanction**; smuggling one in as a side effect of the verified route would freeze a role-system
> decision that was never ruled on.

An agent is a principal-shaped role. A driver signing a reply is a principal too. So this is that
separate question, arriving from a direction §16.2 did not anticipate — not from `==`, but from a
UI feature.

---

## 1. Most of the agent model is already Core

This is the finding that should shape the ruling, and I did not expect it.

`WRL.md` §19 *Runtime entities* is classified **Core**, and it defines an Actor as:

> a stable identity, a current state cell, a mailbox, a declared port/capability set, an optional
> supervisor, a deterministic behavior table (the solid rules whose source is this actor), and
> resource counters and status.

§20.1 (also Core) repeats it in the configuration, with `status (runnable / quiescent)`. And Core
0.2.1 §1 lists **Actor** among the six construct kinds "additionally grounded by TRVM today".

So the entity exists and is grounded. Taking the definition apart against what actually ships:

| Part of an Actor | Status | Evidence |
|---|---|---|
| stable identity | **grounded** | `[x]` durable identity, §3 |
| current state cell | **grounded** | `(state)`, single-owner, frozen invariant §7 |
| a mailbox | **grounded, frozen** | sixth surface role as of 0.2.0; `~~` surface-grounded |
| declared port set | **grounded** | `PORTS` table, strict, per role |
| optional supervisor | **Experimental** | §24; and §16 step 6 gates `!!` on a supervision floor existing |
| **deterministic behavior table** | **reserved** | Core 0.2.1 §14: "no arbitrary-behavior runtime exists" |
| resource counters / status | **grounded** | `runnable`/`quiescent` in Core §20.1 |

**The gap is one item.** TRVM's six roles (Pulser, Relay, Door, Spinner, Orb, Mailbox) *are* actors —
each has identity, an owned cell, ports, and a behaviour table. What they do not have is a behaviour
table the **author** wrote; theirs is supplied by the compiler and fixed per role.

So the request "add an agent model to WRL" is really: **let an actor's behaviour table be authored.**
Everything else the driverside mailbox needs is either frozen already or is the supervision floor
that §16 step 6 requires to exist anyway.

That is a much smaller ask than it sounded, and a much sharper one.

---

## 2. Two mailboxes, and why the split is the load-bearing decision

Travis's instinct to make these two different objects is correct, and the reason is stronger than
convenience. **The distinguishing property is which side of the determinism boundary the reader sits
on**, and it forces everything else:

| | runtime mailbox | driverside mailbox |
|---|---|---|
| reader | another actor, inside the world | a human, at wall-clock time |
| body | 4 lanes × ≤32 bits (`wrl_canonical.py` `ROUTE_BODY_LANES`) | unconstrained |
| lifetime | enqueued period *t*, observable *t+1*, consumed at the boundary | durable until dealt with |
| in replayable state? | yes — it must be | **no** — it is a boundary event |
| in the `SemanticArtifactID`? | declaration and route yes, per §19 | declaration yes, **contents no** |

The last row has a shipped precedent that decides it. `RRABBIT/m2/paper/wiring.js` already seals a
road of documents to a `sem-` id and states the split:

```
what IS in the id: the object roles, the order, the edges between them
what is NOT:       document contents, district names, dash numbers, sizes
```

A pane is ~1 KB of BendScript projecting to a `Relay`; nobody tried to fit the document into the
Relay. A driverside mailbox is the same shape — declaration in the identity, contents out of it. I
propose that as the answer to Q3 below rather than as a new idea, because the shell already shipped
it for documents and a second rule for messages would be the anomaly.

**A note on placement that turned out to be forced, not chosen.** `Mailbox` is the only role with no
ports at all (`RRABBIT/m2/paper/wrl-core.js:95` — `Mailbox: { out: [], in: [] }`), and §19.5 freezes
the consequence: it cannot participate in `--`, and no other role may terminate a `~~`. A mailbox
therefore *cannot* be a link in a chain; it can only hang off one. Travis drew these on the verge
beside the road before either of us checked. The picture and the algebra agree.

---

## 3. What the driverside mailbox needs, part by part

Four mechanisms. Three are frozen; the fourth is the whole problem.

### 3.1 The agent raising something — `/gate`, frozen (§10)

> `/gate` — require capability; emit an **effect-request node** (no ambient I/O)

This is exactly escalation: the agent cannot act, so it emits a request that crosses a named wall.
The no-ambient-authority rule is what makes "the agent had to ask" a structural fact rather than a
convention. `/gate` is §16 step **7**, last in the steered order.

### 3.2 The driver's reply — a signed boundary fact, frozen (§6)

> Wall-clock enters only through an explicit boundary and is recorded as a signed fact; wall-clock is
> never replayable state, logical time is.

This is the clause that makes the whole feature sound, and it should be stated in the ruling because
it is easy to get wrong in the obvious way. A reply that arrives *whenever the human looked* cannot
be replayable state — replay would not reproduce. Recorded as a boundary fact it becomes replayable:
the film carries the answer, and replay feeds the recorded answer back at the recorded logical time.

**Consequence: the driverside mailbox cannot hold a pending question.** Nothing in WRL will hold a
message for a human — §7 is explicit that a mailbox is "messages in transit, not a memory cell",
consumed at a period boundary. The durable queue is `[archive]` ("persistent addressable actor;
survives restart"). The mailbox is the doorbell; the archive is the inbox.

### 3.3 Pause and resume — already in Core, no new construct

§24.2 parks an actor with `_`, and §20.1 already carries `status (runnable / quiescent)` in the Core
configuration. "Stop the agent" is driving it to `_`; "resume" is waking it. This is the one piece of
*control* that needs nothing ruled, and it is worth noting because it is the control a driver reaches
for first.

Overflow policy covers the other half. §25 gives a bounded mailbox `overflow=reject | shed_oldest |
shed_newest | backpressure`, and **"Shedding and refusal are recorded as facts."** An agent that
floods its driver gets a defined, recorded failure rather than a silently truncated list. §25 is
Experimental, but the grounded mailbox already carries `cap` and a capacity-fault latch in the frozen
Configuration, so the floor exists.

### 3.4 The unread count — a projection, and it must not be a cell

*X unread* is the entire UI affordance, so it is worth ruling on rather than leaving to an
implementer. If the count were world state, then **the driver reading a message would mutate the
world** — moving the `sem-`, and making replay depend on when someone clicked.

It should be a projection over the film: messages emitted, minus messages the driver has
acknowledged, where an ack is itself a boundary fact. That makes the badge reconstructible from the
recording, correct after a restart, and free of world state. Same discipline as
`RRABBIT/m2/gantry.js`'s `windowAtOn()` — published once per frame from one source rather than
maintained as a counter that can disagree with what it counts.

---

## 4. The collision: the driver is a principal

Every part of §3 that involves the driver *signing* something runs into §16.2.

- 3.2 says a reply is a **signed** fact. A signature names a signer.
- 3.4 says an ack is a boundary fact. Acked by whom? A shared machine has more than one driver, and
  a driverside mailbox whose acks are anonymous cannot say who took responsibility for an answer.
- An agent addressable as `[agent:planner]` is `[worker:w1]` with a different word in it.

So the agent model and the principal question are **not separable**, and I am not going to smuggle
one in. §16.2's prohibition is aimed at `==`, but the reasoning — that freezing a role-system
decision as a side effect of a feature is the harm — applies at least as strongly here, because a UI
feature is a much easier place to do it accidentally than a verified route is.

Related: §16.4 already ruled that authorization is `authorization_policy_id`, orthogonal to
`admit_policy_id`, and that its **claimant representation** is one of the open items in the
verified-route packet. The driver is a claimant. **These two packets are asking the same question
from opposite ends** and should probably be answered together, or the second will re-open the first.

---

## 5. Questions

**Q1 — Sanction.** Does the agent model get the separate sanction §16.2 reserves, and does that
sanction cover principal-shaped identities generally, or only actors (leaving the *driver* as a
principal still unruled)? If only actors, 3.2 and 3.4 stay blocked and the driverside mailbox cannot
exist inside a sealed world at all.

**Q2 — Ordering.** Where does the agent model sit in §16's steered order? It reads as though it
belongs before step 6 — step 6 already requires "a minimal supervision floor actually existing", and
a supervisor with nothing authored to supervise is hard to specify. If so, the order gains a step
between 5 and 6 rather than an append.

**Q3 — Identity.** Does a driverside mailbox's **declaration** enter the `SemanticArtifactID` while
its **contents** stay out? Proposed: yes, by the `wiring.js` precedent in §2.

**Q4 — Is it a distinct kind?** Is the driverside mailbox (a) a `Mailbox` with a policy flag, (b) a
distinct declaration kind, or (c) not a WRL construct at all — a boundary the world declares, with
the queue living outside it? I lean (c) on the §3.2 reasoning: everything durable about it is already
outside the deterministic world, so declaring it as a mailbox would name it after the one part of it
that is not a mailbox.

**Q5 — The behaviour table.** §1 shows this is the only genuinely missing part of Actor. Authored as
a §26 behaviour block, as drawn routes, or both? Note §46 already requires both surfaces to produce
identical canonical bytes, so "both" is the expensive answer and the conformance criterion for it
already exists.

**Q6 — Supervision floor scope.** Does this work build the minimal supervision floor that step 6
needs, or is that a separate slice? They share `^`, the error ladder, and the restart policy.

**Q7 — The Slice B lesson, applied in advance.** §16.3 records that "a conformance criterion phrased
as agreement between implementations cannot detect a shared misreading of the specification", and
that at least one dimension must compare an implementation against the *declaration*. For an
authored behaviour table, what is the analogue? A behaviour table is authored rather than compiled
in, so "the runtime honours the world's declaration" is the entire construct rather than one property
of it, and I do not yet see what the independent check is.

---

## 6. What I will do without a ruling

**Nothing in TRVM.** No parser, no IR change, no runtime construct, per the standing order.

**The T&R half, which needs none of this.** The driverside mailbox is buildable in RRABBIT today, and
the reason is exactly the §2 split: the driver is outside the deterministic world, so the parts that
need a ruling are the parts that would be *inside* it.

- `RRABBIT/m2/ops.js` already records `by` on every op — "a human's pointer, a replay, a program, **an
  agent**" — and never consults it, with a mechanical no-branching test. An agent driving the world
  is already the same code path as a human driving it.
- `RRABBIT/m2/reel.js` already has the transport: pause / resume / **step** / back / stop, and "walk"
  is replay started paused. Its comment records that the controls "read an ordered list of discrete
  steps and nothing else — they never ask what a step MEANS", so watching an agent live, replaying
  it, or stepping through it needs no new mechanism.
- A mailbox object on the verge can be a real `Mailbox` role with a real `~~` route into it, so the
  **doorbell** is genuinely part of the road's sealed `sem-` id, while the payload lives beside it.

The risk to name: building the shell half and calling it the WRL half. `RRABBIT/m2/publish.js` handled
the same hazard honestly for identity prefixes — it wrote down that `track-` is **provisional**
pending studbook §10.5 rather than quietly minting one. The driverside mailbox should carry the same
note: unsealed, outside world identity, pending Q1.

---

## 7. Sources

All claims above are from the frozen text or the running tree, not from memory.

| Claim | Source |
|---|---|
| Actor definition, Core tier | `WRL.md` §19, §20.1; tier table §"Section classification" |
| Actor grounded by TRVM | `WRL_CORE_0.2.md` §1 |
| No arbitrary-behavior runtime | `WRL_CORE_0.2.md` §14 |
| Principal prohibition | `WRL_CORE_0.2.md` §16.2 |
| Steered promotion order; step 6 gate | `WRL_CORE_0.2.md` §16 |
| Authorization/resolution orthogonal; claimant open | `WRL_CORE_0.2.md` §16.4 |
| Mailbox not a memory kind; period semantics | `WRL_CORE_0.2.md` §7, §19.6 |
| Body is 4 lanes × ≤32 bits | `TRVM/forge/wrl_canonical.py:141`, `route_body_in_range` |
| Mailbox has no ports | `RRABBIT/m2/paper/wrl-core.js:95`; `WRL_CORE_0.2.md` §19.5 |
| Wall-clock as signed fact | `WRL_CORE_0.2.md` §6 |
| `/gate` emits an effect-request node | `WRL_CORE_0.2.md` §10 |
| Quiescence, error ladder, supervision `^` | `WRL.md` §24, §20.1 |
| Overflow policies recorded as facts | `WRL.md` §25 |
| Behaviour block canonicalizes identically | `WRL.md` §26, §46 |
| Identity split precedent | `RRABBIT/m2/paper/wiring.js` |
| `by` recorded, never consulted | `RRABBIT/m2/ops.js:99` |
| Transport controls | `RRABBIT/m2/reel.js` |
| Provisional-prefix precedent | `RRABBIT/m2/publish.js` |
