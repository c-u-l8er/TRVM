"use strict";
// Spinner Bench v0.3 -- front end for the real WRL->IR->CompilePlan->TRVM pipeline.
const $ = (s) => document.querySelector(s);
const SVGNS = "http://www.w3.org/2000/svg";

const state = { src: "", epochs: [], native: null, cur: 1, sel: -1, cands: [],
                graph: null, scen: null, scenSel: null,
                presets: null, scenPreset: "golden", mode: "demo",
                draftRev: 0, replaceSeq: 0,
                session: "main", projects: [], dirty: false,
                recovery: null, ckTimer: null, ckReasons: null,
                job: null,
                // v0.7-1 onboarding (all presentation-only)
                explore: false, view: "author", guideStep: 0, guideCopy: false,
                // v0.7-3 template chooser (currentTemplate = the id being explored)
                templates: null, currentTemplate: null, templateManifest: null };

const ROLE_COLOR = {
  Pulser: "#4ea1ff", Relay: "#3fb950", Spinner: "#c98bff",
  Orb: "#f0883e", Door: "#d29922",
};

function setStatus(msg, cls) {
  const el = $("#status"); el.textContent = msg; el.className = "status " + (cls || "");
}

// v0.5.1 dirty indicator: mark the Save button when the workspace has unsaved
// edits (an Apply that changed the draft). Save / Commit / Open clear it.
function renderDirty() {
  const b = $("#btn-save");
  if (!b) return;
  b.classList.toggle("dirty", !!state.dirty);
  b.textContent = state.dirty ? "Save •" : "Save";
}

// v0.6-0 crash-recovery indicator + debounced checkpoint. A checkpoint writes the
// UNSAVED workspace to the SEPARATE `.recovery/` journal (never advances the
// project revision, moves any identity or activates a candidate). It fires ~1s
// after an authoring change and is cleared server-side by an explicit Save/Commit
// (after a durable write) or Discard.
const _RECOVERY_LABEL = {
  saved: ["", ""],
  recovery_checkpointed: ["⟳ recovery checkpointed", "ck"],
  recovery_available: ["⟳ recovery available", "avail"],
  recovery_stale: ["⟳ recovery stale", "stale"],
  recovery_error: ["⟳ recovery error", "err"],
};
function renderRecovery() {
  const el = $("#recovery-indicator");
  if (!el) return;
  const st = (state.recovery && state.recovery.state) || "saved";
  const [txt, cls] = _RECOVERY_LABEL[st] || [st, ""];
  el.textContent = txt;
  el.title = st === "saved" ? "" :
    "A separate crash-recovery journal holds this project's unsaved workspace";
  el.className = "recovery " + cls;
}
function scheduleCheckpoint(reason) {
  // v0.7-1 D: read-only Golden Demo exploration NEVER writes a recovery journal.
  // (There is also no editable draft to checkpoint while exploring.)
  if (state.explore) return;
  clearTimeout(state.ckTimer);
  state.ckReasons = state.ckReasons || new Set();
  state.ckReasons.add(reason);
  state.ckTimer = setTimeout(doCheckpoint, 1000);
}
async function doCheckpoint() {
  const reasons = Array.from(state.ckReasons || []);
  state.ckReasons = new Set();
  const r = await api("/api/recovery/checkpoint",
    { session_id: state.session, dirty_reasons: reasons });
  if (r.ok) {
    state.recovery = { state: "recovery_checkpointed",
                       recovery_revision: r.recovery_revision };
    renderRecovery();
  } else {
    state.recovery = { state: "recovery_error" }; renderRecovery();
  }
}
async function refreshRecovery() {
  const r = await api("/api/recovery/status?session_id=" +
                      encodeURIComponent(state.session));
  if (!r.ok) return;
  state.recovery = r.recovery; renderRecovery();
  if (r.recovery.state === "recovery_available") await promptRecovery(false);
  else if (r.recovery.state === "recovery_stale") await promptRecovery(true);
}
async function promptRecovery(stale) {
  const ins = await api("/api/recovery/inspect", { session_id: state.session });
  const info = ins.ok ? ins.inspect : {};
  const age = info.checkpointed_at
    ? new Date(info.checkpointed_at * 1000).toLocaleString() : "?";
  const lines = [
    `An UNSAVED workspace was checkpointed for "${state.session}".`,
    `checkpoint: ${age}`,
    `draft: ${info.draft_valid ? "valid candidate" : "INVALID (needs repair)"}`,
    info.candidate_differs ? "candidate differs from the saved active world" : "",
    `undo depth: ${info.undo_depth}`,
    stale ? "This journal is STALE — the saved project changed underneath it." : "",
  ].filter(Boolean).join("\n");
  if (stale) {
    const go = await dialogChoice("Recovery journal is stale", lines, [
      { value: "copy", label: "Open as copy" },
      { value: null, label: "Later" },
    ]);
    if (go !== "copy") return;
    const f = await dialogForm("Open recovered copy", [
      { name: "npid", label: "New project id for the recovered copy",
        value: state.session + "-recovered" },
    ]);
    if (!f || !f.npid) return;
    const r = await api("/api/recovery/open-as-copy",
      { session_id: state.session, new_project_id: f.npid });
    if (!r.ok) { showError(r, "recover-copy error"); return; }
    clearError();
    state.projects = r.projects; await openSession(f.npid);
    setStatus(`opened recovered copy ${f.npid} ✓`, "ok");
    return;
  }
  const choice = await dialogChoice("Unsaved workspace recovered", lines, [
    { value: "recover", label: "Recover" },
    { value: "discard", label: "Discard", danger: true },
    { value: null, label: "Later" },
  ]);
  if (choice === "recover") {
    const r = await api("/api/recovery/recover", { session_id: state.session });
    if (!r.ok) { showError(r, "recover error"); return; }
    clearError();
    const v = r.view;
    state.draftRev = v.semantic_revision; state.graph = v;
    $("#wrl").value = v.text; $("#wrl-b").value = v.text;
    drawCanvas(v); drawDraftStatus(v, null); renderCommits(v, null);
    $("#sem-id").textContent = v.active_semantic_id || v.candidate_semantic_id || "";
    state.dirty = true; renderDirty();
    state.recovery = { state: "recovery_checkpointed" }; renderRecovery();
    setStatus("recovered UNSAVED workspace — remember to Save ✓", "ok");
  } else if (choice === "discard") {
    if (!await dialogConfirm("Discard recovery journal?",
        "This cannot be undone.", true)) return;
    const r = await api("/api/recovery/discard", { session_id: state.session });
    if (r.ok) {
      state.recovery = r.recovery; renderRecovery();
      setStatus("recovery journal discarded", "ok");
    }
  }
}

async function api(path, body) {
  const r = await fetch(path, {
    method: body ? "POST" : "GET",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  return r.json();
}

// ==================== v0.7-2 accessible in-app dialogs =====================
// In-app, focus-managed, ARIA dialogs replace the browser-native
// prompt/alert/confirm for every primary flow (create / make-copy / fork /
// rename / trash / restore / recovery choice / import collisions / destructive
// confirmations). Each returns a Promise; Escape or Cancel resolves to null,
// OK resolves to the field values (form) / chosen value (choice) / true
// (confirm). Focus is trapped while open and restored to the invoking element
// on close (PB17). Nothing here touches any Forge identity.
let _dlgOpen = false;
function _closeDialog(host, back, prev, resolve, value) {
  host.classList.add("hidden");
  host.innerHTML = "";
  _dlgOpen = false;
  if (prev && prev.focus) { try { prev.focus(); } catch (e) { /* gone */ } }
  resolve(value);
}
function _dialog({ title, message, fields, choices, confirmLabel, cancelLabel,
                  danger }) {
  return new Promise((resolve) => {
    const host = $("#dialog-root");
    const prev = document.activeElement;
    _dlgOpen = true;
    host.className = "dialog-root";              // visible
    host.innerHTML = "";
    const back = document.createElement("div");
    back.className = "dlg-backdrop";
    const dlg = document.createElement("div");
    dlg.className = "dlg" + (danger ? " danger" : "");
    dlg.setAttribute("role", "dialog");
    dlg.setAttribute("aria-modal", "true");
    dlg.setAttribute("aria-labelledby", "dlg-title");
    const h = document.createElement("h2");
    h.id = "dlg-title"; h.textContent = title; dlg.appendChild(h);
    if (message) {
      const p = document.createElement("p");
      p.className = "dlg-msg"; p.textContent = message; dlg.appendChild(p);
    }
    const inputs = [];
    (fields || []).forEach((f, i) => {
      const wrap = document.createElement("label");
      wrap.className = "dlg-field";
      wrap.textContent = f.label;
      const inp = document.createElement("input");
      inp.type = "text"; inp.value = f.value || "";
      if (f.placeholder) inp.placeholder = f.placeholder;
      inp.name = f.name;
      wrap.appendChild(inp); dlg.appendChild(wrap);
      inputs.push(inp);
    });
    const val = () => {
      const o = {}; inputs.forEach((inp) => (o[inp.name] = inp.value.trim()));
      return o;
    };
    const foot = document.createElement("div");
    foot.className = "dlg-foot";
    if (choices) {
      choices.forEach((c) => {
        const b = document.createElement("button");
        b.className = "dlg-btn" + (c.danger ? " danger" : "");
        b.textContent = c.label;
        b.onclick = () => _closeDialog(host, back, prev, resolve, c.value);
        foot.appendChild(b);
      });
    } else {
      const cancel = document.createElement("button");
      cancel.className = "dlg-btn dlg-cancel";
      cancel.textContent = cancelLabel || "Cancel";
      cancel.onclick = () => _closeDialog(host, back, prev, resolve, null);
      const ok = document.createElement("button");
      ok.className = "dlg-btn dlg-ok" + (danger ? " danger" : "");
      ok.textContent = confirmLabel || "OK";
      ok.onclick = () => _closeDialog(host, back, prev, resolve,
                                      fields ? val() : true);
      foot.appendChild(cancel); foot.appendChild(ok);
    }
    dlg.appendChild(foot);
    back.appendChild(dlg); host.appendChild(back);
    // Escape closes to null; focus trap keeps Tab inside the dialog.
    dlg.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape") {
        ev.preventDefault();
        _closeDialog(host, back, prev, resolve, choices ? null : null);
      } else if (ev.key === "Enter" && !choices && (fields || confirmLabel)) {
        ev.preventDefault();
        _closeDialog(host, back, prev, resolve, fields ? val() : true);
      } else if (ev.key === "Tab") {
        const f = dlg.querySelectorAll("input, button");
        if (!f.length) return;
        const first = f[0], last = f[f.length - 1];
        if (ev.shiftKey && document.activeElement === first) {
          ev.preventDefault(); last.focus();
        } else if (!ev.shiftKey && document.activeElement === last) {
          ev.preventDefault(); first.focus();
        }
      }
    });
    back.addEventListener("mousedown", (ev) => {
      if (ev.target === back) _closeDialog(host, back, prev, resolve, null);
    });
    (inputs[0] || dlg.querySelector("button")).focus();
  });
}
function dialogAlert(title, message) {
  return _dialog({ title, message, confirmLabel: "OK", cancelLabel: "OK" })
    .then(() => undefined);
}
function dialogConfirm(title, message, danger) {
  return _dialog({ title, message, confirmLabel: danger ? "Confirm" : "OK",
                   danger: !!danger }).then((v) => v === true);
}
function dialogForm(title, fields, message) {
  return _dialog({ title, message, fields, confirmLabel: "OK" });
}
function dialogChoice(title, message, choices) {
  return _dialog({ title, message, choices });
}

