"""Create an HTML report from saved eval runs.

Run:
    .venv/bin/python visualize_results.py

Then open:
    results/report.html
"""
import html
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
OUT = RESULTS / "report.html"


def load_runs():
    runs = []
    for path in sorted(RESULTS.glob("*.json")):
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if "score" not in data or "results" not in data:
            continue
        stamp = path.name.split("_", 1)[0]
        try:
            when = datetime.strptime(stamp, "%Y%m%d-%H%M%S")
            display_time = when.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            when = datetime.fromtimestamp(path.stat().st_mtime)
            display_time = when.strftime("%Y-%m-%d %H:%M:%S")
        data["_file"] = path.name
        data["_time"] = display_time
        data["_sort"] = when
        runs.append(data)
    return sorted(runs, key=lambda r: (r["_sort"], r.get("label", "")))


def esc(value):
    return html.escape(str(value), quote=True)


def rules_for(run):
    return run.get("learned_rules", run.get("reinforcements", []))


def failed_checks(result):
    return [c for c in result.get("checks", []) if not c.get("pass")]


def render_score_chart(runs):
    if not runs:
        return "<p>No result files found.</p>"
    bars = []
    for run in runs:
        score = float(run.get("score", 0))
        pct = round(score * 100)
        label = esc(run.get("label", "run"))
        bars.append(f"""
        <div class="bar-row">
          <div class="bar-label">
            <strong>{label}</strong>
            <span>{esc(run["_time"])}</span>
          </div>
          <div class="bar-track">
            <div class="bar-fill" style="width: {pct}%"></div>
          </div>
          <div class="bar-score">{pct}%</div>
        </div>
        """)
    return "\n".join(bars)


def render_runs(runs):
    blocks = []
    for run in runs:
        rules = rules_for(run)
        results = run.get("results", [])
        passed = sum(1 for r in results if r.get("pass"))
        total = len(results)
        score = round(float(run.get("score", 0)) * 100)

        scenario_rows = []
        for result in results:
            status = "pass" if result.get("pass") else "fail"
            failed = failed_checks(result)
            failed_text = "All checks passed."
            if failed:
                failed_text = "; ".join(c.get("check", "unknown check") for c in failed)
            checks = []
            for check in result.get("checks", []):
                check_status = "pass" if check.get("pass") else "fail"
                evidence = check.get("evidence")
                evidence_html = f"<div class='evidence'>{esc(evidence)}</div>" if evidence else ""
                checks.append(
                    f"<li class='{check_status}'><span>{esc(check.get('kind', 'check'))}</span> "
                    f"{esc(check.get('check', 'unnamed check'))}{evidence_html}</li>"
                )
            scenario_rows.append(f"""
            <details class="scenario {status}">
              <summary>
                <span class="pill {status}">{status.upper()}</span>
                <strong>{esc(result.get("id", "scenario"))}</strong>
                <small>{esc(failed_text)}</small>
              </summary>
              <ul class="checks">{''.join(checks)}</ul>
              <pre>{esc(result.get("transcript", ""))}</pre>
            </details>
            """)

        rule_items = []
        for rule in rules:
            root_cause = rule.get("root_cause", "")
            addresses = ", ".join(rule.get("addresses", []))
            rule_items.append(f"""
            <li>
              <strong>{esc(rule.get("rule", ""))}</strong>
              <p>{esc(root_cause)}</p>
              <small>Targets: {esc(addresses)}</small>
            </li>
            """)
        if not rule_items:
            rule_items.append("<li>No learned rules in this run.</li>")

        blocks.append(f"""
        <section class="run">
          <header>
            <div>
              <h2>{esc(run.get("label", "run"))}</h2>
              <p>{esc(run["_time"])} | {esc(run["_file"])}</p>
            </div>
            <div class="score">{score}%<span>{passed}/{total} passed</span></div>
          </header>
          <h3>Rules Used</h3>
          <ul class="rules">{''.join(rule_items)}</ul>
          <h3>Scenarios</h3>
          {''.join(scenario_rows)}
        </section>
        """)
    return "\n".join(blocks)


