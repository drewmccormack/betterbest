# betterbest

**You've already got good. This gets you the better and the best.**

A [Claude Code](https://www.claude.com/product/claude-code) skill for making an existing thing as
good as it can be through **iterative experiments** — a prompt, a config, a function, an agent
system, an essay, a recipe, a policy doc, a design. Anything you can inspect, change, and measure.

It's a general-purpose adaptation of LLM-driven autoresearch: you improve a *thing* by running one
experiment at a time. Change one thing, run a probe, **read** the result against a rubric, keep it
if better or revert if not. Repeat until the thing is as good as it can be. The judging is always
the model reading the outputs against the rubric — never a regex.

The skill only refines what already exists; it doesn't generate from nothing. You bring the *good*.

## What's in the loop

| Piece | What it is |
|---|---|
| **Artefact** | the thing you're improving (inspectable, mutable, versionable) |
| **Probe** | whatever exercises the artefact and yields something to read (test questions at a prompt, a critic-persona panel for prose, tests+profile for code) |
| **Rubric** | the weighted dimensions you read each result against — each tagged a hard gate or a soft penalty |
| **Journal** | the running record of every experiment and verdict |

Plus the disciplines that make it hold up over a long run: judge by reading (never regex), a
canary that catches stale-variant runs, a fresh-subagent critique of the judge to fight drift, and
a co-evolving rubric. See [`SKILL.md`](./SKILL.md) for the full method.

## Install

**As a plugin (recommended):** in Claude Code, add the marketplace and install:

```
/plugin marketplace add drewmccormack/betterbest
/plugin install betterbest@betterbest
```

**Or as a plain skill:** clone into your Claude Code skills directory:

```bash
git clone https://github.com/drewmccormack/betterbest.git ~/.claude/skills/betterbest
```

Either way, Claude Code discovers it automatically. Then just ask Claude to "make X better",
"improve this", or "iterate on this until it's good", and the skill activates — or invoke it
directly with `/betterbest`.

## Helper scripts

The scripts in [`scripts/`](./scripts) do the mechanical work and **none of the judging**:

- `journal.py` — track best-so-far, plateau length, cost
- `probe_runner.py` — run your probe, capture outputs per iteration
- `judge_helper.py` — render a read-and-fill scoring worksheet (it assigns no scores)
- `canary.py` — verify the probe actually ran the variant you think it did

Run any with `--help`.

## Provenance

This skill was built with test-driven development for skills, then improved by running its own
loop **on itself** across five rounds — each round surfaced a real flaw (a code-vs-prose bias, a
self-referential acceptance bar, a routing bug, a coarse scoring signal) that the previous round
couldn't see. The skill is, in a small way, its own best demonstration.

## License

[MIT](./LICENSE)