// -------------------------------- typed error surface (ErrorPresentationV1) --
// Render a server ErrorPresentationV1 as an accessible banner: the stable title,
// the domain message (NEVER a raw Python exception), and the single suggested
// action. When the error locates a source span or a canvas object we highlight
// it (PB4/PB5). Falls back to a plain string for a legacy `error`.
function _errMsg(x) { return x && typeof x === "object" && x.message ? x.message : x; }
function showError(r, fallback) {
  const pres = r && r.error_presentation;
  const el = $("#error-banner");
  if (!pres) {
    const msg = (r && r.error) || fallback || "error";
    if (el) {
      el.className = "error-banner error";
      el.innerHTML = `<span class="eb-msg"></span>`;
      el.querySelector(".eb-msg").textContent = msg;
      el.classList.remove("hidden");
    }
    setStatus(msg, "err");
    return;
  }
  if (el) {
    el.className = "error-banner " + (pres.severity || "error");
    el.innerHTML =
      `<span class="eb-code"></span><strong class="eb-title"></strong>` +
      `<span class="eb-msg"></span><button class="eb-x" title="dismiss">×</button>`;
    el.querySelector(".eb-code").textContent = pres.code;
    el.querySelector(".eb-title").textContent = pres.title;
    el.querySelector(".eb-msg").textContent = pres.message;
    el.querySelector(".eb-x").onclick = () => el.classList.add("hidden");
    if (pres.action_label) {
      const b = document.createElement("button");
      b.className = "eb-action"; b.textContent = pres.action_label;
      b.onclick = () => runErrorAction(pres);
      el.appendChild(b);
    }
    el.classList.remove("hidden");
  }
  highlightError(pres);
  setStatus(pres.message, pres.severity === "info" ? "" : "err");
}
function clearError() {
  const el = $("#error-banner"); if (el) el.classList.add("hidden");
  document.querySelectorAll(".node.err, .edge.err")
    .forEach((n) => n.classList.remove("err"));
}
// Highlight the implicated source span (in the WRL editor) and/or canvas object.
function highlightError(pres) {
  if (pres.object_id) {
    const n = document.querySelector(`[data-object-id="${pres.object_id}"]`);
    if (n) n.classList.add("err");
  }
  const sp = pres.source_span;
  if (sp && typeof sp.start_line === "number") {
    const ed = $("#wrl");
    if (ed && ed.value) {
      const lines = ed.value.split("\n");
      let off = 0;
      for (let i = 0; i < sp.start_line - 1 && i < lines.length; i++)
        off += lines[i].length + 1;
      const start = off + (sp.start_column || 0);
      const end = off + (sp.end_column || (sp.start_column || 0) + 1);
      try { ed.focus(); ed.setSelectionRange(start, end); } catch (e) { /* ro */ }
    }
  }
}
// The single suggested next action for a retryable error. Most actions are
// context-specific flows already wired elsewhere; here we route the common ones.
function runErrorAction(pres) {
  const code = pres.code;
  if (code === "NATIVE_UNAVAILABLE" || code === "NATIVE_BUILD_FAILED") {
    clearError(); doRun(); return;
  }
  if (code === "WRL_PROJECT_STALE" || code === "WRL_STALE_DRAFT") {
    clearError(); openSession(state.session); return;
  }
  clearError();
}

// ============================ v0.7-1 onboarding ============================
// All state below is PRESENTATION metadata: it lives in browser localStorage only
// and never enters a project document, a SemanticArtifactID, a ScenarioDigest, a
// ReplayBundleID, or an export. Switching a view / advancing a step / dismissing
// the tour recomputes no identity and folds no run.
const LS = {
  get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : v; }
              catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* private mode */ } },
};
const TOUR_SEEN = "forge.tour.seen";
const TOUR_STEP = "forge.tour.step";
const TOUR_ADV = "forge.tour.advanced";
const VIEW_KEY = "forge.view";

// -- progressive disclosure: two workspace views over the same state + APIs -----
function setView(v, persist) {
  if (v !== "author" && v !== "evidence") return;
  state.view = v;
  document.body.setAttribute("data-view", v);
  const a = $("#view-author"), e = $("#view-evidence");
  if (a) { a.classList.toggle("on", v === "author"); a.setAttribute("aria-pressed", v === "author"); }
  if (e) { e.classList.toggle("on", v === "evidence"); e.setAttribute("aria-pressed", v === "evidence"); }
  if (persist !== false) LS.set(VIEW_KEY, v);
}
function restoreView() { setView(LS.get(VIEW_KEY, "author"), false); }

// -- the guided-demo rail -------------------------------------------------------
// Each step highlights an EXISTING panel and (for evidence-side steps) flips the
// workspace to the view that contains it, so the tour never fights the UI.
const GUIDE_STEPS = [
  { panel: "panel-canvas", view: "author", title: "1 · World",
    body: "This is the Golden Demo world graph — a WallRiderLang world of Pulsers, Relays, a Spinner, an Orb and a Door. Its sealed SemanticArtifactID is the world's identity.",
    why: "The world (its objects + wiring + rotor) is the ONLY thing that determines the SemanticArtifactID. Presentation — position, colour, wire curve — never moves it." },
  { panel: "panel-scenario", view: "author", title: "2 · Scenario",
    body: "The Scenario author holds the RUN INPUTS — the per-epoch rotor/fault claims. A scenario is never part of the world's identity; it has its own ScenarioDigest.",
    why: "Separating world meaning from execution inputs is the point: the same sealed world can be folded under many scenarios without changing its identity." },
  { panel: "panel-world", view: "author", title: "3 · Run",
    body: "Run folds the world through the real TRVM interaction-calculus runtime. Scrub the World disc to watch the rotor pose evolve epoch by epoch.",
    why: "Nothing is trusted blindly — the fold is the actual WRL → IR → CompilePlan → TRVM pipeline, not a mock." },
  { panel: "panel-film", view: "evidence", title: "4 · Film",
    body: "Switch to Evidence to read the per-epoch Film v0.7 hashes and the ADMIT projection — the runtime evidence for each epoch.",
    why: "The Film is content-addressed per epoch, so two runs that agree on meaning agree hash-for-hash." },
  { panel: "panel-diff", view: "evidence", title: "5 · Candidate",
    body: "SemanticDiff compares the committed ACTIVE world with your in-editor CANDIDATE. is_empty() ⇔ sem_id(a) == sem_id(b): identical meaning ⇒ identical id.",
    why: "This is the identity bridge law made visible — editing text or wiring moves the candidate id; moving a node on the canvas does not." },
  { panel: "panel-film", view: "evidence", title: "6 · Verify",
    body: "Verify re-folds through the compiled native reducer and asserts ic_ref == ic32 (and, with the oracle on, == fixture). Native parity is a hard gate.",
    why: "The reference and native runtimes must agree bit-for-bit, so a green Verify is real cross-runtime evidence, not a claim." },
];
function guideRender() {
  const i = Math.max(0, Math.min(state.guideStep, GUIDE_STEPS.length - 1));
  const s = GUIDE_STEPS[i];
  $("#gr-count").textContent = `${i + 1} / ${GUIDE_STEPS.length}`;
  $("#gr-step-title").textContent = s.title;
  $("#gr-step-body").textContent = s.body;
  $("#gr-advanced-body").textContent = s.why;
  const adv = $("#gr-advanced");
  if (adv) adv.open = LS.get(TOUR_ADV, "0") === "1";
  $("#gr-back").disabled = i === 0;
  $("#gr-next").textContent = i === GUIDE_STEPS.length - 1 ? "Done" : "Next";
  if (s.view) setView(s.view);
  document.querySelectorAll(".panel.guide-highlight")
    .forEach((p) => p.classList.remove("guide-highlight"));
  const target = document.getElementById(s.panel);
  if (target) target.classList.add("guide-highlight");
}
function guideGoto(i) {
  state.guideStep = Math.max(0, Math.min(i, GUIDE_STEPS.length - 1));
  LS.set(TOUR_STEP, String(state.guideStep));
  guideRender();
}
function guideOpen(fromStart) {
  if (fromStart) state.guideStep = 0;
  else state.guideStep = Number(LS.get(TOUR_STEP, "0")) || 0;
  $("#guide-rail").classList.remove("hidden");
  document.body.classList.add("guide-open");
  guideRender();
}
function guideDismiss() {
  $("#guide-rail").classList.add("hidden");
  document.body.classList.remove("guide-open");
  document.querySelectorAll(".panel.guide-highlight")
    .forEach((p) => p.classList.remove("guide-highlight"));
  LS.set(TOUR_SEEN, "1");
}
function guideNext() {
  if (state.guideStep >= GUIDE_STEPS.length - 1) { guideDismiss(); return; }
  guideGoto(state.guideStep + 1);
}
function guideBack() { guideGoto(state.guideStep - 1); }

// -- first-run landing ----------------------------------------------------------
function showFirstRun(hasLast, lastId) {
  const ov = $("#first-run");
  if (!ov) return;
  $("#fr-resume").classList.toggle("hidden", !hasLast);
  $("#fr-fresh").classList.toggle("hidden", !!hasLast);
  ov.dataset.lastId = hasLast ? (lastId || "") : "";
  ov.classList.remove("hidden");
  if (!hasLast) renderTemplateCards();   // fresh path: the 3-card template chooser
  // focus the primary action for keyboard users
  const primary = hasLast ? $("#fr-open-last") : $("#fr-open");
  if (primary) primary.focus();
}
// v0.7-3: render the immutable Template Catalog as read-only chooser cards. The
// Golden ADMIT Demo is marked recommended (the ruled default) but nothing is
// auto-selected: each card offers an explicit Explore (read-only preview,
// creates nothing) or Use (creates an independent project). The card is a wider
// first-run panel; if the catalog failed to load we fail closed with a message.
function renderTemplateCards() {
  const host = $("#fr-templates");
  const card = $(".fr-card");
  if (!host) return;
  const list = state.templates;
  if (!list || !list.length) {
    // fail closed: only the template subsystem is unavailable — Open Existing
    // Project + the running workspace remain fully usable (PC35).
    host.innerHTML = '<p class="fr-templates-empty">Templates are unavailable '
      + 'right now — you can still open an existing project below.</p>';
    return;
  }
  if (card) card.classList.add("fr-wide");
  host.setAttribute("role", "list");
  host.innerHTML = "";
  list.forEach((t) => {
    const rec = t.template_id === "forge.template.golden-admit.v1";
    const el = document.createElement("div");
    el.className = "tpl-card" + (rec ? " tpl-recommended" : "");
    el.setAttribute("role", "listitem");
    const diff = rec ? "recommended" : (t.difficulty || "");
    el.innerHTML =
      '<div class="tpl-head"><span class="tpl-name"></span>' +
      '<span class="tpl-diff"></span></div>' +
      '<p class="tpl-desc"></p>' +
      '<div class="tpl-actions">' +
      '<button class="tpl-explore">Explore</button>' +
      '<button class="tpl-use">Use</button></div>';
    el.querySelector(".tpl-name").textContent = t.name;
    el.querySelector(".tpl-diff").textContent = diff;
    el.querySelector(".tpl-desc").textContent = t.short_description || "";
    const bx = el.querySelector(".tpl-explore");
    const bu = el.querySelector(".tpl-use");
    // accessible names so the ambiguous "Explore"/"Use" labels announce which
    // template they act on (keyboard + screen-reader; presentation only).
    bx.setAttribute("aria-label", "Explore " + t.name + " (read-only preview)");
    bu.setAttribute("aria-label", "Use " + t.name + " (create an editable project)");
    bx.onclick = () => enterExploreTemplate(t.template_id);
    bu.onclick = () => doUseTemplate(t.template_id);
    host.appendChild(el);
  });
}
// v0.7-3: build the scenario presets panel from a template MANIFEST rather than
// the global demo /api/scenario endpoint, so a preview (and a template-derived
// project) runs the template's OWN scenarios + default. Each manifest scenario
// doc {name, scenario_digest, scenario} becomes a preset keyed by its name.
function loadTemplateScenarios(m) {
  const presets = {};
  (m.scenarios || []).forEach((s) => {
    presets[s.name] = { id: s.name, label: s.name, scenario: s.scenario,
                        scenario_digest: s.scenario_digest };
  });
  state.presets = presets;
  state.scenPreset = m.default_scenario_document_id;
  renderPresetOptions();
  applyPreset(state.scenPreset);
}
// v0.7-3.1: rehydrate the scenario presets from a PROJECT's OWN persisted
// scenario documents (returned by /api/project/open, /api/project/fork, and
// /api/template/use), rather than the global demo /api/scenario endpoint. This
// is the reopen fix: once a project is created (from any template) it owns its
// scenario documents and no longer depends on the template catalog, so a
// reopened Blank restores its one-epoch idle scenario — not Golden/Bench. Each
// persisted doc {name, scenario_digest, scenario} becomes a preset keyed by
// name; `selectedId` is the bound default (a NAME). Returns false when the
// project carries no persisted scenarios (a legacy V1 project) so the caller
// can fall back to the global presets.
function loadProjectScenarios(scenarioDocs, selectedId) {
  if (!Array.isArray(scenarioDocs) || scenarioDocs.length === 0) return false;
  const presets = {};
  scenarioDocs.forEach((s) => {
    presets[s.name] = { id: s.name, label: s.name, scenario: s.scenario,
                        scenario_digest: s.scenario_digest };
  });
  state.presets = presets;
  state.scenPreset = (selectedId && presets[selectedId])
    ? selectedId : scenarioDocs[0].name;
  renderPresetOptions();
  applyPreset(state.scenPreset);
  return true;
}
function hideFirstRun() { const ov = $("#first-run"); if (ov) ov.classList.add("hidden"); }

