/**
 * <amp-nav> — shared top navigation for the [&] Protocol / Ampersand Box Design portfolio.
 *
 * Usage:
 *   <amp-nav property="graphonomous"></amp-nav>
 *   <script type="module" src="/amp-nav.js"></script>
 *
 * Attributes:
 *   property   — one of the canonical property ids (see PROPERTY_MAP below).
 *                Drives the "you are here" highlight. Omit if none apply.
 *                It also selects the placement band (see PLACEMENT): a site at
 *                place 2 or 3 gets a strip above the bar saying where it sits
 *                in the ComputeDriven world, and a site at place 4 gets no nav
 *                at all. A property with no PLACEMENT entry renders the bar
 *                alone, exactly as before.
 *   theme      — "dark" (default) | "light" | "warrant" | "auto"
 *                "warrant" is the legal-vellum (dark) house style for
 *                topology-as-warrant.html — dark ink bg, parchment text, gold accent.
 *   base       — optional override for the portfolio origin used in menu links
 *                (e.g. "https://ampersandboxdesign.com"). Defaults to the link
 *                targets defined in LINKS.
 *
 * Theming:
 *   Expose CSS custom properties on the host element:
 *     --amp-nav-bg, --amp-nav-fg, --amp-nav-muted, --amp-nav-accent,
 *     --amp-nav-border, --amp-nav-hover, --amp-nav-cta-bg, --amp-nav-cta-fg,
 *     --amp-nav-font, --amp-nav-height
 *
 *   Example:
 *     amp-nav { --amp-nav-accent: #4af5c6; }
 *
 * Versioning:
 *   Single source of truth: ampersand-nav/src/amp-nav.js in the ProjectAmp2 repo.
 *   Deploy to each property via scripts/sync-nav.sh.
 *
 * License: MIT (Ampersand Box Design)
 */

// 0.12.0 — 2026-08-25. T&R registered as a property: a LINKS row, a PROPERTY_MAP
// entry, and the Stack menu's first feature banner. Deliberately NO PLACEMENT
// entry — see the note in that table for why the band was removed. Bumped
// rather than left at 0.11.0 because this constant is published as
// `window.__ampNavVersion` and is the ONLY way to tell, from outside, which nav
// a deployed site is actually serving. Several targets live in their own
// repositories and deploy on their own schedule, so "does this site know about
// T&R yet" is a question that gets asked from a browser console, and a stale
// version number is the one thing that makes it unanswerable.
const VERSION = "0.12.0";

// The wordmark in the bar's brand link. Named rather than typed inline because
// the placement band suppresses itself against it (see `renderPlacement`), and
// a rule that compares a rendered string to a different literal of the same
// string is one rename away from silently doing nothing.
const BRAND_NAME = "Ampersand Box Design";

