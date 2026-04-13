"""Check whether every Lantern level is solvable.

Usage:
    python check_winnable.py

The checker mirrors the rules in `lantern_color_mix_puzzle.html`:
- lanterns light their own cell, then all 4 cardinal directions
- walls block beams
- mirrors reflect beams
- splitters split a beam into 2 perpendicular beams
- turners rotate a beam 90 degrees
- targets must match the exact set of colors reaching that cell
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Sequence, Set, Tuple

SZ = 6
DIRS = {
    "U": (-1, 0),
    "R": (0, 1),
    "D": (1, 0),
    "L": (0, -1),
}
DIR_ORDER = ("U", "R", "D", "L")
RIGHT = {"U": "R", "R": "D", "D": "L", "L": "U"}
LEFT = {"U": "L", "L": "D", "D": "R", "R": "U"}
MIRROR_MAP = {
    "/": {"U": "R", "R": "U", "D": "L", "L": "D"},
    "\\": {"U": "L", "L": "U", "D": "R", "R": "D"},
}

COLOR_HEX = {"R": "#FF3B3B", "B": "#2B7FFF", "Y": "#FFD60A"}
COLOR_NAME = {"R": "Red", "B": "Blue", "Y": "Yellow"}
COLOR_BIT = {"R": 1, "B": 2, "Y": 4}
COMBO_INFO = {
    "BR": {"name": "Purple", "hex": "#9B59F0"},
    "RY": {"name": "Orange", "hex": "#FF8C00"},
    "BY": {"name": "Green", "hex": "#30D158"},
    "BRY": {"name": "White", "hex": "#F5F5F5"},
}


def G(r: int, c: int, color: str) -> dict:
    return {"r": r, "c": c, "color": color}


def X(r: int, c: int, need: Sequence[str]) -> dict:
    return {"r": r, "c": c, "need": list(need)}


def M(r: int, c: int, kind: str) -> dict:
    return {"r": r, "c": c, "kind": kind}


def S(r: int, c: int) -> dict:
    return {"r": r, "c": c}


def T(r: int, c: int, turn: str) -> dict:
    return {"r": r, "c": c, "turn": turn}


def W(*cells: Sequence[int]) -> List[List[int]]:
    return [list(cell) for cell in cells]


def level(cfg: dict) -> dict:
    base = {
        "name": "",
        "hint": "",
        "given": [],
        "palette": {},
        "walls": [],
        "mirrors": [],
        "splitters": [],
        "turners": [],
        "targets": [],
    }
    base.update(cfg)
    return base


LEVELS = [
    level({"name": "Spark", "hint": "Start simple: one lantern, one target.", "palette": {"R": 1}, "targets": [X(2, 2, ["R"])]}),
    level({"name": "Cross", "hint": "Two colors crossing creates a mix.", "palette": {"R": 1, "B": 1}, "targets": [X(1, 3, ["R"]), X(3, 1, ["B"]), X(1, 1, ["R", "B"])]}),
    level({"name": "Prism", "hint": "Add yellow and learn the three basic mixes.", "palette": {"R": 2, "B": 2, "Y": 2}, "targets": [X(0, 4, ["R"]), X(4, 0, ["B"]), X(5, 5, ["Y"]), X(2, 2, ["R", "B"]), X(3, 3, ["R", "Y"]), X(1, 1, ["B", "Y"])]}),
    level({"name": "Curtain", "hint": "Walls stop light. Use the gaps to aim around them.", "palette": {"R": 1, "B": 1}, "walls": W([1, 2], [2, 2], [3, 2]), "targets": [X(0, 2, ["R"]), X(5, 2, ["B"]), X(4, 4, ["R", "B"])]}),
    level({"name": "Anchor", "hint": "A fixed lantern changes the whole board.", "given": [G(2, 1, "R")], "palette": {"B": 2, "Y": 2}, "walls": W([1, 3], [2, 3], [3, 3]), "targets": [X(2, 4, ["R"]), X(0, 1, ["B"]), X(4, 1, ["Y"])]}),
    level({"name": "Mirror Bend", "hint": "A mirror can redirect a beam to a new row.", "palette": {"B": 1}, "given": [G(1, 1, "B")], "mirrors": [M(1, 4, "\\")], "targets": [X(4, 4, ["B"]), X(1, 2, ["B"])]}),
    level({"name": "Mirror Pair", "hint": "Two mirrors make a tiny beam tunnel.", "palette": {"R": 1}, "given": [G(4, 4, "R")], "mirrors": [M(4, 1, "\\"), M(2, 1, "/")], "targets": [X(2, 1, ["R"]), X(4, 0, ["R"])]}),
    level({"name": "Splitter Intro", "hint": "This splitter splits one beam into two beams.", "palette": {"R": 1, "B": 1}, "given": [G(0, 2, "B")], "splitters": [S(2, 2)], "targets": [X(2, 0, ["B"]), X(2, 4, ["B"]), X(4, 2, ["R"])]}),
    level({"name": "Split Mix", "hint": "Use the split to stack colors in two different spots.", "palette": {"R": 2, "Y": 2}, "given": [G(0, 3, "B")], "splitters": [S(3, 3)], "targets": [X(3, 1, ["B", "R"]), X(3, 5, ["B", "Y"]), X(5, 3, ["B"])]}),
    level({"name": "Rotor", "hint": "Turners bend light 90° without a mirror.", "palette": {"R": 1}, "given": [G(0, 4, "R")], "turners": [T(2, 4, "cw")], "targets": [X(2, 2, ["R"]), X(4, 4, ["R"])]}),
    level({"name": "Rotor Maze", "hint": "Mix a turner with a mirror to reach a hidden lane.", "palette": {"B": 1}, "given": [G(1, 4, "B")], "walls": W([0, 2], [1, 2], [3, 2], [4, 2]), "mirrors": [M(2, 4, "/")], "turners": [T(2, 1, "ccw")], "targets": [X(2, 0, ["B"]), X(4, 1, ["B"])]}),
    level({"name": "Prism Garden", "hint": "Everything starts to combine now.", "palette": {"R": 2, "B": 2, "Y": 2}, "splitters": [S(2, 2)], "mirrors": [M(1, 4, "\\"), M(4, 1, "/")], "targets": [X(0, 2, ["R"]), X(5, 2, ["B"]), X(3, 4, ["Y"]), X(2, 0, ["R", "B"]), X(2, 5, ["R", "Y"]), X(4, 3, ["B", "Y"])]}),
    level({"name": "White Light", "hint": "All three base colors together create a bright mix.", "palette": {"R": 1, "B": 1, "Y": 1}, "given": [G(0, 0, "R"), G(0, 5, "B")], "walls": W([1, 1], [1, 2], [1, 3]), "splitters": [S(3, 2)], "targets": [X(3, 0, ["R", "B"]), X(3, 4, ["B", "Y"]), X(5, 2, ["R", "B", "Y"])]}),
    level({"name": "Switchback", "hint": "Route light around the blockers with a calm hand.", "palette": {"R": 1, "B": 1}, "given": [G(5, 0, "R")], "walls": W([2, 1], [2, 2], [2, 3], [4, 3]), "mirrors": [M(4, 1, "\\"), M(1, 4, "/")], "targets": [X(5, 3, ["R"]), X(1, 1, ["R"]), X(1, 5, ["B"])]}),
    level({"name": "Lenswork", "hint": "Use a splitter and two turners together.", "palette": {"Y": 1}, "given": [G(0, 2, "Y")], "splitters": [S(2, 2)], "turners": [T(2, 0, "cw"), T(2, 5, "ccw")], "targets": [X(2, 0, ["Y"]), X(2, 5, ["Y"]), X(4, 2, ["Y"])]}),
    level({"name": "Prism Chain", "hint": "A beam can change direction more than once.", "palette": {"R": 1, "B": 1}, "given": [G(0, 1, "R")], "mirrors": [M(0, 4, "\\"), M(3, 4, "/")], "splitters": [S(3, 1)], "targets": [X(3, 0, ["R"]), X(3, 5, ["R"]), X(5, 4, ["B"])]}),
    level({"name": "Kaleidoscope", "hint": "More paths, more intersections, more color mixing.", "palette": {"R": 2, "B": 2, "Y": 2}, "given": [G(5, 1, "R")], "walls": W([1, 0], [1, 1], [1, 2], [4, 3]), "mirrors": [M(0, 3, "/"), M(4, 1, "\\"), M(2, 5, "/")], "splitters": [S(3, 3)], "turners": [T(2, 3, "cw")], "targets": [X(0, 1, ["R"]), X(2, 4, ["B"]), X(4, 4, ["Y"]), X(3, 5, ["R", "B"]), X(5, 3, ["R", "Y"])]}),
    level({"name": "Double Split", "hint": "Two splitters can fan out a single lantern into a web.", "palette": {"B": 2}, "given": [G(0, 2, "B")], "splitters": [S(1, 2), S(4, 3)], "mirrors": [M(2, 0, "\\"), M(3, 5, "/")], "targets": [X(2, 0, ["B"]), X(2, 4, ["B"]), X(5, 3, ["B"])]}),
    level({"name": "Refraction", "hint": "Mirrors, splitters, and turners all in one puzzle.", "palette": {"R": 2, "Y": 2}, "given": [G(1, 5, "R"), G(4, 0, "Y")], "walls": W([2, 2], [2, 3], [3, 2]), "mirrors": [M(1, 2, "\\"), M(4, 4, "/")], "splitters": [S(3, 4)], "turners": [T(3, 1, "ccw")], "targets": [X(1, 0, ["R"]), X(4, 5, ["Y"]), X(3, 0, ["R", "Y"]), X(5, 4, ["Y"])]}),
    level({"name": "Aurora", "hint": "The finale: move freely, bend beams, split them, and finish the full spectrum.", "palette": {"R": 2, "B": 2, "Y": 2}, "given": [G(0, 0, "R"), G(0, 5, "B"), G(5, 2, "Y")], "walls": W([1, 2], [1, 3], [3, 2], [3, 3]), "mirrors": [M(0, 3, "\\"), M(4, 1, "/")], "splitters": [S(2, 2)], "turners": [T(2, 4, "cw"), T(4, 4, "ccw")], "targets": [X(2, 0, ["R"]), X(2, 5, ["B"]), X(4, 0, ["Y"]), X(4, 5, ["R", "B"]), X(5, 5, ["R", "Y"]), X(3, 4, ["B", "Y"]), X(5, 3, ["R", "B", "Y"])]}),
]


def key_of(values: Iterable[str]) -> str:
    return "".join(sorted(values))


def combo_hex(key: str) -> str:
    return COLOR_HEX.get(key, COMBO_INFO.get(key, {}).get("hex", "#888"))


def tile_at(level: dict, r: int, c: int):
    key = (r, c)
    for tile in level["mirrors"]:
        if (tile["r"], tile["c"]) == key:
            return ("mirror", tile["kind"])
    for tile in level["splitters"]:
        if (tile["r"], tile["c"]) == key:
            return ("splitter", None)
    for tile in level["turners"]:
        if (tile["r"], tile["c"]) == key:
            return ("turner", tile["turn"])
    return None


def trace_light(level: dict, lanterns: Sequence[Tuple[int, int, str]]):
    light = [[set() for _ in range(SZ)] for _ in range(SZ)]
    walls = {tuple(cell) for cell in level["walls"]}
    seen = set()
    stack = []

    for r, c, color in lanterns:
        light[r][c].add(color)
        for direction in DIR_ORDER:
            stack.append((r, c, direction, color))

    while stack:
        r, c, direction, color = stack.pop()
        dr, dc = DIRS[direction]
        nr, nc = r + dr, c + dc
        if not (0 <= nr < SZ and 0 <= nc < SZ):
            continue
        if (nr, nc) in walls:
            continue

        state = (nr, nc, direction, color)
        if state in seen:
            continue
        seen.add(state)

        light[nr][nc].add(color)
        tile = tile_at(level, nr, nc)
        if tile is None:
            stack.append((nr, nc, direction, color))
            continue

        kind, value = tile
        if kind == "mirror":
            stack.append((nr, nc, MIRROR_MAP[value][direction], color))
        elif kind == "splitter":
            if direction in ("U", "D"):
                branches = ("L", "R")
            else:
                branches = ("U", "D")
            for branch in branches:
                stack.append((nr, nc, branch, color))
        elif kind == "turner":
            stack.append((nr, nc, RIGHT[direction] if value == "cw" else LEFT[direction], color))

    return light


def is_won(level: dict, light) -> bool:
    for target in level["targets"]:
        colors = light[target["r"]][target["c"]]
        if key_of(colors) != key_of(target["need"]):
            return False
    return True


def open_cells(level: dict) -> List[Tuple[int, int]]:
    blocked = {tuple(cell) for cell in level["walls"]}
    blocked.update((tile["r"], tile["c"]) for tile in level["mirrors"])
    blocked.update((tile["r"], tile["c"]) for tile in level["splitters"])
    blocked.update((tile["r"], tile["c"]) for tile in level["turners"])
    blocked.update((item["r"], item["c"]) for item in level["given"])

    cells = []
    for r in range(SZ):
        for c in range(SZ):
            if (r, c) not in blocked:
                cells.append((r, c))
    return cells


def lantern_colors(level: dict) -> List[str]:
    colors = []
    for color, count in level["palette"].items():
        colors.extend([color] * count)
    return colors


def target_masks(level: dict, light) -> List[int]:
    return [sum(COLOR_BIT[c] for c in light[target["r"]][target["c"]]) for target in level["targets"]]


def effect_is_valid(effect: Sequence[int], current: Sequence[int], need: Sequence[int]) -> bool:
    for cur, add, req in zip(current, effect, need):
        if (cur | add) & ~req:
            return False
    return True


def find_solution(level: dict):
    givens = [(g["r"], g["c"], g["color"]) for g in level["given"]]
    base_light = trace_light(level, givens)

    need = [sum(COLOR_BIT[c] for c in target["need"]) for target in level["targets"]]
    current = target_masks(level, base_light)

    if current == need:
        return []

    open_cells_list = open_cells(level)

    candidates = {color: [] for color in level["palette"]}
    for color, count in level["palette"].items():
        if count <= 0:
            continue
        bit = COLOR_BIT[color]
        for r, c in open_cells_list:
            light = trace_light(level, [(r, c, color)])
            effect = []
            useful = False
            valid = True
            for idx, target in enumerate(level["targets"]):
                add = bit if color in light[target["r"]][target["c"]] else 0
                effect.append(add)
                if add:
                    useful = True
                    if not (need[idx] & add):
                        valid = False
                        break
            if valid and useful:
                candidates[color].append({"r": r, "c": c, "effect": tuple(effect), "bit": bit})

    # If no movable lantern can help, only the givens matter.
    if not any(candidates.values()):
        return [] if current == need else None

    memo = {}

    def remaining_key(counts: Dict[str, int]) -> Tuple[Tuple[str, int], ...]:
        return tuple(sorted((color, count) for color, count in counts.items() if count > 0))

    def search(cur_masks: Tuple[int, ...], counts: Dict[str, int], occupied_mask: int):
        if cur_masks == tuple(need):
            return []

        key = (cur_masks, remaining_key(counts), occupied_mask)
        if key in memo:
            return None

        best_color = None
        best_options = None

        for t_idx, (cur, req) in enumerate(zip(cur_masks, need)):
            missing = req & ~cur
            if not missing:
                continue
            for bit in (1, 2, 4):
                if not (missing & bit):
                    continue
                for color, count in counts.items():
                    if count <= 0 or COLOR_BIT[color] != bit:
                        continue
                    options = []
                    for cand in candidates[color]:
                        cell_mask = 1 << (cand["r"] * SZ + cand["c"])
                        if occupied_mask & cell_mask:
                            continue
                        if not (cand["effect"][t_idx] & bit):
                            continue
                        if not effect_is_valid(cand["effect"], cur_masks, need):
                            continue
                        new_masks = tuple(cur_masks[i] | cand["effect"][i] for i in range(len(cur_masks)))
                        options.append((cand, new_masks, cell_mask))
                    if options and (best_options is None or len(options) < len(best_options)):
                        best_color = color
                        best_options = options

        if not best_options:
            memo[key] = None
            return None

        # Prefer placements that cover the most currently-missing target bits.
        best_options.sort(
            key=lambda item: (
                -sum(1 for a, b in zip(item[1], need) if a == b),
                item[0]["r"],
                item[0]["c"],
            )
        )

        for cand, new_masks, cell_mask in best_options:
            next_counts = dict(counts)
            next_counts[best_color] -= 1
            rest = search(new_masks, next_counts, occupied_mask | cell_mask)
            if rest is not None:
                return [(cand["r"], cand["c"], best_color)] + rest

        memo[key] = None
        return None

    counts = dict(level["palette"])
    result = search(tuple(current), counts, 0)
    if result is not None:
        return givens + result
    return None


def format_solution(lanterns: Sequence[Tuple[int, int, str]]) -> str:
    if not lanterns:
        return "(no movable lanterns needed)"
    return ", ".join(f"{color}@({r},{c})" for r, c, color in lanterns)


def main() -> int:
    all_ok = True
    for idx, level in enumerate(LEVELS, start=1):
        solution = find_solution(level)
        if solution is None:
            all_ok = False
            print(f"[{idx:02d}] {level['name']}: NOT WINNABLE")
        else:
            print(f"[{idx:02d}] {level['name']}: winnable -> {format_solution(solution)}")

    print()
    print("All levels winnable:" , "yes" if all_ok else "no")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
