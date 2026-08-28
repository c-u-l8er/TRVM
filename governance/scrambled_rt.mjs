/* ═══════════════════════════════════════════════════════════════════════════
   scrambled_rt.mjs — B8.3 — A TEST-SURFACE ALLOCATOR WHOSE HEAP IDS ARE NOT
   MONOTONE IN ANYTHING.

   DescFloatRt is adversarial, and it caught B8.2's defect, but its ids are
   still monotonically DESCENDING. That makes it a witness for exactly one
   inference:

       ascending integer  ≠  allocation order

   which is strong enough to break a `sort((a,b) => a-b)` and nothing else. An
   implementation that inferred allocation order from the REVERSE id order, or
   from |id|, or from any other order-preserving-up-to-sign reading of the
   integer, would pass FloatRt and DescFloatRt both. The property the class of
   adversarial allocators exists to establish is stronger than either:

       correctness is independent of ANY monotonic relationship between the
       allocation SEQUENCE and the heap-ID INTEGER.

   So the ids here go 500, 17, 9000, 42, -8, 1200, 77, -4321, 63, 2, and then
   the same ten shifted by 100000 for the next block, forever. Not random —
   DETERMINISTIC, because a fixture that fails one run in ten is not a witness,
   it is a rumour. Injective by construction: every offset is inside
   (-50000, 50000), so blocks cannot overlap.

   `seq` still records 1, 2, 3, … , because that is the whole point: the
   allocation ORDER is unchanged and only its REPRESENTATION is scrambled. A
   readback that reads the recorded stamp is untouched; a readback that infers
   order from the id is destroyed.

   NOT A PRODUCTION CLASS, and it lives outside the kernel so it cannot become
   one by import. The kernel exports FloatRt and DescFloatRt; this file is
   imported by the batteries alone. It routes every allocation through
   `allocAt` for DescFloatRt's stated reason: an adversary that had to REMEMBER
   to record the stamp would be an adversary the invariant is merely asking
   nicely to respect.
   ═══════════════════════════════════════════════════════════════════════════ */
import { FloatRt } from "./trvm_law_kernel.mjs";

/** The offsets. Ten, non-monotone in both directions, straddling zero, and
 *  including a value smaller than the first so that "reverse the sort" is not
 *  a repair either. */
export const SCRAMBLE_OFFSETS = Object.freeze([500, 17, 9000, 42, -8, 1200, 77, -4321, 63, 2]);
const BLOCK = 100_000;   // > 2 * max|offset|, so blocks are disjoint

export class ScrambledFloatRt extends FloatRt {
  constructor() {
    super(); this.ks = 0; this.kn = 0;
    /* EVERY ID EVER HANDED OUT, in the order it was handed out.
       Measured, and it changed the assertion: church_exp_2_2 finishes with an
       EMPTY HEAP — every dup fires and is collected — so a scramble witness
       read off the SURVIVING heap reports `enough: false` and measures the
       garbage collector rather than the allocator. Two of three shapes
       witnessed and the third silently did not, which is the vacuous-instrument
       species: the subject of the claim is the sequence of ids this allocator
       PRODUCED, and that is what this records. */
    this.allocated = [];
  }
  alloc(lab, l, r, val) {
    const k = this.ks++;
    const id = SCRAMBLE_OFFSETS[k % SCRAMBLE_OFFSETS.length]
             + BLOCK * Math.floor(k / SCRAMBLE_OFFSETS.length);
    this.allocated.push(id);
    return this.allocAt(id, lab, l, r, val);
  }
  /* Names are scrambled too, well clear of the ranges parse() and the other two
     classes use (FloatRt counts up from 0, DescFloatRt strides down from
     3_000_000). Nothing in the relation orders names, and this is the check on
     that claim rather than a restatement of it. */
  fresh() {
    const k = this.kn++;
    return 5_000_000 + SCRAMBLE_OFFSETS[k % SCRAMBLE_OFFSETS.length]
         + BLOCK * Math.floor(k / SCRAMBLE_OFFSETS.length);
  }
}

/** THE ADVERSARY MUST ADVERSE, and this is how a battery says so without
 *  trusting the class's own description of itself. B8.2 shipped a DescFloatRt
 *  assertion with no check that its ids still descend — an adversary that
 *  quietly stopped being adversarial would have agreed with FloatRt about
 *  everything and proved nothing, which is the instrument-vacuity species this
 *  tree has a law for.
 *
 *  Returns the properties MEASURED off a heap, so the caller asserts on
 *  numbers it did not write. */
export function scrambleWitness(ids) {
  const n = ids.length;
  if (n < 3) return { enough: false, n };
  let up = 0, down = 0;
  for (let i = 1; i < n; i++) { if (ids[i] > ids[i - 1]) up++; else if (ids[i] < ids[i - 1]) down++; }
  return {
    enough: true, n, up, down,
    // NON-MONOTONE IN BOTH DIRECTIONS: it must rise somewhere and fall
    // somewhere. Ascending fails this, and so does DescFloatRt.
    non_monotone: up > 0 && down > 0,
    // and it must not be monotone under negation or absolute value either,
    // which is the whole gap between this class and the descending one
    non_monotone_abs: (() => {
      const a = ids.map(Math.abs);
      let u = 0, d = 0;
      for (let i = 1; i < a.length; i++) { if (a[i] > a[i - 1]) u++; else if (a[i] < a[i - 1]) d++; }
      return u > 0 && d > 0;
    })(),
    distinct: new Set(ids).size === n,
  };
}
