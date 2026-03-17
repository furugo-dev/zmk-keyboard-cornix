#!/usr/bin/env python3
"""
post-process-nagi.py

1. Creates a temp version of config/cornix.keymap with `&ng KEY` replaced by `&kp KEY`
2. Runs `keymap parse` to get parsed YAML
3. Replaces NAGI layer bindings with Japanese kana labels
4. Runs `keymap draw` and saves SVG to docs/img/<keyboard>-keymap.svg

Usage (from repo root):
    python draw/post-process-nagi.py [keyboard]
    python draw/post-process-nagi.py cornix
"""

import sys
import os
import re
import subprocess
import tempfile

# ---------------------------------------------------------------------------
# Resolve repo root regardless of working directory
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)


def repo_path(*parts: str) -> str:
    return os.path.join(REPO_ROOT, *parts)


# ---------------------------------------------------------------------------
# Hardcoded NAGI position → Japanese label mapping
# position index (0-based) in the flattened binding list
# ---------------------------------------------------------------------------
NAGI_MAPPING: dict[int, dict] = {
    # Row 0
    1:  {"t": "ESC"},             # ng ESC  → keep as ESC
    2:  {"t": "き", "s": "め"},
    3:  {"t": "て", "s": "り"},
    4:  {"t": "し", "s": "ね"},
    5:  {"t": "←", "s": "S←"},
    6:  {"t": "→", "s": "S→"},
    7:  {"t": "さ", "s": "じゅ"},
    8:  {"t": "る", "s": "よ"},
    9:  {"t": "す", "s": "え"},
    # Row 1
    12: {"t": "Q"},               # ng Q → leave as Q
    13: {"t": "ろ", "s": "せ"},
    14: {"t": "け", "s": "み"},
    15: {"t": "と", "s": "に"},
    16: {"t": "か", "s": "ま"},
    17: {"t": "っ", "s": "ち"},
    18: {"t": "く", "s": "や"},
    19: {"t": "あ", "s": "の"},
    20: {"t": "い", "s": "も"},
    21: {"t": "う", "s": "つ"},
    22: {"t": "ー", "s": "ふ"},
    23: {"t": "へ", "s": "ゆ"},
    # Row 2
    25: {"t": "ほ"},
    26: {"t": "ひ"},
    27: {"t": "は", "s": "を"},
    28: {"t": "こ", "s": "、"},
    29: {"t": "そ", "s": "ぬ"},
    # encoder positions 30, 31 → skip (trans)
    32: {"t": "た", "s": "お"},
    33: {"t": "な", "s": "。"},
    34: {"t": "ん", "s": "む"},
    35: {"t": "ら", "s": "わ"},
    36: {"t": "れ"},
    # Row 3 thumb cluster - leave lt/trans as-is
}