// -- read-only Golden Demo exploration -----------------------------------------
// v0.7-1.1: Explore is a GENUINELY read-only mode over the demo/`main`
// pseudo-session. It disables EVERY authoring / persistence / source-mutating
// affordance (not merely "does not persist") and makes both editable textareas
// readonly. It creates no project and (via the scheduleCheckpoint guard) writes
// no recovery journal. "Make an editable copy" is the ONLY persistence transition.
const _EXPLORE_DISABLED = [
  // authoring / persistence
  "#btn-apply", "#btn-save", "#btn-commit", "#btn-draft-undo",
  // Format mutates the WRL buffer, so it is NOT allowed while exploring (Lower
  // only displays, so it stays usable).
  "#btn-format",
  // Library: switching project would silently leave Explore; every mutation is
  // locked. Use Home to reopen the chooser to leave Explore deliberately.
  "#lib-select", "#lib-new", "#lib-fork", "#lib-rename", "#lib-trash",
  "#lib-restore", "#lib-migrate", "#lib-export", "#lib-import",
  // Scenario: the Author toggle, preset selector, and every mutation gesture.
  "#scn-mode-author", "#scn-preset",
  "#scn-add-claim", "#scn-add-reset", "#scn-add-idle",
  "#scn-retransmit", "#scn-equivocate", "#scn-reset-preset"];
// Editors that must become non-editable (their content IS the displayed source).
const _EXPLORE_READONLY = ["#wrl", "#wrl-b"];
function setExplore(on) {
  state.explore = on;
  document.body.classList.toggle("explore", on);
  const b = $("#explore-banner"); if (b) b.classList.toggle("hidden", !on);
  _EXPLORE_READONLY.forEach((id) => { const el = $(id); if (el) el.readOnly = on; });
  if (on) {
    _EXPLORE_DISABLED.forEach((id) => { const el = $(id); if (el) el.disabled = true; });
  } else {
    // Leaving Explore: re-enable, then reconcile the mode-dependent controls so
    // we do not wrongly enable scenario gestures in Demo mode or the Migrate
    // affordance on a non-legacy project.
    _EXPLORE_DISABLED.forEach((id) => { const el = $(id); if (el) el.disabled = false; });
    setGesturesEnabled(state.mode === "author");
    renderLibrary();
  }
}
// Explicitly load the frozen Golden Demo into the workspace. This NEVER reuses
// whatever project happened to be open: it re-points to the `main` pseudo-session,
// loads DEMO_WORLD_SOURCE, and re-lowers so the displayed active/candidate
// identity resets to the demo's frozen SemanticArtifactID.
async function loadDemoWorld() {
  const d = await api("/api/demo");
  state.src = d.src; state.scenPreset = "golden";
  $("#wrl").value = d.src; $("#wrl-a").value = d.src; $("#wrl-b").value = d.src;
  await resetDraft();   // reset the `main` draft session to the demo world
  await doLower();      // re-lower → #sem-id shows the frozen demo identity
}
async function enterExplore() {
  hideFirstRun();
  // 1-4: leave the current project presentation and load the demo explicitly.
  state.session = "main";
  state.mode = "demo";
  await loadDemoWorld();
  await loadScenario();               // 3+5: golden preset, demo scenario mode
  // 5: lock the read-only surfaces (after the demo is loaded).
  setExplore(true);
  setStatus("read-only exploration of the frozen Golden Demo — nothing is saved", "");
  // 6: run the guided fold, then open the rail.
  await doRun();
  guideOpen(true);
}
// Home / Start: reopen the resume/first-run chooser explicitly at any time
// (the ruled non-modal control so a user is never forced into a modal every
// launch but can always get back to the launcher).
async function openChooser() {
  const sess = await api("/api/session");
  const lastId = (sess.ok && sess.last_project_id
    && state.projects.some((p) => p.project_id === sess.last_project_id))
    ? sess.last_project_id : null;
  if (lastId) showFirstRun(true, lastId);
  else showFirstRun(false);
}
// v0.7-3 "Explore Template": the read-only preview path. Rebuilds the in-memory
// `main` pseudo-session from the template's world source (server-side, creating
// no project / recovery / pointer), loads the template's world + own scenarios,
// locks every authoring surface, then folds the default scenario and opens the
// guide. Generalises enterExplore across all three catalog templates.
async function enterExploreTemplate(templateId) {
  hideFirstRun();
  const r = await api("/api/template/preview", { template_id: templateId });
  if (!r.ok) { showFirstRun(false); showError(r, "template preview error"); return; }
  const m = r.template;
  state.session = "main"; state.mode = "demo";
  state.currentTemplate = templateId; state.templateManifest = m;
  state.src = m.canonical_world_source; state.scenPreset = m.default_scenario_document_id;
  $("#wrl").value = m.canonical_world_source;
  $("#wrl-a").value = m.canonical_world_source;
  $("#wrl-b").value = m.canonical_world_source;
  await doLower();                    // re-lower → #sem-id shows the template identity
  loadTemplateScenarios(m);          // the template's OWN scenario presets + default
  setExplore(true);
  setStatus(`read-only preview of “${m.name}” — nothing is saved`, "");
  await doRun();
  guideOpen(true);
}
// v0.7-3 "Use Template": the ONLY template action that creates real state. It
// asks for a new project id, instantiates an INDEPENDENT ForgeProjectV2 from the
// template (preserving its initial semantic/scenario/replay identities + a
// non-authoritative provenance sidecar), then opens it in Author mode running the
// template's own scenarios. A project-id collision re-opens the form pre-filled.
async function doUseTemplate(templateId) {
  const gm = await api("/api/template?template_id=" + encodeURIComponent(templateId));
  if (!gm.ok) { showError(gm, "template error"); return; }
  const m = gm.template;
  let vals = { pid: "", name: m.name }, msg =
    "Create an independent, editable project from this template.";
  for (;;) {
    const f = await dialogForm(`Use “${m.name}”`, [
      { name: "pid", label: "New project id", value: vals.pid },
      { name: "name", label: "Display name", value: vals.name },
    ], msg);
    if (!f || !f.pid) return;
    vals = f;
    const r = await api("/api/template/use",
      { template_id: templateId, project_id: f.pid, name: f.name || f.pid });
    if (r.ok) {
      clearError();
      state.projects = r.projects;
      state.currentTemplate = null; state.templateManifest = m;
      setExplore(false); hideFirstRun();
      // v0.7-3.1: the new project owns its scenario documents (seeded from the
      // template at creation), so openSession rehydrates them from the project
      // itself — no template loader is threaded through.
      await openSession(f.pid);
      setView("author");
      setStatus(`created project ${f.pid} from “${m.name}” ✓`, "ok");
      return;
    }
    const p = r.error_presentation;
    if (p && p.code === "WRL_PROJECT_EXISTS") { msg = p.message; continue; }
    showError(r, "use-template error"); return;
  }
}
// "Make an editable copy": the explore-banner path out of a read-only preview.
// It routes to "Use Template" for whichever template is being explored, so the
// created project is seeded from that exact template (not always the demo).
async function doMakeCopy() {
  if (state.currentTemplate) return doUseTemplate(state.currentTemplate);
  return doUseTemplate("forge.template.golden-admit.v1");
}

// -------------------------------------------------------------- canvas graph
function layout(nodes, edges) {
  // longest-path layering left->right from sources (no incoming edge).
  const inc = {}, adj = {};
  nodes.forEach((n) => { inc[n.id] = 0; adj[n.id] = []; });
  edges.forEach((e) => { if (adj[e.src]) { adj[e.src].push(e.dst); inc[e.dst]++; } });
  const depth = {}; nodes.forEach((n) => (depth[n.id] = 0));
  let frontier = nodes.filter((n) => inc[n.id] === 0).map((n) => n.id);
  const seen = new Set();
  while (frontier.length) {
    const next = [];
    frontier.forEach((id) => {
      (adj[id] || []).forEach((d) => {
        depth[d] = Math.max(depth[d], depth[id] + 1);
        if (!seen.has(d)) { seen.add(d); next.push(d); }
      });
    });
    frontier = next;
  }
  const cols = {};
  nodes.forEach((n) => { (cols[depth[n.id]] = cols[depth[n.id]] || []).push(n.id); });
  const maxD = Math.max(0, ...Object.keys(cols).map(Number));
  const pos = {};
  Object.entries(cols).forEach(([d, ids]) => {
    ids.forEach((id, i) => {
      const x = 40 + (Number(d) / Math.max(1, maxD)) * 320;
      const y = 40 + ((i + 0.5) / ids.length) * 220;
      pos[id] = { x, y };
    });
  });
  return pos;
}