// Canonical URLs per property. The "href" is the destination used in cross-property
// links; the "label" is what visitors see in the dropdown.
//
// Ecosystem products carry a {status, tier} pair (status = display string,
// tier = one of "shipped" | "alpha" | "spec") so the Compose menu can show
// honest version/maturity at-a-glance. Source of truth: STACK_COMPLETION.md.
const LINKS = {
  // Code — the orchestration console for coding agents (repo: c-u-l8er/code).
  // Leads Products: it is the surface a visitor actually drives the stack from.
  // Renamed twice on 2026-08-22, both on Travis's word: the product shipped here as "Code" at
  // code.traaviis.com became "[&] Super", then "Super (CD)". The LINKS key moved with the first
  // rename (`code` → `super`) and stays put through the second — the key is an identifier, and
  // churning it would break every PROPERTY_MAP entry and site declaration for a label change.
  // Note that super/AGENT_SUPER_APP_BLUEPRINT.md Rev F still records the product as "[&] SUPER"
  // and the home as super.TRAAVIIS.com; the name and domain here are the ones Travis gave, and the
  // blueprint is the document that is behind on both.
  super: {
    label: "Super (CD)",
    tagline: "The super-surface — control, placement, evidence and authority above interchangeable engines",
    href: "https://super.computedriven.com",
    status: "in dev",
    tier: "alpha",
  },
  // The operating system, and the only artifact in this table you can download and boot. It got
  // its own domain and repository on 2026-08-25: it had been `computedriven.com` itself, where it
  // was ~80% of the root page's body copy on a domain with three products. The root is now a
  // product index and this is the product.
  //
  // No `tr` key existed here before that date, which is why the Stack menu's banner could not be
  // written until now — `renderBanner` resolves `LINKS[banner.key]` and returns "" for a miss, so
  // a banner naming an absent key renders as silence rather than an error.
  tr: {
    label: "T&R",
    tagline: "The operating system — FreeBSD 15 from pkgbase, carrying its own verifier",
    href: "https://tr.computedriven.com",
    status: "v0.3",
    tier: "shipped",
  },
  // The paid funnel. It is a real deployed site (index / pricing / architecture / security /
  // status) being built in a parallel session, which is why it is listed but carries no rung
  // claim here: this file records where a thing is, and that file records how far along it is.
  cloud: {
    label: "[World] Cloud",
    tagline: "One world, any machine — worlds hosted, forked and restored without provisioning",
    href: "https://cloud.computedriven.com",
    status: "in dev",
    tier: "alpha",
  },

  // Cognitive Primitives — memory / knowledge / reasoning / time / space
  graphonomous: {
    label: "Graphonomous",
    tagline: "Agent memory substrate",
    href: "https://graphonomous.com",
    status: "v0.4.3",
    tier: "shipped",
  },
  bendscript: {
    label: "BendScript",
    tagline: "Graph-first document protocol",
    href: "https://bendscript.com",
    status: "v0.1.0-alpha",
    tier: "alpha",
  },
  deliberatic: {
    label: "Deliberatic",
    tagline: "Argumentation protocol",
    href: "https://deliberatic.com",
    status: "spec only",
    tier: "spec",
  },
  ticktickclock: {
    label: "TickTickClock",
    tagline: "Temporal intelligence",
    href: "https://ticktickclock.com",
    status: "spec only",
    tier: "spec",
  },
  geofleetic: {
    label: "GeoFleetic",
    tagline: "Spatial intelligence",
    href: "https://geofleetic.com",
    status: "spec only",
    tier: "spec",
  },

  // Agent Platform — building, governance, marketplace, spec discipline
  agentelic: {
    label: "Agentelic",
    tagline: "Premium agent builder",
    href: "https://agentelic.com",
    status: "v0.1.0",
    tier: "shipped",
  },
  // Tagline names the direction, status names what is actually serving. Both
  // apps are deployed on Fly (app.fleetprompt.com / app.specprompt.com) and
  // both are the design the landing pages now supersede — so the tier stays
  // "shipped" (true: they run) while the status refuses to let "shipped" be
  // read as "the replay-gated / content-addressed thing ships". It does not.
  fleetprompt: {
    label: "FleetPrompt",
    tagline: "Replay-gated agent registry",
    href: "https://fleetprompt.com",
    status: "live · prior design",
    tier: "shipped",
  },
  specprompt: {
    label: "SpecPrompt",
    tagline: "Content-addressed spec layer",
    href: "https://specprompt.com",
    status: "live · prior design",
    tier: "shipped",
  },
  delegatic: {
    label: "Delegatic",
    tagline: "Agent governance kernel",
    href: "https://delegatic.com",
    status: "v0.1.0",
    tier: "shipped",
  },
  agentromatic: {
    label: "AgenTroMatic",
    tagline: "Deliberation orchestrator",
    href: "https://agentromatic.com",
    status: "spec only",
    tier: "spec",
  },

  // Runtime — execution, layout, hosting
  runefort: {
    label: "RuneFort",
    tagline: "Layout protocol & control plane",
    href: "https://runefort.com",
    status: "v0.1.0-alpha",
    tier: "alpha",
  },
  webhost: {
    label: "WebHost.Systems",
    tagline: "Hosting + Supabase dashboard",
    href: "https://webhost.systems",
    status: "in dev",
    tier: "alpha",
  },

  // Academy — the institutional loop: systems that teach & prove cognition.
  //
  // Every entry below resolves to a live page. Cloudflare Pages serves this site extensionless
  // — /read is canonical and /read.html 308-redirects to it — so the hrefs carry no extension.
  // Pointing at the .html form worked but advertised a redirect from 22 sites, which is the same
  // canonical hygiene the atlas crawl flagged (finding A6). Supervisor was a nav peer until 2026-08-10 and is now a
  // spec doc under Docs — it is a specification, not a surface.
  //
  // Statuses are deliberately unflattering. The whole category is a prototype, and a menu that
  // read "shipped" across a placeholder would be the exact failure the pages themselves refuse.
  academy_home: {
    label: "Academy",
    tagline: "The institutional loop — teach, apply, prove",
    href: "https://academy.opensentience.org",
    status: "prototype",
    tier: "spec",
  },
  academy_read: {
    label: "Read",
    tagline: "Grounded articles — every sentence shows its source",
    href: "https://academy.opensentience.org/read",
    status: "prototype",
    tier: "spec",
  },
  academy_practice: {
    label: "Practice",
    tagline: "Real repository tasks, not exercises",
    href: "https://academy.opensentience.org/practice",
    status: "blocked",
    tier: "spec",
  },
  academy_prove: {
    label: "Prove",
    tagline: "Signed, replayable evidence — six proof gates",
    href: "https://academy.opensentience.org/prove",
    status: "prototype",
    tier: "spec",
  },
  academy_refusals: {
    label: "The refusal log",
    tagline: "Pages we declined to write, and what was missing",
    href: "https://academy.opensentience.org/refusals",
    status: "prototype",
    tier: "spec",
  },
  academy_method: {
    label: "Method",
    tagline: "How Academy is allowed to be wrong",
    href: "https://academy.opensentience.org/method",
    status: "prototype",
    tier: "spec",
  },
  // Rendered by the Academy promo band, not as a column item — see CATEGORIES.academy.promo.
  // It still needs a LINKS entry so `property="masterclass"` resolves and the band can mark
  // itself current when the reader is already on the page.
  // Extensionless. This pointed at `…-masterclass.html` until 2026-08-22, which Pages answers with a
  // 308 to the extensionless form — so every click from all 26 nav targets was advertising a redirect.
  // Same canonical hygiene the atlas crawl flagged as finding A6, and the same rule
  // `compose_masterclass` below was already written to.
  masterclass: {
    label: "The New SDLC, Made Formal",
    tagline: "The long read — every claim with the command that would break it",
    href: "https://ampersandboxdesign.com/agentic-engineering-masterclass",
    status: "live",
    tier: "shipped",
  },
  // The Compose promo band's target — same arrangement as `masterclass` above: rendered by the
  // band, not as a column item, but it still needs a LINKS entry so `property="compose_masterclass"`
  // resolves and the band can mark itself current. Extensionless on purpose: Pages serves
  // capability-composition-masterclass.html at this path, and the slug targets the phrase people
  // search for ("capability composition") rather than the page's title.
  compose_masterclass: {
    label: "Composition Is Not a List",
    tagline: "The long read — two operators, the laws they carry, and three that still fail",
    href: "https://ampersandboxdesign.com/capability-composition-masterclass",
    status: "live",
    tier: "shipped",
  },

  // ---- The Factory — the [&] surface reframed 2026-08-22 -------------------
  //
  // ampersandboxdesign.com used to lead with box-and-box ("the kernel for AI operating systems").
  // It now leads with the production architecture the kernel is the constitution OF, and these
  // entries are that surface. Every href below resolves to a page that exists in
  // AmpersandBoxDesign/site/ — the standing rule from "Point the nav at URLs that exist" and
  // "six entries, six pages that exist" applies here and was checked file-by-file.
  //
  // Extensionless throughout: Pages serves <name>.html at /<name> and 308s the .html form.
  factory_home: {
    label: "The Worldware Factory",
    tagline: "Parallelize the work · prove the assemblies · formalize the joins",
    href: "https://ampersandboxdesign.com/",
  },
  factory_unboxed: {
    label: "Unboxed",
    tagline: "Why a faster boxed process is still a boxed process",
    href: "https://ampersandboxdesign.com/#unboxed",
  },
  factory_join: {
    label: "The marriage station",
    tagline: "Two assemblies join, or are refused with a reason — live",
    href: "https://ampersandboxdesign.com/#compose",
  },
  factory_floor: {
    label: "The factory floor",
    tagline: "18 cells, each carrying the rung it has actually reached",
    href: "https://ampersandboxdesign.com/factory",
  },
  factory_worldware: {
    label: "Worldware",
    // Was "The category above software — a world is the machine, 10 GB to 10 TB". That range is
    // the CURRENT ComputeDriven storage envelope, not the definition of the category, and welding
    // the two together meant every surface quoting this tagline was deriving an ontology from a
    // pricing table. The pages had already been separated; this string had not. Corrected
    // 2026-08-22 on outside review. The sizes still appear — as today's tiers, in the world-sizing
    // panel that computes prices from them, which is the one place they are a fact about anything.
    tagline: "The category above software — software whose unit of operation is a world",
    href: "https://ampersandboxdesign.com/#worldware",
  },
  factory_constitution: {
    label: "The eight rungs",
    tagline: "can it ▸ may it ▸ should it ▸ can it stay true",
    href: "https://ampersandboxdesign.com/#constitution",
  },
  // ComputeDriven is place 1 in PLACEMENT (`computedriven: { place: 1 }`) — that entry drives the
  // placement band and is NOT a LINKS row, so a column item pointing at "computedriven" resolved
  // to nothing. This is the LINKS row. Distinct key on purpose: the two objects are unrelated and
  // sharing a name across them is how the dead reference happened in the first place.
  computedriven_room: {
    label: "ComputeDriven",
    tagline: "The control room — where a human observes, operates and evolves a world",
    href: "https://computedriven.com",
  },

  // ---- Masterclasses — five pages, five that exist ------------------------
  // `masterclass` and `compose_masterclass` above are the first two; they keep their existing keys
  // because the Academy and Compose promo bands resolve `property=` against them.
  masterclasses: {
    label: "All five, and how they fit",
    tagline: "The curriculum as a map — which machine each one teaches",
    href: "https://ampersandboxdesign.com/masterclasses",
  },
  factory_masterclass: {
    label: "The Worldware Factory",
    tagline: "AI factories — the join is the whole problem",
    href: "https://ampersandboxdesign.com/ai-factories-masterclass",
    status: "live",
    tier: "shipped",
  },
  verification_masterclass: {
    label: "Proof as a Production Step",
    tagline: "Continuous verification — 2000 trials, and what they don't buy",
    href: "https://ampersandboxdesign.com/continuous-verification-masterclass",
    status: "live",
    tier: "shipped",
  },
  // Retitled and repointed 2026-08-22. "The Unit Is the World" spent two of its seven sections on
  // an internal vocabulary correction and an unresolved architecture question — true, but a
  // curriculum page is not a defect register, and a reader's first encounter with the idea was
  // arriving as a status meeting about it. Both topics are still published, on /factory. The old
  // URL is a redirect stub, not a deletion. Key left as `world_masterclass` so every property
  // declaring it keeps highlighting without a coordinated rename across sites.
  world_masterclass: {
    label: "Worlds That Pay For Themselves",
    tagline: "What a world costs, what rides along free, and what you can sell on top of one",
    href: "https://ampersandboxdesign.com/world-economics-masterclass",
    status: "live",
    tier: "shipped",
  },
  // Workbench is the proof layer, not a peer product: a run here is what turns practice into a
  // signed, replayable SkillBundle that PRISM can score. It is the one thing in this category
  // that actually runs.
  workbench: {
    label: "Workbench",
    tagline: "Record a session you already ran — it becomes a scored SkillBundle",
    href: "https://workbench.opensentience.org",
    status: "v0.4.0-alpha",
    tier: "alpha",
  },

  // Protocols — the three-protocol stack ([&] + PULSE + PRISM)
  ampersand: {
    label: "[&] Protocol",
    tagline: "Structural composition",
    href: "https://ampersandboxdesign.com/protocol",
  },
  pulse: {
    label: "PULSE",
    tagline: "Temporal algebra for loops",
    href: "https://pulse.opensentience.org",
  },
  prism: {
    label: "PRISM",
    tagline: "Adversarial evaluation discipline",
    href: "https://prism.opensentience.org",
  },
  scope: {
    label: "SCOPE",
    tagline: "Spatial algebra — regions + claims",
    href: "https://opensentience.org/scope.html",
    status: "v0.1 draft",
    tier: "spec",
  },
  invariant_arithmetic: {
    label: "Invariant Arithmetic",
    tagline: "Rungs 1–2 (alethic · axiological)",
    href: "https://opensentience.org/invariant-arithmetic.html",
  },
  trvm: {
    label: "TRVM",
    tagline: "Coordination-free interaction-calculus runtime",
    href: "https://trvm.traaviis.com",
    status: "alpha",
    tier: "alpha",
  },

  // The execution substrate chain: WRLM proposes → WRL seals → TRVM reduces →
  // TRAAVIIS admits. TRVM itself is listed under Protocols (above); the other
  // three surface here, in Research.
  wrl: {
    label: "WallRiderLang",
    tagline: "An executable topology language whose meaning is a hash",
    href: "https://wrl.traaviis.com",
    status: "Core 0.1.2",
    tier: "alpha",
  },
  wrlm: {
    label: "WRLM",
    tagline: "The generative cortex — a proposer over sealed worlds",
    href: "https://github.com/c-u-l8er/TRVM/blob/main/WRLM_RESEARCH_BRIEF.md",
    status: "steps 1–2",
    tier: "alpha",
  },

  // The arithmetic ladder — box-and-box governance kernel (8 rungs, one bridge) + the six
  // living-paper rung pages.
  //
  // NOTE ON COUNTS. This comment used to carry the law total and the history of getting it wrong:
  // 116 in three places, re-derived to 118 on 2026-08-15, and 118 again in the tagline below. On
  // 2026-08-22 the compose runtime gained five laws and every one of those numbers became stale in
  // the same instant — the fourth time. Counts are OUT of this file now. scripts/check-law-counts.mjs
  // derives them from the suites and gates every page that publishes one; the nav is a standalone
  // bundle that cannot run a test suite, so a number here is a number it will eventually ship wrong.
  // The rung count (8) stays: it is a structural fact about the ladder, not a measurement.
  box_and_box: {
    label: "box-and-box",
    tagline: "The governance kernel · 8 rungs · one bridge · npm",
    href: "https://opensentience.org/box-and-box/",
    status: "v0.10.0",
    tier: "shipped",
  },
  weave: {
    label: "Cost is a Type",
    tagline: "Weave — the resource rung as a static cost certificate",
    href: "https://weave.opensentience.org",
  },
  laws: {
    // Was `label: "The 118 laws"`. The count came out of the label on 2026-08-22, the day the
    // compose runtime gained five laws (CD1–CD5, missing ≠ universal) and 118 became 123 — the
    // third time a hand-typed law count in this file has gone stale. The nav is a standalone
    // bundle shipped to every site in the portfolio; it cannot run the suites, so it cannot
    // DERIVE the number, and a number it cannot derive is a number it will eventually ship wrong.
    // laws.html derives and prints the total. This label stops competing with it.
    label: "The compose laws",
    tagline: "Conformance — every law, live",
    // Extensionless: /laws is 200, /laws.html is a 308 to it. Fixed 2026-08-22 alongside
    // `masterclass`, which had the same defect.
    href: "https://ampersandboxdesign.com/laws",
  },
  arith_deontic: {
    label: "Deontic Arithmetic",
    tagline: "Rung 3 — what's allowed (norms ▸ certificate)",
    href: "https://opensentience.org/deontic-arithmetic.html",
  },
  arith_temporal: {
    label: "Temporal Arithmetic",
    tagline: "Rung 4 — safe over time (LTL ▸ supervise)",
    href: "https://opensentience.org/temporal-arithmetic.html",
  },
  arith_reflexive: {
    label: "Reflexive Arithmetic",
    tagline: "Rung 5 — may the rules change (entrenched core)",
    href: "https://opensentience.org/reflexive-arithmetic.html",
  },
  arith_epistemic: {
    label: "Epistemic Arithmetic",
    tagline: "Rung 6 — do we know enough (knows ▸ believes)",
    href: "https://opensentience.org/epistemic-arithmetic.html",
  },
  arith_strategic: {
    label: "Strategic Arithmetic",
    tagline: "Rung 7 — who can ensure it (coalition power)",
    href: "https://opensentience.org/strategic-arithmetic.html",
  },
  arith_resource: {
    label: "Resource Arithmetic",
    tagline: "Rung 8 — can we afford it (affine ledger)",
    href: "https://opensentience.org/resource-arithmetic.html",
  },
  // Was "64 of 116 live". Both halves were stale and the page had moved on:
  // playground.html now imports SUITES from /box-and-box/test/laws.mjs and runs
  // the real 103-law core suite in the browser, so there is no "64" any more and
  // no subset denominator to fix. Read from the page, 2026-08-15.
  arith_playground: {
    label: "Playground",
    tagline: "The 103-law core suite, run live in your browser",
    href: "https://opensentience.org/playground.html",
  },

  // Research / Runtime — OS-001..011 protocol family
  opensentience: {
    label: "OpenSentience",
    tagline: "11 open research protocols",
    href: "https://opensentience.org",
    status: "11 protocols",
    tier: "shipped",
  },
  // `kappa` (an anchor, opensentience.org/#kappa) was deleted 2026-08-22. It was in no menu and
  // had been superseded by proof_kappa, the real machine-checked page in the Results column —
  // but PROPERTY_MAP still routed the `kappa` property to it, so a page declaring itself `kappa`
  // asked the bar to highlight a row that renders nowhere and got a silent no-op. Found by the
  // first run of scripts/check-nav.mjs; the property now points at proof_kappa.

  // Research — the Periodic Table of Agent Invariants + per-invariant proofs.
  // Only the six PROVED invariants get a proof page; the table holds all 43.
  invariants: {
    label: "Periodic Table of Invariants",
    tagline: "43 agent invariants, by family",
    href: "https://opensentience.org/invariants.html",
  },
  // Sits beside `invariants` on purpose, and NOT under Compose. Compose means
  // "capabilities you combine into an agent system" and its Runtime column
  // means "it runs" — a2atraffic runs nothing (its own ledger prints
  // `messages witnessed: 0` and `surface_rung: spec`), so a Runtime slot would
  // put the nav in direct contradiction with the page underneath it. What it
  // actually is, is the outward-facing half of the same census `invariants` is
  // the inward-facing half of: its crosswalk section joins its six-dimension
  // matrix cell-by-cell to that very page. Two entries that cite each other
  // belong in one column. Compose → Runtime becomes correct the day a receipt
  // exists in its witness log, and not before — the same rule the site applies
  // to its own capability cards.
  a2atraffic: {
    label: "A2A Traffic",
    tagline: "The A2A protocol, and what it cannot express",
    href: "https://a2atraffic.com",
  },
  topology_warrant: {
    label: "Topology as Warrant",
    tagline: "Structure earns the right to act",
    href: "https://opensentience.org/topology-as-warrant.html",
  },
  proof_kappa: {
    label: "κ — Cyclicity",
    tagline: "Proved · 1.9M systems, machine-checked",
    href: "https://opensentience.org/proofs/kappa.html",
  },
  proof_phase: {
    label: "π — Phase ordering",
    tagline: "Proved · property-tested",
    href: "https://opensentience.org/proofs/phase-ordering.html",
  },
  proof_nocycles: {
    label: "⊘ — No cycles in authority",
    tagline: "Proved · Delegatic kernel",
    href: "https://opensentience.org/proofs/no-cycles.html",
  },
  proof_monotonic: {
    label: "⊆ — Monotonic inheritance",
    tagline: "Proved · Delegatic kernel",
    href: "https://opensentience.org/proofs/monotonic-inheritance.html",
  },
  proof_deny: {
    label: "⊥ — Deny by default",
    tagline: "Proved · Delegatic kernel",
    href: "https://opensentience.org/proofs/deny-default.html",
  },
  proof_append: {
    label: "⊕ — Append-only audit",
    tagline: "Proved · Delegatic kernel",
    href: "https://opensentience.org/proofs/append-only.html",
  },

  // Docs — quick-jumps into the unified stack-docs atlas (docs.ampersandboxdesign.com),
  // a single filesystem-mirror site covering every project. Rather than linking out to
  // per-product subdomains, these deep-link to the hottest subjects in the stack.
  d_home: {
    label: "Stack docs home",
    tagline: "Every doc, mirrored from the repo",
    href: "https://docs.ampersandboxdesign.com",
  },
  d_index: {
    label: "[&] Protocol docs",
    tagline: "The protocol documentation hub",
    href: "https://docs.ampersandboxdesign.com/#/AmpersandBoxDesign/docs/index.md",
  },
  d_eco: {
    label: "Ecosystem overview",
    tagline: "Every product in the stack, at a glance",
    href: "https://docs.ampersandboxdesign.com/#/ECOSYSTEM.md",
  },
  d_arch: {
    label: "Architecture",
    tagline: "How the core artifacts fit together",
    href: "https://docs.ampersandboxdesign.com/#/AmpersandBoxDesign/docs/architecture.md",
  },
  d_compose: {
    label: "Capability composition",
    tagline: "[&] structural composition (CC2)",
    href: "https://docs.ampersandboxdesign.com/#/AmpersandBoxDesign/docs/CC2-capability-composition.md",
  },
  d_three: {
    label: "The three-protocol stack",
    tagline: "[&] · PULSE · PRISM, working together",
    href: "https://docs.ampersandboxdesign.com/#/PULSE/docs/THREE_PROTOCOL_STACK.md",
  },
  d_memory: {
    label: "Graphonomous — memory",
    tagline: "The continual-learning engine",
    href: "https://docs.ampersandboxdesign.com/#/graphonomous/docs/spec/README.md",
  },
  d_prism: {
    label: "PRISM — evaluation",
    tagline: "Benchmark what's broken & what fits",
    href: "https://docs.ampersandboxdesign.com/#/opensentience.org/docs/spec/OS-009-PRISM-SPECIFICATION.md",
  },
  d_govern: {
    label: "&govern — governance",
    tagline: "Policy, identity, telemetry, cost",
    href: "https://docs.ampersandboxdesign.com/#/AmpersandBoxDesign/docs/capabilities/govern.md",
  },
  d_quickstart: {
    label: "Quickstart",
    tagline: "Run the [&] reference CLI in five minutes",
    href: "https://docs.ampersandboxdesign.com/#/AmpersandBoxDesign/docs/quickstart.md",
  },
  d_faq: {
    label: "FAQ",
    tagline: "Straight answers to the common questions",
    href: "https://docs.ampersandboxdesign.com/#/AmpersandBoxDesign/docs/faq.md",
  },
  d_umbrella: {
    label: "The [&] umbrella",
    tagline: "One pipeline: declare → compose → govern → observe",
    href: "https://docs.ampersandboxdesign.com/#/AmpersandBoxDesign/docs/UMBRELLA.md",
  },
  d_bendscript: {
    label: "BendScript — documents",
    tagline: "The graph-first doc protocol these pages run on",
    href: "https://docs.ampersandboxdesign.com/#/bendscript.com/docs/spec/README.md",
  },
  d_wrl: {
    label: "WallRiderLang — worlds",
    tagline: "Seal a topology to a SemanticArtifactID",
    href: "https://docs.ampersandboxdesign.com/#/WRL",
  },
  d_trvm: {
    label: "TRVM — reduction",
    tagline: "One spec, four packed-word implementations",
    href: "https://docs.ampersandboxdesign.com/#/TRVM",
  },
  d_wrlm: {
    label: "WRLM — proposal",
    tagline: "The only statistical layer in the chain",
    href: "https://docs.ampersandboxdesign.com/#/TRVM/WRLM_RESEARCH_BRIEF.md",
  },
  d_traaviis: {
    label: "TRAAVIIS — evidence",
    tagline: "trvs: content-addressed evaluation environments",
    href: "https://docs.ampersandboxdesign.com/#/TRAAVIIS",
  },
  // Company
  culler: {
    label: "c-u-l8er.link",
    tagline: "Cosmic Ultraviolet Lithographer — the creative studio",
    href: "https://c-u-l8er.link",
  },
  home: {
    label: "Ampersand Box Design",
    tagline: "The factory for evaluated cognitive systems",
    href: "https://ampersandboxdesign.com",
  },
  traaviis: {
    label: "TRAAVIIS",
    tagline: "Evidence-grade environments for evaluating agents",
    href: "https://traaviis.com",
    // Not a test count. The suite collects 532 but has one open identity defect
    // (kernel K27), so "532 tests" would read as 532 green. ORS v1 is the shipped,
    // checkable fact: the Episode Kernel's first transport, profile O1–O30.
    status: "trvs · ORS v1",
    tier: "alpha",
  },
  // Broader than the [&] stack -- it carries the non-portfolio domains too, so
  // it sits under Company rather than in any product column. No status/tier for
  // the same reason c-u-l8er.link and the home entry carry none: it is a
  // property, not a versioned artifact.
  wrand: {
    label: "Wrand.cc",
    tagline: "R&D domain graph — the whole portfolio, drawn",
    href: "https://wrand.cc",
  },
  // SHELL.md r16. This entry shipped a mailto: href and the bare address as its
  // tagline, to 22 targets and every live domain. (Both are named in the commit
  // message, not here: a comment in a published .js file is published, so
  // writing the address down to explain its removal would re-ship it. The first
  // draft of this comment did exactly that.) The
  // page-level mailto anchors were retracted surface by surface, but this one
  // is in JavaScript, and Cloudflare's email obfuscation does not rewrite JS —
  // so the address it was masking in HTML was served in the clear here the
  // whole time. A published .js asset is a published asset; the blocklist that
  // only reads index.html scored this clean. Corrections go to the form, which
  // is the r9 ruling for contact everywhere else on the portfolio.
  contact: {
    label: "Talk to us",
    tagline: "Corrections and questions, through the form",
    href: "https://computedriven.com/#join",
  },
};

