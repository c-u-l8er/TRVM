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

const VERSION = "0.8.2";

// Canonical URLs per property. The "href" is the destination used in cross-property
// links; the "label" is what visitors see in the dropdown.
//
// Ecosystem products carry a {status, tier} pair (status = display string,
// tier = one of "shipped" | "alpha" | "spec") so the Compose menu can show
// honest version/maturity at-a-glance. Source of truth: STACK_COMPLETION.md.
const LINKS = {
  // Code — the orchestration console for coding agents (repo: c-u-l8er/code).
  // Leads Products: it is the surface a visitor actually drives the stack from.
  code: {
    label: "Code",
    tagline: "Orchestration console for coding agents",
    href: "https://code.traaviis.com",
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
  masterclass: {
    label: "The New SDLC, Made Formal",
    tagline: "The long read — every claim with the command that would break it",
    href: "https://ampersandboxdesign.com/agentic-engineering-masterclass.html",
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

  // The arithmetic ladder — box-and-box governance kernel (8 rungs, one bridge,
  // 116 property-tested laws) + the six living-paper rung pages + playground + laws.
  box_and_box: {
    label: "box-and-box",
    tagline: "The governance kernel · 8 rungs · 116 laws · npm",
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
    label: "The 116 laws",
    tagline: "Conformance — every law, live",
    href: "https://ampersandboxdesign.com/laws.html",
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
  arith_playground: {
    label: "Playground",
    tagline: "Interactive law sandbox · 64 of 116 live",
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
  kappa: {
    label: "κ-Routing proof",
    tagline: "Topology determines deliberation",
    href: "https://opensentience.org/#kappa",
  },

  // Research — the Periodic Table of Agent Invariants + per-invariant proofs.
  // Only the six PROVED invariants get a proof page; the table holds all 43.
  invariants: {
    label: "Periodic Table of Invariants",
    tagline: "43 agent invariants, by family",
    href: "https://opensentience.org/invariants.html",
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
  d_code: {
    label: "Code — the console",
    tagline: "Lanes, budgets, gates — the orchestration harness",
    href: "https://github.com/c-u-l8er/code",
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
  contact: {
    label: "Talk to us",
    tagline: "hello@ampersandboxdesign.com",
    href: "mailto:hello@ampersandboxdesign.com",
  },
};

// Map "property" attribute value to the category + item it lives in, for the
// "you are here" highlight. Properties not in this map still render the nav
// (no highlight). Internal aliases ("ampersandboxdesign" → "home") are fine.
const PROPERTY_MAP = {
  // Hero products — appear in the Products dropdown
  code: { category: "products", item: "code" },
  graphonomous: { category: "products", item: "graphonomous" },
  bendscript: { category: "products", item: "bendscript" },
  runefort: { category: "products", item: "runefort" },
  // Compose — Cognitive Primitives column
  deliberatic: { category: "compose", item: "deliberatic" },
  ticktickclock: { category: "compose", item: "ticktickclock" },
  geofleetic: { category: "compose", item: "geofleetic" },
  // Compose — Agent Platform column
  agentelic: { category: "compose", item: "agentelic" },
  fleetprompt: { category: "compose", item: "fleetprompt" },
  specprompt: { category: "compose", item: "specprompt" },
  delegatic: { category: "compose", item: "delegatic" },
  agentromatic: { category: "compose", item: "agentromatic" },
  // Compose — Runtime column
  webhost: { category: "compose", item: "webhost" },
  // Academy — institutional loop
  workbench: { category: "academy", item: "workbench" },
  // The Academy prototype identifies as `academy`. It has no nav item of its own yet — the
  // entry lands when the reading layer serves a page (ACADEMY.md §6, C1) — so it highlights
  // the category without claiming an item inside it.
  academy: { category: "academy", item: "academy_home" },
  academy_read: { category: "academy", item: "academy_read" },
  academy_practice: { category: "academy", item: "academy_practice" },
  academy_prove: { category: "academy", item: "academy_prove" },
  academy_refusals: { category: "academy", item: "academy_refusals" },
  academy_method: { category: "academy", item: "academy_method" },
  masterclass: { category: "academy", item: "masterclass" },
  // Other categories
  ampersand: { category: "protocols", item: "ampersand" },
  ampersandboxdesign: { category: "company", item: "home" },
  pulse: { category: "protocols", item: "pulse" },
  prism: { category: "protocols", item: "prism" },
  scope: { category: "protocols", item: "scope" },
  trvm: { category: "protocols", item: "trvm" },
  wrl: { category: "research", item: "wrl" },
  wrlm: { category: "research", item: "wrlm" },
  invariant_arithmetic: { category: "research", item: "invariant_arithmetic" },
  box_and_box: { category: "research", item: "box_and_box" },
  weave: { category: "research", item: "weave" },
  laws: { category: "research", item: "laws" },
  arith_deontic: { category: "research", item: "arith_deontic" },
  arith_temporal: { category: "research", item: "arith_temporal" },
  arith_reflexive: { category: "research", item: "arith_reflexive" },
  arith_epistemic: { category: "research", item: "arith_epistemic" },
  arith_strategic: { category: "research", item: "arith_strategic" },
  arith_resource: { category: "research", item: "arith_resource" },
  arith_playground: { category: "research", item: "arith_playground" },
  opensentience: { category: "research", item: "opensentience" },
  kappa: { category: "research", item: "kappa" },
  invariants: { category: "research", item: "invariants" },
  topology_warrant: { category: "research", item: "topology_warrant" },
  proof_kappa: { category: "research", item: "proof_kappa" },
  proof_phase: { category: "research", item: "proof_phase" },
  proof_nocycles: { category: "research", item: "proof_nocycles" },
  proof_monotonic: { category: "research", item: "proof_monotonic" },
  proof_deny: { category: "research", item: "proof_deny" },
  proof_append: { category: "research", item: "proof_append" },
  // TRAAVIIS is listed twice (Company + the Research substrate column); the
  // highlight resolves to Company, the same way graphonomous resolves to
  // Products despite also appearing under Compose.
  traaviis: { category: "company", item: "traaviis" },
  wrand: { category: "company", item: "wrand" },
  culler: { category: "company", item: "culler" },
  docs: { category: "docs", item: null },
};

// Top-level structure. Order = display order.
//
// A category may be either flat (one column, `items: [...]`) or a mega-menu
// (multiple columns, `mega: true, columns: [{label, items}, ...]`). The mega
// shape is used by Compose to lay out the full ecosystem product catalog
// across the three architectural layers.
const CATEGORIES = [
  {
    id: "products",
    label: "Products",
    items: ["code", "graphonomous", "bendscript", "runefort"],
  },
  {
    id: "protocols",
    label: "Protocols",
    items: ["ampersand", "pulse", "prism", "scope", "trvm"],
  },
  {
    id: "research",
    label: "Research",
    mega: true,
    columns: [
      {
        label: "Protocols & Census",
        items: ["opensentience", "invariants", "topology_warrant", "weave"],
      },
      {
        label: "Proven Invariants",
        items: [
          "proof_kappa",
          "proof_phase",
          "proof_nocycles",
          "proof_monotonic",
          "proof_deny",
          "proof_append",
        ],
      },
      {
        // The kernel-level entry points: the package, its conformance, the sandbox.
        label: "The Arithmetic Ladder",
        items: ["box_and_box", "laws", "arith_playground"],
      },
      {
        // The execution substrate, in the order a world moves through it:
        // WRLM proposes → WRL seals → TRVM reduces → TRAAVIIS admits. WRLM is
        // the only statistical layer; the other three are total + deterministic.
        label: "The Execution Substrate",
        items: ["wrl", "trvm", "wrlm", "traaviis"],
      },
      {
        // The eight rungs themselves, as individual living-paper pages
        // (invariant_arithmetic covers rungs 1–2; arith_* are rungs 3–8).
        label: "The Eight Rungs",
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
    id: "academy",
    label: "Academy",
    mega: true,
    columns: [
      {
        label: "The loop",
        items: ["academy_home", "academy_method"],
      },
      {
        label: "Three layers",
        items: ["academy_read", "academy_practice", "academy_prove"],
      },
      {
        label: "Evidence",
        items: ["workbench", "academy_refusals"],
      },
    ],
    // A full-width band under the columns. `key` points at a LINKS entry so the band can mark
    // itself current, and so its href has one definition rather than two.
    promo: {
      key: "masterclass",
      eyebrow: "Long read",
      title: "The New SDLC, Made Formal",
      body: "Google named the discipline. This is the substrate underneath it — and every claim on the page ships the command that would break it.",
      cta: "Read the masterclass",
    },
  },
  {
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
        items: ["d_wrl", "d_trvm", "d_wrlm", "d_traaviis", "d_code"],
      },
    ],
  },
  {
    id: "company",
    label: "Company",
    items: ["culler", "home", "traaviis", "wrand", "contact"],
  },
  {
    id: "compose",
    label: "Compose",
    mega: true,
    columns: [
      {
        label: "Cognitive Primitives",
        items: [
          "graphonomous",
          "deliberatic",
          "ticktickclock",
          "geofleetic",
        ],
      },
      {
        label: "Agent Platform",
        items: [
          "agentelic",
          "fleetprompt",
          "specprompt",
          "delegatic",
          "agentromatic",
        ],
      },
      {
        label: "Runtime",
        items: ["opensentience", "webhost"],
      },
    ],
  },
];

// The subscribe list is a mailbox, not a service — there is no signup form and
// no newsletter platform behind this. A mailto is the whole mechanism, which is
// why the label promises a subscription and not a product. If a real list ever
// exists, swap the href; do not swap the label ahead of it.
// The qualifier is a span so it can drop out when the bar runs out of room —
// the desktop bar is ~1270px of nowrap content and starts clipping under about
// 1300px, which is most laptops. Wide screens get "Join ComputeDriven",
// everything narrower gets "Join", and the mobile sheet always has room for the
// full thing. Interpolated raw into innerHTML below, so markup is fine.
const CTA = {
  label: 'Join<span class="cta-long"> ComputeDriven</span> →',
  href: "https://computedriven.com",
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
    --amp-nav-height: 56px;
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

  .dropdown a {
    display: block;
    padding: 0.6rem 0.75rem;
    border-radius: 6px;
    color: var(--amp-nav-fg);
    text-decoration: none;
    transition: background 120ms ease;
  }

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
    margin-top: 2px;
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
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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
    width: min(calc(var(--cols, 3) * 220px + 2rem), calc(100vw - 2rem));
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
    margin: 0 0 0.4rem 0;
    padding: 0 0.75rem;
    font-size: 10px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: var(--amp-nav-muted);
  }

  /* Status pill — version / "spec only" / "in dev" */
  .dropdown a .label-row {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .dropdown .status {
    display: inline-block;
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

  @media (max-width: 1300px) {
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
  const highlight = PROPERTY_MAP[property] ?? null;
  const currentCategory = highlight?.category ?? null;
  const currentItem = highlight?.item ?? null;

  const escapeAttr = (s) => String(s).replace(/"/g, "&quot;");

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
        <div class="${dropdownClass}" role="menu"${cat.mega ? ` style="--cols:${cat.columns.length}"` : ""}>
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
        ${body}
        ${renderPromo(cat.promo)}
      </div>
    `;
  };

  return `
    <style>${STYLE}</style>
    <div class="bar" part="bar">
      <a class="brand" href="https://ampersandboxdesign.com" aria-label="Ampersand Box Design">
        <span class="mark">&</span>
        <span class="wordmark">Ampersand Box Design</span>
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
    return "56px";
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