function drawCanvas(graph) {
  const svg = $("#canvas"); svg.innerHTML = "";
  const pos = layout(graph.nodes, graph.edges);
  graph.edges.forEach((e) => {
    const a = pos[e.src], b = pos[e.dst]; if (!a || !b) return;
    const p = document.createElementNS(SVGNS, "path");
    const socket = e.kind === "SocketControl";
    p.setAttribute("class", "edge " + (socket ? "socket" : "sig"));
    p.setAttribute("d", `M${a.x + 26} ${a.y} C ${(a.x + b.x) / 2} ${a.y}, ${(a.x + b.x) / 2} ${b.y}, ${b.x - 26} ${b.y}`);
    p.setAttribute("marker-end", "url(#arrow)");
    svg.appendChild(p);
    const t = document.createElementNS(SVGNS, "text");
    t.setAttribute("class", "edge-label");
    t.setAttribute("x", (a.x + b.x) / 2); t.setAttribute("y", (a.y + b.y) / 2 - 3);
    t.setAttribute("text-anchor", "middle");
    t.textContent = socket ? "socket" : "sig";
    svg.appendChild(t);
  });
  graph.nodes.forEach((n) => {
    const p = pos[n.id]; if (!p) return;
    const g = document.createElementNS(SVGNS, "g");
    g.setAttribute("class", "node");
    g.setAttribute("data-object-id", n.id);
    g.setAttribute("transform", `translate(${p.x},${p.y})`);
    const rect = document.createElementNS(SVGNS, "rect");
    rect.setAttribute("x", -26); rect.setAttribute("y", -15);
    rect.setAttribute("width", 52); rect.setAttribute("height", 30);
    rect.setAttribute("rx", 6);
    rect.setAttribute("fill", "#12171f");
    rect.setAttribute("stroke", ROLE_COLOR[n.role] || "#888");
    g.appendChild(rect);
    const id = document.createElementNS(SVGNS, "text");
    id.setAttribute("text-anchor", "middle"); id.setAttribute("y", -1);
    id.textContent = n.id; g.appendChild(id);
    const role = document.createElementNS(SVGNS, "text");
    role.setAttribute("class", "role"); role.setAttribute("text-anchor", "middle");
    role.setAttribute("y", 10); role.textContent = n.role; g.appendChild(role);
    svg.appendChild(g);
  });
  // arrow marker
  const defs = document.createElementNS(SVGNS, "defs");
  defs.innerHTML = `<marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3"
    orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#7f8ea3"/></marker>`;
  svg.insertBefore(defs, svg.firstChild);
}

// ---------------------------------------------------- text ⇄ draft convergence
// v0.4-4c: the WRL editor text is applied to the server-side draft as ONE atomic
// ReplaceWorldSourceV1 transaction (POST /api/draft/source → CanvasSession
// .apply_text). The reconciled canvas view re-renders the SAME converged
// candidate the identity spine seals, and the transaction status (candidate_valid
// / semantic_noop / semantic_invalid / syntax_error) + DraftDiff + diagnostics are
// surfaced. base_revision is auto-based server-side (single-user session), so the
// atomic swap + idempotency hold without the browser tracking CAS.
function drawDraftStatus(view, apply) {
  const el = $("#draft-status");
  if (apply && apply.error) {
    el.className = "draft-status err";
    el.innerHTML = `draft error — <code>${apply.error}</code>`; return;
  }
  const st = apply ? apply.status : (view.candidate_valid ? "candidate_valid" : "semantic_invalid");
  const cls = { candidate_valid: "ok", semantic_noop: "noop",
                semantic_invalid: "invalid", syntax_error: "err" }[st] || "";
  const badge = { candidate_valid: "candidate valid",
                  semantic_noop: "semantic no-op (identical bytes)",
                  semantic_invalid: "parseable but invalid",
                  syntax_error: "syntax error" }[st] || st || "draft";
  const short = (s) => (s ? s.slice(0, 22) + "…" : "—");
  let diff = "";
  if (apply && apply.draft_diff) {
    const dd = apply.draft_diff, parts = [];
    if (dd.objects_added.length) parts.push("+obj " + dd.objects_added.join(","));
    if (dd.objects_removed.length) parts.push("−obj " + dd.objects_removed.join(","));
    if (dd.objects_changed.length) parts.push("~obj " + dd.objects_changed.join(","));
    if (dd.edges_added.length) parts.push("+edge " + dd.edges_added.length);
    if (dd.edges_removed.length) parts.push("−edge " + dd.edges_removed.length);
    if (parts.length) diff = `<div class="d-diff">DraftDiff: ${parts.join(" · ")}</div>`;
  }
  let diag = "";
  if (apply && apply.diagnostics && apply.diagnostics.length)
    diag = `<div class="d-diag">` + apply.diagnostics.map((d) =>
      `<code>${d.code}</code> ${d.message}`).join("<br>") + `</div>`;
  el.className = "draft-status " + cls;
  el.innerHTML =
    `<span class="d-badge">${badge}</span> rev <b>${view.semantic_revision}</b> · ` +
    `candidate <code>${short(view.candidate_semantic_id)}</code>` +
    (view.candidate_valid ? "" : ` <span class="d-inv">(not runnable — repair)</span>`) +
    diff + diag;
}
async function doApplyDraft() {
  const source = $("#wrl").value;
  setStatus("applying to draft…");
  state.replaceSeq += 1;
  const r = await api("/api/draft/source", {
    session_id: state.session, replace_id: "ui-" + Date.now() + "-" + state.replaceSeq,
    source });                       // base_revision auto-based server-side
  if (!r.ok) { setStatus(r.error, "err"); drawDraftStatus({ semantic_revision: state.draftRev, candidate_semantic_id: null, candidate_valid: false }, { error: r.error }); return; }
  state.draftRev = r.apply.semantic_revision;
  state.graph = r.view;              // keep scenario spinner/orb pickers in sync
  drawCanvas(r.view);
  drawDraftStatus(r.view, r.apply);
  renderCommits(r.view, null);
  if (r.view.candidate_semantic_id) $("#sem-id").textContent = r.view.candidate_semantic_id;
  const msg = { candidate_valid: "draft applied ✓ candidate valid",
                semantic_noop: "no semantic change (identical bytes)",
                semantic_invalid: "draft applied · candidate INVALID (repair)",
                syntax_error: "syntax error — draft unchanged" }[r.apply.status] || r.apply.status;
  setStatus(`${msg} · rev ${r.apply.semantic_revision}`,
            r.apply.status === "candidate_valid" ? "ok"
              : r.apply.status === "semantic_noop" ? "" : "err");
  if (r.apply.status !== "semantic_noop") {
    state.dirty = true; renderDirty(); scheduleCheckpoint("text");
  }
}
async function doDraftUndo() {
  const r = await api("/api/draft/undo", { session_id: state.session });
  if (!r.ok) { setStatus(r.error || "undo error", "err"); return; }
  if (!r.undone) { setStatus("nothing to undo in draft", ""); return; }
  state.draftRev = r.view.semantic_revision; state.graph = r.view;
  drawCanvas(r.view); drawDraftStatus(r.view, null); renderCommits(r.view, null);
  if (r.view.candidate_semantic_id) $("#sem-id").textContent = r.view.candidate_semantic_id;
  state.dirty = true; renderDirty(); scheduleCheckpoint("undo");
  setStatus(`draft undo → rev ${r.view.semantic_revision} ✓`, "ok");
}
async function resetDraft() {
  const r = await api("/api/draft/reset", { session_id: state.session });
  if (r.ok) { state.draftRev = r.view.semantic_revision; drawDraftStatus(r.view, null);
              renderCommits(r.view, null); }
}
// commit/undo history + scenario-compatibility surfacing. The commit log is a
// pure session projection; the scenario-compat block surfaces the identity law
// a committed world change obeys — ScenarioDigest INVARIANT, only ReplayBundleID
// moves — so an author sees the consequence of promoting a candidate.
function renderCommits(view, compat) {
  const el = $("#draft-commits");
  if (!el) return;
  const short = (s) => (s ? s.slice(0, 18) + "…" : "—");
  const commits = (view && view.commits) || [];
  let log = commits.length
    ? commits.map((c) => `#${c.index} → <code>${short(c.active_semantic_id)}</code>`).join(" · ")
    : "no commits yet";
  let compatHtml = "";
  if (compat) {
    if (!compat.changed) {
      compatHtml = `<div class="cx-noop">no-op commit — active world unchanged; ` +
        `ScenarioDigest <code>${short(compat.scenario_digest)}</code> invariant, ReplayBundleID unchanged</div>`;
    } else {
      const inv = compat.digest_invariant ? "invariant ✓" : "MOVED ✗";
      compatHtml = `<div class="cx-move">world changed → scenario rebinds: ` +
        `ScenarioDigest <code>${short(compat.scenario_digest)}</code> ${inv}, ` +
        `ReplayBundleID <code>${short(compat.replay_bundle_old)}</code> → ` +
        `<code>${short(compat.replay_bundle_new)}</code></div>`;
    }
  }
  el.innerHTML = `<span class="cx-label">commits (${commits.length})</span> ${log}` +
    ` · <span class="cx-undo">undo depth ${view ? view.undo_depth : 0}</span>` + compatHtml;
}
async function doCommit() {
  const r = await api("/api/draft/commit", { session_id: state.session });
  if (!r.ok) { setStatus(r.error || "commit error", "err"); return; }
  state.draftRev = r.view.semantic_revision; state.graph = r.view;
  drawCanvas(r.view); drawDraftStatus(r.view, null); renderCommits(r.view, r.scenario_compat);
  if (r.view.active_semantic_id) $("#sem-id").textContent = r.view.active_semantic_id;
  const moved = r.scenario_compat && r.scenario_compat.changed;
  state.dirty = false; renderDirty();
  clearTimeout(state.ckTimer);           // Commit persisted durably → journal cleared
  state.recovery = { state: "saved" }; renderRecovery();
  setStatus(`committed → active ${r.commit.active_semantic_id.slice(0, 20)}…` +
            (moved ? " · scenario rebinds (digest invariant)" : " · no-op"), "ok");
}