// Map "property" attribute value to the category + item it lives in, for the
// "you are here" highlight. Properties not in this map still render the nav
// (no highlight). Internal aliases ("ampersandboxdesign" → "home") are fine.
// ONE CANONICAL HOME PER PROPERTY. Many items appear in two or three menus on purpose — TRVM is
// in Factory, Stack and Research; box-and-box in Factory and Research; Graphonomous in Stack and
// Compose — and that cross-linking is the point. But when a reader is STANDING ON a site, exactly
// one root may light up, or the bar is answering "where am I?" with a shrug. This table is where
// that single answer is decided, and it is the reason duplication above is reuse rather than a
// second home. Rebuilt 2026-08-22 for the seven-root bar: `products` and `protocols` became
// `stack`, `academy` became `learn`.
const PROPERTY_MAP = {
  // ---- Factory: the ampersandboxdesign.com surface and the world it runs ---------------------
  ampersandboxdesign: { category: "factory", item: "factory_home" },
  factory: { category: "factory", item: "factory_floor" },
  // ComputeDriven is place 1 — it IS the world — and its canonical root is the factory that
  // produces it, not the Stack column that also lists it as a surface.
  computedriven: { category: "factory", item: "computedriven_room" },

  // ---- Stack: the installed machines (was Products + Protocols) ------------------------------
  // T&R resolves to the Stack BANNER, not a column row — `renderBanner` compares `banner.key`
  // against `currentItem` exactly as a column item does, so "you are here" lights the banner.
  tr: { category: "stack", item: "tr" },
  super: { category: "stack", item: "super" },
  cloud: { category: "factory", item: "cloud" },
  graphonomous: { category: "stack", item: "graphonomous" },
  bendscript: { category: "stack", item: "bendscript" },
  runefort: { category: "stack", item: "runefort" },
  agentelic: { category: "stack", item: "agentelic" },
  fleetprompt: { category: "stack", item: "fleetprompt" },
  specprompt: { category: "stack", item: "specprompt" },
  delegatic: { category: "stack", item: "delegatic" },
  agentromatic: { category: "stack", item: "agentromatic" },
  webhost: { category: "stack", item: "webhost" },
  ampersand: { category: "stack", item: "ampersand" },
  pulse: { category: "stack", item: "pulse" },
  prism: { category: "stack", item: "prism" },
  scope: { category: "stack", item: "scope" },

  // ---- Compose: the primitives that exist only to be joined ----------------------------------
  deliberatic: { category: "compose", item: "deliberatic" },
  ticktickclock: { category: "compose", item: "ticktickclock" },
  geofleetic: { category: "compose", item: "geofleetic" },

  // ---- Research ------------------------------------------------------------------------------
  opensentience: { category: "research", item: "opensentience" },
  // TRAAVIIS moved out of Company on 2026-08-22. It is runtime research, it was already in the
  // substrate column, and Company stopped being the place properties land when nothing else fits.
  traaviis: { category: "research", item: "traaviis" },
  wrl: { category: "research", item: "wrl" },
  wrlm: { category: "research", item: "wrlm" },
  trvm: { category: "research", item: "trvm" },
  box_and_box: { category: "research", item: "box_and_box" },
  laws: { category: "research", item: "laws" },
  weave: { category: "research", item: "weave" },
  invariant_arithmetic: { category: "research", item: "invariant_arithmetic" },
  arith_deontic: { category: "research", item: "arith_deontic" },
  arith_temporal: { category: "research", item: "arith_temporal" },
  arith_reflexive: { category: "research", item: "arith_reflexive" },
  arith_epistemic: { category: "research", item: "arith_epistemic" },
  arith_strategic: { category: "research", item: "arith_strategic" },
  arith_resource: { category: "research", item: "arith_resource" },
  arith_playground: { category: "research", item: "arith_playground" },
  kappa: { category: "research", item: "proof_kappa" },
  invariants: { category: "research", item: "invariants" },
  a2atraffic: { category: "research", item: "a2atraffic" },
  topology_warrant: { category: "research", item: "topology_warrant" },
  proof_kappa: { category: "research", item: "proof_kappa" },
  proof_phase: { category: "research", item: "proof_phase" },
  proof_nocycles: { category: "research", item: "proof_nocycles" },
  proof_monotonic: { category: "research", item: "proof_monotonic" },
  proof_deny: { category: "research", item: "proof_deny" },
  proof_append: { category: "research", item: "proof_append" },

  // ---- Learn: the curriculum and the institution that teaches it (was Academy) ---------------
  // The five masterclasses used to resolve to Factory while the `masterclass` key fed Academy's
  // promo band — two roots claiming one curriculum. Learn ends that: every masterclass page
  // highlights Learn, and Factory keeps one of them as a contextual promo without owning it.
  // Listed in curriculum order (01–05) to match the Learn column. Order carries no behaviour
  // here — this is a lookup keyed by `property=` — but the two lists were written together and
  // drifted together, so keeping them in the same sequence is what makes a mismatch visible.
  masterclasses: { category: "learn", item: "masterclasses" },
  masterclass: { category: "learn", item: "masterclass" },
  compose_masterclass: { category: "learn", item: "compose_masterclass" },
  factory_masterclass: { category: "learn", item: "factory_masterclass" },
  verification_masterclass: { category: "learn", item: "verification_masterclass" },
  world_masterclass: { category: "learn", item: "world_masterclass" },
  // The Academy prototype identifies as `academy`. It has no nav item of its own yet — the
  // entry lands when the reading layer serves a page (ACADEMY.md §6, C1) — so it highlights
  // the category without claiming an item inside it.
  academy: { category: "learn", item: "academy_home" },
  academy_read: { category: "learn", item: "academy_read" },
  academy_practice: { category: "learn", item: "academy_practice" },
  academy_prove: { category: "learn", item: "academy_prove" },
  academy_refusals: { category: "learn", item: "academy_refusals" },
  academy_method: { category: "learn", item: "academy_method" },
  workbench: { category: "learn", item: "workbench" },

  // ---- Docs / Company ------------------------------------------------------------------------
  docs: { category: "docs", item: null },
  wrand: { category: "company", item: "wrand" },
  culler: { category: "company", item: "culler" },
};