def preprocess_keymap(src_path: str, dst_path: str) -> None:
    """Replace &ng KEY with &kp KEY so keymap-drawer can parse it."""
    with open(src_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Replace `&ng ` with `&kp ` (behavior name substitution)
    content = re.sub(r"&ng\b", "&kp", content)
    with open(dst_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[preprocess] wrote temp keymap to {dst_path}")


def run_keymap_parse(config_path: str, keymap_path: str) -> str:
    """Run `keymap parse` and return the YAML string."""
    cmd = ["keymap", "-c", config_path, "parse", "-z", keymap_path]
    print(f"[parse] running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[parse] STDERR:\n{result.stderr}", file=sys.stderr)
        raise RuntimeError(f"keymap parse failed with code {result.returncode}")
    return result.stdout


def run_keymap_draw(config_path: str, yaml_path: str, svg_path: str) -> None:
    """Run `keymap draw` and write SVG to svg_path."""
    cmd = ["keymap", "-c", config_path, "draw", yaml_path]
    print(f"[draw] running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[draw] STDERR:\n{result.stderr}", file=sys.stderr)
        raise RuntimeError(f"keymap draw failed with code {result.returncode}")
    os.makedirs(os.path.dirname(svg_path), exist_ok=True)
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(result.stdout)
    print(f"[draw] SVG saved to {svg_path}")


def replace_nagi_layer(parsed_yaml: str, mapping: dict[int, dict]) -> str:
    """
    Parse the keymap-drawer YAML, replace NAGI layer bindings with Japanese
    labels, and return the modified YAML string.
    """
    try:
        import yaml
    except ImportError:
        raise RuntimeError("pyyaml is required: pip install pyyaml")

    data = yaml.safe_load(parsed_yaml)

    layers: dict = data.get("layers", {})
    nagi_key = None
    # Find the Naginata layer (may be keyed as "Naginata" or by index)
    for key in layers:
        if isinstance(key, str) and key.lower() in ("naginata", "nagi"):
            nagi_key = key
            break
    if nagi_key is None:
        # Fall back: try index 1 if layers is a list
        if isinstance(layers, list) and len(layers) > 1:
            nagi_key = 1
        else:
            print("[replace] WARNING: NAGI layer not found in parsed YAML; skipping replacement")
            return parsed_yaml

    print(f"[replace] Found NAGI layer key: {nagi_key!r}")
    keys_list: list = layers[nagi_key]

    for pos, label in mapping.items():
        if pos >= len(keys_list):
            continue
        current = keys_list[pos]
        # Only replace non-null entries that were parsed from ng bindings
        if current is None:
            continue
        keys_list[pos] = label

    # Dump back to YAML
    output = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return output


CORNIX_LAYOUT_KEYS = [
    # Row 0 (12 keys)
    {"x": 0,    "y": 0.5},
    {"x": 1,    "y": 0.5},
    {"x": 2,    "y": 0.25},
    {"x": 3,    "y": 0},
    {"x": 4,    "y": 0.25},
    {"x": 5,    "y": 0.5},
    {"x": 8.5,  "y": 0.5},
    {"x": 9.5,  "y": 0.3},
    {"x": 10.5, "y": 0},
    {"x": 11.5, "y": 0.33},
    {"x": 12.5, "y": 0.5},
    {"x": 13.5, "y": 0.5},
    # Row 1 (12 keys)
    {"x": 0,    "y": 1.5},
    {"x": 1,    "y": 1.5},
    {"x": 2,    "y": 1.25},
    {"x": 3,    "y": 1},
    {"x": 4,    "y": 1.25},
    {"x": 5,    "y": 1.5},
    {"x": 8.5,  "y": 1.5},
    {"x": 9.5,  "y": 1.3},
    {"x": 10.5, "y": 1},
    {"x": 11.5, "y": 1.33},
    {"x": 12.5, "y": 1.5},
    {"x": 13.5, "y": 1.5},
    # Row 2 (14 keys, includes 2 encoder button positions)
    {"x": 0,    "y": 2.55},
    {"x": 1,    "y": 2.55},
    {"x": 2,    "y": 2.25},
    {"x": 3,    "y": 2},
    {"x": 4,    "y": 2.25},
    {"x": 5,    "y": 2.55},
    {"x": 6,    "y": 2},
    {"x": 7.5,  "y": 2},
    {"x": 8.5,  "y": 2.55},
    {"x": 9.5,  "y": 2.3},
    {"x": 10.5, "y": 2},
    {"x": 11.5, "y": 2.33},
    {"x": 12.5, "y": 2.55},
    {"x": 13.5, "y": 2.55},
    # Row 3 (12 keys, with rotated thumb cluster)
    {"x": 0,    "y": 3.55},
    {"x": 1,    "y": 3.55},
    {"x": 2,    "y": 3.3},
    {"x": 3.5,  "y": 3.63},
    {"x": 4.5,  "y": 3.7,  "r": 11.93,  "rx": 5,    "ry": 4.75},
    {"x": 5.5,  "y": 3.65, "r": 23,     "rx": 5,    "ry": 4.75},
    {"x": 7.64, "y": 5.38, "r": -23,    "rx": 5,    "ry": 4.75},
    {"x": 9,    "y": 3.75, "r": -11.93, "rx": 9.25, "ry": 4.75},
    {"x": 10,   "y": 3.63},
    {"x": 11.5, "y": 3.38},
    {"x": 12.5, "y": 3.55},
    {"x": 13.5, "y": 3.55},
]


def inject_layout(parsed_yaml: str) -> str:
    """Inject the Cornix physical layout into the parsed YAML using qmk_info_json."""
    try:
        import yaml
    except ImportError:
        raise RuntimeError("pyyaml is required: pip install pyyaml")

    data = yaml.safe_load(parsed_yaml)
    layout_json_path = repo_path("draw", "cornix-layout.json")
    data["layout"] = {"qmk_info_json": layout_json_path, "layout_name": "LAYOUT"}
    print(f"[layout] injected qmk_info_json: {layout_json_path}")
    return yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)


# ---------------------------------------------------------------------------
# Dynamic naginata C source parser
# ---------------------------------------------------------------------------

# GitHub Raw URL — always references the latest main branch
_NAGI_C_URL = (
    "https://raw.githubusercontent.com/furugo-dev/zmk-naginata-v17"
    "/main/src/behaviors/behavior_naginata.c"
)

# Bit position → ZMK key name (matches B_Q=1<<0, B_W=1<<1, ... in the C source)
_BIT_TO_KEY: dict[int, str] = {
    0: "Q",  1: "W",  2: "E",  3: "R",  4: "T",
    5: "Y",  6: "U",  7: "I",  8: "O",  9: "P",
    10: "A", 11: "S", 12: "D", 13: "F", 14: "G",
    15: "H", 16: "J", 17: "K", 18: "L", 19: "SEMI",
    20: "Z", 21: "X", 22: "C", 23: "V", 24: "B",
    25: "N", 26: "M", 27: "COMMA", 28: "DOT", 29: "SLASH",
    30: "SPACE",
}
_B_VALUES: dict[str, int] = {f"B_{v}": (1 << k) for k, v in _BIT_TO_KEY.items()}
_B_SPACE = 1 << 30

# NAGI layer position index → ZMK key name (from config/cornix.keymap binding order)
_KEY_TO_POS: dict[str, int] = {
    "W": 2,  "E": 3,  "R": 4,  "T": 5,  "Y": 6,  "U": 7,  "I": 8,  "O": 9,
    "Q": 12, "A": 13, "S": 14, "D": 15, "F": 16, "G": 17,
    "H": 18, "J": 19, "K": 20, "L": 21, "SEMI": 22, "P": 23,
    "Z": 25, "X": 26, "C": 27, "V": 28, "B": 29,
    "N": 32, "M": 33, "COMMA": 34, "DOT": 35, "SLASH": 36,
}

# Roman kana token sequence → Japanese character
_ROMAN_TO_KANA: dict[str, str] = {
    "A": "あ", "I": "い", "U": "う", "E": "え", "O": "お",
    "KA": "か", "KI": "き", "KU": "く", "KE": "け", "KO": "こ",
    "SA": "さ", "SI": "し", "SU": "す", "SE": "せ", "SO": "そ",
    "TA": "た", "TI": "ち", "TU": "つ", "TE": "て", "TO": "と",
    "NA": "な", "NI": "に", "NU": "ぬ", "NE": "ね", "NO": "の",
    "HA": "は", "HI": "ひ", "HU": "ふ", "HE": "へ", "HO": "ほ",
    "MA": "ま", "MI": "み", "MU": "む", "ME": "め", "MO": "も",
    "YA": "や", "YU": "ゆ", "YO": "よ",
    "RA": "ら", "RI": "り", "RU": "る", "RE": "れ", "RO": "ろ",
    "WA": "わ", "WO": "を",
    "NN": "ん", "XTU": "っ", "MINUS": "ー",
    "ZYU": "じゅ",
    "COMMAENTER": "、↩", "DOTENTER": "。↩", "SPACE": "SPC",
}

# Keys whose C entries have no kana output (special function), supply labels directly
_FUNCTION_FALLBACKS: dict[str, tuple[str, str]] = {
    "T": ("←", "S←"),
    "Y": ("→", "S→"),
}

_ENTRY_RE = re.compile(
    r"\{\s*\.shift\s*=\s*(?P<shift>[^,]+?)\s*,"
    r"\s*\.douji\s*=\s*(?P<douji>[^,]+?)\s*,"
    r"\s*\.kana\s*=\s*\{(?P<kana>[^}]+)\}"
    r"\s*,\s*\.func\s*=\s*(?P<func>\w+)\s*\}"
)


def _resolve_expr(expr: str) -> int:
    """Evaluate a B_X|B_Y expression → integer. Returns -1 on unknown token."""
    val = 0
    for token in expr.strip().split("|"):
        token = token.strip()
        if token in ("NONE", "0", "0UL", "0ul", ""):
            continue
        if token not in _B_VALUES:
            return -1
        val |= _B_VALUES[token]
    return val


def _kana_tokens_to_japanese(kana_field: str) -> str | None:
    tokens = [t.strip() for t in kana_field.split(",") if t.strip() not in ("NONE", "")]
    if not tokens:
        return None
    return _ROMAN_TO_KANA.get("".join(tokens))


def fetch_nagi_c_source() -> str | None:
    """Fetch the latest behavior_naginata.c from GitHub main branch."""
    import urllib.request
    print(f"[nagi-src] fetching {_NAGI_C_URL}")
    try:
        with urllib.request.urlopen(_NAGI_C_URL, timeout=15) as resp:
            src = resp.read().decode("utf-8")
            print(f"[nagi-src] fetched {len(src)} bytes from GitHub")
            return src
    except Exception as e:
        print(f"[nagi-src] GitHub fetch failed: {e}", file=sys.stderr)
        return None


def build_nagi_mapping_from_c(src: str) -> dict[int, dict] | None:
    """Parse ngdickana[] from C source and return {pos: {t/s: kana}} mapping."""
    key_data: dict[str, dict] = {}

    for m in _ENTRY_RE.finditer(src):
        shift_val = _resolve_expr(m.group("shift"))
        douji_val = _resolve_expr(m.group("douji"))

        if shift_val == -1 or douji_val == -1:
            continue
        # Only single-bit douji (one key at a time)
        if not (douji_val > 0 and (douji_val & (douji_val - 1)) == 0):
            continue
        # Only plain (0) or space-shift
        if shift_val != 0 and shift_val != _B_SPACE:
            continue

        kana_str = _kana_tokens_to_japanese(m.group("kana"))
        if kana_str is None:
            continue

        key_name = _BIT_TO_KEY[douji_val.bit_length() - 1]
        slot = "s" if shift_val == _B_SPACE else "t"
        entry = key_data.setdefault(key_name, {})
        if slot not in entry:  # first occurrence wins
            entry[slot] = kana_str

    # Supplement function keys (T/Y) that have no kana in ngdickana[]
    for key_name, (plain_label, shift_label) in _FUNCTION_FALLBACKS.items():
        entry = key_data.setdefault(key_name, {})
        entry.setdefault("t", plain_label)
        entry.setdefault("s", shift_label)

    # Convert key_name → position index
    result: dict[int, dict] = {}
    for key_name, labels in key_data.items():
        pos = _KEY_TO_POS.get(key_name)
        if pos is None:
            continue
        entry = {k: v for k, v in labels.items() if v}
        if entry:
            result[pos] = entry

    print(f"[nagi-src] parsed {len(result)} positions from C source")
    return result if result else None


def main() -> None:
    keyboard = sys.argv[1] if len(sys.argv) > 1 else "cornix"
    print(f"[main] keyboard={keyboard}")

    config_path = repo_path("draw", f"config-{keyboard}.yaml")
    keymap_src = repo_path("config", f"{keyboard}.keymap")
    svg_out = repo_path("docs", "img", f"{keyboard}-keymap.svg")

    if not os.path.isfile(config_path):
        print(f"ERROR: config not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(keymap_src):
        print(f"ERROR: keymap not found: {keymap_src}", file=sys.stderr)
        sys.exit(1)

    # 1. Try GitHub (latest main)
    c_src = fetch_nagi_c_source()
    # 2. Fall back to local docker-workspace clone
    if c_src is None:
        local_path = repo_path(
            ".docker-workspace", "zmk-naginata-v17", "src", "behaviors", "behavior_naginata.c"
        )
        if os.path.isfile(local_path):
            print(f"[nagi-src] using local fallback: {local_path}")
            with open(local_path, encoding="utf-8") as f:
                c_src = f.read()
    # 3. Parse or use hardcoded fallback
    dynamic_mapping = build_nagi_mapping_from_c(c_src) if c_src else None
    mapping = dynamic_mapping if dynamic_mapping is not None else NAGI_MAPPING
    if dynamic_mapping is None:
        print("[nagi-src] WARNING: using hardcoded NAGI_MAPPING fallback")

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_keymap = os.path.join(tmpdir, f"{keyboard}.keymap")
        temp_yaml = os.path.join(tmpdir, f"{keyboard}.yaml")

        # Step 1: preprocess keymap (&ng → &kp)
        preprocess_keymap(keymap_src, temp_keymap)

        # Step 2: parse keymap to YAML
        parsed_yaml = run_keymap_parse(config_path, temp_keymap)

        # Step 3: inject physical layout
        yaml_with_layout = inject_layout(parsed_yaml)

        # Step 4: replace NAGI layer with Japanese labels
        processed_yaml = replace_nagi_layer(yaml_with_layout, mapping)

        # Write processed YAML to temp file
        with open(temp_yaml, "w", encoding="utf-8") as f:
            f.write(processed_yaml)
        print(f"[main] processed YAML written to {temp_yaml}")

        # Step 5: draw SVG
        run_keymap_draw(config_path, temp_yaml, svg_out)

    print(f"[main] done. SVG at {svg_out}")


if __name__ == "__main__":
    main()
