"""Tasks, arms, seeded draws, prompts and parsing. No network in this module."""

from __future__ import annotations

import json
import random
import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
K = 8  # items per answer, the same in every arm
N_DIMENSIONS = 3  # dimensions drawn per sample in the nudged arm
TODO_MARK = "TODO(Nathan)"


@dataclass(frozen=True)
class Task:
    id: str
    vignette: str
    ask: str
    item: str
    item_plural: str
    type: str = ""  # the decision type; two people share one type and one codebook


@dataclass(frozen=True)
class Arm:
    name: str
    template: str  # file stem under arms/
    shape: str  # which JSON shape the answer takes: items | notes | responses | properties
    follow_up: bool = False  # a second turn after a fresh plain answer
    draw: str | None = None  # "word" or "dimensions"


ARMS: dict[str, Arm] = {
    a.name: a
    for a in [
        Arm("plain", "plain", "items"),
        Arm("think_diverse", "think_diverse", "notes"),
        Arm("verbalized", "verbalized", "responses"),
        Arm("what_else", "what_else", "items", follow_up=True),
        Arm("random_word", "random_word", "notes", draw="word"),
        Arm("properties", "properties", "properties"),
        Arm("properties_nudged", "properties", "properties", draw="dimensions"),
    ]
}


def load_tasks(path: Path) -> list[Task]:
    """Read a tasks file. Top-level ask/item/item_plural are defaults for each task."""
    data = tomllib.loads(path.read_text())
    tasks = []
    for t in data.get("task", []):
        merged = {k: data[k] for k in ("ask", "item", "item_plural") if k in data} | t
        tasks.append(
            Task(
                id=merged["id"],
                vignette=merged["vignette"].strip(),
                ask=merged["ask"],
                item=merged["item"],
                item_plural=merged["item_plural"],
                type=merged.get("type", merged["id"]),
            )
        )
    ids = [t.id for t in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate task ids in {path}")
    return tasks


def read_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def make_draw(arm: Arm, seed: int, model: str, task_id: str, sample: int) -> dict:
    """The random material for one sample. A plain seeded uniform pick, logged with
    the generation, so samples are independent and the run can be reproduced."""
    if arm.draw is None:
        return {}
    rng = random.Random(f"{seed}:{model}:{task_id}:{arm.name}:{sample}")
    if arm.draw == "word":
        return {"word": rng.choice(read_lines(ROOT / "data" / "words.txt"))}
    if arm.draw == "dimensions":
        dims = rng.sample(read_lines(ROOT / "data" / "dimensions.txt"), N_DIMENSIONS)
        return {"dimensions": dims}
    raise ValueError(f"unknown draw {arm.draw!r}")


def _template(stem: str, arms_dir: Path) -> str:
    text = (arms_dir / f"{stem}.md").read_text().strip()
    if TODO_MARK in text:
        raise RuntimeError(f"arms/{stem}.md still has its {TODO_MARK} line; write the prompt first")
    return text


def _fill(text: str, task: Task, draw: dict) -> str:
    fields = {
        "vignette": task.vignette,
        "ask": task.ask,
        "k": K,
        "item": task.item,
        "item_plural": task.item_plural,
        "word": draw.get("word", ""),
        "dimensions": ", ".join(draw.get("dimensions", [])),
    }
    return text.format(**fields)


def first_prompt(arm: Arm, task: Task, draw: dict, arms_dir: Path | None = None) -> str:
    """The first user message. For a follow-up arm this is the plain prompt."""
    arms_dir = arms_dir or ROOT / "arms"
    if arm.follow_up:
        return _fill(_template("plain", arms_dir), task, {})
    text = _template(arm.template, arms_dir)
    if arm.draw == "dimensions":
        text = text + "\n\n" + _template("properties_nudge", arms_dir)
    return _fill(text, task, draw)


def follow_up_prompt(arm: Arm, task: Task, arms_dir: Path | None = None) -> str:
    return _fill(_template(arm.template, arms_dir or ROOT / "arms"), task, {})


def _obj(props: dict) -> dict:
    return {
        "type": "object",
        "properties": props,
        "required": list(props),
        "additionalProperties": False,
    }


_STRINGS = {"type": "array", "items": {"type": "string"}}

SCHEMAS: dict[str, dict] = {
    "items": _obj({"items": _STRINGS}),
    "notes": _obj({"notes": {"type": "string"}, "items": _STRINGS}),
    "responses": _obj(
        {
            "responses": {
                "type": "array",
                "items": _obj({"text": {"type": "string"}, "probability": {"type": "number"}}),
            }
        }
    ),
    "properties": _obj(
        {
            "properties": {
                "type": "array",
                "items": _obj({"name": {"type": "string"}, "alternative": {"type": "string"}}),
            },
            "items": _STRINGS,
        }
    ),
}


def parse_answer(shape: str, text: str) -> dict:
    """Pull the scored items (and the property log, if any) out of a JSON answer.
    Verbalized sampling's probabilities are kept in the raw text but not used."""
    data = json.loads(text)
    if shape == "responses":
        items = [r["text"] for r in data["responses"]]
    else:
        items = list(data["items"])
    return {
        "items": [i.strip() for i in items],
        "properties": data.get("properties", []),
    }
