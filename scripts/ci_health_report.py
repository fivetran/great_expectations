#!/usr/bin/env python3
"""
ci_health_report.py - CI Health Report Generator
=================================================

Generates a Markdown health report for *scheduled* runs of the ci.yml workflow
over a configurable lookback window (default: 28 days).

Requirements
------------
* Python 3.10+
* ``gh`` CLI (https://cli.github.com/) installed and authenticated with at
  least ``repo`` scope (read access to Actions).

Usage
-----
    python scripts/ci_health_report.py [--days N] [--output FILE] [--workers N]

Arguments
---------
--days N      Look-back window in days (default: 28)
--output FILE Output file path (default: ci_health_report_YYYYMMDD_HHMM.md)
--workers N   Parallel workers for fetching per-run job data (default: 8)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = "great-expectations/great_expectations"
WORKFLOW = "ci.yml"
DEFAULT_DAYS = 28
DEFAULT_WORKERS = 8


# ---------------------------------------------------------------------------
# Terminal helpers
# ---------------------------------------------------------------------------


def _err(msg: str, *, end: str = "\n") -> None:
    print(msg, end=end, flush=True, file=sys.stderr)


def _die(msg: str, hint: str = "") -> None:
    print(f"\n\033[31mERROR:\033[0m {msg}", file=sys.stderr)
    if hint:
        print(f"  \033[33mHint:\033[0m {hint}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------


def preflight_checks() -> None:
    """Verify gh is installed, authenticated, and has repo access."""
    # 1. gh installed?
    try:
        r = subprocess.run(["gh", "--version"], check=False, capture_output=True)
    except FileNotFoundError:
        _die(
            "'gh' CLI is not installed.",
            "Install from https://cli.github.com/ then run 'gh auth login'.",
        )
    if r.returncode != 0:
        _die("'gh' CLI exited with an error.", "Try reinstalling from https://cli.github.com/")

    # 2. gh authenticated?
    r = subprocess.run(["gh", "auth", "status"], check=False, capture_output=True, text=True)
    if r.returncode != 0:
        _die("gh is not authenticated.", "Run: gh auth login")

    # 3. Repo accessible?
    r = subprocess.run(
        ["gh", "api", f"repos/{REPO}", "--jq", ".name"],
        check=False,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        _die(
            f"Cannot access repository '{REPO}'.",
            "Check your token scopes: gh auth refresh -s repo",
        )

    _err("      gh OK")


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------


def _gh_api_lines(
    endpoint: str,
    jq_filter: str,
    paginate: bool = False,
    **query_params: str,
) -> list:
    """
    Run ``gh api <endpoint> [--paginate] --jq <filter>``.

    Query parameters are appended directly to the URL so that gh keeps the
    request method as GET.  Using ``-f`` flags causes gh to default to POST,
    which returns 404 for Actions endpoints.

    With ``--jq``, gh prints one JSON value per line per page.  We parse every
    non-empty line and return the collected objects.

    Raises RuntimeError on non-zero exit.
    """
    if query_params:
        qs = "&".join(f"{k}={v}" for k, v in query_params.items())
        full_endpoint = f"{endpoint}?{qs}"
    else:
        full_endpoint = endpoint

    cmd = ["gh", "api"]
    if paginate:
        cmd.append("--paginate")
    cmd.append(full_endpoint)
    cmd += ["--jq", jq_filter]

    r = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or f"gh api failed for {endpoint}")

    items = []
    for raw in r.stdout.splitlines():
        stripped = raw.strip()
        if stripped:
            try:
                items.append(json.loads(stripped))
            except json.JSONDecodeError:
                pass
    return items


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------


def fetch_runs(since: datetime) -> list[dict]:
    """Return all scheduled ci.yml runs on or after ``since``."""
    _err("  Fetching workflow run list...", end="")
    # We omit the `created` API filter because its query-string encoding with
    # the gh CLI is unreliable; Python-side filtering on the small result set is fine.
    runs = _gh_api_lines(
        f"repos/{REPO}/actions/workflows/{WORKFLOW}/runs",
        ".workflow_runs[]",
        paginate=True,
        event="schedule",
        per_page="100",
    )
    runs = [r for r in runs if _parse_dt(r["created_at"]) >= since]
    _err(f" {len(runs)} runs found.")
    return runs


def fetch_jobs(run_id: int) -> list[dict]:
    """Return all jobs for a single workflow run."""
    return _gh_api_lines(
        f"repos/{REPO}/actions/runs/{run_id}/jobs",
        ".jobs[]",
        paginate=True,
        per_page="100",
    )


def _parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------


def _percentile(data: list[float], p: float) -> float | None:
    """Return the p-th percentile (0-100) of *data* using linear interpolation."""
    if not data:
        return None
    sd = sorted(data)
    n = len(sd)
    if n == 1:
        return sd[0]
    idx = (n - 1) * p / 100.0
    lo = int(idx)
    hi = min(lo + 1, n - 1)
    return sd[lo] + (sd[hi] - sd[lo]) * (idx - lo)


def _fmt(seconds: float | None) -> str:
    """Human-readable duration string."""
    if seconds is None:
        return "N/A"
    s = int(seconds)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    return f"{m}m {s:02d}s"


def _run_duration(run: dict) -> float | None:
    start = run.get("run_started_at") or run.get("created_at")
    end = run.get("updated_at")
    if not start or not end:
        return None
    d = (_parse_dt(end) - _parse_dt(start)).total_seconds()
    return d if d > 0 else None


def _job_duration(job: dict) -> float | None:
    s, e = job.get("started_at"), job.get("completed_at")
    if not s or not e:
        return None
    d = (_parse_dt(e) - _parse_dt(s)).total_seconds()
    return d if d > 0 else None


def _week_start(dt: datetime) -> str:
    """Return the Monday of the week containing *dt* as YYYY-MM-DD."""
    monday = dt - timedelta(days=dt.weekday())
    return monday.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Markdown table builder
# ---------------------------------------------------------------------------


class MDTable:
    def __init__(self, headers: list[str]) -> None:
        self.headers = headers
        self.rows: list[list[str]] = []

    def add(self, *cells: str) -> None:
        self.rows.append([str(c) for c in cells])

    def render(self) -> list[str]:
        widths = [
            max(len(h), *(len(r[i]) for r in self.rows if i < len(r)), 3)
            for i, h in enumerate(self.headers)
        ]

        def _pad(cells: list[str]) -> str:
            return (
                "| "
                + " | ".join(
                    (cells[i] if i < len(cells) else "").ljust(widths[i])
                    for i in range(len(self.headers))
                )
                + " |"
            )

        sep = "| " + " | ".join("-" * w for w in widths) + " |"
        lines = [_pad(self.headers), sep]
        lines.extend(_pad(r) for r in self.rows)
        return lines


# ---------------------------------------------------------------------------
# Report sections
# ---------------------------------------------------------------------------


def _section_summary(md: list[str], stats: dict) -> None:
    total = stats["total"]
    succeeded = stats["succeeded"]
    failed = stats["failed"]
    cancelled = stats["cancelled"]
    run_durs = stats["run_durs"]
    t = MDTable(["Metric", "Value"])
    t.add("Total completed runs", str(total))
    t.add(
        "Successful runs",
        f"{len(succeeded)} ({len(succeeded) / total * 100:.1f}%)" if total else "0",
    )
    t.add(
        "Failed / timed-out runs",
        f"{len(failed)} ({len(failed) / total * 100:.1f}%)" if total else "0",
    )
    t.add("Cancelled runs", str(len(cancelled)))
    avg = sum(run_durs) / len(run_durs) if run_durs else None
    t.add("Avg run time (successful runs)", _fmt(avg))
    t.add("P50 run time", _fmt(_percentile(run_durs, 50)))
    t.add("P90 run time", _fmt(_percentile(run_durs, 90)))
    t.add("P99 run time", _fmt(_percentile(run_durs, 99)))
    md.extend(["## Summary", ""])
    md.extend(t.render())
    md.append("")


def _section_weekly(md: list[str], completed: list[dict]) -> None:
    week_stats: dict[str, dict[str, int]] = {}
    for run in completed:
        wk = _week_start(_parse_dt(run["created_at"]))
        ws = week_stats.setdefault(wk, {"total": 0, "failed": 0})
        ws["total"] += 1
        if run["conclusion"] in ("failure", "timed_out"):
            ws["failed"] += 1

    t = MDTable(["Week of (Mon)", "Total", "Failed", "Success Rate"])
    for wk in sorted(week_stats):
        ws = week_stats[wk]
        tot = ws["total"]
        fail = ws["failed"]
        rate = f"{(tot - fail) / tot * 100:.0f}%" if tot else "N/A"
        t.add(wk, str(tot), str(fail), rate)

    md.extend(["## Weekly Breakdown", ""])
    md.extend(["_Counts across all completed runs per calendar week (Mon-Sun, UTC)._", ""])
    md.extend(t.render())
    md.append("")


def _section_failed_runs(
    md: list[str], failed: list[dict], jobs_by_run: dict[int, list[dict]]
) -> None:
    md.extend([f"## Failed Runs ({len(failed)})", ""])
    if not failed:
        md.extend(["_No failed runs in this period._", ""])
        return

    t = MDTable(["Date (UTC)", "Run", "Duration", "Failing Jobs"])
    for run in sorted(failed, key=lambda r: r["created_at"], reverse=True):
        failing_jobs = sorted(
            j["name"] for j in jobs_by_run.get(run["id"], []) if j.get("conclusion") == "failure"
        )
        jobs_cell = ", ".join(f"`{n}`" for n in failing_jobs) if failing_jobs else "_unknown_"
        t.add(
            run["created_at"][:10],
            f"[#{run['id']}]({run['html_url']})",
            _fmt(_run_duration(run)),
            jobs_cell,
        )
    md.extend(t.render())
    md.append("")


def _section_failing_jobs(md: list[str], top_failing: list[tuple[str, int]], total: int) -> None:
    md.extend(["## Most Common Failing Jobs", ""])
    if not top_failing:
        md.extend(["_No job failures recorded in this period._", ""])
        return

    md.extend(["_Percentage of completed runs where this job failed at least once._", ""])
    t = MDTable(["Rank", "Job", "Failure Count", "% of Runs"])
    for i, (name, count) in enumerate(top_failing[:25], 1):
        pct = f"{count / total * 100:.1f}%" if total else "N/A"
        t.add(str(i), f"`{name}`", str(count), pct)
    md.extend(t.render())
    md.append("")


def _section_slowest_jobs(md: list[str], job_perf: list[tuple[str, list[float]]]) -> None:
    md.extend(["## Slowest Jobs (by P90 duration)", ""])
    if not job_perf:
        md.extend(["_No job timing data available._", ""])
        return

    md.extend(["_P50/P90/P99 computed across all completed runs (success + failure)._", ""])
    t = MDTable(["Rank", "Job", "Samples", "P50", "P90", "P99"])
    for i, (name, samples) in enumerate(job_perf[:30], 1):
        t.add(
            str(i),
            f"`{name}`",
            str(len(samples)),
            _fmt(_percentile(samples, 50)),
            _fmt(_percentile(samples, 90)),
            _fmt(_percentile(samples, 99)),
        )
    md.extend(t.render())
    md.append("")


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def generate_report(
    runs: list[dict],
    jobs_by_run: dict[int, list[dict]],
    days: int,
    output: str,
) -> None:
    now = datetime.now(tz=timezone.utc)
    since = now - timedelta(days=days)

    # Partition runs by conclusion
    completed = [r for r in runs if r["status"] == "completed"]
    succeeded = [r for r in completed if r["conclusion"] == "success"]
    failed = [r for r in completed if r["conclusion"] in ("failure", "timed_out")]
    cancelled = [r for r in completed if r["conclusion"] == "cancelled"]
    total = len(completed)

    # Run-level timing (successful only - avoids skew from interrupted runs)
    run_durs = [d for r in succeeded if (d := _run_duration(r)) is not None]

    # Job-level aggregation
    job_fail_counts: dict[str, int] = {}
    job_dur_samples: dict[str, list[float]] = {}
    for run in completed:
        for job in jobs_by_run.get(run["id"], []):
            name = job["name"]
            conclusion = job.get("conclusion")
            dur = _job_duration(job)
            if conclusion == "failure":
                job_fail_counts[name] = job_fail_counts.get(name, 0) + 1
            if dur is not None and conclusion in ("success", "failure"):
                job_dur_samples.setdefault(name, []).append(dur)

    top_failing = sorted(job_fail_counts.items(), key=lambda x: -x[1])
    job_perf = sorted(
        list(job_dur_samples.items()),
        key=lambda x: -(_percentile(x[1], 90) or 0),
    )

    # Build Markdown
    md: list[str] = []
    md.append("# CI Health Report")
    md.append("")
    period = f"{since.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')} ({days} days)"
    md.append(f"**Period:** {period}  ")
    md.append(f"**Workflow:** `{WORKFLOW}` (scheduled runs only)  ")
    md.append(f"**Repository:** [{REPO}](https://github.com/{REPO})  ")
    md.append(f"**Generated:** {now.strftime('%Y-%m-%d %H:%M UTC')}  ")
    md.append("")
    md.append("---")
    md.append("")

    _section_summary(
        md,
        {
            "total": total,
            "succeeded": succeeded,
            "failed": failed,
            "cancelled": cancelled,
            "run_durs": run_durs,
        },
    )
    _section_weekly(md, completed)
    _section_failed_runs(md, failed, jobs_by_run)
    _section_failing_jobs(md, top_failing, total)
    _section_slowest_jobs(md, job_perf)

    md.append("---")
    md.append("")
    md.append(
        "_Report generated using [`gh` CLI](https://cli.github.com/). "
        "All times in UTC. Run durations are wall-clock time for the entire workflow run._"
    )
    md.append("")

    Path(output).write_text("\n".join(md), encoding="utf-8")
    _err(f"\n\033[32mReport written to:\033[0m {output}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Generate a CI health report (scheduled runs) as Markdown.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument(
        "--days",
        type=int,
        default=DEFAULT_DAYS,
        help="Look-back window in days",
    )
    ap.add_argument(
        "--output",
        default=None,
        help="Output file path (default: ci_health_report_YYYYMMDD_HHMM.md)",
    )
    ap.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help="Parallel workers for per-run job fetching",
    )
    args = ap.parse_args()

    since = datetime.now(tz=timezone.utc) - timedelta(days=args.days)
    output = args.output or f"CI Health Report - {since.strftime('%B %Y')}.md"

    _err("=== CI Health Report Generator ===")
    _err(f"    Repo     : {REPO}")
    _err(f"    Workflow : {WORKFLOW}")
    _err(f"    Lookback : {args.days} days")
    _err(f"    Output   : {output}")
    _err("")

    _err("[1/3] Checking gh CLI...")
    preflight_checks()
    _err(f"\n[2/3] Fetching data since {since.strftime('%Y-%m-%d')}...")

    runs = fetch_runs(since)
    if not runs:
        _err("No completed scheduled runs found in the given window. Nothing to report.")
        sys.exit(0)

    _err(f"  Fetching job data for {len(runs)} runs ({args.workers} workers)...")
    jobs_by_run: dict[int, list[dict]] = {}
    done = 0

    def _fetch(run: dict) -> tuple[int, list[dict]]:
        rid = run["id"]
        try:
            return rid, fetch_jobs(rid)
        except RuntimeError as exc:
            _err(f"\n  [warn] run {rid}: {exc}")
            return rid, []

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(_fetch, r): r for r in runs}
        for fut in as_completed(futures):
            rid, jobs = fut.result()
            jobs_by_run[rid] = jobs
            done += 1
            print(f"\r  {done}/{len(runs)} runs processed...", end="", flush=True, file=sys.stderr)
    _err("")

    _err("\n[3/3] Generating report...")
    generate_report(runs, jobs_by_run, args.days, output)


if __name__ == "__main__":
    main()
