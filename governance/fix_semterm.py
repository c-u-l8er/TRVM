# fix_semterm.py — sharpen cases 1-2: assert id-divergence + refusal.
src = open('build_v1.py', encoding='utf-8').read()
a = '''  // 1-2. mutation WITHOUT resealing — dies at the commitment
  { const m = clone(honest.film); m.terminal.budget = 1;
    cases.push(["budget-mutation-unsealed", expect(m, "sem-film-id-mismatch")]); }
  { const m = clone(honest.film); m.terminal.remaining_work = -7;
    cases.push(["work-mutation-unsealed", expect(m, "sem-film-id-mismatch")]); }'''
b = '''  // 1-2. mutation WITHOUT resealing. TWO independent teeth, both asserted:
  // the commitment now COVERS the field (id diverges — the audit found
  // budget_mutation_preserves_id:true, exactly this property missing),
  // and replay refuses regardless (semantic re-derivation fires first in
  // replay order, same as replayFloat: world, then commitment).
  { const m = clone(honest.film); m.terminal.budget = 1;
    const idDiverges = semFilmIdOf(m.terminal) !== m.film_id;
    const r = replaySemFilm(V.term, m, FloatRt);
    cases.push(["budget-mutation-unsealed", idDiverges && !r.ok]); }
  { const m = clone(honest.film); m.terminal.remaining_work = -7;
    const idDiverges = semFilmIdOf(m.terminal) !== m.film_id;
    const r = replaySemFilm(V.term, m, FloatRt);
    cases.push(["work-mutation-unsealed", idDiverges && !r.ok]); }'''
assert src.count(a) == 1, "anchor A"
src = src.replace(a, b)
c = '12/12 terminal forgeries refused on their declared reasons: commitment (2x sem-film-id-mismatch), budget lie + overrun (sem-budget-mismatch),'
d = ('12/12 terminal forgeries refused: unsealed mutations now CHANGE the commitment '
     '(id divergence asserted; the audit found budget_mutation_preserves_id:true — '
     'precisely this property missing) AND are refused by re-derivation; '
     'budget lie + overrun (sem-budget-mismatch),')
assert src.count(c) == 1, "anchor C"
src = src.replace(c, d)
open('build_v1.py', 'w', encoding='utf-8').write(src)
print("cases 1-2 sharpened")
