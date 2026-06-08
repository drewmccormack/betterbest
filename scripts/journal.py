#!/usr/bin/env python3
"""betterbest journal — the experiment log for an iterative-improvement run.

Mechanical only. It records what YOU (the driving LLM) decide; it makes NO judgments
of its own. One row per experiment (iteration): the mutation tried, the score the LLM
gave by reading, and the keep/revert verdict.

Layout (created under the run dir you pass with --run):
    <run>/RUN.md         human-readable running log (best-so-far, every verdict)
    <run>/journal.jsonl  one JSON object per experiment (machine-readable, replayable)
    <run>/iterations/NNN/  per-iteration scratch (mutation.md, variant.diff, verdict.md)

Usage:
    journal.py init   --run DIR --artefact PATH --rubric PATH [--baseline-score N]
    journal.py log    --run DIR --mutation "..." --score N --verdict keep|revert \
                       [--note "..."] [--cost-usd F]
    journal.py status --run DIR        # prints best-so-far, iteration count, plateau length
"""
import argparse, json, os, sys, datetime

def _now():
    # wall-clock stamp; fine for a human log
    return datetime.datetime.now().isoformat(timespec="seconds")

def _paths(run):
    return (os.path.join(run, "RUN.md"),
            os.path.join(run, "journal.jsonl"),
            os.path.join(run, "iterations"))

def _read_rows(jsonl):
    if not os.path.exists(jsonl):
        return []
    with open(jsonl) as f:
        return [json.loads(l) for l in f if l.strip()]

def cmd_init(a):
    run_md, jsonl, iters = _paths(a.run)
    os.makedirs(iters, exist_ok=True)
    meta = {
        "type": "init", "ts": _now(),
        "artefact": a.artefact, "rubric": a.rubric,
        "baseline_score": a.baseline_score,
    }
    with open(jsonl, "w") as f:
        f.write(json.dumps(meta) + "\n")
    with open(run_md, "w") as f:
        f.write(f"# betterbest run\n\n")
        f.write(f"- started: {meta['ts']}\n")
        f.write(f"- artefact: `{a.artefact}`\n")
        f.write(f"- rubric: `{a.rubric}`\n")
        if a.baseline_score is not None:
            f.write(f"- baseline score: **{a.baseline_score}**\n")
        f.write(f"\n| iter | mutation | score | verdict | best | note |\n")
        f.write(f"|---|---|---|---|---|---|\n")
    print(f"initialized run at {a.run}")

def cmd_log(a):
    run_md, jsonl, iters = _paths(a.run)
    rows = _read_rows(jsonl)
    exps = [r for r in rows if r.get("type") == "experiment"]
    n = len(exps) + 1
    # best-so-far = max kept score (baseline counts as the floor)
    init = next((r for r in rows if r.get("type") == "init"), {})
    best = init.get("baseline_score")
    for r in exps:
        if r["verdict"] == "keep" and (best is None or r["score"] > best):
            best = r["score"]
    if a.verdict == "keep" and (best is None or a.score > best):
        best = a.score
    row = {
        "type": "experiment", "ts": _now(), "iter": n,
        "mutation": a.mutation, "score": a.score, "verdict": a.verdict,
        "best_so_far": best, "note": a.note, "cost_usd": a.cost_usd,
    }
    with open(jsonl, "a") as f:
        f.write(json.dumps(row) + "\n")
    os.makedirs(os.path.join(iters, f"{n:03d}"), exist_ok=True)
    with open(run_md, "a") as f:
        f.write(f"| {n} | {a.mutation} | {a.score} | {a.verdict} | "
                f"{best} | {a.note or ''} |\n")
    print(f"logged iteration {n}: {a.verdict} (score {a.score}, best {best})")

def cmd_status(a):
    _, jsonl, _ = _paths(a.run)
    rows = _read_rows(jsonl)
    exps = [r for r in rows if r.get("type") == "experiment"]
    init = next((r for r in rows if r.get("type") == "init"), {})
    best = init.get("baseline_score")
    best_iter = 0
    for r in exps:
        if r["verdict"] == "keep" and (best is None or r["score"] > best):
            best, best_iter = r["score"], r["iter"]
    # plateau = experiments since best improved
    plateau = (exps[-1]["iter"] - best_iter) if exps else 0
    total_cost = sum(r.get("cost_usd") or 0 for r in exps)
    print(json.dumps({
        "iterations": len(exps),
        "best_so_far": best,
        "best_at_iter": best_iter,
        "plateau_len": plateau,
        "total_cost_usd": round(total_cost, 4),
    }, indent=2))

def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("init"); pi.set_defaults(fn=cmd_init)
    pi.add_argument("--run", required=True)
    pi.add_argument("--artefact", required=True)
    pi.add_argument("--rubric", required=True)
    pi.add_argument("--baseline-score", type=float, default=None, dest="baseline_score")

    pl = sub.add_parser("log"); pl.set_defaults(fn=cmd_log)
    pl.add_argument("--run", required=True)
    pl.add_argument("--mutation", required=True)
    pl.add_argument("--score", type=float, required=True)
    pl.add_argument("--verdict", choices=["keep", "revert"], required=True)
    pl.add_argument("--note", default=None)
    pl.add_argument("--cost-usd", type=float, default=None, dest="cost_usd")

    ps = sub.add_parser("status"); ps.set_defaults(fn=cmd_status)
    ps.add_argument("--run", required=True)

    a = p.parse_args()
    a.fn(a)

if __name__ == "__main__":
    main()