// ---------------------------------------------------------------------------
// PLACEMENT — where the reader currently is, in the ComputeDriven world.
//
// COMPUTEDRIVEN_POSITIONING_PLAN.md §6.2 asks for this on each LINKS entry,
// under the key `tier`. It cannot go there: `tier` is already taken on LINKS
// and means maturity ("shipped" | "alpha" | "spec"), it is read by
// renderStatus() to colour the status pill, and a numeric 1–4 in that slot
// would silently repaint every pill in the menu. So placement lives in its own
// table, keyed by the `property` attribute rather than by menu item — which is
// also the more honest shape, because placement is a fact about the SITE the
// nav is embedded in, not about a row in a dropdown. The plan's field name is
// therefore `place`, not `tier`.
//
//   place 1  The Place            — no band; it IS the place
//   place 2  Product with a rung  — "the {layer} layer of ComputeDriven"
//   place 3  Specification        — "a specification in the ComputeDriven world"
//   place 4  Not part of it       — the whole nav is removed
//
// `rung` is the EVIDENCE rung (spec → in_tree → live_local → live_deployed →
// external), not the five-step drive/track/replay ladder. Doctrine rule 2: it
// renders what is stored and nothing else. A missing rung renders `?`, never
// `spec` and never blank — an invented status is worse than a missing one
// because it stops the question being asked. Several entries below are
// deliberately `null` for exactly that reason.
//
// Two standing cautions on these values:
//   · R3 (compute moves into the OS; the Fly apps wind down) will move the
//     `live_deployed` rungs that rest on a Fly MCP. They are true today.
//   · Whether agentelic / fleetprompt / specprompt belong at place 2 rather
//     than 3 is reserved to Travis (plan §5, Tier 3 note). They sit at 3 here
//     because that is what the plan says, not because it was decided again.
const PLACEMENT = {
  // ---- place 1: the world page -------------------------------------------
  computedriven: { place: 1 },

  // ---- place 2: products with a defensible rung (plan §5, Tier 2) ---------
  ampersandboxdesign: {
    name: "Ampersand Box Design",
    place: 2,
    layer: "governance",
    // The plan states two rungs for this domain — site `live_deployed`, kernel
    // `in_tree`. The band names the kernel, so it carries the kernel's rung.
    // Doctrine: when in doubt, downgrade.
    rung: "in_tree",
  },
  // NO `tr` ENTRY, ON PURPOSE. One was added on 2026-08-25 (place 2, layer "operating system",
  // rung live_local) and removed the same day on Travis's call: the band it produced sat above the
  // T&R page's own header reading "the operating system layer of ComputeDriven · live_local", and
  // that page is a product page whose first screen is a download, not a position statement.
  // Without an entry the property renders the portfolio bar alone, which is the documented
  // degradation path and is what is wanted here. Do not "fix" its absence.
  graphonomous: { name: "Graphonomous", place: 2, layer: "memory", rung: "live_deployed" },
  opensentience: {
    name: "OpenSentience",
    place: 2,
    layer: "research",
    // Plan §5: "mixed" across OS-001…OS-011. There is no single rung for
    // eleven protocols, so there is no rung here.
    rung: null,
  },
  traaviis: {
    name: "TRAAVIIS",
    place: 2,
    layer: "evidence",
    // Plan §5 marks this "? — verify" and nobody has. Left unmeasured on
    // purpose; the `?` is the finding.
    rung: null,
  },
  delegatic: { name: "Delegatic", place: 2, layer: "authorization", rung: "live_deployed" },
  webhost: {
    name: "WebHost.Systems",
    place: 2,
    layer: "runtime",
    // Plan §5: no index.html in tree, so there is no marketing surface to
    // place. Whether it is built or demoted to place 3 is [TRAVIS].
    rung: null,
  },

  // ---- place 3: specifications (plan §5, Tier 3) --------------------------
  // `spec` is the served document, via the stack-docs atlas. Every path below
  // was checked to exist in the tree on 2026-08-15.
  deliberatic: {
    name: "Deliberatic",
    place: 3,
    rung: "spec",
    spec: "https://docs.ampersandboxdesign.com/#/deliberatic.com/docs/spec/README.md",
  },
  ticktickclock: {
    name: "TickTickClock",
    place: 3,
    rung: "spec",
    spec: "https://docs.ampersandboxdesign.com/#/ticktickclock.com/docs/spec/README.md",
  },
  geofleetic: {
    name: "GeoFleetic",
    place: 3,
    rung: "spec",
    spec: "https://docs.ampersandboxdesign.com/#/geofleetic.com/docs/spec/README.md",
  },
  agentromatic: {
    name: "AgenTroMatic",
    place: 3,
    rung: "spec",
    spec: "https://docs.ampersandboxdesign.com/#/agentromatic.com/docs/spec/README.md",
  },
  bendscript: {
    name: "BendScript",
    place: 3,
    rung: "spec",
    spec: "https://docs.ampersandboxdesign.com/#/bendscript.com/docs/spec/README.md",
  },
  runefort: {
    name: "RuneFort",
    place: 3,
    // alpha per plan §5, not `spec` — and the spec is not a README: this is the
    // one Tier 3 domain with no docs/spec/README.md in tree. CLAUDE.md still
    // points at that filename and it does not exist.
    rung: null,
    spec: "https://docs.ampersandboxdesign.com/#/runefort.com/docs/spec/runefort.protocol.md",
  },
  agentelic: {
    name: "Agentelic",
    place: 3,
    rung: "live_deployed",
    spec: "https://docs.ampersandboxdesign.com/#/agentelic.com/docs/spec/README.md",
  },
  fleetprompt: {
    name: "FleetPrompt",
    place: 3,
    rung: "live_deployed",
    spec: "https://docs.ampersandboxdesign.com/#/fleetprompt.com/docs/spec/README.md",
  },
  specprompt: {
    name: "SpecPrompt",
    place: 3,
    rung: "live_deployed",
    spec: "https://docs.ampersandboxdesign.com/#/specprompt.com/docs/spec/README.md",
  },
  // Inert today: alkeyword.com/index.html carries no <amp-nav>, and the live
  // site deploys from a separate repository, so nothing here reaches it.
  alkeyword: {
    name: "alkeyword",
    place: 3,
    rung: "live_deployed",
    spec: "https://docs.ampersandboxdesign.com/#/alkeyword.com/docs/spec/README.md",
  },
  // Both halves of this entry's old comment — "nothing to link and no rung to
  // state" — were closed on 2026-08-17 and it now has a LINKS row above.
  //
  // Still true, and still the reason the fan-out cannot reach it: the repository
  // is `c-u-l8er/a2atraffic.com` in ~/Projects, outside this tree, so
  // sync-nav.sh has no target for it and its amp-nav.js must be vendored by hand.
  //
  // The rung is no longer `null`. The surface publishes
  // https://a2atraffic.com/records/surface.json, which states `surface_rung:
  // "spec"` with `rung_witness: "none"` and says on the page that it collects
  // nothing — a reading of published documents, which is exactly what spec
  // permits. That is a stored, checkable rung rather than an assumed one, so it
  // is rendered instead of `?`. Downgrade it, do not raise it, unless that
  // record changes: the one thing on the page that runs is a client-side Agent
  // Card inspector, and one live_local tool does not lift a whole surface.
  a2atraffic: { name: "A2A Traffic", place: 3, rung: "spec" },

  // ---- place 4: not part of this story (plan §5, Tier 4) ------------------
  // The nav is removed entirely from these. None of them are sync targets in
  // sync-nav.sh and none embed <amp-nav> from this repository today, so this
  // branch changes nothing until one of them does — it is the mechanism, put in
  // place ahead of the sites, not a silent removal from anything live.
  toolboxhvac: { place: 4 },
  brokenrecord: { place: 4 },
  gpscoord: { place: 4 },
  istrav: { place: 4 },
  subvind: { place: 4 },
  wrand: { place: 4 },
  container: { place: 4 },
};

// Human-readable rung, and the one place `?` is produced.
const RUNG_LABEL = (rung) => (rung ? rung : "?");

// The name the placement band would print, or `null` if no band renders.
//
// ONE predicate, consulted by both the thing that DRAWS the band
// (`renderPlacement`) and the thing that RESERVES SPACE for it
// (`_heightForInject`). Those were two independent reads of PLACEMENT until
// 2026-08-22, and they agreed only because both happened to test `place`. The
// moment the band gained a second suppression rule they disagreed: the band
// stopped drawing, `_heightForInject` kept returning 86px because the property
// was still place 2, and every page cleared 30px for a band that was no longer
// there — a hole between the portfolio bar and the host page's own header.
//
// The band's own STYLE comment already warns that getting this height wrong
// "does not throw and does not warn". That is the argument for one predicate
// rather than two readings of the same table.
const BAND_NAME = (property) => {
  const p = PLACEMENT[property];
  if (!p || p.place === 1 || p.place === 4) return null;
  // THIRD SUPPRESSION RULE — the host page already says it, better.
  //
  // SHELL.md §1 asks every surface to carry its own placement band: the layer
  // sentence, the rung chip, AND a `covers` span bounding what that rung
  // actually applies to. This component draws no `covers` span and cannot —
  // it knows the property, not what is live on the page. So where both render,
  // a visitor reads the same sentence twice in two wordings before reaching the
  // h1, with two rung chips that CAN DISAGREE: on opensentience.org the nav
  // printed `?` from this table while the page's own band printed the rung the
  // surface had derived. Measured 2026-08-22: 11 of the portfolio's surfaces
  // were shipping the doubled claim.
  //
  // Same reasoning as the two rules above — the page does not need to be told
  // what it has already said — and keyed on what is actually in the document
  // rather than on a list of property ids, so it stays right as surfaces adopt
  // the shell. The page's band wins because it is the one with `covers`.
  //
  // Reading the light DOM here is safe for BOTH callers: the band is the first
  // element in <body> and this component is loaded as a deferred module, so the
  // document is parsed before either `renderPlacement` or `_heightForInject`
  // runs. Guarded for non-browser contexts (SSR, tests) where there is no
  // document at all, in which case nothing is drawn and nothing is reserved.
  if (typeof document !== "undefined" && document.querySelector(".band")) return null;
  // Named on the PLACEMENT entry rather than looked up: several properties
  // have no LINKS row of their own (ampersandboxdesign is `home`, alkeyword
  // and a2atraffic have none), and a band that silently prints a raw property
  // id because a lookup missed is the kind of thing nobody notices.
  const name = p.name ?? LINKS[property]?.label ?? property;
  // The band is a "you are here" for a visitor who landed on a portfolio site
  // and does not know it belongs to ComputeDriven. On the property whose name
  // IS the bar's wordmark, it stacks that name directly above an identical one
  // and tells the visitor nothing they cannot read 40px lower. Same reasoning
  // as `place === 1` above — the page does not need to be told where it is —
  // so it is the same rule, keyed on identity rather than on a hardcoded
  // property id, and it will follow the wordmark if that is renamed.
  return name === BRAND_NAME ? null : name;
};

