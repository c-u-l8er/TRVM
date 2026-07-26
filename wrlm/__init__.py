"""WRLM -- the proposer/cortex layer above the WRL/TRVM/TRAAVIIS substrate.

    The model proposes. The edit algebra constrains. TRVM disposes.
    TRAAVIIS admits.

This package is the *offline* half of that sentence: the objects that say what
a task is, what counts as solving it, and how a world gets in here from the
engine. It deliberately imports NOTHING from `forge/` -- it consumes frozen
payloads and canonical artifacts, and re-derives every identity it is handed.

Identity ladder (each rung derived from the one below, never asserted):

    sem-    a sealed world                    forge
    goal-   an objective                      goalspec
    task-   a goal + its base world + how it was generated   taskbundle
    case-   what the model is actually asked  taskbundle (dedup unit)

Design of record: `TRVM/WRLM_RESEARCH_BRIEF.md`.
"""

WRLM_VERSION = "0"

__all__ = ["errors", "goalspec", "worldview", "taskbundle", "worldrecord"]