def main():
    runs = load_runs()
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agent Improvement Report</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f7f4;
      --ink: #202124;
      --muted: #6a6f73;
      --line: #d8d6cf;
      --panel: #ffffff;
      --good: #197348;
      --bad: #b42318;
      --accent: #2563eb;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
    }}
    main {{
      width: min(1120px, calc(100vw - 32px));
      margin: 32px auto 56px;
    }}
    h1 {{ margin: 0 0 8px; font-size: 32px; }}
    h2, h3 {{ margin: 0; }}
    .intro {{ color: var(--muted); margin: 0 0 24px; }}
    .chart, .run {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 20px;
      margin: 18px 0;
    }}
    .bar-row {{
      display: grid;
      grid-template-columns: minmax(170px, 260px) 1fr 64px;
      gap: 14px;
      align-items: center;
      margin: 12px 0;
    }}
    .bar-label span, header p, small, .score span {{
      display: block;
      color: var(--muted);
      font-size: 13px;
      margin-top: 3px;
    }}
    .bar-track {{
      height: 18px;
      border: 1px solid var(--line);
      background: #eceae4;
      border-radius: 999px;
      overflow: hidden;
    }}
    .bar-fill {{
      height: 100%;
      background: linear-gradient(90deg, var(--accent), var(--good));
    }}
    .bar-score {{ text-align: right; font-weight: 700; }}
    .run header {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 14px;
      margin-bottom: 16px;
    }}
    .score {{
      min-width: 96px;
      text-align: right;
      font-size: 30px;
      font-weight: 800;
    }}
    .rules {{ padding-left: 20px; }}
    .rules p {{ margin: 6px 0; color: var(--muted); }}
    .scenario {{
      border: 1px solid var(--line);
      border-radius: 8px;
      margin: 10px 0;
      background: #fff;
    }}
    .scenario summary {{
      cursor: pointer;
      display: grid;
      grid-template-columns: auto 180px 1fr;
      gap: 10px;
      align-items: center;
      padding: 12px;
    }}
    .pill {{
      font-size: 12px;
      font-weight: 800;
      border-radius: 999px;
      padding: 4px 8px;
      color: white;
    }}
    .pill.pass {{ background: var(--good); }}
    .pill.fail {{ background: var(--bad); }}
    .checks {{ margin: 0; padding: 0 20px 10px 44px; }}
    .checks li {{ margin: 8px 0; }}
    .checks li.pass {{ color: var(--good); }}
    .checks li.fail {{ color: var(--bad); }}
    .checks span {{
      color: var(--muted);
      display: inline-block;
      min-width: 48px;
      text-transform: uppercase;
      font-size: 11px;
      font-weight: 800;
    }}
    .evidence {{ color: var(--muted); margin-top: 4px; }}
    pre {{
      white-space: pre-wrap;
      margin: 0;
      padding: 14px;
      border-top: 1px solid var(--line);
      background: #f7f7f4;
      overflow: auto;
      font-size: 13px;
      line-height: 1.45;
    }}
    @media (max-width: 720px) {{
      .bar-row {{ grid-template-columns: 1fr; }}
      .bar-score {{ text-align: left; }}
      .run header {{ display: block; }}
      .score {{ text-align: left; margin-top: 12px; }}
      .scenario summary {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main>
    <h1>Agent Improvement Report</h1>
    <p class="intro">Generated from saved JSON files in <code>results/</code>. Higher bars mean more scenarios passed.</p>
    <section class="chart">
      <h2>Score Over Runs</h2>
      {render_score_chart(runs)}
    </section>
    {render_runs(runs)}
  </main>
</body>
</html>
"""
    RESULTS.mkdir(exist_ok=True)
    OUT.write_text(page)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