// Top-level structure. Order = display order.
//
// A category may be either flat (one column, `items: [...]`) or a mega-menu
// (multiple columns, `mega: true, columns: [{label, items}, ...]`). The mega
// shape is used by Compose to lay out the full ecosystem product catalog
// across the three architectural layers.
// SEVEN ROOTS, reordered 2026-08-22 (nav v0.11.0). The bar previously ran
//
//   Factory · Products · Protocols · Research · Academy · Docs · Company · Compose
//
// which is eight roots organised by two taxonomies that are ours, not the reader's:
// Products-vs-Protocols is an implementation filing system, and Academy-vs-Masterclasses is a
// publishing one. Neither is a question anybody arrives with. Worse, Compose sat last while the
// thesis moved to "parallelize the work, prove the assemblies, FORMALIZE THE JOINS" — the central
// technical operation of the whole factory was in the least-read position on the bar.
//
// Each root now answers one question, and left-to-right they tell the argument in order:
//
//   Factory   what is it?              Compose   how do independently made things join?
//   Stack     what is in it?           Research  what are we discovering?
//   Learn     how do I understand it?  Docs      how do I build against it?
//   Company   who builds it?
//
// Products + Protocols merged into STACK (a machine inventory, not a catalogue). Academy demoted
// into LEARN — it is not deleted and loses no pages; it stops being one of the ontological
// categories of the company and becomes what it actually is, one learning environment inside the
// factory. That is the stronger role: Academy owns READ→PRACTICE→PROVE, the factory owns the
// whole loop through BUILD→COMPOSE→SHIP→OBSERVE.
//
// ONE CANONICAL HOME PER PROPERTY. Items appear in several menus on purpose — TRVM is in both
// Stack and Research, box-and-box in both Factory and Research, Graphonomous in both Stack and
// Compose — but PROPERTY_MAP gives each site exactly one place that highlights when you are
// standing on it. Cross-linking is reuse; two homes would be an unanswerable "where am I?".
//
// Width: seven roots is one fewer than eight, so the bar came in ~70px. See the CTA note below.
const CATEGORIES = [
  {
    id: "factory",
    label: "Factory",
    mega: true,
    columns: [
      {
        // The argument, in the order the page makes it.
        label: "The line",
        items: ["factory_home", "factory_unboxed", "factory_join", "factory_floor"],
      },
      {
        // What governs the line. box_and_box and laws also live under Research → Arithmetic;
        // that is reuse, not duplication, and the renderer handles it.
        label: "The constitution",
        items: ["factory_constitution", "box_and_box", "laws", "ampersand"],
      },
      {
        label: "Worlds",
        items: ["factory_worldware", "wrl", "trvm", "computedriven_room"],
      },
    ],
    // The commercial surface leads the menu rather than closing a column. It was the last row of
    // "Worlds", underneath four free destinations, which is the wrong place for the one thing in
    // the portfolio anybody is asked to pay for.
    banner: {
      key: "cloud",
      mark: "[World] Cloud",
      title: "Run a world without running the substrate",
      body: "Hosted worlds — fork, restore and move between a laptop and a datacentre as one artifact. The local tier stays free and complete.",
      cta: "See the tiers",
    },
    // The five-masterclass column that lived here moved to Learn. Factory keeps exactly one
    // masterclass — this promo — because it explains the concept the menu is named after, which
    // is a different job from housing the curriculum.
    promo: {
      key: "factory_masterclass",
      eyebrow: "Long read",
      title: "The Worldware Factory",
      body: "Everyone is building AI factories and the term already means three different things. Unboxing without checked joins is faster and wrong at exactly the same rate — the arithmetic is on the page, and so is every gap.",
      cta: "Read the masterclass",
    },
  },
  {
    // Moved from last to second. Compose is the central technical operation of the factory, and
    // the first column is now the JOIN ITSELF rather than more product rows — without it this
    // menu read as a second catalogue with an abstract name on top.
    id: "compose",
    label: "Compose",
    mega: true,
    columns: [
      {
        label: "Composition",
        items: ["factory_join", "compose_masterclass", "ampersand", "laws"],
      },
      {
        label: "Cognitive Primitives",
        items: ["graphonomous", "deliberatic", "ticktickclock", "geofleetic"],
      },
      {
        label: "Agent Platform",
        items: ["agentelic", "fleetprompt", "specprompt", "delegatic", "agentromatic"],
      },
      {
        label: "Runtime",
        items: ["opensentience", "webhost"],
      },
    ],
    // The same argument as Factory's banner, applied to the other operation.
    // Compose says what MAY join; Super is where a join is actually exercised
    // — so the surface leads the menu rather than sitting in a column as one
    // more product row, which is where it was and which made the central
    // technical operation look like it had no operator's console.
    banner: {
      key: "super",
      mark: "Super (CD)",
      title: "The surface you compose on",
      body: "Engines are interchangeable; authority, placement and evidence are not. Point Claude Code, Codex or whatever comes next at a world — Super holds the identity, the budget and the receipts.",
      cta: "Open Super",
    },
    promo: {
      key: "compose_masterclass",
      eyebrow: "Long read",
      title: "Composition Is Not a List",
      body: "Four ecosystems converged on the word capability in 2026 and shipped no operator for combining two. Here are two operators, the laws they carry, and the ones that still fail.",
      cta: "Read the masterclass",
    },
  },
  {
    // Products + Protocols, merged. The old split made sense when [&] was a loose ecosystem; it
    // stopped making sense when [&] became one factory composed of machinery. This is the
    // installed-machine inventory, which is why the promo points at the floor.
    id: "stack",
    label: "Stack",
    mega: true,
    columns: [
      {
        label: "Machines & surfaces",
        items: ["computedriven_room", "cloud", "super", "graphonomous", "bendscript", "runefort"],
      },
      {
        label: "Agent machinery",
        items: ["agentelic", "fleetprompt", "specprompt", "delegatic", "agentromatic"],
      },
      {
        label: "Protocols",
        items: ["ampersand", "pulse", "prism", "scope"],
      },
      {
        label: "World & runtime",
        items: ["wrl", "trvm", "wrlm", "traaviis", "webhost"],
      },
    ],
    // Third banner, same argument as Factory's and Compose's applied to this menu. Factory leads
    // with the thing you pay for, Compose with the thing you operate from — Stack is the
    // installed-machine inventory, and every other row in it is a library, a protocol or a
    // service. T&R is the only entry a visitor can download and run, which makes it exactly the
    // row that should not be the sixth item in a column of six.
    //
    // Note it is NOT also listed in "Machines & surfaces" below. cloud and super are each a
    // banner in one menu and a column row in another, which the file calls reuse rather than
    // duplication — but banner and column in the SAME menu is the duplication that comment is
    // distinguishing itself from.
    banner: {
      key: "tr",
      mark: "T&R",
      title: "The one machine here you can boot",
      body: "Everything else in this menu is a library, a protocol or a service. T&R is the one you boot — FreeBSD 15 assembled from pkgbase, no installer, no first-boot download, carrying the verifier that re-derives its own claims.",
      cta: "Download T&R",
    },
    // The obvious promo line here was "18 factory cells · view the floor →". It does not say 18.
    // The nav is a standalone bundle with no access to the CELLS arrays the number comes from, so
    // it would be a hand-typed count in the one file of the portfolio that has already shipped
    // two of those wrong. factory_floor's own tagline carries the count, next to the data.
    promo: {
      key: "factory_floor",
      eyebrow: "The floor",
      title: "These are the machines installed in the factory",
      body: "Every cell on the floor carries the evidence rung it has actually reached — spec, in tree, live local, live deployed — and the ones whose rung was never recorded say so rather than guessing.",
      cta: "View the floor",
    },
  },
  {
    id: "research",
    label: "Research",
    mega: true,
    columns: [
      {
        label: "Open research",
        items: ["opensentience", "invariants", "a2atraffic", "topology_warrant", "weave"],
      },
      {
        label: "Results",
        items: ["proof_kappa", "proof_phase", "proof_nocycles", "proof_monotonic", "proof_deny", "proof_append"],
      },
      {
        // The kernel-level entry points: the package, its conformance, the sandbox.
        label: "Arithmetic",
        items: ["box_and_box", "laws", "arith_playground"],
      },
      {
        // The execution substrate, in the order a world moves through it:
        // WRLM proposes → WRL seals → TRVM reduces → TRAAVIIS admits. WRLM is
        // the only statistical layer; the other three are total + deterministic.
        label: "Runtime research",
        items: ["wrl", "trvm", "wrlm", "traaviis"],
      },
      {
        // The eight rungs themselves, as individual living-paper pages
        // (invariant_arithmetic covers rungs 1–2; arith_* are rungs 3–8).
        label: "Modalities",
        items: [
          "invariant_arithmetic",
          "arith_deontic",
          "arith_temporal",
          "arith_reflexive",
          "arith_epistemic",
          "arith_strategic",
          "arith_resource",
        ],
      },
    ],
  },
  {
    // Learn describes the visitor's intent; Academy declared an institution. Academy is still
    // here, as one column — a learning environment inside [&] rather than a peer of the factory.
    // This is also where the five masterclasses now live, which resolves the old coupling where
    // Factory housed the curriculum while the `masterclass` key fed Academy's promo band.
    id: "learn",
    label: "Learn",
    mega: true,
    columns: [
      {
        // All five exist as pages. Ordered as the curriculum orders them — and the curriculum
        // numbers itself, on /masterclasses, whose cards are 01–05 in this sequence:
        //   01 masterclass · 02 compose_masterclass · 03 factory_masterclass
        //   04 verification_masterclass · 05 world_masterclass
        // That numbering is the authority; this list follows it. It did not until 2026-08-25:
        // `factory_masterclass` (03) sat in slot 2, so the menu opened on 03 · 01 · 02 · 04 · 05
        // while the comment above it claimed curriculum order. The pages themselves say the order
        // is cumulative ("Five machines, and the order that makes them cumulative"), which makes a
        // reader following the menu top-to-bottom meet the arrangement before the two things
        // being arranged. If a masterclass is added or renumbered, re-derive from the card
        // numbers on /masterclasses rather than from this list.
        label: "Masterclasses",
        items: [
          "masterclasses",
          "masterclass",
          "compose_masterclass",
          "factory_masterclass",
          "verification_masterclass",
          "world_masterclass",
        ],
      },
      {
        label: "Academy",
        items: ["academy_home", "academy_read", "academy_practice", "academy_prove"],
      },
      {
        label: "Practice & proof",
        items: ["workbench", "prism", "academy_refusals", "academy_method"],
      },
    ],
    promo: {
      key: "masterclass",
      eyebrow: "Long read",
      title: "The New SDLC, Made Formal",
      body: "Google named the discipline. This is the substrate underneath it — and every claim on the page ships the command that would break it.",
      cta: "Read the masterclass",
    },
  },
  {
    // NOT merged into Learn. Learn answers "why does this work?"; Docs answers "what field goes
    // in this manifest?". Collapsing them is a common and expensive mistake.
    id: "docs",
    label: "Docs",
    mega: true,
    columns: [
      {
        label: "Start here",
        items: ["d_home", "d_quickstart", "d_index", "d_eco", "d_faq"],
      },
      {
        label: "The protocol stack",
        items: ["d_arch", "d_umbrella", "d_compose", "d_three"],
      },
      {
        label: "Engines & capabilities",
        items: ["d_memory", "d_prism", "d_bendscript", "d_govern"],
      },
      {
        label: "Execution substrate",
        items: ["d_wrl", "d_trvm", "d_wrlm", "d_traaviis"],
      },
    ],
  },
  {
    // Smaller on purpose. Company is not where orphaned sites go — a nav bar is not a sitemap.
    // TRAAVIIS left: it is runtime research and its canonical home is now Research, where the
    // substrate column already carried it. culler and wrand stay because they are real
    // organisational entities a visitor may need to place, not surplus properties.
    id: "company",
    label: "Company",
    items: ["home", "culler", "wrand", "contact"],
  },
];

// The subscribe list is a mailbox, not a service — there is no signup form and
// no newsletter platform behind this. A mailto is the whole mechanism, which is
// why the label promises a subscription and not a product. If a real list ever
// exists, swap the href; do not swap the label ahead of it.
// The qualifier is a span so it can drop out when the bar runs out of room.
// UPDATED 2026-08-22 (third pass) — breakpoint re-measured, 1380 -> 1140. Two things shrank the
// bar at once: the seven-root restructure, and the CTA changing from "Join ComputeDriven" to
// "[World] Cloud". Measured in the browser rather than estimated: the suffix span costs 49px
// (" Cloud") where it used to cost 113px (" ComputeDriven"), the seven roots total 646px, and at a
// 1277px viewport there is 209px of slack between the last root and the CTA. So the suffix stops
// fitting near 1129px, and 1380 was hiding "Cloud" on every laptop for no reason — the bar had
// been carrying a threshold tuned for a wider bar and a longer word.
// UPDATED 2026-08-22 (second pass, v0.11.0) — the seven-root bar is NARROWER than the eight-root
// one it replaces. Products + Protocols merged into Stack and Academy folded into Learn, so two
// roots left and one arrived: net −1 root and ~−70px of nowrap content. The earlier note in this
// slot recorded the Factory root pushing the bar to ~1330px and the CTA drop-out breakpoint from
// 1300 to 1380; the bar is back to roughly where it was before Factory landed. The breakpoint is
// LEFT AT 1380 deliberately — it is a threshold for hiding a two-word suffix, nothing renders
// wrong above or below it, and re-tuning it by eye against a measurement nobody re-took is how
// the previous figure in this comment stopped being true. Wide screens get "Join ComputeDriven",
// everything narrower gets "Join", and the mobile sheet always has room for the full thing.
// Interpolated raw into innerHTML below, so markup is fine.
// Repointed 2026-08-22 from computedriven.com ("Join ComputeDriven") to the paid tier. The bar's
// one call to action now names the one thing anybody is asked to pay for; the free control room is
// still reachable from Factory and from Stack, where a free destination belongs.
//
// The cta-long span is kept and now wraps "Cloud": the mark is [World] Cloud, and [World] alone is
// still a recognisable stub at narrow widths where the suffix drops out. Losing "Cloud" costs less
// than losing the bracket, which is the part that reads as ours.
const CTA = {
  // Every part is an ELEMENT and the spacing comes from `gap` on the flex container, because
  // literal spaces do not survive here. `.cta` is display:flex, so the text node, the suffix span
  // and the arrow are three flex ITEMS, and whitespace at a flex item's edge is collapsed away —
  // the painted gap between "[World]" and "Cloud" measured 0px. This predates the [World] Cloud
  // rename: the old label was `Join<span class="cta-long"> ComputeDriven</span> →` with the same
  // two spaces in the same two places, so the button has been rendering "Join→" at every width
  // below the suffix breakpoint. A space you cannot see in the source is a space that is not there.
  label: '<span>[World]</span><span class="cta-long">Cloud</span><span class="cta-arrow" aria-hidden="true">→</span>',
  href: "https://cloud.computedriven.com",
};

