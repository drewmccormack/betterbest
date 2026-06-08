#!/usr/bin/env python3
"""betterbest canary — verify the experiment actually ran the variant you THINK it ran.

The silent-infrastructure-regression failure: you believe iteration 14 tested variant v14,
but a stale path / cached config / un-applied edit means the probe actually exercised v12.
The score looks fine; it's measuring the wrong thing. Every downstream iteration builds on a
phantom. This check makes that failure LOUD instead of silent.

It compares a DECLARED property of the variant against an OBSERVED property in the probe's
output, and exits non-zero (with a banner) on mismatch. Run it EVERY iteration, before you
trust the score — it is cheap.

Two modes:

  # 1. Hash mode: the artefact you edited must be the one the probe consumed.
  #    --declared-file is what you edited; --observed-file is what the probe loaded
  #    (e.g. a path echoed in the probe log, or a copy the harness made).
  canary.py --declared-file prompts/extract.txt --observed-file prompts/extract.prod.txt

  # 2. Marker mode: a token you planted in the variant must appear in the probe output.
  #    e.g. you put "VARIANT=v14" in the prompt and the probe echoes the loaded prompt /
  #    the model id / a feature flag into its log.
  canary.py --expect "VARIANT=v14" --in run/iter014/probe.out
  canary.py --expect "claude-opus-4-8" --in run/iter014/probe.out   # model-id pin

Exit 0 = match (trust the score). Exit 2 = MISMATCH (the score is invalid; stop and fix).
"""
import argparse, hashlib, os, sys

BANNER = "=" * 60

def fail(msg):
    print(BANNER, file=sys.stderr)
    print("CANARY MISMATCH — THE SCORE IS NOT MEASURING YOUR VARIANT", file=sys.stderr)
    print(msg, file=sys.stderr)
    print("Do NOT log this iteration. Fix the apply/probe path, then re-run.", file=sys.stderr)
    print(BANNER, file=sys.stderr)
    sys.exit(2)

def _sha(path):
    if not os.path.exists(path):
        fail(f"file not found: {path}")
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--declared-file", help="the variant file you edited")
    p.add_argument("--observed-file", help="the file the probe actually loaded")
    p.add_argument("--expect", help="marker string that must appear in the probe output")
    p.add_argument("--in", dest="infile", help="probe output file to search for --expect")
    a = p.parse_args()

    did_check = False

    if a.declared_file or a.observed_file:
        if not (a.declared_file and a.observed_file):
            fail("hash mode needs BOTH --declared-file and --observed-file")
        d, o = _sha(a.declared_file), _sha(a.observed_file)
        if d != o:
            fail(f"declared {a.declared_file} ({d[:12]}) != "
                 f"observed {a.observed_file} ({o[:12]}).\n"
                 f"The probe consumed a DIFFERENT file than the one you edited.")
        did_check = True

    if a.expect:
        if not a.infile:
            fail("marker mode needs --in <probe output file>")
        if not os.path.exists(a.infile):
            fail(f"probe output not found: {a.infile}")
        with open(a.infile, errors="replace") as f:
            text = f.read()
        if a.expect not in text:
            fail(f"marker {a.expect!r} NOT found in {a.infile}.\n"
                 f"The probe output does not show your declared variant ran.")
        did_check = True

    if not did_check:
        fail("no check requested — pass hash mode and/or marker mode args. "
             "A canary that checks nothing is worse than none.")

    print("canary OK — probe ran the declared variant")
    sys.exit(0)

if __name__ == "__main__":
    main()
