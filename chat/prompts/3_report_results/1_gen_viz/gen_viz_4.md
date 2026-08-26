# gen_viz_4 — report_results

> Phase: `gen_paper_repo` · `gen_viz`
> Run: `iter1_eb86f00c4c5a` — Why Per-Key Cache Decay Rarely Beats a Cheaper Shorter Reset
>
> Full, verbatim record of every prompt the AI Inventor pipeline gave this agent — system-user, human-user and skill-input — in the order they landed. Nothing truncated.

## Task: `gen_viz_4` (terminal_claude_agent)

### [1] SYSTEM-USER prompt · 2026-08-26 21:49:04 UTC

````
<research_methodology>
Create figures that belong in a top-venue paper.

- Every figure needs a clear takeaway visible at a glance.
- Choose chart types that match the data relationship (comparisons, trends, correlations, distributions).
- Include uncertainty (error bars, confidence intervals) when showing experimental results.
- Keep it clean — no clutter, clear labels with units, readable at print size.
</research_methodology>

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
Your workspace: `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/4_gen_paper_repo/_2_gen_viz/gen_viz_4`

CRITICAL: Every file you create, write, or save MUST be inside this workspace directory (subdirectories OK). You MUST NOT write files anywhere outside this path — external paths are READ-ONLY. Use absolute paths for all file operations.

EVERY file write MUST start with `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/4_gen_paper_repo/_2_gen_viz/gen_viz_4/`:
GOOD: `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/4_gen_paper_repo/_2_gen_viz/gen_viz_4/file.py`, `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/4_gen_paper_repo/_2_gen_viz/gen_viz_4/results/out.json`
BAD: `/tmp/file.py`, `~/output.json`, `./file.py`, any path outside the workspace
</workspace>

<task>
Render a publication-quality DATA figure for a top-tier venue research paper.

This figure plots numbers, so it is RENDERED from those numbers — not drawn by an image model. Use the aii-data-fig-gen skill. The output is deterministic: run it once, look at it, fix the spec if the data or labels are wrong, run it again.

STEPS:
1. Read the skill: `.claude/skills/aii-data-fig-gen/SKILL.md`.
2. Pick the chart type that fits the specification below. `python <skill>/scripts/chart_gen.py --list-types` lists them; `--example <type>` prints a complete spec to copy.
3. Write your spec to `fig_memory_spec.json` in your workspace. Put EVERY numeric value from the specification into it — the spec is the figure.
4. Render it:
   `python <skill>/scripts/chart_gen.py --spec fig_memory_spec.json --out fig_memory_v0`
   That writes `fig_memory_v0.pdf` (the deliverable, vector) and `fig_memory_v0.png` (for you to look at).
5. READ THE PNG BACK and check it against the checklist below.
6. If anything is wrong, edit the spec and re-render. Repeat until clean — this is cheap and deterministic, so there is no attempt limit and no reason to accept a flawed figure.

DELIVERABLE: `fig_memory_v0.pdf` in your workspace root. Leave `fig_memory_spec.json` there too — it is the figure's source, and the step files it next to the figure so the figure stays reproducible.

Verification checklist (after EVERY render) — these are the things only you can check, because they are about whether the figure says what you meant:
- Every number in the figure matches the specification — no invented or dropped values
- Axis labels state what is measured AND its units
- Axis ranges make the comparison readable rather than flattening it
- The chart type still makes the point once you can see it drawn
- The caption describes what is actually drawn

The generator already REFUSES the rest rather than shipping them, so a figure you can read back cannot have them: overlapping or cut-off labels, a legend covering the data, a series drawn without a name beside named ones, two series a reader cannot tell apart, and a fit or a scale that the data cannot support. When it exits non-zero the message names the exact key, index or label and what to change — do that rather than re-rolling.

Reach for a generator first, and hand-write only if none fits. Every type in `--list-types` already carries the house style, the data-integrity checks and the layout fixes, so using one is less work than plotting by hand and the result matches every other figure in the paper.

If nothing in the catalogue fits, writing matplotlib yourself is expected and supported — novel figures exist. When you do, import the house style AND its layout passes so the figure still belongs to the set — `apply_house_style`, `place_legend`, `place_point_label`, `fit_legends`, `clear_legends_of_data`, `fit_tick_labels`, `fit_titles`, `rasterize_dense_clouds`, `assert_legends_clear_of_data`, `assert_series_are_distinguishable`, `assert_axis_names_are_unique` from `chart_style`, and `fit_point_labels` + `assert_text_is_legible` from `chart_geometry`, the last of which raises if any label ends up printed over another or cut off at the edge. Build legends with `place_legend` and point names with `place_point_label` — a legend made with a bare `ax.legend` cannot be reflowed when it turns out too wide, and a name written with a bare `ax.annotate` will not be moved off the marker it landed on. The "Use a generator when one fits" section of SKILL.md has the exact snippet and the order to call them in. What you lose is the automatic checking that the picture agrees with the numbers, so verify every value yourself against the specification.
</task>

