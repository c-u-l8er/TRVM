# Round 27 B1.2 — the layer B1 presumed and did not have

**Pack:** `TRVM_B12_REVIEW_PACK.tar.gz`. Extract anywhere, run `./verify.sh`.
This run: **24 attempted / 24 passed / 0 failed / 0 skipped.**

You took interpretation B and you were right. B1 froze an architecture the compiler could not
express, and you saw it before a line of B2 was written.

---

## 1. There was no target-AST layer, so a port had nowhere to live

Confirmed: `lower()` built an ic32 **string**. A port could only have become `$input_x` — spelling as
semantics, the defect the ruling forbids, reintroduced by the absence of the representation it
presumes.

`TRVM-TARGET-TEMPLATE-v1`, minimal, exactly today's fragment, with its own content-bound encoding id:

```
Template := church(n) | add(Template, Template) | port(source_name)
```

**And I-4a is now structural rather than promised.** A template contains **no binder names and no dup
labels** — `emit()` invents both from its shape by the declared depth-first policy. Two emitters
allocating `_impl17` and `q93` cannot differ in the template because *there is no field an allocation
could occupy*. That is a better answer than asking the emitter to behave. `emit()` refuses a template
still holding a port.

I took one liberty worth flagging: your sketch listed `lam`/`app`/`dup`/binders as template nodes. I
kept `church(n)` and `add(a,b)` opaque and pushed **all** allocation into `emit()`, which is what makes
"no field an allocation could occupy" literally true. The cost is that the template does not yet model
target binders structurally, so a future fragment with real lambdas will need to extend the grammar
rather than inherit it. Say if you would rather have the fuller AST now.

## 2. The regression, which is why doing this before B2 was safe

```
pre-B1.2   lower(add(2,3)).target_term    129 chars
post-B1.2  emit(template)                 129 chars     BYTE-IDENTICAL
```

Verified against the previous commit's `lower()`, and on a nested fixture. Same six-frame film, same
normal form, same value 5, refinement still FILM-EVIDENCED. Introducing the phase changed neither the
executable term nor its outcome.

## 3. `LoweringReceipt` was still the pre-B1 relation

You were right that it is load-bearing. It ends at `target_template_sem_id` now (receipt domain v2); a
receipt ending at the term keeps asserting lowering produced the executable term, which the two-level
ruling denies.

## 4. The hashed semantics were still incomplete — B1.1's own defect, one round later

`lowered_ops` was `["const","add"]`, so **B2 adding `input` would have moved `LOWERING_SEM_ID`**.
Exactly your interpretation-B point. The whole fragment including `input` is in the semantics now with
its rule frozen:

```
{op:"input", name:N}  →  {t:"port", source_name:N}      N carried through UNCHANGED
```

and `lower-input-not-implemented` is an **operational** refusal in `LOWERING_STATUS`, not a semantic
one. **Measured by simulating B2** — deleting the refusal line so `input` lowers, *and* flipping both
lifecycle flags:

```
baseline                     lsem-d95ee1cbc0e8f37   isem-bf9434fc751a2fb
input lowering IMPLEMENTED   lsem-d95ee1cbc0e8f37   isem-bf9434fc751a2fb
+ implemented: true          lsem-d95ee1cbc0e8f37   isem-bf9434fc751a2fb
```

Neither moves. The B1.1 promise is now true rather than nearly true. And the simulated B2 produces the
right template for your I-4c fixture:

```
x + (x + y)  →  {t:add, a:{t:port,x}, b:{t:add, a:{t:port,x}, b:{t:port,y}}}
ports ["x","y"] · emit → emit-unbound-port: x
```

## 5. `consumed_inputs`, named so it cannot be erased

Your grant-versus-footprint framing is in `INSTANTIATION_SEMANTICS`. Supplied and consumed inputs are
different sets, `inputs_sem_id` commits to the whole supplied record, and no `input_footprint` is
emitted yet — named rather than implied, so B2 cannot collapse it by accident.

## 6. The stale header

Fixed. It drew `program_sem_id → target_term_sem_id` and said the inputs model was undecided while the
sections below said the opposite — a file contradicting itself, which is the class this tree does not
tolerate anywhere else.

---

## Gate

grid **v1.36.0** — 77 entries / 372 citations · `lowering.mjs` **0.4.0** · negative battery
**221/221** (six new B1.2 forgeries) · lowering **12/12**, refinement unchanged and still
FILM-EVIDENCED · derive 45/45 · realm 24/24 · bridge 48/48 · film 16/16 · twelve paired probes ·
harness 9/9 · runner 3/3 · pack **24/24, 0 skipped**. `cert_id a08ee15d…` — **thirtieth** consecutive
round.

---

## B2 is now small

1. Delete one refusal line: `input` → `T.port(name)`.
2. `instantiate(template, inputs)` → closed term + `InstantiationReceipt`, verified by independent
   re-instantiation. No film. Extras ignored, missing refused, scope stated in the witness.
3. **I-4a** — same source name, different allocation → same `target_template_sem_id`. Structural now.
4. **I-4b** — different source name, same allocation → different id.
5. **I-4c** on the mandated `x + (x + y)`, all the way through: correct binding → target term → native
   execution → **7**; swapped → **8**; and the correct `InstantiationReceipt` accepts only the
   7-producing term. Your "causally meaningful all the way to the outcome" version.
6. Then the `add(2,3)` regression restated through `instantiate({})` — same ic32 bytes, same film,
   same outcome — so the layer's arrival is provable rather than assumed.

Then `church_exp_2_2` and the dedicated DUP-ERA fixture.
