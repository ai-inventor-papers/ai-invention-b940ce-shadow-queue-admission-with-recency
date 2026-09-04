# gen_demo_art_evaluation_1 — report_results

> Phase: `gen_paper_repo` · `gen_demo_art`
> Run: `iter1_eb86f00c4c5a` — Why Per-Key Cache Decay Rarely Beats a Cheaper Shorter Reset
>
> Full, verbatim record of every prompt the AI Inventor pipeline gave this agent — system-user, human-user and skill-input — in the order they landed. Nothing truncated.

## Task: `gen_demo_art_evaluation_1` (terminal_claude_agent)

### [1] SYSTEM-USER prompt · 2026-08-26 22:06:27 UTC

````
<conversion_philosophy>
**MINIMAL CHANGES — PRESERVE THE ORIGINAL CODE**

The goal is to make the artifact's code READABLE, UNDERSTANDABLE, and RUNNABLE in a short time
to someone reviewing the research, with the option to easily scale parameters back to original
values for a full run (which can take much longer). Think of this as annotating and reformatting,
not refactoring.

**DO:**
- Split the original script into logical notebook cells (imports, setup, processing, results)
- Add markdown cells BETWEEN code cells explaining what each section does and why
- Add inline comments where the logic is non-obvious
- Add a visualization/summary cell at the end showing key outputs
- Fix hardcoded file paths to use the GitHub data loading pattern

**DO NOT:**
- Rewrite functions or change algorithms
- Rename variables or restructure logic
- Add error handling, type hints, or "improvements" that weren't in the original
- Simplify or "clean up" the original code
- Remove any original comments or logic
- Change the computational approach

The reader should recognize the original script when looking at the notebook — it's the
same code, just split into cells with explanatory markdown between sections.
</conversion_philosophy>

<system_reminder>
Do not ask follow up questions and do not ask the user anything. Execute all steps independently.
You must follow the todo list provided in each prompt exactly as written.
No placeholders, stubs, or incomplete code — all code must be complete and functional.
</system_reminder>

<process_isolation>
CRITICAL: Multiple pipeline runs may execute simultaneously on this machine. `ps aux | grep method.py` matches ALL runs, not just yours.
- NEVER kill processes by name (`killall`, `pkill -f`, `ps aux | grep ... | xargs kill`). This kills OTHER runs' processes.
- NEVER monitor processes by name (`ps aux | grep method.py`). You will see other runs' processes and get confused.
- ALWAYS use PID-based process management:
  Run: `uv run method.py & PID=$!` or `timeout <seconds> uv run method.py & PID=$!`
  Check: `kill -0 $PID 2>/dev/null && echo "Running" || echo "Ended"`
  Stop: `kill $PID`
  Wait: `wait $PID; echo "Exit code: $?"`
  Monitor: `tail -f logs/run.log & TAIL_PID=$!` then `kill $TAIL_PID` when done
</process_isolation>

<workspace>
Your workspace: `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_2/art_QhkYY9QvbyCV`

CRITICAL: Every file you create, write, or save MUST be inside this workspace directory (subdirectories OK). You MUST NOT write files anywhere outside this path — external paths are READ-ONLY. Use absolute paths for all file operations.

EVERY file write MUST start with `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_2/art_QhkYY9QvbyCV/`:
GOOD: `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_2/art_QhkYY9QvbyCV/file.py`, `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_2/art_QhkYY9QvbyCV/results/out.json`
BAD: `/tmp/file.py`, `~/output.json`, `./file.py`, any path outside the workspace
</workspace>

<tool_use>
Maximize parallel tool calls. Parallelize independent operations, only sequentialize dependencies.
- Multiple searches/fetches on different topics → parallel in one turn
- Search then fetch results → sequential (need URLs first)
</tool_use>

<task>
Convert this artifact's Python script into a demo notebook with MINIMAL changes to the original code.
Split into cells, add markdown explanations between sections, add a visualization cell at the end.
Output: mini_demo_data.json + code_demo.ipynb (notebook that loads data from GitHub URL)
</task>

