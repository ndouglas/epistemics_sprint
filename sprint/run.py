"""Generate answers: tasks x arms x samples for one model, appended to a JSONL file.

    uv run python -m sprint.run show --tasks tasks/control.toml
    uv run python -m sprint.run generate --model haiku --tasks tasks/control.toml --samples 2
    uv run python -m sprint.run cost runs/pilot

Runs are resumable: a (model, task, arm, sample) that already has an "ok" row is skipped.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
import tomllib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from sprint.core import (
    ARMS,
    K,
    ROOT,
    SCHEMAS,
    Arm,
    Task,
    first_prompt,
    follow_up_prompt,
    load_tasks,
    make_draw,
    parse_answer,
)

MAX_TOKENS = 8000
MAX_ATTEMPTS = 3  # tries to get exactly K items before giving up on a sample


@dataclass
class Reply:
    text: str
    stop_reason: str
    input_tokens: int
    output_tokens: int
    served_by: str


def load_models(path: Path | None = None) -> dict:
    return tomllib.loads((path or ROOT / "models.toml").read_text())


def load_env_file(path: Path | None = None) -> None:
    """Read KEY=value lines from the git-ignored .env. The project's file wins over
    the shell, so a stale key exported elsewhere can't shadow it."""
    path = path or ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip().strip("\"'")