// ---------------------------------------------------------------- library
// v0.5-4: the Library manages MULTIPLE named, persisted worlds over the same
// ProjectSessionCache. Each project is its own durable ForgeProjectV1 document;
// the browser tracks the current session_id (== project_id) in state.session and
// drives every canvas endpoint against it. project_id is the immutable identity
// key (Rename changes only the display name); Fork copies the SAVED world into a
// new project at revision 0; Trash is a reversible soft-delete.
function renderLibrary() {
  const sel = $("#lib-select");
  if (!sel) return;
  sel.innerHTML = "";
  state.projects.forEach((p) => {
    const o = document.createElement("option");
    o.value = p.project_id;
    // v0.6-3: flag a legacy v1 project so the author knows it is read-only until
    // migrated (project_version is absent for pre-v0.6-3 server payloads → assume v2)
    const legacy = p.project_version === "forge.project.v1";
    o.textContent = `${p.name} (${p.project_id}) · rev ${p.revision}`
      + (legacy ? " · v1" : "");
    if (p.project_id === state.session) o.selected = true;
    sel.appendChild(o);
  });
  // show the Migrate affordance only for a legacy v1 CURRENT project
  const cur = state.projects.find((p) => p.project_id === state.session);
  const mig = $("#lib-migrate");
  if (mig) mig.classList.toggle("hidden",
    !(cur && cur.project_version === "forge.project.v1"));
}
async function loadProjects() {
  const r = await api("/api/projects");
  if (r.ok) { state.projects = r.projects; renderLibrary(); }
}
// v0.7-3: load the immutable template catalog card summaries for the first-run
// chooser. Identity-verified server-side at startup; on failure state.templates
// stays null and the chooser shows a fail-closed message.
async function loadTemplates() {
  const r = await api("/api/templates");
  state.templates = (r && r.ok) ? r.templates : null;
}
// v0.6-2 startup/project UX: on a reload, land back in the LAST project the author
// opened instead of re-dumping the demo world. The pointer is written server-side
// on every open/new/fork and self-heals: a pointer at a trashed/removed project
// resolves to null, so we simply keep the demo. Returns true when we restored.
async function restoreLastSession() {
  const r = await api("/api/session");
  if (r.ok && r.last_project_id && r.last_project_id !== state.session
      && state.projects.some((p) => p.project_id === r.last_project_id)) {
    await openSession(r.last_project_id);   // openSession() also refreshes recovery
    setStatus(`resumed last project ${r.last_project_id} ✓`, "ok");
    return true;
  }
  return false;
}
async function openSession(pid) {
  state.session = pid;
  const r = await api("/api/project/open", { project_id: pid });
  if (!r.ok) { setStatus(r.error || "open error", "err"); return; }
  const v = r.view;
  state.draftRev = v.semantic_revision; state.graph = v;
  $("#wrl").value = v.text; $("#wrl-b").value = v.text;
  drawCanvas(v); drawDraftStatus(v, null); renderCommits(v, null);
  $("#sem-id").textContent = v.active_semantic_id || v.candidate_semantic_id || "";
  renderLibrary();
  state.dirty = false; renderDirty();
  // v0.7-3.1: a project owns its scenario documents. Rehydrate the presets from
  // the project-open payload for EVERY reopen (never infer from the originating
  // template, never re-read the catalog), so a reopened Blank restores its idle
  // scenario and the Bench its 9-epoch acceptance run. A legacy V1 project has no
  // persisted scenario docs, so we fall back to the global demo presets.
  if (!loadProjectScenarios(r.scenario_documents, r.selected_scenario_document_id))
    await loadScenario();
  await doRun();
  setStatus(`opened project ${pid} · rev ${v.semantic_revision} ✓`, "ok");
  await refreshRecovery();
}
async function doNewProject() {
  // PB8: a project-id collision re-opens the SAME form pre-filled with the entered
  // values plus the typed reason, rather than discarding the user's input.
  let vals = { pid: "", name: "" }, msg;
  for (;;) {
    const f = await dialogForm("Create a project", [
      { name: "pid", label: "New project id (A–Z a–z 0–9 . _ - , ≤64 chars)",
        value: vals.pid },
      { name: "name", label: "Display name", value: vals.name },
    ], msg);
    if (!f || !f.pid) return;
    vals = f;
    const r = await api("/api/project/new", { project_id: f.pid, name: f.name || f.pid });
    if (r.ok) {
      clearError(); state.projects = r.projects; await openSession(f.pid);
      setStatus(`created project ${f.pid} ✓`, "ok"); return;
    }
    const p = r.error_presentation;
    if (p && p.code === "WRL_PROJECT_EXISTS") { msg = p.message; continue; }
    showError(r, "new error"); return;
  }
}
async function doForkProject() {
  let vals = { pid: "", name: "" }, msg;
  for (;;) {
    const f = await dialogForm(`Fork "${state.session}"`, [
      { name: "pid", label: "New project id", value: vals.pid },
      { name: "name", label: "Fork display name (blank = auto)", value: vals.name },
    ], msg);
    if (!f || !f.pid) return;
    vals = f;
    const r = await api("/api/project/fork",
      { source_id: state.session, project_id: f.pid, name: f.name || undefined });
    if (r.ok) {
      clearError(); state.projects = r.projects; await openSession(f.pid);
      setStatus(`forked ${state.session} ✓`, "ok"); return;
    }
    const p = r.error_presentation;
    if (p && p.code === "WRL_PROJECT_EXISTS") { msg = p.message; continue; }
    showError(r, "fork error"); return;
  }
}
async function doRenameProject() {
  const cur = state.projects.find((p) => p.project_id === state.session);
  const f = await dialogForm(`Rename project "${state.session}"`, [
    { name: "name", label: "Display name", value: cur ? cur.name : state.session },
  ]);
  if (!f || !f.name) return;
  const r = await api("/api/project/rename", { project_id: state.session, name: f.name });
  if (!r.ok) { showError(r, "rename error"); return; }
  clearError();
  state.projects = r.projects; renderLibrary();
  setStatus(`renamed → ${f.name} ✓`, "ok");
}
async function doTrashProject() {
  if (state.session === "main") {
    setStatus("cannot trash the default 'main' project", "err"); return;
  }
  if (!await dialogConfirm(`Move "${state.session}" to trash?`,
      "Non-destructive — a restorable tombstone; shared world objects are untouched.",
      true)) return;
  const r = await api("/api/project/trash", { project_id: state.session });
  if (!r.ok) { showError(r, "trash error"); return; }
  clearError();
  state.projects = r.projects;
  const next = state.projects.length ? state.projects[0].project_id : "main";
  await openSession(next);
  setStatus("trashed ✓", "ok");
}
// v0.5.1 Save: persist the COMPLETE workspace (a valid OR invalid draft, the raw
// editor buffer, undo + scenario state) WITHOUT activating a candidate — distinct
// from Commit. Clears the dirty flag.
async function doSaveProject() {
  const r = await api("/api/project/save", { session_id: state.session });
  if (!r.ok) { setStatus(r.error || "save error", "err"); return; }
  state.projects = r.projects; renderLibrary();
  state.dirty = false; renderDirty();
  clearTimeout(state.ckTimer);           // Save persisted durably → journal cleared
  state.recovery = { state: "saved" }; renderRecovery();
  setStatus(`saved workspace ${state.session} · rev ${r.project_revision} ✓`, "ok");
}
// v0.6-3 Migrate: forward-only, identity-preserving upgrade of the CURRENT legacy
// v1 project to the v2 workspace format (moves no world identity, preserves the
// revision). After it succeeds the project is Save-able; we re-open it so the live
// session + Library reflect the migrated v2 document.
async function doMigrateProject() {
  const r = await api("/api/project/migrate", { project_id: state.session });
  if (!r.ok) { setStatus(r.error || "migrate error", "err"); return; }
  state.projects = r.projects;
  await openSession(state.session);        // re-open the now-v2 project (refreshes Library)
  setStatus(`migrated ${state.session} → v2 · rev ${r.project_revision} ✓`, "ok");
}
// v0.5.1 Restore: list the non-destructive trash tombstones and restore one.
async function doRestoreProject() {
  const r = await api("/api/project/trash");
  if (!r.ok) { setStatus(r.error || "trash-list error", "err"); return; }
  if (!r.trash.length) { setStatus("trash is empty", "ok"); return; }
  const choices = r.trash.map((t) => ({
    value: t.trash_id,
    label: `${t.name} (${t.original_project_id}) · rev ${t.deleted_project_revision}`,
  }));
  choices.push({ value: null, label: "Cancel" });
  const tid = await dialogChoice("Restore a trashed project",
    "Pick a tombstone to restore.", choices);
  if (!tid) return;
  const entry = r.trash.find((t) => t.trash_id === tid);
  let body = { trash_id: entry.trash_id };
  // if the original id is still live, offer to land it under a new id
  if (state.projects.some((p) => p.project_id === entry.original_project_id)) {
    const f = await dialogForm(`id "${entry.original_project_id}" is taken`, [
      { name: "npid", label: "Restore under new id",
        value: entry.original_project_id + "-restored" },
    ], "That project id is already in use; choose another.");
    if (!f || !f.npid) return;
    body.project_id = f.npid;
  }
  const rr = await api("/api/project/restore", body);
  if (!rr.ok) { showError(rr, "restore error"); return; }
  clearError();
  state.projects = rr.projects;
  await openSession(rr.project_id);
  setStatus(`restored ${rr.project_id} ✓`, "ok");
}
async function doExportProject() {
  const mode = ($("#lib-export-mode") && $("#lib-export-mode").value) || "full";
  const r = await api("/api/project/export",
    { project_id: state.session, export_mode: mode });
  if (!r.ok) { setStatus(r.error || "export error", "err"); return; }
  const blob = new Blob([JSON.stringify(r.bundle, null, 2)],
    { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  const suffix = r.export_mode === "thin" ? ".thin" : "";
  a.href = url; a.download = `${state.session}${suffix}.forge.json`;
  document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
  setStatus(`exported ${state.session} · ${r.export_mode}` +
    (r.shallow_history ? " (history stripped)" : "") +
    ` (${r.bundle_id.slice(0, 15)}…) ✓`, "ok");
}
async function doImportProject(file) {
  if (!file) return;
  let bundle;
  try { bundle = JSON.parse(await file.text()); }
  catch (e) { setStatus("import: not valid JSON", "err"); return; }
  let pid = "", msg = "If the id collides with a live project the import is refused.";
  for (;;) {
    const f = await dialogForm("Import a project", [
      { name: "pid", label: "Import under project id (blank = keep bundle's id)",
        value: pid },
    ], msg);
    if (f === null) return;
    pid = f.pid;
    const r = await api("/api/project/import",
      { bundle, project_id: f.pid || undefined });
    if (r.ok) {
      clearError(); state.projects = r.projects; await openSession(r.project_id);
      setStatus(`imported project ${r.project_id} ✓`, "ok"); return;
    }
    const p = r.error_presentation;
    if (p && p.code === "WRL_PROJECT_EXISTS") { msg = p.message; continue; }
    showError(r, "import error"); return;
  }
}

// -------------------------------------------------------------- world disc
// Full rotation angle of a quaternion (w,x,y,z): 2·atan2(|xyz|, w). Unlike a
// z-only projection this MOVES for a rotation about any axis (e.g. the y-axis
// turn 128.0.128.0), so every non-identity state is visible on the disc.
function qAngle(q) { return 2 * Math.atan2(Math.hypot(q[1], q[2], q[3]), q[0]); }
// Dominant rotation axis label (or "identity" when the vector part is zero, i.e.
// a scalar-only quaternion — a genuine no-rotation that differs only in scale).
function qAxis(q) {
  const v = [Math.abs(q[1]), Math.abs(q[2]), Math.abs(q[3])];
  const m = Math.max(...v);
  return m === 0 ? "identity" : "xyz"[v.indexOf(m)];
}
function axisTag(q) { const a = qAxis(q); return a === "identity" ? "" : " (" + a + ")"; }
function degOf(q) { return Math.round(qAngle(q) * 180 / Math.PI); }
function arrow(svg, cx, cy, r, ang, color, label) {
  const x = cx + r * Math.sin(ang), y = cy - r * Math.cos(ang);
  const l = document.createElementNS(SVGNS, "line");
  l.setAttribute("x1", cx); l.setAttribute("y1", cy);
  l.setAttribute("x2", x); l.setAttribute("y2", y);
  l.setAttribute("stroke", color); l.setAttribute("stroke-width", 3);
  l.setAttribute("stroke-linecap", "round"); svg.appendChild(l);
  const dot = document.createElementNS(SVGNS, "circle");
  dot.setAttribute("cx", x); dot.setAttribute("cy", y); dot.setAttribute("r", 4);
  dot.setAttribute("fill", color); svg.appendChild(dot);
  const t = document.createElementNS(SVGNS, "text");
  t.setAttribute("x", x); t.setAttribute("y", y - 7);
  t.setAttribute("text-anchor", "middle");
  t.setAttribute("font", "9px monospace"); t.setAttribute("fill", color);
  t.textContent = label; svg.appendChild(t);
}
function drawDisc(row) {
  const svg = $("#disc"); svg.innerHTML = "";
  const cx = 150, cy = 140, R = 100;
  const ring = document.createElementNS(SVGNS, "circle");
  ring.setAttribute("cx", cx); ring.setAttribute("cy", cy); ring.setAttribute("r", R);
  ring.setAttribute("fill", "none");
  ring.setAttribute("stroke", row && row.fault ? "#f85149" : "#2a3441");
  ring.setAttribute("stroke-width", row && row.fault ? 4 : 2);
  svg.appendChild(ring);
  if (!row) return;
  arrow(svg, cx, cy, R - 12, qAngle(row.rotor), "#c98bff", "rotor" + axisTag(row.rotor));
  arrow(svg, cx, cy, R - 42, qAngle(row.pose), "#f0883e", "pose(orb)" + axisTag(row.pose));
  const f = document.createElementNS(SVGNS, "text");
  f.setAttribute("x", cx); f.setAttribute("y", 268);
  f.setAttribute("text-anchor", "middle"); f.setAttribute("font", "11px monospace");
  f.setAttribute("fill", row.fault ? "#f85149" : "#3fb950");
  f.textContent = row.fault ? "orb fault: LATCHED" : "orb fault: clear";
  svg.appendChild(f);
}
function showEpoch(t) {
  state.cur = t;
  const row = state.epochs.find((r) => r.t === t);
  $("#ep-range").value = t;
  $("#ep-label").textContent = row ? `epoch ${t}/${state.epochs.length}` : "";
  drawDisc(row);
  if (row) {
    const q = (a) => a.join(".");
    const rot = (a) => { const x = qAxis(a); return `${degOf(a)}°${x === "identity" ? " identity" : " about " + x}`; };
    $("#world-readout").innerHTML =
      `<b>${row.label}</b><br>rotor=<b>${q(row.rotor)}</b> <span class="rot">(${rot(row.rotor)})</span> · ` +
      `pose=<b>${q(row.pose)}</b> <span class="rot">(${rot(row.pose)})</span> · fault=<b>${row.fault}</b>`;
  }
  drawAdmit(row);
  document.querySelectorAll("#film-body tr").forEach((tr) =>
    tr.classList.toggle("active", Number(tr.dataset.t) === t));
}

// The upgraded Film panel: surface what ADMIT actually proved for the selected
// epoch — exactly the projection Film v0.7 seals (admit.film_bytes_v7) plus the
// EpochControl applied this epoch. Read-only sidecar; changes no identity.
function drawAdmit(row) {
  const el = $("#admit-detail"); el.innerHTML = "";
  if (!row || !row.admit) return;
  const a = row.admit;
  const ev = (x) => `w${x.writer}·s${x.sequence}`;
  const ec = a.epoch_control || { set_rotor: {}, reset_fault: [] };
  const ecParts = [];
  Object.entries(ec.set_rotor || {}).forEach(([sp, r]) =>
    ecParts.push(`SetRotor <code>${sp}</code>=<code>${r.join(".")}</code>`));
  (ec.reset_fault || []).forEach((ob) =>
    ecParts.push(`ResetFault <code>${ob}</code>`));
  const faultBadges =
    (a.fact_capacity_fault ? `<span class="cap">fact overflow</span>` : "") +
    (a.receipt_capacity_fault ? `<span class="cap">receipt overflow</span>` : "") +
    (!a.fact_capacity_fault && !a.receipt_capacity_fault
      ? `<span class="cap ok">no overflow</span>` : "");
  const recTag = (s) =>
    `<span class="rec ${s}">${s}</span>`;
  el.innerHTML =
    `<div class="admit-head">ADMIT · epoch ${row.t} ` +
    `<span class="policy">${a.policy}</span> ${faultBadges}</div>` +
    `<div class="admit-ec"><span class="lbl">applied EpochControl</span> ` +
    `${ecParts.length ? ecParts.join(" · ") : "<em>none (idle / rejected)</em>"}</div>` +
    `<div class="admit-cols">` +
      `<div class="admit-col"><div class="lbl">observed facts (${a.facts.length})</div>` +
        (a.facts.length ? a.facts.map((f) =>
          `<div class="frow"><span class="ek">${ev(f)}</span> ` +
          `<code>${f.payload}</code> <span class="dg">d=${f.digest} pk=${f.payload_key}</span></div>`
        ).join("") : `<div class="frow"><em>none</em></div>`) + `</div>` +
      `<div class="admit-col"><div class="lbl">acceptance receipts (${a.receipts.length}) · immutable</div>` +
        (a.receipts.length ? a.receipts.map((r) =>
          `<div class="frow"><span class="ek">${ev(r)}</span> ` +
          `<span class="oc ${r.outcome.startsWith("Applied") ? "applied" : "rejected"}">${r.outcome}</span> ` +
          `<span class="dg">acc=${r.accepted_digest} @ep${r.accepted_epoch}</span></div>`
        ).join("") : `<div class="frow"><em>none</em></div>`) + `</div>` +
      `<div class="admit-col"><div class="lbl">derived recognition</div>` +
        (a.recognition.length ? a.recognition.map((g) =>
          `<div class="frow"><span class="ek">${ev(g)}</span> ${recTag(g.state)}</div>`
        ).join("") : `<div class="frow"><em>none</em></div>`) + `</div>` +
    `</div>`;
  el.scrollIntoView({ block: "nearest" });
}

// -------------------------------------------------------------- film + id
function drawFilm() {
  const tb = $("#film-body"); tb.innerHTML = "";
  state.epochs.forEach((r) => {
    const tr = document.createElement("tr"); tr.dataset.t = r.t;
    let nat = '<span class="nat-skip">—</span>';
    if (state.native && state.native.skipped) nat = '<span class="nat-skip">skip</span>';
    else if (state.native) {
      const e = state.native.epochs.find((x) => x.t === r.t);
      nat = e && e.match ? '<span class="nat-yes">✓</span>'
                         : '<span class="nat-no">✗</span>';
    }
    tr.innerHTML = `<td>${r.t}</td><td>${r.label}</td>` +
      `<td class="film-hash">${r.film.slice(0, 18)}…</td><td>${nat}</td>`;
    tr.onclick = () => showEpoch(r.t); tb.appendChild(tr);
  });
}
function drawProvenance(prov) {
  const el = $("#provenance"); el.innerHTML = "";
  if (!prov || !prov.length) return;
  prov.forEach((p) => {
    if (!p.policy) return; // only policy-governed names carry provenance
    const d = document.createElement("div"); d.className = "prov";
    d.innerHTML =
      `<div class="tag">named-rotor provenance · not sealed</div>` +
      `spinner <code>${p.spinner}</code> · rotor <code>${p.rotor_name}</code> ` +
      `@ n=${p.n} → <code>${p.value ? p.value.join(".") : "?"}</code>` +
      `<div class="note">policy <code>${p.policy}</code> is BUILD provenance; ` +
      `it never enters the sealed bytes. The id is geometry-dependent ` +
      `(value depends on n).</div>`;
    el.appendChild(d);
  });
}

// -------------------------------------------------------------- actions
async function doLower() {
  state.src = $("#wrl").value;
  setStatus("lowering…");
  const r = await api("/api/lower", { src: state.src });
  if (!r.ok) { setStatus(r.error, "err"); renderDiags([{ code: "LOWER", message: r.error, render: r.error }]); return; }
  $("#sem-id").textContent = r.semantic_artifact_id;
  $("#wrl-a").value = state.src;
  state.graph = r.graph;
  drawCanvas(r.graph);
  renderDiags(r.diagnostics);
  drawProvenance(r.provenance);
  setStatus("lowered ✓ " + r.semantic_artifact_id.slice(0, 14) + "…", "ok");
  return r;
}
function renderDiags(diags) {
  const el = $("#diagnostics"); el.innerHTML = "";
  if (!diags || !diags.length) {
    el.innerHTML = `<div class="diag clean">clean — no diagnostics</div>`; return;
  }
  diags.forEach((d) => {
    const div = document.createElement("div"); div.className = "diag";
    div.innerHTML = `<span class="code">${d.code}</span> ${d.message}` +
      (d.object_id ? ` <em>(${d.object_id})</em>` : "");
    el.appendChild(div);
  });
}
async function doFormat() {
  const r = await api("/api/lower", { src: $("#wrl").value });
  if (r.ok && r.formatted && !r.formatted.startsWith("(format")) {
    $("#wrl").value = r.formatted; setStatus("formatted ✓", "ok");
  } else setStatus("format unavailable", "err");
}
const _sleep = (ms) => new Promise((res) => setTimeout(res, ms));

// v0.6-1: a run/verify is a CANCELLABLE background job. Submit it, poll for
// state + progress, and surface a Cancel button while it runs. The compute is
// decoupled from these polls -- navigating away never aborts it. Returns the
// completed result payload, or null on failure/cancel (status already set).
function _showCancel(on) {
  const b = $("#btn-cancel");
  if (b) b.classList.toggle("hidden", !on);
}
// A PERSISTENT progress panel: it renders the job's monotonic state
// (queued → running → completed | failed | cancelled), its phase and epoch
// count, and stays visible after the job settles so the result is inspectable.
// Switching workspace views never clears it (PB11-PB13). Cancelled is styled
// distinctly from failed (PB12).
const _JOB_STATE_LABEL = {
  queued: "queued", running: "running", completed: "completed ✓",
  failed: "failed ✗", cancelled: "cancelled",
};
function renderJobProgress(kind, s) {
  const el = $("#job-progress");
  if (!el) return;
  const p = (s && s.progress) || {};
  const st = s ? s.state : "queued";
  const total = p.total || 0, done = p.done || 0;
  const pct = total ? Math.round((done / total) * 100) : (st === "completed" ? 100 : 0);
  el.className = "job-progress " + st;
  el.classList.remove("hidden");
  const ph = p.phase ? `<span class="jp-phase">${p.phase}</span>` : "";
  el.innerHTML =
    `<span class="jp-kind">${kind}</span>` +
    `<span class="jp-state">${_JOB_STATE_LABEL[st] || st}</span>` +
    ph +
    `<span class="jp-count">${done}/${total}</span>` +
    `<span class="jp-bar"><i style="width:${pct}%"></i></span>`;
}
async function runJob(kind, extra) {
  clearError();
  renderJobProgress(kind, { state: "queued", progress: {} });
  const sub = await api("/api/jobs",
    Object.assign({ kind, src: $("#wrl").value, scenario: state.scen }, extra));
  if (!sub.ok) { showError(sub, "job submit error"); return null; }
  const jid = sub.job.job_id; state.job = jid; _showCancel(true);
  try {
    for (;;) {
      const g = await api("/api/jobs/" + encodeURIComponent(jid));
      if (!g.ok) { showError(g, "job poll error"); return null; }
      const s = g.job;
      renderJobProgress(kind, s);
      if (s.state === "completed") { state.lastJob = s; return s.result; }
      if (s.state === "failed") {
        state.lastJob = s;
        if (s.error_presentation) showError(s);
        else setStatus(s.error || "job failed", "err");
        return null;
      }
      if (s.state === "cancelled") {
        state.lastJob = s; setStatus(`${kind} cancelled`, ""); return null;
      }
      await _sleep(220);
    }
  } finally { state.job = null; _showCancel(false); }
}
async function doCancel() {
  if (!state.job) return;
  await api("/api/jobs/" + encodeURIComponent(state.job) + "/cancel", {});
  setStatus("cancel requested…");
}
async function doRun() {
  // In Author mode the run is driven by the edited ScenarioV1; when it equals the
  // Golden preset this is byte-identical to omitting it (proven in slice 1).
  const r = await runJob("run");
  if (!r || !r.ok) { if (r && !r.ok) showError(r, "run error"); return; }
  clearError();
  state.epochs = r.epochs; state.native = null;
  $("#sem-id").textContent = r.semantic_artifact_id;
  if (r.scenario_digest) $("#scen-id").textContent = r.scenario_digest;
  $("#ep-range").max = r.epochs.length;
  drawFilm(); showEpoch(1);
  setStatus(`ran ${r.epochs.length} epochs (ic_ref) ✓`, "ok");
}
async function doVerify() {
  if (!state.epochs.length) await doRun();
  const r = await runJob("verify");
  if (!r || !r.ok) { if (r && !r.ok) showError(r, "verify error"); return; }
  clearError();
  state.native = r; if (r.scenario_digest) $("#scen-id").textContent = r.scenario_digest;
  drawFilm(); showEpoch(state.cur);
  if (r.skipped) setStatus("native gated off (ref-only)", "");
  else setStatus(r.parity ? "native ic32 == ic_ref ✓ (all epochs)"
                          : "NATIVE MISMATCH ✗", r.parity ? "ok" : "err");
}

// -------------------------------------------------------------- semantic diff
function renderDiff(r) {
  const v = $("#diff-verdict"), c = $("#diff-changes"); c.innerHTML = "";
  if (!r.ok) { v.className = "diff-verdict draft"; v.textContent = r.error; return; }
  const short = (s) => (s ? s.slice(0, 22) + "…" : "—");
  if (r.mode === "sealed") {
    const same = r.is_empty;
    v.className = "diff-verdict " + (same ? "same" : "moved");
    v.innerHTML =
      `<div>${same ? "identical identity — no semantic change"
                   : r.changes.length + " semantic change(s) — identity MOVES"}</div>` +
      `<div class="law">sem(A)=<code>${short(r.sem_a)}</code> ` +
      `${r.ids_equal ? "==" : "≠"} sem(B)=<code>${short(r.sem_b)}</code> · ` +
      `bridge law is_empty ⇔ ids_equal: ${r.bridge_holds ? "HOLDS ✓" : "VIOLATED ✗"}</div>`;
  } else {
    v.className = "diff-verdict draft";
    v.innerHTML =
      `<div>draft diff (tolerant · no identity claim) — ${r.changes.length} change(s)</div>` +
      `<div class="law">a side could not seal: ` +
      `<code>${_errMsg(r.seal_error || r.sem_a_error || r.sem_b_error) || "?"}</code></div>`;
  }
  r.changes.forEach((ch) => {
    const d = document.createElement("div"); d.className = "diff-change";
    d.innerHTML = `<span class="kind">${ch.kind}</span> ` +
      `<span class="key">${ch.key}</span>` +
      (ch.detail && ch.detail.length
        ? ` <span class="detail">: ${ch.detail.join(", ")}</span>` : "");
    c.appendChild(d);
  });
}
async function doDiff() {
  const a = $("#wrl").value, b = $("#wrl-b").value;
  $("#wrl-a").value = a;
  setStatus("diffing…");
  const r = await api("/api/diff", { a, b });
  renderDiff(r);
  if (!r.ok) { setStatus("diff error", "err"); return; }
  if (r.mode === "sealed")
    setStatus(r.is_empty ? "diff: identity unchanged ✓"
                         : `diff: ${r.changes.length} change(s), id moves`, "ok");
  else setStatus("draft diff (no id claim)", "");
}

// -------------------------------------------------------------- completion
async function doComplete() {
  const ta = $("#wrl");
  const r = await api("/api/complete", { src: ta.value, offset: ta.selectionStart });
  const box = $("#complete");
  if (!r.ok || !r.candidates.length || r.context === "NONE") {
    box.classList.add("hidden"); state.cands = []; return;
  }
  state.cands = r.candidates; state.sel = 0; state.prefix = r.prefix || "";
  box.innerHTML = `<div class="head">${r.context}${r.prefix ? " · " + r.prefix : ""}</div>` +
    r.candidates.map((c, i) =>
      `<div class="item ${i === 0 ? "sel" : ""}" data-i="${i}">${c}</div>`).join("");
  box.querySelectorAll(".item").forEach((it) =>
    (it.onclick = () => insertCand(Number(it.dataset.i))));
  box.classList.remove("hidden");
}
function insertCand(i) {
  const ta = $("#wrl"), c = state.cands[i]; if (c == null) return;
  const off = ta.selectionStart, pfx = state.prefix || "";
  const rest = c.slice(pfx.length);
  ta.value = ta.value.slice(0, off) + rest + ta.value.slice(off);
  ta.selectionStart = ta.selectionEnd = off + rest.length;
  $("#complete").classList.add("hidden"); ta.focus();
}

// -------------------------------------------------------------- scenario author
// The editable ScenarioV1 (run inputs). Every edit reposts to the PURE /api/scenario
// endpoint for a live ScenarioDigest + typed WRL_BAD_SCENARIO feedback (no run, no
// lock); "Run this scenario" folds it. The world's SemanticArtifactID is never
// touched by any scenario edit — only the ScenarioDigest moves (acceptance 1 & 2).
function spinnerNames() {
  return state.graph ? state.graph.nodes.filter((n) => n.role === "Spinner").map((n) => n.id) : [];
}
function orbNames() {
  return state.graph ? state.graph.nodes.filter((n) => n.role === "Orb").map((n) => n.id) : [];
}
function renumberScen() { state.scen.epochs.forEach((e, i) => (e.epoch = i + 1)); }
function nextWriter() {
  let m = 0;
  state.scen.epochs.forEach((e) => e.claims.forEach((c) => { if (c.writer_id > m) m = c.writer_id; }));
  return m + 1;
}
function selectScen(epoch, claim) { state.scenSel = { epoch, claim }; renderScenario(); }
function activeEpochIdx() {
  if (state.scenSel && state.scenSel.epoch != null) return state.scenSel.epoch;
  return Math.max(0, state.scen.epochs.length - 1);
}
function selectedClaim() {
  const s = state.scenSel;
  if (!s || s.claim == null || s.claim < 0) return null;
  const ep = state.scen.epochs[s.epoch];
  return ep ? ep.claims[s.claim] || null : null;
}

function renderScenario() {
  if (!state.scen) return;
  const sel = state.scenSel;
  const ro = state.mode === "demo";          // Demo = immutable preset, read-only
  const tb = document.createElement("tbody");
  state.scen.epochs.forEach((ep, ei) => {
    if (!ep.claims.length) {
      const tr = document.createElement("tr");
      tr.className = "ep-start idle" + (ro ? " readonly" : "") +
        (!ro && sel && sel.epoch === ei && sel.claim === -1 ? " sel" : "");
      tr.innerHTML = `<td>${ep.epoch}</td><td>${ep.label || ""}</td>` +
        `<td colspan="5">idle — no claims</td><td></td>`;
      if (!ro) tr.onclick = () => selectScen(ei, -1);
      tb.appendChild(tr);
      return;
    }
    ep.claims.forEach((c, ci) => {
      const isReset = c.operation === "ResetFault";
      // Demo mode renders every claim as immutable text (no inputs, no delete,
      // no selection) so a preset can NEVER be mutated in the regression view.
      if (ro) {
        const tr = document.createElement("tr");
        tr.className = (ci === 0 ? "ep-start " : "") + "readonly";
        const payTxt = isReset ? "—" : (c.payload.rotor || []).join(".");
        tr.innerHTML =
          `<td>${ci === 0 ? ep.epoch : ""}</td>` +
          `<td>${ci === 0 ? (ep.label || "") : ""}</td>` +
          `<td>${c.writer_id}</td><td>${c.sequence}</td>` +
          `<td>${c.operation}</td><td>${c.target}</td>` +
          `<td>${payTxt}</td><td></td>`;
        tb.appendChild(tr);
        return;
      }
      const tr = document.createElement("tr");
      tr.className = (ci === 0 ? "ep-start" : "") +
        (sel && sel.epoch === ei && sel.claim === ci ? " sel" : "");
      tr.innerHTML =
        `<td>${ci === 0 ? ep.epoch : ""}</td>` +
        `<td>${ci === 0 ? (ep.label || "") : ""}</td>` +
        `<td><input class="w" type="number" min="0" value="${c.writer_id}"></td>` +
        `<td><input class="s" type="number" min="0" value="${c.sequence}"></td>` +
        `<td><select class="op">` +
          `<option${isReset ? "" : " selected"}>SetRotor</option>` +
          `<option${isReset ? " selected" : ""}>ResetFault</option></select></td>` +
        `<td><input class="target" value="${c.target}"></td>` +
        `<td>${isReset ? '<span class="op-reset">—</span>'
          : `<input class="payload" value="${(c.payload.rotor || []).join(".")}">`}</td>` +
        `<td><button class="del" title="delete claim">✕</button></td>`;
      tr.querySelector("input.w").onchange = (e) => { c.writer_id = parseInt(e.target.value) || 0; pushScenario(); };
      tr.querySelector("input.s").onchange = (e) => { c.sequence = parseInt(e.target.value) || 0; pushScenario(); };
      tr.querySelector("select.op").onchange = (e) => {
        c.operation = e.target.value;
        if (c.operation === "ResetFault") { c.payload = {}; if (orbNames().length) c.target = orbNames()[0]; }
        else { c.payload = { rotor: [16, 0, 0, 0] }; if (spinnerNames().length) c.target = spinnerNames()[0]; }
        renderScenario(); pushScenario();
      };
      tr.querySelector("input.target").onchange = (e) => { c.target = e.target.value.trim(); pushScenario(); };
      const pay = tr.querySelector("input.payload");
      if (pay) pay.onchange = (e) => {
        c.payload = { rotor: e.target.value.split(".").map((x) => parseInt(x.trim()) || 0).slice(0, 4) };
        pushScenario();
      };
      tr.querySelector("button.del").onclick = (e) => {
        e.stopPropagation(); ep.claims.splice(ci, 1); state.scenSel = null; renderScenario(); pushScenario();
      };
      tr.querySelectorAll("input, select").forEach((el) =>
        el.addEventListener("click", (e) => e.stopPropagation()));
      tr.onclick = () => selectScen(ei, ci);
      tb.appendChild(tr);
    });
  });
  const table = $("#scenario-table");
  table.innerHTML = `<thead><tr><th>ep</th><th>label</th><th>w</th><th>s</th>` +
    `<th>op</th><th>target</th><th>payload</th><th></th></tr></thead>`;
  table.appendChild(tb);
}

async function pushScenario() {
  if (!state.scen) return;
  const r = await api("/api/scenario", { src: $("#wrl").value, scenario: state.scen });
  const el = $("#scen-digest");
  if (!r.ok) {
    el.className = "scen-digest err";
    el.innerHTML = `invalid scenario — <code>${r.error}</code>`;
  } else {
    el.className = "scen-digest ok";
    const sh = (s) => (s ? s.slice(0, 24) + "…" : "—");
    el.innerHTML =
      `ScenarioDigest <code>${r.scenario_digest}</code><br>` +
      `world <code>${sh(r.world_semantic_id)}</code> · ` +
      `ReplayBundle <code>${sh(r.replay_bundle_id)}</code>`;
    $("#scen-id").textContent = r.scenario_digest;
  }
}

function scnAddClaim() {
  const ep = state.scen.epochs[activeEpochIdx()]; if (!ep) return;
  if (ep.claims.length >= 4) { setStatus("epoch at MAX_BATCH (4)", "err"); return; }
  const n = nextWriter();
  ep.claims.push({ writer_id: n, sequence: n, operation: "SetRotor",
                   target: spinnerNames()[0] || "sp", payload: { rotor: [16, 0, 0, 0] } });
  selectScen(activeEpochIdx(), ep.claims.length - 1); pushScenario();
}
function scnAddReset() {
  const ep = state.scen.epochs[activeEpochIdx()]; if (!ep) return;
  if (ep.claims.length >= 4) { setStatus("epoch at MAX_BATCH (4)", "err"); return; }
  const n = nextWriter();
  ep.claims.push({ writer_id: n, sequence: n, operation: "ResetFault",
                   target: orbNames()[0] || "ob", payload: {} });
  selectScen(activeEpochIdx(), ep.claims.length - 1); pushScenario();
}
function scnAddIdle() {
  const ei = activeEpochIdx();
  state.scen.epochs.splice(ei + 1, 0, { epoch: 0, label: "idle", claims: [] });
  renumberScen(); selectScen(ei + 1, -1); pushScenario();
}
function scnRetransmit() {
  const c = selectedClaim();
  if (!c) { setStatus("select a claim to retransmit", "err"); return; }
  // EXACT envelope (same writer/sequence/payload) in a LATER epoch: the admit
  // first-receipt policy yields NO second effect (acceptance item 3).
  const copy = JSON.parse(JSON.stringify(c));
  state.scen.epochs.push({ epoch: 0, label: `retransmit w${c.writer_id}s${c.sequence}`, claims: [copy] });
  renumberScen(); selectScen(state.scen.epochs.length - 1, 0); pushScenario();
}
function scnEquivocate() {
  const c = selectedClaim();
  if (!c) { setStatus("select a claim to equivocate", "err"); return; }
  // SAME event key (writer/sequence), DIFFERENT payload → conflicting fact →
  // recognition becomes disputed while the immutable receipt stays (item 4).
  const copy = JSON.parse(JSON.stringify(c));
  if (copy.operation === "SetRotor") {
    const rr = (copy.payload.rotor || [0, 0, 0, 0]).slice(0, 4);
    rr[0] = (rr[0] || 0) + 1; copy.payload = { rotor: rr };
  }
  state.scen.epochs.push({ epoch: 0, label: `equivocate w${c.writer_id}s${c.sequence}`, claims: [copy] });
  renumberScen(); selectScen(state.scen.epochs.length - 1, 0); pushScenario();
}
async function loadScenario() {
  const r = await api("/api/scenario");           // GET → both immutable presets
  if (!r.ok) return;
  state.presets = r.presets || null;
  renderPresetOptions();
  applyPreset(state.scenPreset);
}
// Rebuild the #scn-preset options to match state.presets (the demo golden/bench
// pair, or a template's own scenario docs). Keeps the selector honest when the
// active preset set changes between the demo/library and a template.
function renderPresetOptions() {
  const sel = $("#scn-preset");
  if (!sel || !state.presets) return;
  const cur = state.scenPreset;
  sel.innerHTML = "";
  Object.values(state.presets).forEach((p) => {
    const o = document.createElement("option");
    o.value = p.id; o.textContent = p.label; sel.appendChild(o);
  });
  if (state.presets[cur]) sel.value = cur;
}
function applyPreset(id) {
  const p = state.presets && state.presets[id];
  if (!p) return;
  state.scenPreset = id;
  state.scen = JSON.parse(JSON.stringify(p.scenario));   // editable copy
  state.scenSel = null;
  const tag = $("#scen-mode");
  if (tag) tag.textContent = state.mode === "author"
    ? `${p.label} · editing a copy`
    : `${p.label} · preset (read-only)`;
  const sel = $("#scn-preset");
  if (sel) sel.value = id;
  renderScenario(); pushScenario();
}
async function scnResetPreset() {
  if (!state.presets) await loadScenario();
  else applyPreset(state.scenPreset);
  const p = state.presets && state.presets[state.scenPreset];
  setStatus(`scenario reset to ${p ? p.label : "preset"}`, "ok");
}

// Gesture buttons that mutate the scenario copy; disabled in Demo mode so a
// preset can never be edited in the regression view.
const GESTURE_IDS = ["#scn-add-claim", "#scn-add-reset", "#scn-add-idle",
                     "#scn-retransmit", "#scn-equivocate", "#scn-reset-preset"];
function setGesturesEnabled(on) {
  GESTURE_IDS.forEach((id) => { const b = $(id); if (b) b.disabled = !on; });
}
function setMode(m) {
  if (m !== "demo" && m !== "author") return;
  state.mode = m;
  $("#scn-mode-demo").classList.toggle("on", m === "demo");
  $("#scn-mode-author").classList.toggle("on", m === "author");
  setGesturesEnabled(m === "author");
  // Re-copy the pristine preset: switching to Demo discards edits, switching to
  // Author starts from a fresh editable copy.
  applyPreset(state.scenPreset);
  const p = state.presets && state.presets[state.scenPreset];
  const label = p ? p.label : "preset";
  const tag = $("#scen-mode");
  if (tag) tag.textContent = m === "demo"
    ? `${label} · preset (read-only)`
    : `${label} · editing a copy`;
  pushScenario();
}

// -------------------------------------------------------------- wiring
async function init() {
  const d = await api("/api/demo");
  state.src = d.src; $("#wrl").value = d.src;
  $("#wrl-a").value = d.src; $("#wrl-b").value = d.src;
  $("#btn-lower").onclick = doLower;
  $("#btn-format").onclick = doFormat;
  $("#btn-run").onclick = doRun;
  $("#btn-verify").onclick = doVerify;
  $("#btn-cancel").onclick = doCancel;
  $("#btn-diff").onclick = doDiff;
  $("#btn-apply").onclick = doApplyDraft;
  $("#btn-draft-undo").onclick = doDraftUndo;
  $("#btn-save").onclick = doSaveProject;
  $("#btn-commit").onclick = doCommit;
  $("#btn-reset").onclick = () => { $("#wrl").value = d.src; $("#wrl-b").value = d.src; boot(); };
  $("#lib-select").onchange = (e) => openSession(e.target.value);
  $("#lib-new").onclick = doNewProject;
  $("#lib-fork").onclick = doForkProject;
  $("#lib-rename").onclick = doRenameProject;
  $("#lib-trash").onclick = doTrashProject;
  $("#lib-restore").onclick = doRestoreProject;
  $("#lib-migrate").onclick = doMigrateProject;
  $("#lib-export").onclick = doExportProject;
  $("#lib-import").onclick = () => $("#lib-import-file").click();
  $("#lib-import-file").onchange = (e) => {
    const f = e.target.files[0]; e.target.value = ""; doImportProject(f);
  };
  $("#scn-add-claim").onclick = scnAddClaim;
  $("#scn-add-reset").onclick = scnAddReset;
  $("#scn-add-idle").onclick = scnAddIdle;
  $("#scn-retransmit").onclick = scnRetransmit;
  $("#scn-equivocate").onclick = scnEquivocate;
  $("#scn-reset-preset").onclick = scnResetPreset;
  $("#scn-mode-demo").onclick = () => setMode("demo");
  $("#scn-mode-author").onclick = () => setMode("author");
  setGesturesEnabled(state.mode === "author");   // Demo default → gestures off
  // v0.7-1 onboarding wiring (all presentation-only)
  $("#view-author").onclick = () => setView("author");
  $("#view-evidence").onclick = () => setView("evidence");
  $("#btn-home").onclick = openChooser;   // v0.7-1.1: reopen the chooser explicitly
  $("#btn-guide").onclick = () => guideOpen(false);
  $("#gr-next").onclick = guideNext;
  $("#gr-back").onclick = guideBack;
  $("#gr-dismiss").onclick = guideDismiss;
  $("#gr-advanced").addEventListener("toggle",
    (e) => LS.set(TOUR_ADV, e.target.open ? "1" : "0"));
  $("#btn-make-copy").onclick = doMakeCopy;
  // first-run landing actions (v0.7-3: the fresh path is the template chooser;
  // its Explore/Use buttons are wired per-card in renderTemplateCards)
  $("#fr-explore-alt").onclick = enterExplore;   // resume path: "explore demo instead"
  $("#fr-open").onclick = () => { hideFirstRun(); const s = $("#lib-select"); if (s) s.focus(); };
  $("#fr-choose").onclick = () => { hideFirstRun(); const s = $("#lib-select"); if (s) s.focus(); };
  $("#fr-open-last").onclick = () => {
    const ov = $("#first-run"); const pid = ov ? ov.dataset.lastId : "";
    hideFirstRun(); if (pid) openSession(pid);
  };
  restoreView();                                 // apply saved Author/Evidence pref
  $("#scn-preset").onchange = (e) => applyPreset(e.target.value);
  $("#scn-run").onclick = () => { doRun(); };
  $("#ep-range").oninput = (e) => showEpoch(Number(e.target.value));
  $("#ep-prev").onclick = () => showEpoch(Math.max(1, state.cur - 1));
  $("#ep-next").onclick = () => showEpoch(Math.min(state.epochs.length, state.cur + 1));
  const ta = $("#wrl");
  ta.addEventListener("input", () => { clearTimeout(state.t); state.t = setTimeout(doComplete, 120); });
  ta.addEventListener("keydown", (e) => {
    const box = $("#complete");
    if (box.classList.contains("hidden")) return;
    if (e.key === "Escape") box.classList.add("hidden");
    else if (e.key === "Tab" || e.key === "Enter") {
      if (state.cands.length) { e.preventDefault(); insertCand(state.sel); }
    } else if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      state.sel = (state.sel + (e.key === "ArrowDown" ? 1 : -1) + state.cands.length) % state.cands.length;
      box.querySelectorAll(".item").forEach((it, i) => it.classList.toggle("sel", i === state.sel));
    }
  });
  document.addEventListener("click", (e) => {
    if (!e.target.closest("#complete") && e.target !== ta) $("#complete").classList.add("hidden");
  });
  boot();
}
// v0.6-4 release self-check: hit /api/health at boot. The server re-lowers the
// demo world fresh and confirms it reproduces DEMO_WORLD_SEMANTIC_ID; if the
// identity spine ever fails to reproduce, surface a hard, visible warning
// instead of silently serving a broken build. Tags the header version with the
// server-reported bench version + cache occupancy on success.
async function checkHealth() {
  try {
    const h = await (await fetch("/api/health")).json();
    const ver = $(".ver");
    if (!h.identity_ok) {
      if (ver) ver.classList.add("bad");
      setStatus("release self-check FAILED — demo world no longer reproduces its identity", "err");
      return;
    }
    if (ver) {
      ver.textContent = h.bench_version;
      ver.title = "release self-check ✓ · identity_ok · prog cache "
        + h.caches.prog.size + "/" + h.caches.prog.cap
        + " · traj cache " + h.caches.traj.size + "/" + h.caches.traj.cap;
    }
  } catch (e) { /* health is a non-blocking release surface */ }
}

async function boot() {
  // v0.7-1.1 SHELL-FIRST startup. Resolve the startup PATH from CHEAP metadata
  // only — project list, last-session pointer, recovery status, onboarding
  // preference. We do NOT lower or run any world here; the chosen path
  // (Explore / Open / Create / Recover) does its own expensive fold. This fixes
  // the v0.7-1 defect where the demo folded under a hidden overlay before the
  // user could choose, and where Explore could show the last project.
  await loadProjects();
  await loadTemplates();
  const sess = await api("/api/session");
  const lastId = (sess.ok && sess.last_project_id
    && state.projects.some((p) => p.project_id === sess.last_project_id))
    ? sess.last_project_id : null;
  const tourSeen = LS.get(TOUR_SEEN, "0") === "1";

  // Precedence: recovery available → recovery choice; else last project →
  // auto-restore (after onboarding) / resume chooser (first launch); else the
  // fresh first-run launcher. Recovery inspection for the last project happens
  // BEFORE that project is ever run.
  let recoveryPending = false;
  if (lastId) {
    const rs = await api("/api/recovery/status?session_id="
                         + encodeURIComponent(lastId));
    if (rs.ok && (rs.recovery.state === "recovery_available"
                  || rs.recovery.state === "recovery_stale")) {
      recoveryPending = true;
      state.session = lastId;
      state.recovery = rs.recovery; renderRecovery();
      await promptRecovery(rs.recovery.state === "recovery_stale");  // before any run
      await openSession(lastId);           // then load + run the resolved project
    }
  }
  if (!recoveryPending) {
    if (lastId && tourSeen) {
      await openSession(lastId);           // auto-restore, NO modal (v0.6-2 behaviour)
      setStatus(`resumed last project ${lastId} ✓`, "ok");
    } else if (lastId) {
      showFirstRun(true, lastId);          // first launch after a project: resume chooser
    } else {
      showFirstRun(false);                 // fresh store → launcher, nothing folded
    }
  }
  await checkHealth();   // v0.6-4 release self-check (shallow — folds nothing)
}
init();