<artifact_info>
id: art_QhkYY9QvbyCV
type: evaluation
title: FDR-Corrected Cache Decay Verdict
summary: >-
  This evaluation re-analyzes the 36-group bootstrap results from the Per-Key Decay vs Global Cache Reset experiment (art_gQEGVMwa8ZKC)
  without re-running the underlying 108-cell cache simulation sweep. It (1) computes a two-sided percentile-bootstrap p-value
  per group and applies Benjamini-Hochberg and Benjamini-Yekutieli FDR correction via statsmodels.stats.multitest.multipletests,
  finding 26/36 groups (including all 3 win-corner groups at ratio=0.01, alpha=1.2) survive at q=0.05, while flagging that
  the groups' shared-seed structure violates BH's independence/PRDS assumption; (2) re-simulates ONLY the win-corner cell
  (ratio=0.01, alpha=1.2, all 4 drift scenarios, 3 seeds) across a 3x3 grid of CoV threshold pairs (108 targeted proposed-only
  runs, baseline reused from existing data), finding the advantage holds in only 12/36 threshold-scenario combinations and
  reproduces the original 0.5/1.5 result exactly (delta=0.0) as an internal consistency check; (3) derives an analytical per-request
  operation-count table from method.py's actual estimator code plus a wall-clock microbenchmark, finding the proposed estimator
  costs ~1.7x the operations and ~2.1x the wall-clock time of the baseline; (4) documents that no short-reset-ablation baseline
  exists anywhere in the experiment artifact (explicit gap, not fabricated), and runs the already-built simulator once each
  for baseline/proposed on the real Twitter cluster026 trace (loaded fresh from art_f48a8QRaZrIB, 80,000 requests, 67,681
  distinct keys), finding steady-state hit-ratio parity within the pre-registered 1-percentage-point margin (-0.42pp) plus
  an explicitly-labeled exploratory/unvalidated changepoint-based recovery comparison since the real trace has no ground-truth
  drift labels; and (5) recomputes a single corrected memory-overhead figure directly from phaseC's memory_footprint_table
  (5.14x-5.68x, mean 5.22x), resolving the inconsistency between the experiment's own 'roughly 3-5x' prose and the hypothesis's
  pre-registered 5.1-5.7x figure in favor of the latter, and confirming this exceeds the pre-registered 'no more than ~2x'
  disconfirmation bound. All five sub-analyses are synthesized into one non-hedged final verdict: INCONCLUSIVE_UNDERPOWERED.
  The win-corner groups survive FDR correction, but the threshold-sensitivity grid shows the win is a knife-edge artifact
  of the specific 0.5/1.5 CoV threshold pair (holding in only a third of nearby threshold choices), no short-reset-ablation
  control was ever run to rule out simple baseline under-tuning, the real-trace evidence only supports parity (not a recovery-speed
  advantage), and the corrected 5.14x-5.68x memory overhead is disproportionate to a benefit that does not survive robustness
  checks. Downstream paper-writing steps should present the per-key decay mechanism as an unconfirmed, likely tuning-fragile
  result rather than a genuine advance, and should use the corrected 5.14x-5.68x memory figure (not the artifact's own 'roughly
  3-5x') whenever memory overhead is quoted.
workspace_path: >-
  /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_2/gen_art/gen_art_evaluation_1
out_expected_files:
- eval.py
- full_eval_out.json
- mini_eval_out.json
- preview_eval_out.json
out_demo_files:
- path: eval.py
  description: Evaluation script with metrics computation
</artifact_info>

<github_repo>
Repo URL: https://github.com/ai-inventor-papers/ai-invention-b940ce-shadow-queue-admission-with-recency
Raw data URL: https://raw.githubusercontent.com/ai-inventor-papers/ai-invention-b940ce-shadow-queue-admission-with-recency/main/round-2/evaluation-1/demo/mini_demo_data.json

URLs won't work yet — files pushed to GitHub AFTER notebook creation.
Use local fallback pattern so notebook works locally (now) and in Colab (after deployment).
</github_repo>

<data_file_sizes>
Data files come in three sizes:
- preview_*_out.json — READ THIS to inspect the data structure
- mini_*_out.json (~3 examples) — use for prototyping/testing
- full_*_out.json (complete) — use for the final production run. NEVER open it directly (too large to read into context). Instead, extract values programmatically with shell commands (e.g. grep) or a Python script (use aii-long-running-tasks skill for scripts).
</data_file_sizes>

<install_dependencies_pattern>
Follow the aii-colab skill exactly. It has the install cell pattern, pre-installed package list, numpy 2.0 compat shims, and all Colab-specific rules.
</install_dependencies_pattern>

<data_loading_pattern>
`mini_demo_data.json` = curated subset for the demo.
Use this pattern for Colab compatibility (GitHub URL with local fallback):
```python
GITHUB_DATA_URL = "https://raw.githubusercontent.com/ai-inventor-papers/ai-invention-b940ce-shadow-queue-admission-with-recency/main/round-2/evaluation-1/demo/mini_demo_data.json"
import json, os

def load_data():
    try:
        import urllib.request
        with urllib.request.urlopen(GITHUB_DATA_URL) as response:
            return json.loads(response.read().decode())
    except Exception: pass
    if os.path.exists("mini_demo_data.json"):
        with open("mini_demo_data.json") as f: return json.load(f)
    raise FileNotFoundError("Could not load mini_demo_data.json")
```
</data_loading_pattern>

<notebook_structure>
--- Setup ---
Cell 1 (markdown): Title, description, what this artifact does.
Cell 2 (code): Install dependencies — follow the aii-colab skill's install cell pattern exactly. Fill in all packages imported by the artifact's code.
Cell 3 (code): Imports — copy original import block as-is, plus any additional imports needed for the notebook (e.g. matplotlib for visualization).
Cell 4 (code): Data loading helper — use the <data_loading_pattern> above.
Cell 5 (code): `data = load_data()`

--- Config ---
Config cell (code): Define ALL tunable parameters (iterations, epochs, n_samples, hidden_size, etc.) as variables at the top of this cell. Start with the ABSOLUTE MINIMUM values — the smallest that produce any output at all (e.g. 1 iteration, 2 samples, smallest array size). These get gradually increased during testing — see TODOs.

--- Processing ---
Remaining cells: One code cell per logical section of the original script. Add a markdown cell BEFORE each code cell. Copy code as closely as possible, with these changes:
  1. Replace file paths to use the loaded `data` variable.
  2. Use the config variables from the config cell (NOT hardcoded values).
  3. Minimal fixes are allowed if something doesn't work in notebook context (e.g. adjusting paths, removing CLI args, fixing imports), but keep changes to the absolute minimum.

--- Results ---
Visualization cell (code): Print key results in a readable table, plot numeric data with matplotlib if appropriate.
</notebook_structure>

<priority>
WORKING > OPTIMIZED. A small-scale demo that runs correctly is the goal. Once the notebook passes with minimum config values, scale up only if time permits — do NOT spend multiple retries chasing larger parameters. If a working version exists, finish and move on.
</priority>

<max_notebook_total_runtime>600s (10 min)</max_notebook_total_runtime>

<test_environment>
To test-run the notebook in a clean environment (simulating Colab), create a disposable `.nb_env` in your workspace:
```bash
/usr/local/bin/python3.12 -m venv .nb_env
.nb_env/bin/pip install -q pip jupyter ipykernel
.nb_env/bin/jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=600 code_demo.ipynb --output code_demo.ipynb
rm -rf .nb_env
```
The timeout is set to <max_notebook_total_runtime>. The entire notebook must finish within this time.

What happens: the .venv starts empty (just jupyter). When the notebook's install cell runs, `google.colab` is NOT in sys.modules, so ALL packages get installed — non-Colab packages unconditionally, and Colab packages (numpy, pandas, etc.) at Colab's exact versions via the guard block. The result mirrors Colab's environment as closely as possible. If a cell fails, fix the notebook and re-run.
</test_environment>

FIRST, add ALL of these to your todo list using your task/todo-tracking tool:

CRITICAL: Todo content must be copied exactly as is written here, with NO CHANGES. These todos are intentionally detailed so that another LLM could read each one without any external context and understand exactly what it has to do.


<todos>
TODO 1. Read and STRICTLY follow these skills: aii-colab, aii-long-running-tasks.
TODO 2. Read demo file and relevant preview_* files (preview only). Understand script structure: imports, setup, processing, output. Identify ALL tunable parameters (iterations, epochs, n_samples, hidden_size, batch_size, etc.) — these go in the config cell.
TODO 3. Create `mini_demo_data.json`: curated subset from at most ONE dataset (no more than 100 diverse examples). CRITICAL: do NOT read/grep full output file — may crash. Use `head -c 5000` or stream first entries with Python to pick examples.
TODO 4. Create `code_demo.ipynb` via NotebookEdit following <notebook_structure>. Set ALL config parameters to ABSOLUTE MINIMUM values — the smallest that produce any output (e.g. 1 iteration, 2 samples, smallest array sizes). Test-run using <test_environment>. Fix all errors until it passes.
TODO 5. GRADUALLY SCALE (but don't overdo it): increase config params step by step (e.g. ~2x each round). After each increase: test-run, record runtime, fix errors. STOP SCALING as soon as results look meaningful — a working small-scale demo beats a failed large-scale one. If full original params fit within <max_notebook_total_runtime> (10% margin), use them. Otherwise keep whatever works and comment out the true original values. Do NOT spend more than 2-3 scaling rounds.
TODO 6. Verify: (1) code_demo.ipynb contains GITHUB_DATA_URL = "https://raw.githubusercontent.com/ai-inventor-papers/ai-invention-b940ce-shadow-queue-admission-with-recency/main/round-2/evaluation-1/demo/mini_demo_data.json" exactly, (2) mini_demo_data.json exists, (3) uses GitHub URL pattern not just open('mini_demo_data.json').
</todos>

---

Output the result as JSON to: `./.terminal_claude_agent_struct_out.json`

JSON Schema:
```json
{
  "$defs": {
    "DemoExpectedFiles": {
      "description": "Expected output files from code demo notebook generation.",
      "properties": {
        "notebook": {
          "default": "",
          "description": "Path to the generated demo notebook. Example: 'code_demo.ipynb'",
          "title": "Notebook",
          "type": "string"
        },
        "mini_data_file": {
          "default": "",
          "description": "Path to the mini demo data JSON (curated subset). Example: 'mini_demo_data.json'",
          "title": "Mini Data File",
          "type": "string"
        }
      },
      "title": "DemoExpectedFiles",
      "type": "object"
    }
  },
  "description": "Dataset/experiment/evaluation \u2192 Jupyter notebook demo.\n\nTitle and summary come from the parent artifact (gen_art step),\nnot from the demo agent. The agent only outputs expected files.",
  "properties": {
    "out_expected_files": {
      "$ref": "#/$defs/DemoExpectedFiles",
      "description": "All output files you created. Must include the demo notebook."
    }
  },
  "required": [],
  "title": "CodeDemo",
  "type": "object"
}
```

IMPORTANT: this task is NOT complete until `./.terminal_claude_agent_struct_out.json` exists and contains JSON matching the schema above.
````

### [2] HUMAN-USER prompt · 2026-08-26 22:06:27 UTC

```
Cache admission policies for skewed key popularity in read-heavy key-value stores
```

### [3] SKILL-INPUT — aii-colab · 2026-08-26 22:06:31 UTC

The agent loaded the **aii-colab** skill; its `SKILL.md` (the instructions injected into the agent's context) follows verbatim.

````
---
name: aii-colab
description: "Pins Google Colab's runtime for generated Jupyter notebooks — Python 3.12, the exact pre-installed versions of numpy, pandas, scikit-learn, scipy, torch, transformers and more, and the install cell guarded on google.colab that installs those versions locally but never on Colab, where reinstalling them corrupts already-loaded C extensions. ALWAYS read before writing, editing or testing any .ipynb meant to run on Colab. Triggers: Colab, notebook, ipynb, google.colab, /content, numpy.dtype size changed, ABI mismatch, np.alltrue removed in NumPy 2.0, pip install inside a notebook, nbconvert execute, Colab RAM tiers and session timeouts. NOT for plain Python scripts and repo code (aii-python), for measuring or budgeting local hardware (aii-use-hardware), or for renting cloud GPUs (aii-runpod)."
---

## Colab Runtime (as of 2026-02)

- **Python**: 3.12.12
- **OS**: Linux 6.6.105+ x86_64, glibc 2.35

## Critical Rule: Do NOT pip install pre-installed packages ON COLAB

Colab's core scientific packages have **compiled C extensions** linked against each other at specific ABI versions. Installing ANY different version (even a minor bump) partially overwrites files while the loaded `.so` extensions stay in memory, causing:

- `ValueError: numpy.dtype size changed` (numpy 1.x vs 2.x ABI)
- `ImportError: cannot import name '_center'` (numpy 2.0 vs 2.2 ABI)
- Silent corruption of scipy/sklearn/pandas internals

**On Colab: do NOT install these packages. Use Colab's versions.**
**Locally: MUST install these packages at Colab's exact versions** to match the Colab environment.

## Pre-installed Core Packages

These are pre-installed on Colab. On Colab: skip them. Locally: install at these exact versions.

```
numpy==2.0.2
pandas==2.2.2
scikit-learn==1.6.1
scipy==1.16.3
matplotlib==3.10.0
seaborn==0.13.2
torch==2.9.0+cpu
tensorflow==2.19.0
xgboost==3.1.3
lightgbm==4.6.0
networkx==3.6.1
Pillow==11.3.0
opencv-python==4.13.0.92
sympy==1.14.0
statsmodels==0.14.6
bokeh==3.7.3
plotly==5.24.1
nltk==3.9.1
spacy==3.8.11
transformers==5.0.0
datasets==4.0.0
tokenizers==0.22.2
huggingface_hub==1.4.0
openai==2.17.0
requests==2.32.4
beautifulsoup4==4.13.5
lxml==6.0.2
pydantic==2.12.3
tqdm==4.67.3
rich==13.9.4
tabulate==0.9.0
PyYAML==6.0.3
jsonschema==4.26.0
h5py==3.15.1
Cython==3.0.12
numba==0.60.0
dask==2025.12.0
polars==1.31.0
pyarrow==18.1.0
```

## Install Cell Pattern

The install cell must work on BOTH Colab and local Jupyter. Use this conditional pattern:

```python
import subprocess, sys
def _pip(*a): subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', *a])

# Packages NOT pre-installed on Colab (always install everywhere)
_pip('some-rare-pkg==1.2.3')

# Core packages (pre-installed on Colab, install locally to match Colab env)
if 'google.colab' not in sys.modules:
    _pip('numpy==2.0.2', 'pandas==2.2.2', 'scikit-learn==1.6.1', 'scipy==1.16.3', 'matplotlib==3.10.0')
```

**How this works:**
- On **Colab**: `google.colab` is in `sys.modules` → skips core packages (uses Colab's pre-installed ones) → only installs non-Colab packages
- **Locally**: `google.colab` is NOT in `sys.modules` → installs core packages at Colab's exact versions → local .venv matches Colab's environment as closely as possible

Rules:
- CRITICAL: On Colab, pip installing ANY version of numpy/pandas/sklearn/scipy/matplotlib (even the same version) CORRUPTS the pre-loaded C extensions. These MUST be behind the `google.colab` guard.
- Check the pre-installed package list above. If a package is on that list, put it in the `google.colab` guard block. If not, install it unconditionally.
- For the local (non-Colab) install, use the EXACT versions from the list above so the local environment matches Colab.
- Do NOT use `--force-reinstall` — corrupts Colab system packages.
- Do NOT use `%pip` or `!pip` — use the `_pip()` helper for proper conditional control.
- `%%capture` hides install noise — only add AFTER testing is done.
- If a package requires a newer numpy/scipy than Colab has, that package is INCOMPATIBLE with Colab — find an older version or alternative.

### Example

Code imports: `numpy`, `pandas`, `sklearn`, `matplotlib`, `imodels`, `dit`, `rich`

```python
import subprocess, sys
def _pip(*a): subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', *a])

# imodels, dit — NOT on Colab, always install
_pip('imodels==2.0.4')
_pip('--no-deps', 'dit==1.5')

# numpy, pandas, sklearn, matplotlib, rich — pre-installed on Colab, install locally only
if 'google.colab' not in sys.modules:
    _pip('numpy==2.0.2', 'pandas==2.2.2', 'scikit-learn==1.6.1', 'matplotlib==3.10.0', 'rich==13.9.4')
```

### Checking if a package is pre-installed

Before adding a package to the install cell, check:
1. Is it in the pre-installed list above?
2. If unsure, skip it — Colab has 500+ packages pre-installed. If the import works without installing, it's pre-installed.

## NumPy 2.0 Compatibility for Non-Colab Packages

Colab has **numpy 2.0.2**. NumPy 2.0 removed several long-deprecated APIs that older packages still use. If a non-Colab package was written for numpy 1.x, it may crash at runtime with errors like:

- `AttributeError: np.alltrue was removed in the NumPy 2.0 release`
- `AttributeError: np.sometrue was removed in the NumPy 2.0 release`
- `AttributeError: np.product was removed in the NumPy 2.0 release`

**Fix**: Add a compat shim in the imports cell (BEFORE importing the affected package):

```python
import numpy as np
if not hasattr(np, "alltrue"): np.alltrue = np.all
if not hasattr(np, "sometrue"): np.sometrue = np.any
if not hasattr(np, "product"): np.product = np.prod
```

**When to add this**: After installing non-Colab packages, test-run the notebook. If you get `AttributeError: np.X was removed`, add the corresponding shim. Common offenders: `dit`, older scientific libraries that haven't been updated for numpy 2.0.

## Colab-Specific Gotchas

1. **No kernel restart after pip install** — Unlike local Jupyter, Colab doesn't cleanly reload C extensions after pip install. Once numpy/scipy/sklearn are loaded, their C code stays in memory forever until full runtime reset.

2. **`%pip` vs `_pip()` helper** — In notebook install cells, use the `_pip()` helper (see pattern above) so you can wrap installs in Python `if` conditionals. `%pip` and `!pip` can't be used inside if/else blocks.

3. **File system** — `/content/` is the working directory. Files persist within a session but are lost on runtime disconnect.

4. **Memory** — Free tier: ~12GB RAM. Pro: ~25-50GB. Monitor with `!free -h`.

5. **Timeouts** — Free tier disconnects after ~90 min idle, ~12 hours max session. Pro: longer.

6. **`%%capture`** — Suppresses all cell output including errors. Only use on install cells AFTER verifying they work. During development, leave install output visible.

## Testing Notebooks Locally (Simulating Colab)

The goal: create a clean Python 3.12 .venv that mirrors Colab's environment, then run the notebook in it.

```bash
python3.12 -m venv .nb_env
.nb_env/bin/pip install -q pip jupyter ipykernel
.nb_env/bin/jupyter nbconvert --to notebook --execute code_demo.ipynb --output code_demo.ipynb
rm -rf .nb_env
```

**What happens when the notebook runs in this .venv:**
1. The .venv starts empty (just jupyter + ipykernel)
2. The install cell runs → `google.colab` is NOT in sys.modules
3. Non-Colab packages get installed unconditionally
4. Core packages (numpy, pandas, etc.) get installed at Colab's exact versions via the `google.colab` guard
5. Result: the .venv now has the same packages as Colab + the extra non-Colab packages = as close to Colab as possible

This ensures the notebook works from scratch with an environment matching Colab. If a cell fails, fix the notebook and re-run.
````

### [4] SKILL-INPUT — aii-long-running-tasks · 2026-08-26 22:06:31 UTC

The agent loaded the **aii-long-running-tasks** skill; its `SKILL.md` (the instructions injected into the agent's context) follows verbatim.

````
---
name: aii-long-running-tasks
description: "Scales an experiment or evaluation up in stages — mini, 10, 50, 100, 200, then the largest run that fits — recording runtime at each step and extrapolating time-per-example against the remaining time budget before growing further, with background execution and hard RLIMIT_AS and RLIMIT_CPU caps. ALWAYS read before launching any script expected to run for many minutes or hours over a dataset. Triggers: long-running job, overnight or unattended run, time budget, how many examples fit, extrapolate runtime, start small then scale up, run in background and poll, avoid a timeout, full-dataset evaluation, resource limits. NOT for choosing the concurrency mechanism itself (aii-parallel-computing), measuring the machine's CPU, RAM or GPU (aii-use-hardware), or provisioning cloud pods (aii-runpod)."
---

## Core Principles

1. **Time budget first**: Read your time/runtime constraints before running anything. Set every Bash timeout to fit within the budget.
2. **Start small, scale up**: Run on minimal input first, fix errors, then increase scale.
3. **Extrapolate before scaling**: Use recorded runtimes to predict whether the next step fits in the budget. Don't guess — calculate.
4. **Background execution**: For anything that takes >1 min, run in background (`run_in_background=true`) and do useful work while waiting.
5. **Stop early if needed**: Quality results on less data beats a timeout or crash. It's always acceptable to stop at a smaller scale.

---

## Gradual Scaling Sequence

Run code at increasing data sizes, checking runtime at each step.

Substitute your actual file names:
- `{mini_file}` — mini JSON (3 examples) from dependency workspace
- `{full_file}` — full dataset from dependency workspace
- `{script}` — your processing script (e.g., `./method.py`, `./eval.py`)
- `{schema}` — JSON schema to validate output against

**STEP 1 — MINI DATA:** Run `{script}` on `{mini_file}`. Do NOT truncate logs. Fix all errors. Validate output against `{schema}`. Verify you are NOT using mock scripts, mock data, or mock APIs.

**STEP 2 — 10 EXAMPLES:** Modify `{script}` to load only the first 10 examples from `{full_file}`. Run and fix errors. Validate schema. Record the runtime.

**STEP 3 — 50 EXAMPLES:** Load first 50 examples from `{full_file}`. Run and fix errors. Record runtime. **EXTRAPOLATE**: Using runtimes from steps 2-3, estimate time per example. Calculate how many examples fit in your remaining time budget. If 50 already used most of the budget, stop here.

**STEP 4 — 100 EXAMPLES (if budget allows):** Load first 100 examples. Run and fix errors. Record runtime. Re-extrapolate with the new data point.

**STEP 5 — 200 EXAMPLES (if budget allows):** Load first 200 examples from `{full_file}`. Run and fix errors. Record runtime.

**STEP 6 — MAXIMIZE:** Using all recorded runtimes, extrapolate time-per-example (it may not be perfectly linear — account for overhead). Calculate the maximum number of examples that fits within your remaining time budget with a 10% safety margin. Load that many (or all if they fit). Run and validate.

## Final Testing Phase

After completing the scaling sequence, redo the entire sequence **one more time** up to your final example count:

mini → 10 → 50 → 100 → 200 → max

At each scale: look for issues, fix problems, validate output, ensure it completes within time limits.

---

## Background Execution

For any step that takes >1 min, run as a **background task**:

1. Launch with Bash `run_in_background=true`
2. While it runs, use the time productively:
   - Sanity-check previous outputs
   - Verify file integrity (correct field names, non-empty values)
   - Review code for edge cases at larger scale
   - Prepare the next step
3. Check back on the background task to get results
4. If it failed, fix errors and re-run

---

## Resource Limits

Set hard RAM and CPU time limits so code fails fast instead of crashing the system. Read limits from `<hardware>` and leave headroom for the OS (e.g., if 16GB total, cap at 14GB).

Python example using stdlib `resource` module:
```python
import resource
resource.setrlimit(resource.RLIMIT_AS, (14 * 1024**3, 14 * 1024**3))  # 14GB RAM
resource.setrlimit(resource.RLIMIT_CPU, (3600, 3600))  # 1 hour CPU time
```
Exceeding RAM raises `MemoryError`. Exceeding CPU time sends `SIGKILL`.

## Monitoring

At each step, record runtime AND check resource usage (`free -h` for RAM, `top -bn1 | head -5` for CPU). If memory usage is climbing toward the limit or CPU is pegged, stop and investigate before scaling further.
````

### [5] SYSTEM-USER prompt · 2026-08-26 22:14:56 UTC

```
<validation-feedback>
Attempt 1 failed validation.

The output file `.terminal_claude_agent_struct_out.json` does not exist yet. Produce it as JSON matching the schema.

Produce `.terminal_claude_agent_struct_out.json` again so it contains corrected JSON that matches the schema. Do not invent new fields.
</validation-feedback>
```

### [6] SYSTEM-USER prompt · 2026-08-26 22:15:18 UTC

```
<validation-feedback>
Attempt 2 failed validation.

The output file `.terminal_claude_agent_struct_out.json` does not exist yet. Produce it as JSON matching the schema.

Produce `.terminal_claude_agent_struct_out.json` again so it contains corrected JSON that matches the schema. Do not invent new fields.
</validation-feedback>
```

### [7] SYSTEM-USER prompt · 2026-08-26 22:17:13 UTC

````
<conversion_philosophy>
**MINIMAL CHANGES — PRESERVE THE ORIGINAL CODE**

The goal is to make the artifact's code READABLE, UNDERSTANDABLE, and RUNNABLE in a short time
to someone reviewing the research, with the option to easily scale parameters back to original
values for a full run (which can take much longer). Think of this as annotating and reformatting,
not refactoring.

**DO:**
- Split the original script into logical notebook cells (imports, setup, processing, results)
- Add markdown cells BETWEEN code cells explaining what each section does and why
- Add inline comments where the logic is non-obvious
- Add a visualization/summary cell at the end showing key outputs
- Fix hardcoded file paths to use the GitHub data loading pattern

**DO NOT:**
- Rewrite functions or change algorithms
- Rename variables or restructure logic
- Add error handling, type hints, or "improvements" that weren't in the original
- Simplify or "clean up" the original code
- Remove any original comments or logic
- Change the computational approach

The reader should recognize the original script when looking at the notebook — it's the
same code, just split into cells with explanatory markdown between sections.
</conversion_philosophy>

<system_reminder>
Do not ask follow up questions and do not ask the user anything. Execute all steps independently.
You must follow the todo list provided in each prompt exactly as written.
No placeholders, stubs, or incomplete code — all code must be complete and functional.
</system_reminder>

<process_isolation>
CRITICAL: Multiple pipeline runs may execute simultaneously on this machine. `ps aux | grep method.py` matches ALL runs, not just yours.
- NEVER kill processes by name (`killall`, `pkill -f`, `ps aux | grep ... | xargs kill`). This kills OTHER runs' processes.
- NEVER monitor processes by name (`ps aux | grep method.py`). You will see other runs' processes and get confused.
- ALWAYS use PID-based process management:
  Run: `uv run method.py & PID=$!` or `timeout <seconds> uv run method.py & PID=$!`
  Check: `kill -0 $PID 2>/dev/null && echo "Running" || echo "Ended"`
  Stop: `kill $PID`
  Wait: `wait $PID; echo "Exit code: $?"`
  Monitor: `tail -f logs/run.log & TAIL_PID=$!` then `kill $TAIL_PID` when done
</process_isolation>

<CRITICAL_WARNING__PREVIOUS_ATTEMPT_CRASHED>
YOUR PREVIOUS EXECUTION ATTEMPT CATASTROPHICALLY FAILED.
The entire worker container crashed after 655s.
Error: output_format validation failed after 2 retries: The output file `.terminal_claude_agent_struct_out.json` does not exist yet. Produce it as JSON matching the schema.

Last messages before the crash:
  - [agent_response] The venv exists but pip install of jupyter never completed. Let me retry it directly (foreground, with a generous timeout).
  - [agent_tool_call: Bash] Tool: Bash
cd /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_2/art_QhkYY9QvbyCV
.nb_env/bin/pip install -q pip jupyter ipykernel > /tmp/pipinstall.log 2>&1 &
echo "started PID $!"
  - [agent_tool_result: Bash] Tool: Bash
Result:
{"stdout": "started PID 304", "stderr": "", "interrupted": false, "isImage": false, "noOutputExpected": false}
  - [agent_tool_call: Monitor] Tool: Monitor
{'command': 'until ! kill -0 304 2>/dev/null; do sleep 5; done; echo INSTALL_DONE; tail -20 /tmp/pipinstall.log', 'description': 'wait for jupyter pip install to finish', 'timeout_ms': 300000, 'persistent': False}
  - [agent_tool_result: Monitor] Tool: Monitor
Result:
{"taskId": "bg4syi21y", "timeoutMs": 300000, "persistent": false}
  - [agent_tool_call: Bash] Tool: Bash
echo waiting for jupyter install
  - [agent_tool_result: Bash] Tool: Bash
Result:
{"stdout": "waiting for jupyter install", "stderr": "", "interrupted": false, "isImage": false, "noOutputExpected": false}
  - [agent_response] Waiting for the jupyter install to complete before executing the notebook test.
  - [agent_tool_call: Bash] Tool: Bash
tail -30 /tmp/pipinstall.log 2>&1; echo ---; ls .nb_env/bin/ | grep -i jupyter
  - [agent_tool_result: Bash] Tool: Bash
Result:
{"stdout": "---", "stderr": "", "interrupted": false, "isImage": false, "returnCodeInterpretation": "No matches found", "noOutputExpected": false}
  - [agent_tool_call: Bash] Tool: Bash
ps aux | grep -i "[p]ip install" ; ps aux | grep -i "[3]04"
cd /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_2/art_QhkYY9QvbyCV
cat /tmp/pipinstall.log
ls -la /tmp/pipinstall.log
  - [agent_tool_result: Bash] Tool: Bash
Result:
{"stdout": "root         214  0.0  0.0   4500  3332 ?        Ss   22:12   0:00 /bin/bash -c source /root/.claude/shell-snapshots/snapshot-bash-1787781989405-3qheeb.sh 2>/dev/null || true && shopt -u extglob 2>/dev/null || true && { \\builtin unalias -- 'unsetenv'; \\builtin unset -f -- 'unsetenv'; } >/dev/null 2>&1 || true && eval 'cd /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_2/art_QhkYY9QvbyCV python3 -c \"import json; json.load(open('\"'\"'code_demo.ipynb'\"'\"')); print('\"'\"'valid json'\"'\"')\" /usr/local/bin/python3.12 -m venv .nb_env 2>&1 | tail -5 .nb_env/bin/pip install -q pip jupyter ipykernel 2>&1 | tail -10' < /dev/null && pwd -P >| /tmp/claude-b0f8-cwd\nroot         224  2.9  0.0  97136 91756 ?        S    22:13   0:03 /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_2/art_QhkYY9QvbyCV/.nb_env/bin/python3.12 .nb_env/bin/pip install -q pip jupyter ipykernel\nroot         233  0.0  0.0   4500  3320 ?        Ss   22:14   0:00 /bin/bash -c source /root/.claude/shell-snapshots/snapshot-bash-1787781989405-3qheeb.sh 2>/dev/null || true && shopt -u extglob 2>/dev/null || true && { \\builtin unalias -- 'unsetenv'; \\builtin unset -f -- 'unsetenv'; } >/dev/null 2>&1 || true && eval 'until ! kill -0 $(pgrep -f \"pip install -q pip jupyter\" | head -1) 2>/dev/null; do sleep 3; done; echo DONE' < /dev/null && pwd -P >| /tmp/claude-77ef-cwd\nroot         304  9.1  0.0  81780 76536 ?        S    22:15   0:01 /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_2/art_QhkYY9QvbyCV/.nb_env/bin/python3.12 .nb_env/bin/pip install -q pip jupyter ipykernel\nroot         304  9.0  0.0  81780 76536 ?        S    22:15   0:01 /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_2/art_QhkYY9QvbyCV/.nb_env/bin/python3.12 .nb_env/bin/pip install -q pip jupyter ipykernel\nroot         311  0.0  0.0   4500  3408 ?        Ss   22:15   0:00 /bin/bash -c source /root/.claude/shell-snapshots/snapshot-bash-1787781989405-3qheeb.sh 2>/dev/null || true && shopt -u extglob 2>/dev/null || true && { \\builtin unalias -- 'unsetenv'; \\builtin unset -f -- 'unsetenv'; } >/dev/null 2>&1 || true && eval 'until ! kill -0 304 2>/dev/null; do sleep 5; done; echo INSTALL_DONE; tail -20 /tmp/pipinstall.log' < /dev/null && pwd -P >| /tmp/claude-c495-cwd\n-rw-r--r-- 1 root root 0 Aug 26 22:15 /tmp/pipinstall.log", "stderr": "", "interrupted": false, "isImage": false, "noOutputExpected": false}
  - [agent_tool_call: Bash] Tool: Bash
echo still waiting on background pip installs
  - [agent_tool_result: Bash] Tool: Bash
Result:
{"stdout": "still waiting on background pip installs", "stderr": "", "interrupted": false, "isImage": false, "noOutputExpected": false}
  - [agent_response] Waiting for the jupyter/ipykernel install (running in background) to finish before I execute and validate the notebook.

This was NOT a normal code error — the entire container died. Study the error
and last messages above carefully. Identify what caused the crash and be
EXTREMELY careful to avoid repeating it. Do NOT use the same approach.
</CRITICAL_WARNING__PREVIOUS_ATTEMPT_CRASHED>

<workspace>
Your workspace: `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_2/art_QhkYY9QvbyCV`

CRITICAL: Every file you create, write, or save MUST be inside this workspace directory (subdirectories OK). You MUST NOT write files anywhere outside this path — external paths are READ-ONLY. Use absolute paths for all file operations.

EVERY file write MUST start with `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_2/art_QhkYY9QvbyCV/`:
GOOD: `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_2/art_QhkYY9QvbyCV/file.py`, `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/4_gen_paper_repo/_3_gen_demo_art/notebook_workspaces/iter_2/art_QhkYY9QvbyCV/results/out.json`
BAD: `/tmp/file.py`, `~/output.json`, `./file.py`, any path outside the workspace
</workspace>

<tool_use>
Maximize parallel tool calls. Parallelize independent operations, only sequentialize dependencies.
- Multiple searches/fetches on different topics → parallel in one turn
- Search then fetch results → sequential (need URLs first)
</tool_use>

<task>
Convert this artifact's Python script into a demo notebook with MINIMAL changes to the original code.
Split into cells, add markdown explanations between sections, add a visualization cell at the end.
Output: mini_demo_data.json + code_demo.ipynb (notebook that loads data from GitHub URL)
</task>

<artifact_info>
id: art_QhkYY9QvbyCV
type: evaluation
title: FDR-Corrected Cache Decay Verdict
summary: >-
  This evaluation re-analyzes the 36-group bootstrap results from the Per-Key Decay vs Global Cache Reset experiment (art_gQEGVMwa8ZKC)
  without re-running the underlying 108-cell cache simulation sweep. It (1) computes a two-sided percentile-bootstrap p-value
  per group and applies Benjamini-Hochberg and Benjamini-Yekutieli FDR correction via statsmodels.stats.multitest.multipletests,
  finding 26/36 groups (including all 3 win-corner groups at ratio=0.01, alpha=1.2) survive at q=0.05, while flagging that
  the groups' shared-seed structure violates BH's independence/PRDS assumption; (2) re-simulates ONLY the win-corner cell
  (ratio=0.01, alpha=1.2, all 4 drift scenarios, 3 seeds) across a 3x3 grid of CoV threshold pairs (108 targeted proposed-only
  runs, baseline reused from existing data), finding the advantage holds in only 12/36 threshold-scenario combinations and
  reproduces the original 0.5/1.5 result exactly (delta=0.0) as an internal consistency check; (3) derives an analytical per-request
  operation-count table from method.py's actual estimator code plus a wall-clock microbenchmark, finding the proposed estimator
  costs ~1.7x the operations and ~2.1x the wall-clock time of the baseline; (4) documents that no short-reset-ablation baseline
  exists anywhere in the experiment artifact (explicit gap, not fabricated), and runs the already-built simulator once each
  for baseline/proposed on the real Twitter cluster026 trace (loaded fresh from art_f48a8QRaZrIB, 80,000 requests, 67,681
  distinct keys), finding steady-state hit-ratio parity within the pre-registered 1-percentage-point margin (-0.42pp) plus
  an explicitly-labeled exploratory/unvalidated changepoint-based recovery comparison since the real trace has no ground-truth
  drift labels; and (5) recomputes a single corrected memory-overhead figure directly from phaseC's memory_footprint_table
  (5.14x-5.68x, mean 5.22x), resolving the inconsistency between the experiment's own 'roughly 3-5x' prose and the hypothesis's
  pre-registered 5.1-5.7x figure in favor of the latter, and confirming this exceeds the pre-registered 'no more than ~2x'
  disconfirmation bound. All five sub-analyses are synthesized into one non-hedged final verdict: INCONCLUSIVE_UNDERPOWERED.
  The win-corner groups survive FDR correction, but the threshold-sensitivity grid shows the win is a knife-edge artifact
  of the specific 0.5/1.5 CoV threshold pair (holding in only a third of nearby threshold choices), no short-reset-ablation
  control was ever run to rule out simple baseline under-tuning, the real-trace evidence only supports parity (not a recovery-speed
  advantage), and the corrected 5.14x-5.68x memory overhead is disproportionate to a benefit that does not survive robustness
  checks. Downstream paper-writing steps should present the per-key decay mechanism as an unconfirmed, likely tuning-fragile
  result rather than a genuine advance, and should use the corrected 5.14x-5.68x memory figure (not the artifact's own 'roughly
  3-5x') whenever memory overhead is quoted.
workspace_path: >-
  /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_2/gen_art/gen_art_evaluation_1
out_expected_files:
- eval.py
- full_eval_out.json
- mini_eval_out.json
- preview_eval_out.json
out_demo_files:
- path: eval.py
  description: Evaluation script with metrics computation
</artifact_info>

<github_repo>
Repo URL: https://github.com/ai-inventor-papers/ai-invention-b940ce-shadow-queue-admission-with-recency
Raw data URL: https://raw.githubusercontent.com/ai-inventor-papers/ai-invention-b940ce-shadow-queue-admission-with-recency/main/round-2/evaluation-1/demo/mini_demo_data.json

URLs won't work yet — files pushed to GitHub AFTER notebook creation.
Use local fallback pattern so notebook works locally (now) and in Colab (after deployment).
</github_repo>

<data_file_sizes>
Data files come in three sizes:
- preview_*_out.json — READ THIS to inspect the data structure
- mini_*_out.json (~3 examples) — use for prototyping/testing
- full_*_out.json (complete) — use for the final production run. NEVER open it directly (too large to read into context). Instead, extract values programmatically with shell commands (e.g. grep) or a Python script (use aii-long-running-tasks skill for scripts).
</data_file_sizes>

<install_dependencies_pattern>
Follow the aii-colab skill exactly. It has the install cell pattern, pre-installed package list, numpy 2.0 compat shims, and all Colab-specific rules.
</install_dependencies_pattern>

<data_loading_pattern>
`mini_demo_data.json` = curated subset for the demo.
Use this pattern for Colab compatibility (GitHub URL with local fallback):
```python
GITHUB_DATA_URL = "https://raw.githubusercontent.com/ai-inventor-papers/ai-invention-b940ce-shadow-queue-admission-with-recency/main/round-2/evaluation-1/demo/mini_demo_data.json"
import json, os

def load_data():
    try:
        import urllib.request
        with urllib.request.urlopen(GITHUB_DATA_URL) as response:
            return json.loads(response.read().decode())
    except Exception: pass
    if os.path.exists("mini_demo_data.json"):
        with open("mini_demo_data.json") as f: return json.load(f)
    raise FileNotFoundError("Could not load mini_demo_data.json")
```
</data_loading_pattern>

<notebook_structure>
--- Setup ---
Cell 1 (markdown): Title, description, what this artifact does.
Cell 2 (code): Install dependencies — follow the aii-colab skill's install cell pattern exactly. Fill in all packages imported by the artifact's code.
Cell 3 (code): Imports — copy original import block as-is, plus any additional imports needed for the notebook (e.g. matplotlib for visualization).
Cell 4 (code): Data loading helper — use the <data_loading_pattern> above.
Cell 5 (code): `data = load_data()`

--- Config ---
Config cell (code): Define ALL tunable parameters (iterations, epochs, n_samples, hidden_size, etc.) as variables at the top of this cell. Start with the ABSOLUTE MINIMUM values — the smallest that produce any output at all (e.g. 1 iteration, 2 samples, smallest array size). These get gradually increased during testing — see TODOs.

--- Processing ---
Remaining cells: One code cell per logical section of the original script. Add a markdown cell BEFORE each code cell. Copy code as closely as possible, with these changes:
  1. Replace file paths to use the loaded `data` variable.
  2. Use the config variables from the config cell (NOT hardcoded values).
  3. Minimal fixes are allowed if something doesn't work in notebook context (e.g. adjusting paths, removing CLI args, fixing imports), but keep changes to the absolute minimum.

--- Results ---
Visualization cell (code): Print key results in a readable table, plot numeric data with matplotlib if appropriate.
</notebook_structure>

<priority>
WORKING > OPTIMIZED. A small-scale demo that runs correctly is the goal. Once the notebook passes with minimum config values, scale up only if time permits — do NOT spend multiple retries chasing larger parameters. If a working version exists, finish and move on.
</priority>

<max_notebook_total_runtime>600s (10 min)</max_notebook_total_runtime>

<test_environment>
To test-run the notebook in a clean environment (simulating Colab), create a disposable `.nb_env` in your workspace:
```bash
/usr/local/bin/python3.12 -m venv .nb_env
.nb_env/bin/pip install -q pip jupyter ipykernel
.nb_env/bin/jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=600 code_demo.ipynb --output code_demo.ipynb
rm -rf .nb_env
```
The timeout is set to <max_notebook_total_runtime>. The entire notebook must finish within this time.

What happens: the .venv starts empty (just jupyter). When the notebook's install cell runs, `google.colab` is NOT in sys.modules, so ALL packages get installed — non-Colab packages unconditionally, and Colab packages (numpy, pandas, etc.) at Colab's exact versions via the guard block. The result mirrors Colab's environment as closely as possible. If a cell fails, fix the notebook and re-run.
</test_environment>

FIRST, add ALL of these to your todo list using your task/todo-tracking tool:

CRITICAL: Todo content must be copied exactly as is written here, with NO CHANGES. These todos are intentionally detailed so that another LLM could read each one without any external context and understand exactly what it has to do.


<todos>
TODO 1. Read and STRICTLY follow these skills: aii-colab, aii-long-running-tasks.
TODO 2. Read demo file and relevant preview_* files (preview only). Understand script structure: imports, setup, processing, output. Identify ALL tunable parameters (iterations, epochs, n_samples, hidden_size, batch_size, etc.) — these go in the config cell.
TODO 3. Create `mini_demo_data.json`: curated subset from at most ONE dataset (no more than 100 diverse examples). CRITICAL: do NOT read/grep full output file — may crash. Use `head -c 5000` or stream first entries with Python to pick examples.
TODO 4. Create `code_demo.ipynb` via NotebookEdit following <notebook_structure>. Set ALL config parameters to ABSOLUTE MINIMUM values — the smallest that produce any output (e.g. 1 iteration, 2 samples, smallest array sizes). Test-run using <test_environment>. Fix all errors until it passes.
TODO 5. GRADUALLY SCALE (but don't overdo it): increase config params step by step (e.g. ~2x each round). After each increase: test-run, record runtime, fix errors. STOP SCALING as soon as results look meaningful — a working small-scale demo beats a failed large-scale one. If full original params fit within <max_notebook_total_runtime> (10% margin), use them. Otherwise keep whatever works and comment out the true original values. Do NOT spend more than 2-3 scaling rounds.
TODO 6. Verify: (1) code_demo.ipynb contains GITHUB_DATA_URL = "https://raw.githubusercontent.com/ai-inventor-papers/ai-invention-b940ce-shadow-queue-admission-with-recency/main/round-2/evaluation-1/demo/mini_demo_data.json" exactly, (2) mini_demo_data.json exists, (3) uses GitHub URL pattern not just open('mini_demo_data.json').
</todos>

---

Output the result as JSON to: `./.terminal_claude_agent_struct_out.json`

JSON Schema:
```json
{
  "$defs": {
    "DemoExpectedFiles": {
      "description": "Expected output files from code demo notebook generation.",
      "properties": {
        "notebook": {
          "default": "",
          "description": "Path to the generated demo notebook. Example: 'code_demo.ipynb'",
          "title": "Notebook",
          "type": "string"
        },
        "mini_data_file": {
          "default": "",
          "description": "Path to the mini demo data JSON (curated subset). Example: 'mini_demo_data.json'",
          "title": "Mini Data File",
          "type": "string"
        }
      },
      "title": "DemoExpectedFiles",
      "type": "object"
    }
  },
  "description": "Dataset/experiment/evaluation \u2192 Jupyter notebook demo.\n\nTitle and summary come from the parent artifact (gen_art step),\nnot from the demo agent. The agent only outputs expected files.",
  "properties": {
    "out_expected_files": {
      "$ref": "#/$defs/DemoExpectedFiles",
      "description": "All output files you created. Must include the demo notebook."
    }
  },
  "required": [],
  "title": "CodeDemo",
  "type": "object"
}
```

IMPORTANT: this task is NOT complete until `./.terminal_claude_agent_struct_out.json` exists and contains JSON matching the schema above.
````

### [8] HUMAN-USER prompt · 2026-08-26 22:17:13 UTC

```
Cache admission policies for skewed key popularity in read-heavy key-value stores
```

### [9] SYSTEM-USER prompt · 2026-08-26 22:18:45 UTC

```
<validation-feedback>
Attempt 1 failed validation.

The output file `.terminal_claude_agent_struct_out.json` does not exist yet. Produce it as JSON matching the schema.

Produce `.terminal_claude_agent_struct_out.json` again so it contains corrected JSON that matches the schema. Do not invent new fields.
</validation-feedback>
```

### [10] SYSTEM-USER prompt · 2026-08-26 22:28:29 UTC

```
<validation-feedback>
Attempt 2 failed validation.

The output file `.terminal_claude_agent_struct_out.json` does not exist yet. Produce it as JSON matching the schema.

Produce `.terminal_claude_agent_struct_out.json` again so it contains corrected JSON that matches the schema. Do not invent new fields.
</validation-feedback>
```
