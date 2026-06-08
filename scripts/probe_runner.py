#!/usr/bin/env python3
"""betterbest probe runner — run the experiment, capture outputs in a fixed layout.

The probe is whatever EXERCISES the artefact and produces something measurable: a command
that fires test questions at a prompt, a script that runs a recipe through critic personas,
a test+profile run for a function, a render of a layout. betterbest does not care WHAT it is,
only that it is:
  - deterministic enough that two runs of the same variant are comparable,
  - cheap enough to run every iteration,
  - FIXED across the run (don't change the probe mid-run or scores stop comparing).

This wrapper just runs your probe command and captures stdout/stderr/exit-code/wall-time into
the iteration dir, so the driving LLM can READ the raw outputs and judge them. It does NO
scoring. The command is yours; it is run via the shell you pass.

Usage:
    probe_runner.py --run RUNDIR --iter 14 -- <your probe command ...>
    # e.g.
    probe_runner.py --run run/ --iter 14 -- python probe.py --prompt prompts/extract.txt

Writes:
    RUNDIR/iterations/014/probe.out   (stdout)
    RUNDIR/iterations/014/probe.err   (stderr)
    RUNDIR/iterations/014/probe.meta  (exit code, seconds, command)
Prints the path to probe.out so you can read it next.
"""
import argparse, os, subprocess, sys, time, json

def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run", required=True)
    p.add_argument("--iter", type=int, required=True)
    p.add_argument("cmd", nargs=argparse.REMAINDER,
                   help="-- then your probe command")
    a = p.parse_args()

    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    if not cmd:
        print("no probe command given (put it after --)", file=sys.stderr)
        sys.exit(1)

    itdir = os.path.join(a.run, "iterations", f"{a.iter:03d}")
    os.makedirs(itdir, exist_ok=True)
    out_p = os.path.join(itdir, "probe.out")
    err_p = os.path.join(itdir, "probe.err")
    meta_p = os.path.join(itdir, "probe.meta")

    t0 = time.time()
    with open(out_p, "w") as out, open(err_p, "w") as err:
        rc = subprocess.call(cmd, stdout=out, stderr=err)
    secs = round(time.time() - t0, 2)

    with open(meta_p, "w") as f:
        json.dump({"cmd": cmd, "exit_code": rc, "seconds": secs}, f, indent=2)

    print(f"probe done: exit={rc} seconds={secs}")
    print(f"READ THE OUTPUT and judge it against the rubric: {out_p}")
    if rc != 0:
        print(f"(non-zero exit — check {err_p})", file=sys.stderr)
    # do not fail the run on a non-zero probe; the LLM decides what that means

if __name__ == "__main__":
    main()