const STYLE = /* css */ `
  :host {
    --amp-nav-bg: rgba(8, 9, 12, 0.78);
    --amp-nav-fg: #e2e0db;
    --amp-nav-muted: #8b8a95;
    --amp-nav-accent: #4af5c6;
    --amp-nav-border: rgba(255, 255, 255, 0.08);
    --amp-nav-hover: rgba(255, 255, 255, 0.04);
    --amp-nav-cta-bg: #e2e0db;
    --amp-nav-cta-fg: #08090c;
    --amp-nav-font: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
    /* Inside the shadow root --amp-nav-height is the BAR's height. In the host
       document, the same name is injected onto :root by _heightForInject() and
       means the TOTAL space the component occupies — bar plus placement band
       when one renders. The two never collide because :host declares its own,
       and the name is shared on purpose: pages and _offsetHostFixedNavs()
       already offset themselves with var(--amp-nav-height), and that has to
       keep meaning "how far down does my content start". */
    --amp-nav-height: 56px;
    --amp-nav-band-height: 30px;
    --amp-nav-z: 9999;

    display: block;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: var(--amp-nav-z);
    font-family: var(--amp-nav-font);
    font-size: 13px;
    line-height: 1;
    color: var(--amp-nav-fg);
    -webkit-font-smoothing: antialiased;
  }

  :host([theme="light"]) {
    --amp-nav-bg: rgba(255, 255, 255, 0.85);
    --amp-nav-fg: #08090c;
    --amp-nav-muted: #6b6980;
    --amp-nav-border: rgba(0, 0, 0, 0.08);
    --amp-nav-hover: rgba(0, 0, 0, 0.04);
    --amp-nav-cta-bg: #08090c;
    --amp-nav-cta-fg: #f5f5f0;
  }

  /* Topology-as-Warrant "legal vellum" house style: dark ink ground, warm
     parchment type, a single gold accent. Matches
     opensentience.org/topology-as-warrant.html so the nav reads as the top
     edge of the sealed document, not a separate chrome bar. */
  :host([theme="warrant"]) {
    --amp-nav-bg: rgba(22, 19, 16, 0.9);
    --amp-nav-fg: #e8e2d2;
    --amp-nav-muted: #8c8472;
    --amp-nav-accent: #c9a24b;
    --amp-nav-border: rgba(232, 226, 210, 0.12);
    --amp-nav-hover: rgba(232, 226, 210, 0.06);
    --amp-nav-cta-bg: #c9a24b;
    --amp-nav-cta-fg: #161310;
  }

  /* ---- placement band --------------------------------------------------
     A strip above the bar saying where the reader is in the ComputeDriven
     world. It only renders for place 2 and 3; place 1 is the world page and
     place 4 has no nav at all. Its height is part of --amp-nav-height, which
     _heightForInject() recomputes — otherwise the band would sit on top of
     the host page's first 30 pixels. */
  .place {
    position: relative;
    /* border-box so the band is exactly --amp-nav-band-height including its
       rule, and 56 + 30 is the honest total. Note .bar is content-box and has
       always been 1px taller than the 56px it injects; that 1px predates this
       band and is left alone rather than silently corrected here. */
    box-sizing: border-box;
    height: var(--amp-nav-band-height);
    background: var(--amp-nav-bg);
    backdrop-filter: saturate(180%) blur(14px);
    -webkit-backdrop-filter: saturate(180%) blur(14px);
    border-bottom: 1px solid var(--amp-nav-border);
    display: flex;
    align-items: center;
    gap: 0.55rem;
    padding: 0 clamp(0.75rem, 3vw, 1.5rem);
    font-size: 11px;
    letter-spacing: 0.02em;
    color: var(--amp-nav-muted);
    overflow-x: auto;
    scrollbar-width: none;
    white-space: nowrap;
  }
  .place::-webkit-scrollbar { display: none; }
  .place .who { color: var(--amp-nav-fg); }
  .place .sep { opacity: 0.45; }

  /* The rung chip states an evidence rung and nothing else. A question mark is
     a real answer and must not be dressed as one of the others: it gets the
     muted outline, never the accent. (No backticks in here — STYLE is a
     template literal and one in a comment closes it, which is a syntax error
     700 lines further down.) */
  .place .rung {
    border: 1px solid var(--amp-nav-border);
    border-radius: 3px;
    padding: 0.15em 0.45em;
    text-transform: uppercase;
    font-size: 10px;
    letter-spacing: 0.08em;
    color: var(--amp-nav-muted);
  }
  .place .rung[data-rung="live_deployed"],
  .place .rung[data-rung="external"] {
    color: var(--amp-nav-accent);
    border-color: color-mix(in srgb, var(--amp-nav-accent) 45%, transparent);
  }
  .place .rung[data-rung="live_local"],
  .place .rung[data-rung="in_tree"] {
    color: var(--amp-nav-fg);
    border-color: color-mix(in srgb, var(--amp-nav-fg) 35%, transparent);
  }
  .place a {
    color: var(--amp-nav-muted);
    text-decoration: none;
    border-bottom: 1px solid transparent;
  }
  .place a:hover {
    color: var(--amp-nav-fg);
    border-bottom-color: var(--amp-nav-border);
  }
  .place .home {
    margin-left: auto;
    padding-left: 0.75rem;
  }
  /* 745, measured across 370–800 on 2026-08-15: the full band (name + line +
     chip + spec link + home) needs 729px of content, so it clears at a 745px
     viewport and not at 731. Below that the line is dropped rather than left to
     scroll — the band has overflow-x: auto so nothing ever pushes the PAGE
     sideways, but a placement band you have to swipe to read has stopped
     placing you.
     What is left after the line is dropped needs 398px, so below a ~412px
     viewport the band does scroll inside itself (measured: 410 scrolls, 415
     fits exactly at 400/400). That is the accepted floor — a 30px strip
     clipping its own tail, not the document moving. */
  @media (max-width: 745px) {
    .place .layerline { display: none; }
    .place .layerline + .sep { display: none; }
  }

  .bar {
    position: relative;
    height: var(--amp-nav-height);
    background: var(--amp-nav-bg);
    backdrop-filter: saturate(180%) blur(14px);
    -webkit-backdrop-filter: saturate(180%) blur(14px);
    border-bottom: 1px solid var(--amp-nav-border);
    display: flex;
    align-items: center;
    padding: 0 clamp(1rem, 3vw, 2rem);
    gap: 1.5rem;
  }

  .brand {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    text-decoration: none;
    color: var(--amp-nav-fg);
    letter-spacing: 0.02em;
    font-weight: 500;
    white-space: nowrap;
  }

  .brand .mark {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    border: 1px solid var(--amp-nav-border);
    border-radius: 4px;
    font-weight: 700;
    color: var(--amp-nav-accent);
  }

  .brand .wordmark {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--amp-nav-muted);
  }

  nav.items {
    display: flex;
    gap: 0.25rem;
    align-items: center;
    flex: 1;
    justify-content: center;
  }

  .item {
    position: relative;
  }

  .item > button,
  .item > a {
    appearance: none;
    background: none;
    border: 0;
    color: var(--amp-nav-fg);
    font: inherit;
    padding: 0.6rem 0.9rem;
    border-radius: 6px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    text-decoration: none;
    transition: background 120ms ease, color 120ms ease;
  }

  .item > button:hover,
  .item > a:hover,
  .item > button:focus-visible,
  .item > a:focus-visible {
    background: var(--amp-nav-hover);
    outline: none;
  }

  .item[aria-current="true"] > button,
  .item[aria-current="true"] > a {
    color: var(--amp-nav-accent);
  }

  .chev {
    width: 10px;
    height: 10px;
    transition: transform 160ms ease;
    opacity: 0.6;
  }

  .item[data-open="true"] .chev {
    transform: rotate(180deg);
  }

  .dropdown {
    position: absolute;
    top: calc(100% + 8px);
    left: 0;
    min-width: 280px;
    background: var(--amp-nav-bg);
    backdrop-filter: saturate(180%) blur(14px);
    -webkit-backdrop-filter: saturate(180%) blur(14px);
    border: 1px solid var(--amp-nav-border);
    border-radius: 10px;
    padding: 0.5rem;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
    display: none;
    flex-direction: column;
    gap: 0.125rem;
  }

  .item[data-open="true"] .dropdown {
    display: flex;
  }

  /* Vertical rhythm, retuned 2026-08-22 after the Learn menu was flagged as hard to read.
     The fault was not "not enough space" — it was that the space was distributed wrongly. A menu
     item is a group (title + status pill + tagline), and a group only reads as one when the space
     INSIDE it is clearly smaller than the space AROUND it. It was the other way round: 2px from
     title to tagline, but a wrapped two-line title spread on default line-height, so the item's
     own lines sat further apart than the items did. Now: tight line-height inside, a real margin
     between. See .label-row below for the third part of the same fault. */
  .dropdown a {
    display: block;
    padding: 0.45rem 0.75rem;
    margin-bottom: 0.3rem;
    border-radius: 6px;
    color: var(--amp-nav-fg);
    text-decoration: none;
    transition: background 120ms ease;
  }

  .dropdown a:last-child { margin-bottom: 0; }

  .dropdown a:hover,
  .dropdown a:focus-visible {
    background: var(--amp-nav-hover);
    outline: none;
  }

  .dropdown a[aria-current="true"] {
    color: var(--amp-nav-accent);
  }

  .dropdown .tagline {
    display: block;
    margin-top: 3px;
    line-height: 1.42;
    font-size: 11px;
    color: var(--amp-nav-muted);
    letter-spacing: 0;
  }

  /* Mega dropdown — multi-column layout for the Compose catalog and Research.
     Each menu is sized from its OWN column count (--cols, set inline at render)
     rather than one shared min-width: Research carries five columns and Compose
     three, and a single width would leave one of them either cramped or sparse.
     auto-fit reflows to fewer, wider columns when the viewport can't fit them
     all — the desktop nav still shows down to 861px, where five will not fit. */
  .item[data-open="true"] .dropdown.mega {
    display: grid;
  }

  .dropdown.mega {
    /* Was repeat(auto-fit, minmax(200px, 1fr)), and that is why widening the menu did not widen
       its columns. auto-fit creates as many tracks as WILL FIT, not as many as there are columns:
       Learn has three, but at 905px the grid laid out FOUR tracks of 203px, left the last one
       empty, and squeezed the three real ones — so every extra pixel of menu width went into a
       column with nothing in it. The count is known at render (--cols), so ask for it. */
    grid-template-columns: repeat(var(--cols, 3), minmax(0, 1fr));
    align-items: start;
    gap: 1.25rem;
    padding: 1rem;
    /* Centered on the BAR, not on the trigger button. Centering a wide menu on
       its own trigger pushes it off-screen whenever the trigger sits near an
       edge — Research (leftish, 5 columns) fell off the left, Compose (last
       button) off the right. The bar is the full viewport, so this is the one
       anchor that keeps every mega menu on-screen at every width. */
    left: 50%;
    transform: translateX(-50%);
    /* --colw is set inline at render from the column count. A flat 220px was tuned for Research,
       which carries five columns and needs them narrow; applying the same width to a THREE-column
       menu left Learn 725px wide inside a 1277px viewport with 193px of text area, so every one of
       its six masterclass titles wrapped to two lines. The titles need 164–234px. Fewer columns can
       afford wider ones, and the min() below still clamps to the viewport on small screens.

       box-sizing is border-box here because it was not, and the clamp was wrong by exactly the
       padding: the min() set the CONTENT width, then 1rem of padding was added on each side, so
       Research came out 1001px inside a 1000px viewport and hung 8px off the left edge. The
       "+ 2rem" in the first arm shows the author was already thinking in border-box.
       The gap term is explicit for the same reason — with it, --colw is the width a column
       ACTUALLY gets, rather than a number that has to be pre-compensated for gutters.
       (No backticks in comments inside this template literal — see .label-row.) */
    box-sizing: border-box;
    width: min(
      calc(var(--cols, 3) * var(--colw, 220px) + (var(--cols, 3) - 1) * 1.25rem + 2rem),
      calc(100vw - 2rem)
    );
  }

  /* Between the mobile-sheet breakpoint (860px) and 1100px, exact tracks would squeeze Research's
     five columns to ~170px. Reflowing is better there — but ONLY there. Applying auto-fit to every
     menu in the band put four tracks under Learn's three columns again, one of them empty, which
     is the bug this file just finished fixing at desktop width. --gridnarrow is set per menu at
     render: five-column menus reflow, everything else keeps its exact tracks and simply gets
     narrower as the width clamp bites. */
  @media (max-width: 1100px) {
    .dropdown.mega { grid-template-columns: var(--gridnarrow, repeat(auto-fit, minmax(180px, 1fr))); }
  }

  /* Mega triggers drop their positioning context so the menu resolves against
     .bar. Flat dropdowns keep hanging off their own .item. */
  .item:has(> .dropdown.mega) {
    position: static;
  }

  .dropdown.mega .col {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
    min-width: 0;
  }

  /* Promo band — spans every column of the mega menu, whatever --cols is.
     Selector is deliberately two classes: ".dropdown a" (0,1,1) sets display:block and its own
     padding, and would beat a bare ".promo" (0,1,0) no matter where this rule sits. */
  .dropdown .promo,
  .mobile-section .promo {
    grid-column: 1 / -1;
    display: grid;
    grid-template-areas:
      "eyebrow cta"
      "title   cta"
      "body    cta";
    grid-template-columns: 1fr auto;
    align-items: center;
    column-gap: 1.25rem;
    row-gap: 0.15rem;
    margin-top: 0.4rem;
    padding: 0.85rem 1rem;
    border: 1px solid var(--amp-nav-border);
    border-radius: 10px;
    background:
      linear-gradient(115deg, color-mix(in srgb, var(--amp-nav-accent) 12%, transparent) 0%, transparent 62%),
      var(--amp-nav-hover);
    text-decoration: none;
    transition: border-color 0.15s ease, transform 0.15s ease;
  }
  /* Also outruns ".dropdown a:hover", which would otherwise flatten the gradient. */
  .dropdown .promo:hover,
  .mobile-section .promo:hover {
    background:
      linear-gradient(115deg, color-mix(in srgb, var(--amp-nav-accent) 18%, transparent) 0%, transparent 62%),
      var(--amp-nav-hover);
    border-color: color-mix(in srgb, var(--amp-nav-accent) 55%, transparent);
    transform: translateY(-1px);
  }
  .dropdown .promo[aria-current="page"],
  .mobile-section .promo[aria-current="page"] { border-color: color-mix(in srgb, var(--amp-nav-accent) 45%, transparent); }

  .promo-eyebrow {
    grid-area: eyebrow;
    font-size: 9.5px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    color: var(--amp-nav-accent);
  }
  .promo-title {
    grid-area: title;
    font-size: 13.5px;
    font-weight: 600;
    color: var(--amp-nav-fg);
    line-height: 1.3;
  }
  .promo-body {
    grid-area: body;
    font-size: 11.5px;
    line-height: 1.5;
    color: var(--amp-nav-muted);
  }
  .promo-cta {
    grid-area: cta;
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    white-space: nowrap;
    padding: 0.4rem 0.7rem;
    border-radius: 7px;
    font-size: 11.5px;
    font-weight: 600;
    background: var(--amp-nav-cta-bg, var(--amp-nav-accent));
    color: var(--amp-nav-cta-fg, #08090c);
  }
  .promo-cta svg { width: 9px; height: 9px; flex: none; }

  /* Narrow menus and the mobile sheet: stack the CTA under the copy. */
  @media (max-width: 560px) {
    .dropdown .promo {
      grid-template-areas: "eyebrow" "title" "body" "cta";
      grid-template-columns: 1fr;
      row-gap: 0.35rem;
    }
    .dropdown .promo-cta { justify-self: start; margin-top: 0.2rem; }
  }
  /* The sheet opens at <=860px but the stacking query above fires at <=560px, which would leave
     the band in its two-column form in the 561–860px sheet. Stack it unconditionally in there. */
  .mobile-section .promo {
    margin-top: 0.6rem;
    grid-template-areas: "eyebrow" "title" "body" "cta";
    grid-template-columns: 1fr;
    row-gap: 0.35rem;
  }
  .mobile-section .promo-cta { justify-self: start; margin-top: 0.2rem; }

  .dropdown.mega .col h4 {
    margin: 0 0 0.55rem 0;
    padding: 0 0.75rem;
    font-size: 10px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: var(--amp-nav-muted);
  }

  /* Feature banner — spans every column, sits ABOVE them. Louder than a menu row and quieter
     than the page it links to. Uses the accent as a fill rather than as text colour, because at
     the top of a menu an accent-on-dark row reads as "selected" rather than as "different". */
  .dropdown.mega .feature,
  .mobile-section .feature {
    grid-column: 1 / -1;
    display: flex;
    align-items: center;
    gap: 0.85rem;
    margin: 0 0 0.9rem 0;
    padding: 0.7rem 0.85rem;
    border-radius: 9px;
    text-decoration: none;
    border: 1px solid color-mix(in srgb, var(--amp-nav-accent) 34%, transparent);
    background:
      linear-gradient(90deg,
        color-mix(in srgb, var(--amp-nav-accent) 13%, transparent),
        color-mix(in srgb, var(--amp-nav-accent) 4%, transparent) 62%,
        transparent);
    transition: border-color 140ms ease, background 140ms ease;
  }
  .dropdown.mega .feature:hover,
  .dropdown.mega .feature:focus-visible,
  .mobile-section .feature:hover {
    border-color: color-mix(in srgb, var(--amp-nav-accent) 62%, transparent);
    background:
      linear-gradient(90deg,
        color-mix(in srgb, var(--amp-nav-accent) 20%, transparent),
        color-mix(in srgb, var(--amp-nav-accent) 7%, transparent) 62%,
        transparent);
    outline: none;
  }
  .feature-mark {
    flex: none;
    font-size: 12.5px;
    font-weight: 600;
    letter-spacing: 0.02em;
    color: var(--amp-nav-accent);
    padding: 0.28rem 0.5rem;
    border: 1px solid color-mix(in srgb, var(--amp-nav-accent) 40%, transparent);
    border-radius: 6px;
    white-space: nowrap;
  }
  .feature-copy { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
  .feature-title {
    font-size: 13px;
    font-weight: 600;
    line-height: 1.3;
    color: var(--amp-nav-fg);
  }
  .feature-body {
    font-size: 11px;
    line-height: 1.4;
    color: var(--amp-nav-muted);
  }
  .feature-cta {
    margin-left: auto;
    flex: none;
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 11.5px;
    font-weight: 600;
    color: var(--amp-nav-accent);
    white-space: nowrap;
  }
  .feature-cta svg { width: 9px; height: 9px; flex: none; }
  /* Narrow menus and the sheet: the CTA drops under the copy rather than squeezing the title. */
  @media (max-width: 620px) {
    .dropdown.mega .feature, .mobile-section .feature { flex-wrap: wrap; }
    .feature-cta { margin-left: 0; width: 100%; }
  }

  /* Status pill — version / "spec only" / "in dev" */
  /* Was inline-flex with flex-wrap:wrap, which made the title span and the status pill two flex
     ITEMS. A title that wrapped to two lines took the full width, so the pill was pushed onto a
     third line of its own — "Worlds That Pay For / Themselves / (live)" — and every long-titled
     entry became a three-line block with a floating pill in the middle of the menu.
     As a block with an inline pill, the pill flows after the last word of the title and wraps only
     when it genuinely does not fit.
     NOTE: no backticks in comments inside this template literal — one closes it early and turns the
     whole module into a SyntaxError. This comment was written with them and the sync gate refused
     it, which is the second time that gate has paid for itself. */
  .dropdown a .label-row {
    display: block;
    line-height: 1.32;
  }

  .dropdown .status {
    display: inline-block;
    /* The .label-row gap went with the flexbox; the pill carries its own leading space now. */
    margin-left: 0.42rem;
    vertical-align: 1px;
    font-size: 10px;
    line-height: 1;
    padding: 2px 6px;
    border: 1px solid var(--amp-nav-border);
    border-radius: 999px;
    color: var(--amp-nav-muted);
    letter-spacing: 0.04em;
    white-space: nowrap;
  }

  .dropdown .status[data-tier="shipped"] {
    color: var(--amp-nav-accent);
    border-color: color-mix(in srgb, var(--amp-nav-accent) 35%, transparent);
  }

  .dropdown .status[data-tier="alpha"] {
    color: #f5c66a;
    border-color: rgba(245, 198, 106, 0.4);
  }

  .dropdown .status[data-tier="spec"] {
    color: var(--amp-nav-muted);
    opacity: 0.85;
  }

  /* Mobile mirrors of the same status pill */
  .mobile-section .status {
    display: inline-block;
    margin-left: 0.5rem;
    font-size: 10px;
    line-height: 1;
    padding: 2px 6px;
    border: 1px solid var(--amp-nav-border);
    border-radius: 999px;
    color: var(--amp-nav-muted);
    letter-spacing: 0.04em;
    vertical-align: middle;
  }
  .mobile-section .status[data-tier="shipped"] {
    color: var(--amp-nav-accent);
    border-color: color-mix(in srgb, var(--amp-nav-accent) 35%, transparent);
  }
  .mobile-section .status[data-tier="alpha"] {
    color: #f5c66a;
    border-color: rgba(245, 198, 106, 0.4);
  }
  .mobile-section .col-label {
    display: block;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: var(--amp-nav-muted);
    margin: 0.6rem 0 0.25rem 0;
  }

  .spacer {
    flex: 1;
  }

  .cta {
    display: inline-flex;
    align-items: center;
    /* Spacing between the label parts. Not literal spaces — see the CTA definition above. */
    gap: 0.34em;
    padding: 0.55rem 0.9rem;
    border-radius: 6px;
    background: var(--amp-nav-cta-bg);
    color: var(--amp-nav-cta-fg);
    text-decoration: none;
    font-weight: 600;
    letter-spacing: 0.01em;
    white-space: nowrap;
    transition: transform 120ms ease, opacity 120ms ease;
  }

  .cta:hover,
  .cta:focus-visible {
    transform: translateY(-1px);
    outline: none;
  }

  /* Raised 1300 → 1380 on 2026-08-22, when the Factory root was added.
     The full CTA ("Join ComputeDriven →") costs ~130px; the eighth root costs ~62px. Measured at
     1310px the bar overflowed its container by 3px — a narrow but real broken window between the
     old breakpoint and the width the bar actually fits at. Shortening the CTA earlier closes it
     with room to spare, which is exactly what this rule exists to do. Re-measure if a ninth root
     is ever added: bar.scrollWidth minus bar.clientWidth must be 0 or less at every width.
     (No backticks in this comment — STYLE is a template literal and one would close it.) */
  @media (max-width: 1140px) {
    .cta .cta-long {
      display: none;
    }
  }

  .burger {
    display: none;
    appearance: none;
    background: none;
    border: 1px solid var(--amp-nav-border);
    border-radius: 6px;
    color: var(--amp-nav-fg);
    padding: 0.45rem 0.55rem;
    cursor: pointer;
    margin-left: auto;
  }

  .burger svg {
    display: block;
    width: 18px;
    height: 18px;
  }

  .mobile-sheet {
    display: none;
    position: fixed;
    inset: var(--amp-nav-height) 0 0 0;
    background: var(--amp-nav-bg);
    backdrop-filter: saturate(180%) blur(20px);
    -webkit-backdrop-filter: saturate(180%) blur(20px);
    padding: 1rem;
    overflow-y: auto;
    border-top: 1px solid var(--amp-nav-border);
  }

  .mobile-sheet[data-open="true"] {
    display: block;
  }

  .mobile-section {
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--amp-nav-border);
  }

  .mobile-section:last-child {
    border-bottom: 0;
  }

  .mobile-section h3 {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--amp-nav-muted);
    margin: 0 0 0.5rem 0;
    font-weight: 500;
  }

  .mobile-section a {
    display: block;
    padding: 0.65rem 0;
    color: var(--amp-nav-fg);
    text-decoration: none;
    font-size: 14px;
  }

  .mobile-section a[aria-current="true"] {
    color: var(--amp-nav-accent);
  }

  .mobile-section .tagline {
    font-size: 11px;
    color: var(--amp-nav-muted);
    margin-top: 2px;
  }

  .mobile-cta {
    margin-top: 1rem;
    display: block;
    text-align: center;
    padding: 0.8rem;
    border-radius: 6px;
    background: var(--amp-nav-cta-bg);
    color: var(--amp-nav-cta-fg);
    text-decoration: none;
    font-weight: 600;
  }

  @media (max-width: 860px) {
    nav.items,
    .cta {
      display: none;
    }
    .burger {
      display: inline-flex;
    }
    .spacer {
      display: none;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    * {
      transition: none !important;
    }
  }
`;

