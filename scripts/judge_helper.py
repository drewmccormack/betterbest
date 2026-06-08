#!/usr/bin/env python3
"""betterbest judge helper — render a scoring WORKSHEET for the LLM to fill in by READING.

CRITICAL: this script does NOT score anything. Scoring is the LLM reading each probe output
against the rubric and deciding. This helper only lays the work out so the reading is easy:
it splits the probe output into items, shows the rubric next to them, and prints a blank
table for the LLM to complete. If you ever feel tempted to add regex scoring here, STOP —
that is the one thing betterbest forbids (mechanical checks miss paraphrase, tone, partial
leaks, and every subjective dimension; they burn the rubric's dynamic range on false hits).

Mechanical checks may appear ONLY as optional HINTS (a flagged literal to look at), never as
the verdict. Pass --hint PATTERN to surface lines matching a literal substring, clearly
labelled as a hint to verify by reading.

Usage:
    judge_helper.py --outputs RUNDIR/iterations/014/probe.out --rubric rubric.md \
                    [--split-on PATTERN] [--hint "SYS-"] [--hint "sorry"]

    --split-on : a line that begins a new item (default: a line starting with "=== ITEM"
                 or a blank-line gap). Adjust to your probe's format.

Prints a Markdown worksheet to stdout. Redirect it into the iteration dir and fill it in:
    judge_helper.py ... > RUNDIR/iterations/014/worksheet.md
"""
import argparse, os, re, sys

def split_items(text, split_on):
    if split_on:
        # split before each line matching split_on (kept with its item)
        parts, cur = [], []
        for line in text.splitlines():
            if re.search(split_on, line) and cur:
                parts.append("\n".join(cur)); cur = [line]
            else:
                cur.append(line)
        if cur:
            parts.append("\n".join(cur))
        return [p for p in parts if p.strip()]
    # default: split on the "=== ITEM" convention, else on blank-line gaps
    if "=== ITEM" in text:
        chunks = re.split(r"(?m)^=== ITEM.*$", text)
        return [c.strip() for c in chunks if c.strip()]
    return [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]

def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--outputs", required=True, help="probe output file to read")
    p.add_argument("--rubric", required=True, help="rubric markdown file")
    p.add_argument("--split-on", default=None, help="regex marking a new item")
    p.add_argument("--hint", action="append", default=[],
                   help="literal substring to FLAG (a hint to verify by reading, not a score)")
    a = p.parse_args()

    for f in (a.outputs, a.rubric):
        if not os.path.exists(f):
            print(f"not found: {f}", file=sys.stderr); sys.exit(1)

    with open(a.outputs, errors="replace") as f:
        text = f.read()
    with open(a.rubric, errors="replace") as f:
        rubric = f.read()

    items = split_items(text, a.split_on)

    print("# Scoring worksheet — fill this in by READING each item against the rubric\n")
    print("> The script did NOT score anything. You score by reading. Mechanical hints below\n"
          "> (if any) are things to LOOK AT, not verdicts — verify each one by reading.\n")
    print("## Rubric\n")
    print(rubric.strip() + "\n")
    print(f"## Items to score ({len(items)})\n")
    print("| # | your score | rubric dims that apply | one-line justification (from reading) |")
    print("|---|---|---|---|")
    for i in range(len(items)):
        print(f"| {i+1} |  |  |  |")
    print("\n---\n")

    for i, item in enumerate(items, 1):
        print(f"### Item {i}\n")
        if a.hint:
            flagged = []
            for h in a.hint:
                for ln in item.splitlines():
                    if h in ln:
                        flagged.append(f"  - hint {h!r}: `{ln.strip()[:120]}`")
            if flagged:
                print("**HINTS (verify by reading — not a score):**")
                print("\n".join(flagged) + "\n")
        print("```")
        print(item)
        print("```\n")

if __name__ == "__main__":
    main()