class AnthropicProvider:
    """One call, one answer. No fallback model: if the named model declines, the
    row is recorded as a refusal, since an answer from another model would be a
    different condition."""

    def __init__(self) -> None:
        import anthropic

        self._anthropic = anthropic
        self.client = anthropic.AsyncAnthropic(max_retries=5)

    async def ask(self, model: dict, messages: list[dict], schema: dict) -> Reply:
        response = await self.client.messages.create(
            model=model["id"],
            max_tokens=MAX_TOKENS,
            thinking=model["thinking"],
            output_config={
                "effort": model["effort"],
                "format": {"type": "json_schema", "schema": schema},
            },
            messages=messages,
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        return Reply(
            text=text,
            stop_reason=response.stop_reason,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            served_by=response.model,
        )


class OpenAIProvider:
    """The same contract for an OpenAI model: one call, a JSON answer in the arm's
    schema, reasoning held off so no arm gets hidden reasoning."""

    def __init__(self) -> None:
        import openai

        self.client = openai.AsyncOpenAI(max_retries=5)

    async def ask(self, model: dict, messages: list[dict], schema: dict) -> Reply:
        response = await self.client.chat.completions.create(
            model=model["id"],
            messages=messages,
            max_completion_tokens=MAX_TOKENS,
            reasoning_effort=model["effort"],
            response_format={"type": "json_schema", "json_schema": {"name": "answer", "strict": True, "schema": schema}},
        )
        choice = response.choices[0]
        refused = bool(choice.message.refusal)
        stop = "refusal" if refused else {"stop": "end_turn", "length": "max_tokens"}.get(choice.finish_reason, choice.finish_reason)
        return Reply(
            text=choice.message.content or "",
            stop_reason=stop,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            served_by=response.model,
        )


PROVIDERS = {"anthropic": AnthropicProvider, "openai": OpenAIProvider}


async def one_sample(
    provider, model_name: str, model: dict, task: Task, arm: Arm, sample: int, seed: int
) -> dict:
    """Run one sample and return its row. Never raises for a bad answer; the
    status field says what happened."""
    draw = make_draw(arm, seed, model_name, task.id, sample)
    messages = [{"role": "user", "content": first_prompt(arm, task, draw)}]
    row = {
        "model": model_name,
        "model_id": model["id"],
        "task": task.id,
        "type": task.type or task.id,
        "arm": arm.name,
        "sample": sample,
        "seed": seed,
        "draw": draw,
        "k": K,
        "input_tokens": 0,
        "output_tokens": 0,
        "attempts": 0,
        "status": "error",
    }
    started = time.time()

    def spend(reply: Reply) -> None:
        row["input_tokens"] += reply.input_tokens
        row["output_tokens"] += reply.output_tokens
        row["served_by"] = reply.served_by

    try:
        if arm.follow_up:
            first = await provider.ask(model, messages, SCHEMAS["items"])
            spend(first)
            if first.stop_reason != "end_turn":
                row["status"] = first.stop_reason
                return row
            row["first_turn"] = first.text
            messages += [
                {"role": "assistant", "content": first.text},
                {"role": "user", "content": follow_up_prompt(arm, task)},
            ]
        row["messages"] = messages
        for attempt in range(1, MAX_ATTEMPTS + 1):
            row["attempts"] = attempt
            reply = await provider.ask(model, messages, SCHEMAS[arm.shape])
            spend(reply)
            row["raw"] = reply.text
            if reply.stop_reason != "end_turn":
                row["status"] = reply.stop_reason  # refusal, max_tokens, ...
                return row
            parsed = parse_answer(arm.shape, reply.text)
            row["items"] = parsed["items"]
            row["properties"] = parsed["properties"]
            if len(parsed["items"]) == K and all(parsed["items"]):
                row["status"] = "ok"
                return row
            row["status"] = "bad_count"
    except Exception as exc:  # recorded, and retried on the next run
        row["status"] = "error"
        row["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        row["seconds"] = round(time.time() - started, 2)
    return row


def done_keys(path: Path) -> set[tuple]:
    if not path.exists():
        return set()
    keys = set()
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row["status"] == "ok":
            keys.add((row["model"], row["task"], row["arm"], row["sample"]))
    return keys


async def generate(
    provider,
    model_name: str,
    model: dict,
    tasks: list[Task],
    arms: list[Arm],
    samples: int,
    out: Path,
    seed: int = 0,
    concurrency: int = 8,
) -> dict:
    out.parent.mkdir(parents=True, exist_ok=True)
    skip = done_keys(out)
    jobs = [
        (task, arm, s)
        for task in tasks
        for arm in arms
        for s in range(samples)
        if (model_name, task.id, arm.name, s) not in skip
    ]
    gate = asyncio.Semaphore(concurrency)
    counts: dict[str, int] = defaultdict(int)

    async def work(task: Task, arm: Arm, s: int) -> None:
        async with gate:
            row = await one_sample(provider, model_name, model, task, arm, s, seed)
        with out.open("a") as f:
            f.write(json.dumps(row) + "\n")
        counts[row["status"]] += 1

    await asyncio.gather(*(work(*job) for job in jobs))
    return {"ran": len(jobs), "skipped": len(skip), **counts}


def cost_table(path: Path, models: dict) -> list[tuple]:
    """(model, arm, rows, input tokens, output tokens, dollars), every row counted."""
    totals: dict[tuple, list] = defaultdict(lambda: [0, 0, 0])
    for line in path.read_text().splitlines():
        row = json.loads(line)
        t = totals[(row["model"], row["arm"])]
        t[0] += 1
        t[1] += row["input_tokens"]
        t[2] += row["output_tokens"]
    table = []
    for (model, arm), (n, tin, tout) in sorted(totals.items()):
        m = models[model]
        dollars = tin / 1e6 * m["price_in"] + tout / 1e6 * m["price_out"]
        table.append((model, arm, n, tin, tout, round(dollars, 4)))
    return table


def pick_arms(names: str | None) -> list[Arm]:
    if not names:
        return list(ARMS.values())
    return [ARMS[n] for n in names.split(",")]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="sprint.run")
    sub = p.add_subparsers(dest="cmd", required=True)

    show = sub.add_parser("show", help="print each arm's prompt for the first task; no API calls")
    show.add_argument("--tasks", type=Path, required=True)
    show.add_argument("--arms")

    gen = sub.add_parser("generate", help="call the model and append rows")
    gen.add_argument("--model", required=True)
    gen.add_argument("--tasks", type=Path, required=True)
    gen.add_argument("--arms")
    gen.add_argument("--samples", type=int, default=10)
    gen.add_argument("--limit-tasks", type=int)
    gen.add_argument("--run", default="pilot")
    gen.add_argument("--seed", type=int, default=0)
    gen.add_argument("--concurrency", type=int, default=8)

    cost = sub.add_parser("cost", help="tokens and dollars per model and arm")
    cost.add_argument("run_dir", type=Path)

    args = p.parse_args(argv)

    if args.cmd == "show":
        task = load_tasks(args.tasks)[0]
        for arm in pick_arms(args.arms):
            draw = make_draw(arm, 0, "show", task.id, 0)
            print(f"===== {arm.name}  ({arm.shape}) draw={draw}")
            try:
                text = first_prompt(arm, task, draw)
                print(text)
                if arm.follow_up:
                    print("--- second turn ---")
                    print(follow_up_prompt(arm, task))
                print(f"[{len(text.split())} words]\n")
            except RuntimeError as exc:
                print(f"(not ready: {exc})\n")
        return 0

    if args.cmd == "generate":
        load_env_file()
        models = load_models()
        tasks = load_tasks(args.tasks)[: args.limit_tasks]
        if not tasks:
            print(f"no tasks in {args.tasks}", file=sys.stderr)
            return 1
        arms = pick_arms(args.arms)
        for arm in arms:  # fail before spending anything if a prompt isn't written
            first_prompt(arm, tasks[0], make_draw(arm, args.seed, args.model, tasks[0].id, 0))
        out = ROOT / "runs" / args.run / "generations.jsonl"
        summary = asyncio.run(
            generate(
                PROVIDERS[models[args.model].get("provider", "anthropic")](),
                args.model,
                models[args.model],
                tasks,
                arms,
                args.samples,
                out,
                args.seed,
                args.concurrency,
            )
        )
        print(json.dumps(summary), f"-> {out}")
        return 0

    if args.cmd == "cost":
        total = 0.0
        for model, arm, n, tin, tout, dollars in cost_table(
            args.run_dir / "generations.jsonl", load_models()
        ):
            total += dollars
            print(f"{model:8} {arm:18} rows={n:5} in={tin:9} out={tout:9} ${dollars:8.4f}")
        print(f"total ${total:.4f}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