const TEMPLATE = (property) => {
  // place 4 — "not part of this story". The nav is removed, which means it
  // renders nothing at all rather than rendering an empty bar: an empty fixed
  // 56px strip at the top of the page is worse than no nav.
  if (PLACEMENT[property]?.place === 4) return "";

  const highlight = PROPERTY_MAP[property] ?? null;
  const currentCategory = highlight?.category ?? null;
  const currentItem = highlight?.item ?? null;

  const escapeAttr = (s) => String(s).replace(/"/g, "&quot;");

  // Column width by column count. A menu with fewer columns gets wider ones, because the total is
  // bounded by the viewport rather than by the column: three columns at Research's 220px wastes
  // half the screen and wraps every title in the menu. Five columns at 280px would not fit.
  // Widths chosen against the longest titles actually in each menu, measured in the browser.
  const megaColWidth = (n) => (n <= 3 ? "280px" : n === 4 ? "244px" : "220px");
  // Narrow-band (861-1100px) track template. Only the five-column menu reflows; fewer columns
  // keep their exact tracks so no menu ever lays out an empty one.
  const megaNarrowGrid = (n) =>
    n >= 5 ? "repeat(auto-fit, minmax(180px, 1fr))" : `repeat(${n}, minmax(0, 1fr))`;

  const renderStatus = (link) =>
    link.status
      ? `<span class="status" data-tier="${escapeAttr(link.tier ?? "spec")}">${link.status}</span>`
      : "";

  const renderItem = (key) => {
    const link = LINKS[key];
    if (!link) return "";
    const isCurrent = key === currentItem;
    const status = renderStatus(link);
    return `
      <a href="${link.href}" ${isCurrent ? 'aria-current="true"' : ""} data-key="${key}">
        <span class="label-row"><span>${link.label}</span>${status}</span>
        ${link.tagline ? `<span class="tagline">${link.tagline}</span>` : ""}
      </a>
    `;
  };

  // Full-width band beneath a mega menu's columns. Spans every column via grid-column: 1 / -1,
  // so it stays one band whatever --cols is set to.
  const renderPromo = (promo) => {
    if (!promo) return "";
    const link = LINKS[promo.key];
    if (!link) return "";
    const isCurrent = promo.key === currentItem;
    return `
      <a class="promo" href="${escapeAttr(link.href)}" role="menuitem"${isCurrent ? ' aria-current="page"' : ""}>
        <span class="promo-eyebrow">${promo.eyebrow}</span>
        <span class="promo-title">${promo.title}</span>
        <span class="promo-body">${promo.body}</span>
        <span class="promo-cta">${isCurrent ? "You are reading it" : promo.cta}<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M3 1.5 L6.5 5 L3 8.5" stroke="currentColor" stroke-width="1.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg></span>
      </a>
    `;
  };

  // A FEATURE BANNER, rendered ABOVE the columns. Deliberately not a second .promo: the promo band
  // is a long-read teaser that sits under the menu and reads as "more to read". A commercial
  // surface people are meant to reach needs the opposite placement and a different voice, and
  // burying it as the last row of a column — where it started — put the one paid destination in
  // the portfolio below four free ones.
  const renderBanner = (banner) => {
    if (!banner) return "";
    const link = LINKS[banner.key];
    if (!link) return "";
    const isCurrent = banner.key === currentItem;
    return `
      <a class="feature" href="${escapeAttr(link.href)}" role="menuitem"${isCurrent ? ' aria-current="page"' : ""}>
        <span class="feature-mark">${banner.mark}</span>
        <span class="feature-copy">
          <span class="feature-title">${banner.title}</span>
          <span class="feature-body">${banner.body}</span>
        </span>
        <span class="feature-cta">${banner.cta}<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M3 1.5 L6.5 5 L3 8.5" stroke="currentColor" stroke-width="1.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg></span>
      </a>
    `;
  };

  const renderCategory = (cat) => {
    const isCurrent = cat.id === currentCategory;
    const dropdownInner = cat.mega
      ? cat.columns
          .map(
            (col) => `
        <div class="col">
          <h4>${col.label}</h4>
          ${col.items.map(renderItem).join("")}
        </div>
      `,
          )
          .join("")
      : cat.items.map(renderItem).join("");
    const dropdownClass = cat.mega ? "dropdown mega" : "dropdown";
    return `
      <div class="item" data-category="${cat.id}" ${isCurrent ? 'aria-current="true"' : ""}>
        <button type="button" aria-haspopup="true" aria-expanded="false">
          <span>${cat.label}</span>
          <svg class="chev" viewBox="0 0 10 10" aria-hidden="true">
            <path d="M1.5 3.5 L5 7 L8.5 3.5" stroke="currentColor" stroke-width="1.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
        <div class="${dropdownClass}" role="menu"${cat.mega ? ` style="--cols:${cat.columns.length};--colw:${megaColWidth(cat.columns.length)};--gridnarrow:${megaNarrowGrid(cat.columns.length)}"` : ""}>
          ${cat.mega ? renderBanner(cat.banner) : ""}
          ${dropdownInner}
          ${cat.mega ? renderPromo(cat.promo) : ""}
        </div>
      </div>
    `;
  };

  const renderMobileLink = (key) => {
    const link = LINKS[key];
    if (!link) return "";
    const isCurrent = key === currentItem;
    const status = link.status
      ? `<span class="status" data-tier="${escapeAttr(link.tier ?? "spec")}">${link.status}</span>`
      : "";
    return `
      <a href="${link.href}" ${isCurrent ? 'aria-current="true"' : ""}>
        ${link.label}${status}
        ${link.tagline ? `<span class="tagline">${link.tagline}</span>` : ""}
      </a>
    `;
  };

  const mobileSection = (cat) => {
    const body = cat.mega
      ? cat.columns
          .map(
            (col) => `
        <span class="col-label">${col.label}</span>
        ${col.items.map(renderMobileLink).join("")}
      `,
          )
          .join("")
      : cat.items.map(renderMobileLink).join("");
    return `
      <div class="mobile-section">
        <h3>${cat.label}</h3>
        ${renderBanner(cat.banner)}
        ${body}
        ${renderPromo(cat.promo)}
      </div>
    `;
  };

  // The placement band. Renders for place 2 and 3 only: place 1 is the world
  // page and does not need to be told where it is, and place 4 never gets here
  // because TEMPLATE returns nothing at all for it.
  const renderPlacement = () => {
    // Whether a band renders at all, and what it is called, is BAND_NAME's
    // question — the same call `_heightForInject` makes to size the gap.
    const name = BAND_NAME(property);
    if (name === null) return "";
    const p = PLACEMENT[property];
    const rung = RUNG_LABEL(p.rung);
    const chip = `<span class="rung" data-rung="${escapeAttr(p.rung ?? "unknown")}" title="evidence rung">${rung}</span>`;

    const line =
      p.place === 2
        ? `<span class="layerline">the ${escapeAttr(p.layer ?? "?")} layer of ComputeDriven</span>`
        : `<span class="layerline">a specification in the ComputeDriven world</span>`;

    const specLink = p.spec
      ? `<span class="sep">·</span><a href="${escapeAttr(p.spec)}">read the spec</a>`
      : "";

    return `
      <div class="place" part="place" data-place="${p.place}">
        <span class="who">${name}</span>
        <span class="sep">—</span>
        ${line}
        <span class="sep">·</span>
        ${chip}
        ${specLink}
        <a class="home" href="https://computedriven.com">ComputeDriven →</a>
      </div>
    `;
  };

  return `
    <style>${STYLE}</style>
    ${renderPlacement()}
    <div class="bar" part="bar">
      <a class="brand" href="https://ampersandboxdesign.com" aria-label="${BRAND_NAME}">
        <span class="mark">&</span>
        <span class="wordmark">${BRAND_NAME}</span>
      </a>
      <nav class="items" aria-label="Portfolio">
        ${CATEGORIES.map(renderCategory).join("")}
      </nav>
      <span class="spacer"></span>
      <a class="cta" href="${CTA.href}">${CTA.label}</a>
      <button class="burger" type="button" aria-label="Open menu" aria-expanded="false">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
          <path d="M3 6h18M3 12h18M3 18h18"/>
        </svg>
      </button>
    </div>
    <div class="mobile-sheet" role="dialog" aria-label="Portfolio menu">
      ${CATEGORIES.map(mobileSection).join("")}
      <a class="mobile-cta" href="${CTA.href}">${CTA.label}</a>
    </div>
  `;
};

class AmpNav extends HTMLElement {
  static get observedAttributes() {
    return ["property", "theme"];
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._onDocClick = this._onDocClick.bind(this);
    this._onKeydown = this._onKeydown.bind(this);
  }

  connectedCallback() {
    this._injectHostStyles();
    this._render();
    document.addEventListener("click", this._onDocClick);
    document.addEventListener("keydown", this._onKeydown);
  }

  /**
   * Inject a one-time <style> element into the host document so page content
   * sits below the portfolio nav (body padding + anchor scroll-padding).
   * Offsetting the host's own fixed/sticky nav is handled separately in
   * _offsetHostFixedNavs() so we don't disturb non-fixed positioned headers.
   */
  _injectHostStyles() {
    if (typeof document === "undefined") return;
    if (document.getElementById("amp-nav-host-styles")) return;
    const h = AmpNav._heightForInject(this);
    const style = document.createElement("style");
    style.id = "amp-nav-host-styles";
    const overlay = this.hasAttribute("overlay");
    style.textContent = `
      :root { --amp-nav-height: ${h}; }
      ${overlay ? "" : "body { padding-top: var(--amp-nav-height); }"}
      /* Honor the portfolio nav when the browser scrolls to anchors or
         snap points — prevents anchor targets from landing behind the nav. */
      html { scroll-padding-top: var(--amp-nav-height); }
    `;
    document.head.appendChild(style);
    // Offset the site's OWN fixed/sticky top nav so it sits below the portfolio
    // nav. This is done in JS (not a broadcast CSS rule) because `top` is only a
    // no-op on static elements — on `position: relative`/`absolute` content it
    // shifts the element out of place. We therefore only touch elements whose
    // computed position is actually `fixed` or `sticky`.
    this._offsetHostFixedNavs();
  }

  /**
   * Push the host site's own fixed/sticky top nav below the portfolio nav.
   * Only elements that are genuinely fixed or sticky are offset, so we never
   * disturb relatively/absolutely positioned headers that are page content.
   * Runs once on connect plus a couple of deferred passes to catch navs that
   * mount slightly after the portfolio nav.
   */
  _offsetHostFixedNavs() {
    if (typeof document === "undefined") return;
    const SEL =
      'body nav, body header, body [role="banner"], body .site-nav, body .navbar, body .topbar';
    const apply = () => {
      document.querySelectorAll(SEL).forEach((el) => {
        if (el.tagName === "AMP-NAV" || el.closest("amp-nav")) return;
        const pos = getComputedStyle(el).position;
        if (pos === "fixed" || pos === "sticky") {
          el.style.top = "var(--amp-nav-height)";
        }
      });
    };
    apply();
    requestAnimationFrame(apply);
    setTimeout(apply, 500);
  }

  static _heightForInject(el) {
    // Allow per-host override via attribute or CSS var; default 56px.
    const attr = el.getAttribute("height");
    if (attr) return /^\d+$/.test(attr) ? `${attr}px` : attr;

    // This is the TOTAL the host page must clear, not the bar's height — see
    // the note on --amp-nav-height in STYLE. Getting this wrong does not throw
    // and does not warn; too small puts the placement band on top of the first
    // 30 pixels of every page it ships to, and too large leaves a 30px hole
    // between the bar and the host page's own header. Both have happened.
    //
    // Asked of BAND_NAME rather than re-derived from `place`, so the space is
    // reserved if and only if `renderPlacement` draws something into it.
    const property = el.getAttribute("property") ?? "";
    if (PLACEMENT[property]?.place === 4) return "0px";
    return BAND_NAME(property) === null ? "56px" : "86px"; // 56 bar + 30 band
  }

  disconnectedCallback() {
    document.removeEventListener("click", this._onDocClick);
    document.removeEventListener("keydown", this._onKeydown);
  }

  attributeChangedCallback() {
    if (this.shadowRoot) this._render();
  }

  _render() {
    const property = this.getAttribute("property") ?? "";
    this.shadowRoot.innerHTML = TEMPLATE(property);
    this._wire();
  }

  _wire() {
    const root = this.shadowRoot;

    // Desktop dropdowns
    root.querySelectorAll(".item[data-category] > button").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const item = btn.parentElement;
        const open = item.getAttribute("data-open") === "true";
        this._closeAll();
        if (!open) {
          item.setAttribute("data-open", "true");
          btn.setAttribute("aria-expanded", "true");
        }
      });
    });

    // Mobile burger
    const burger = root.querySelector(".burger");
    const sheet = root.querySelector(".mobile-sheet");
    if (burger && sheet) {
      burger.addEventListener("click", (e) => {
        e.stopPropagation();
        const open = sheet.getAttribute("data-open") === "true";
        sheet.setAttribute("data-open", open ? "false" : "true");
        burger.setAttribute("aria-expanded", open ? "false" : "true");
      });
    }
  }

  _closeAll() {
    const root = this.shadowRoot;
    root.querySelectorAll(".item[data-open='true']").forEach((el) => {
      el.setAttribute("data-open", "false");
      const btn = el.querySelector("button");
      if (btn) btn.setAttribute("aria-expanded", "false");
    });
  }

  _onDocClick(e) {
    // Click outside shadow tree closes dropdowns
    if (!this.contains(e.target) && !e.composedPath().includes(this)) {
      this._closeAll();
    } else {
      // Click inside but outside an open item also closes
      const path = e.composedPath();
      const insideItem = path.some(
        (n) => n.classList && n.classList.contains("item"),
      );
      if (!insideItem) this._closeAll();
    }
  }

  _onKeydown(e) {
    if (e.key === "Escape") {
      this._closeAll();
      const sheet = this.shadowRoot.querySelector(".mobile-sheet");
      if (sheet) sheet.setAttribute("data-open", "false");
      const burger = this.shadowRoot.querySelector(".burger");
      if (burger) burger.setAttribute("aria-expanded", "false");
    }
  }
}

if (!customElements.get("amp-nav")) {
  customElements.define("amp-nav", AmpNav);
}

// Expose version for diagnostics
if (typeof window !== "undefined") {
  window.__ampNavVersion = VERSION;
}