<figure_specification>
Figure ID: fig_memory
Title: Memory and Compute Overhead
Caption: Left: memory-footprint overhead of the per-key-decay estimator relative to the global-reset baseline, at three cache-to-key-space ratios (Zipf alpha=1.0). Right: per-request compute cost, both an analytical elementary-operation count and a wall-clock microbenchmark over 100,000 calls. Both cost measures exceed the hypothesis's own pre-registered disconfirmation bound of roughly 2x memory.
Data and chart description: Two-panel figure, 16:9 aspect ratio, side by side. Left panel: grouped bar chart, x-axis 'Cache-to-key-space ratio' with three categories '0.01', '0.05', '0.10', y-axis 'Memory overhead (proposed / baseline)', range 0 to 6, single bar series 'Memory overhead ratio' with values 5.137, 5.169, 5.271, with a horizontal dashed reference line at y=2.0 labeled 'pre-registered disconfirmation bound (~2x)' and at y=1.0 labeled 'parity'. Annotate the overall measured range across all 9 (ratio, skew) cells as a text box: 'full range across 9 cells: 5.14x - 5.68x, mean 5.22x'. Right panel: grouped bar chart, x-axis with two categories 'Analytical op count' and 'Wall-clock (100k calls)', y-axis left 'Baseline (elementary ops or seconds)' and paired bars per category: for 'Analytical op count' baseline=25 ops, proposed=43 ops (ratio 1.72x); for 'Wall-clock (100k calls)' baseline=0.178 seconds, proposed=0.380 seconds (ratio 2.13x). Use two distinct colors for 'Baseline' and 'Proposed per-key decay' series consistent across both panels, with a shared legend. Add ratio labels above each pair: '1.72x' and '2.13x'.
Aspect Ratio: 16:9
Summary: Quantifies the corrected 5.14x-5.68x memory overhead and the 1.72x-2.13x compute overhead of per-key decay versus the global-reset baseline.
</figure_specification>


---

Output the result as JSON to: `./.terminal_claude_agent_struct_out.json`

JSON Schema:
```json
{
  "$defs": {
    "VizExpectedFiles": {
      "description": "Expected output files from viz generation.",
      "properties": {
        "image_path": {
          "description": "Path to the generated figure image file. Example: 'fig1_v0.jpg'",
          "title": "Image Path",
          "type": "string"
        }
      },
      "required": [
        "image_path"
      ],
      "title": "VizExpectedFiles",
      "type": "object"
    }
  },
  "description": "Structured output from viz figure generation agent.",
  "properties": {
    "title": {
      "description": "Figure title in plain, everyday language \u2014 short and jargon-free so a non-expert grasps it at a glance. Aim for about 4-8 words (~40 characters).",
      "maxLength": 90,
      "minLength": 12,
      "title": "Title",
      "type": "string"
    },
    "summary": {
      "description": "Brief summary of the generated figure: what it shows, style, any issues fixed",
      "maxLength": 5000,
      "minLength": 500,
      "title": "Summary",
      "type": "string"
    },
    "out_expected_files": {
      "$ref": "#/$defs/VizExpectedFiles",
      "description": "Output file you created. Must include the generated figure image path."
    }
  },
  "required": [
    "title",
    "summary",
    "out_expected_files"
  ],
  "title": "VizFigureOutput",
  "type": "object"
}
```

IMPORTANT: this task is NOT complete until `./.terminal_claude_agent_struct_out.json` exists and contains JSON matching the schema above.
````

### [2] HUMAN-USER prompt · 2026-08-26 21:49:04 UTC

```
Cache admission policies for skewed key popularity in read-heavy key-value stores
```

### [3] SYSTEM-USER prompt · 2026-08-26 21:50:28 UTC

```
[Image: original 2400x1350, displayed at 2000x1125. Multiply coordinates by 1.20 to map to original image.]
```

### [4] SYSTEM-USER prompt · 2026-08-26 21:50:54 UTC

```
[Image: original 2400x1350, displayed at 2000x1125. Multiply coordinates by 1.20 to map to original image.]
```
