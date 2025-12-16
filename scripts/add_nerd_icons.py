from pathlib import Path
from typing import Iterable, List, Tuple, Dict

ROMAN_MASTERS = [
    "68A78E10-2392-4B34-B44D-B6A5B48D0FD1",
    "B7DB719C-51CF-4BC3-BA18-7A6A1AAC666B",
    "50ED6B91-33B7-40F5-8C2C-B1BEC3C77CF0",
    "D010C1AA-6BDD-4F06-9849-880CC2F29E88",
]

ITALIC_MASTERS = [
    "m006",
    "87470510-D880-4621-BF85-70AEEA552FBA",
    "90828D4A-10F7-4870-818F-40FC947ECC22",
    "00586AEE-0022-45ED-9612-7F804652F2C7",
]

GlyphShape = Dict[str, object]
Node = Tuple[int, int, str]


def plus_shape(cx: int, cy: int, arm: int = 150, thickness: int = 70) -> GlyphShape:
    half = thickness // 2
    left = cx - arm
    right = cx + arm
    top = cy - arm
    bottom = cy + arm
    nodes: List[Node] = [
        (cx - half, top, "l"),
        (cx + half, top, "l"),
        (cx + half, cy - half, "l"),
        (right, cy - half, "l"),
        (right, cy + half, "l"),
        (cx + half, cy + half, "l"),
        (cx + half, bottom, "l"),
        (cx - half, bottom, "l"),
        (cx - half, cy + half, "l"),
        (left, cy + half, "l"),
        (left, cy - half, "l"),
        (cx - half, cy - half, "l"),
    ]
    return {"closed": 1, "nodes": nodes}


def base_file_shapes() -> List[GlyphShape]:
    return [
        {
            "closed": 1,
            "nodes": [
                (220, -60, "l"),
                (880, -60, "l"),
                (1140, 200, "l"),
                (1140, 1180, "l"),
                (220, 1180, "l"),
                (220, -60, "l"),
            ],
        },
        {
            "closed": 1,
            "nodes": [
                (880, -60, "l"),
                (880, 200, "l"),
                (1140, 200, "l"),
            ],
        },
    ]


def badge_shapes() -> List[GlyphShape]:
    outer = {
        "closed": 1,
        "nodes": [
            (600, 260, "l"),
            (840, 380, "l"),
            (980, 640, "l"),
            (840, 900, "l"),
            (600, 1020, "l"),
            (360, 900, "l"),
            (220, 640, "l"),
            (360, 380, "l"),
        ],
    }
    inner = {
        "closed": 1,
        "nodes": [
            (600, 440, "l"),
            (760, 520, "l"),
            (840, 680, "l"),
            (760, 840, "l"),
            (600, 920, "l"),
            (440, 840, "l"),
            (360, 680, "l"),
            (440, 520, "l"),
        ],
    }
    return [outer, inner]


def format_nodes(nodes: Iterable[Node]) -> str:
    return "\n".join(f"({x},{y},{t})," for x, y, t in nodes).rstrip(',')


def format_shapes(shapes: List[GlyphShape]) -> str:
    shape_chunks = []
    for shape in shapes:
        if "ref" in shape:
            shape_chunks.append("{\nref = %s;\n}" % shape["ref"])
            continue
        nodes = shape["nodes"]
        chunk = ["{", f"closed = {shape.get('closed', 1)};", "nodes = (", format_nodes(nodes), ");", "}"]
        shape_chunks.append("\n".join(chunk))
    return ",\n".join(shape_chunks)


def format_layer(layer_id: str, shapes: List[GlyphShape], width: int = 1200) -> str:
    return "\n".join(
        [
            "{",
            f"layerId = \"{layer_id}\";",
            "shapes = (",
            format_shapes(shapes),
            ");",
            f"width = {width};",
            "}",
        ]
    )


def format_glyph(name: str, shapes: List[GlyphShape], codepoint: int | None = None, width: int = 1200) -> str:
    layers = [format_layer(master, shapes, width) for master in ROMAN_MASTERS]
    content = ["{", f"glyphname = {name};", "layers = (", ",\n".join(layers), ");"]
    if codepoint is not None:
        content.append(f"unicode = {codepoint};")
    content.append("}")
    return "\n".join(content)


def write_glyphs(directory: Path, icons: List[dict]):
    for icon in icons:
        content = format_glyph(icon["name"], icon["shapes"], icon.get("unicode"))
        (directory / f"{icon['name']}.glyph").write_text(content + "\n")


def write_italic_glyphs(directory: Path, icons: List[dict]):
    for icon in icons:
        layers = [format_layer(master, icon["shapes"], icon.get("width", 1200)) for master in ITALIC_MASTERS]
        content = ["{", f"glyphname = {icon['name']};", "layers = (", ",\n".join(layers), ");"]
        if icon.get("unicode") is not None:
            content.append(f"unicode = {icon['unicode']};")
        content.append("}")
        (directory / f"{icon['name']}.glyph").write_text("\n".join(content) + "\n")


def ensure_orders(order_path: Path, names: List[str]):
    lines = order_path.read_text().splitlines()
    if not lines:
        return
    # Remove closing paren
    if lines[-1].strip() == ")":
        lines = lines[:-1]
    if lines and lines[-1].endswith(',') is False:
        lines[-1] = lines[-1] + ','
    existing = [ln.rstrip(',') for ln in lines[1:]]
    for name in names:
        if name not in existing:
            lines.append(f"{name},")
            existing.append(name)
    if lines:
        lines.append(")")
    order_path.write_text("\n".join(lines) + "\n")


def ensure_glyph_order(fontinfo: Path, names: List[str]):
    text = fontinfo.read_text()
    name_pos = text.index("name = glyphOrder;")
    start = text.index("(", name_pos)
    depth = 0
    end = None
    for idx, ch in enumerate(text[start:], start):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                end = idx
                break
    if end is None:
        return
    body = text[start + 1 : end].strip().split("\n")
    entries = [ln.strip().rstrip(",") for ln in body if ln.strip()]
    changed = False
    for name in names:
        if name not in entries:
            entries.append(name)
            changed = True
    if not changed:
        return
    new_body = "\n".join(f"{entry}," for entry in entries[:-1]) + f"\n{entries[-1]}\n"
    new_text = text[: start + 1] + "\n" + new_body + text[end:]
    fontinfo.write_text(new_text)


def build_icons() -> List[dict]:
    file_base = base_file_shapes()
    badge = badge_shapes()

    def file_icon(extra_shapes: List[GlyphShape]) -> List[GlyphShape]:
        return file_base + extra_shapes

    icons = [
        {
            "name": "dev_cplusplus",
            "unicode": 0xE7A3,
            "shapes": file_icon(
                [
                    {
                        "closed": 1,
                        "nodes": [
                            (320, 260, "l"),
                            (820, 260, "l"),
                            (820, 360, "l"),
                            (440, 360, "l"),
                            (440, 900, "l"),
                            (820, 900, "l"),
                            (820, 1000, "l"),
                            (320, 1000, "l"),
                        ],
                    },
                    plus_shape(940, 520),
                    plus_shape(940, 820),
                ]
            ),
        },
        {
            "name": "dev_cmake",
            "unicode": 0xE794,
            "shapes": file_icon(
                [
                    {
                        "closed": 1,
                        "nodes": [(320, 1100, "l"), (1040, 1100, "l"), (600, 220, "l")],
                    },
                    {
                        "closed": 1,
                        "nodes": [(600, 1100, "l"), (1040, 1100, "l"), (600, 600, "l")],
                    },
                    {
                        "closed": 1,
                        "nodes": [(320, 1100, "l"), (600, 1100, "l"), (600, 600, "l")],
                    },
                ]
            ),
        },
        {
            "name": "dev_python",
            "unicode": 0xE73C,
            "shapes": file_icon(
                [
                    {
                        "closed": 1,
                        "nodes": [
                            (320, 620, "l"),
                            (820, 620, "l"),
                            (820, 980, "l"),
                            (560, 980, "l"),
                            (560, 820, "l"),
                            (320, 820, "l"),
                        ],
                    },
                    {
                        "closed": 1,
                        "nodes": [
                            (320, 260, "l"),
                            (320, 620, "l"),
                            (580, 620, "l"),
                            (580, 460, "l"),
                            (820, 460, "l"),
                            (820, 260, "l"),
                        ],
                    },
                    {
                        "closed": 1,
                        "nodes": [(700, 720, "l"), (760, 720, "l"), (760, 780, "l"), (700, 780, "l")],
                    },
                    {
                        "closed": 1,
                        "nodes": [(380, 420, "l"), (440, 420, "l"), (440, 480, "l"), (380, 480, "l")],
                    },
                ]
            ),
        },
        {
            "name": "dev_go",
            "unicode": 0xE724,
            "shapes": file_icon(
                [
                    {
                        "closed": 1,
                        "nodes": [
                            (320, 260, "l"),
                            (820, 260, "l"),
                            (820, 460, "l"),
                            (620, 460, "l"),
                            (620, 560, "l"),
                            (760, 560, "l"),
                            (760, 700, "l"),
                            (440, 700, "l"),
                            (440, 900, "l"),
                            (820, 900, "l"),
                            (820, 1000, "l"),
                            (320, 1000, "l"),
                        ],
                    },
                    {
                        "closed": 1,
                        "nodes": [(860, 260, "l"), (1140, 260, "l"), (1140, 1000, "l"), (860, 1000, "l")],
                    },
                    {
                        "closed": 1,
                        "nodes": [(940, 360, "l"), (1060, 360, "l"), (1060, 900, "l"), (940, 900, "l")],
                    },
                ]
            ),
        },
        {
            "name": "dev_java",
            "unicode": 0xE738,
            "shapes": file_icon(
                [
                    {
                        "closed": 1,
                        "nodes": [(340, 340, "l"), (900, 340, "l"), (840, 640, "l"), (360, 640, "l")],
                    },
                    {
                        "closed": 1,
                        "nodes": [(900, 400, "l"), (1060, 400, "l"), (1060, 580, "l"), (900, 580, "l")],
                    },
                    {
                        "closed": 1,
                        "nodes": [(320, 640, "l"), (940, 640, "l"), (940, 700, "l"), (320, 700, "l")],
                    },
                    {
                        "closed": 1,
                        "nodes": [(480, 760, "l"), (540, 760, "l"), (540, 1020, "l"), (480, 1020, "l")],
                    },
                    {
                        "closed": 1,
                        "nodes": [(680, 760, "l"), (740, 760, "l"), (740, 980, "l"), (680, 980, "l")],
                    },
                ]
            ),
        },
        {
            "name": "dev_markdown",
            "unicode": 0xE73E,
            "shapes": file_icon(
                [
                    {
                        "closed": 1,
                        "nodes": [(300, 360, "l"), (1040, 360, "l"), (1040, 900, "l"), (300, 900, "l")],
                    },
                    {
                        "closed": 1,
                        "nodes": [(360, 420, "l"), (980, 420, "l"), (980, 840, "l"), (360, 840, "l")],
                    },
                    {
                        "closed": 1,
                        "nodes": [(400, 420, "l"), (520, 840, "l"), (640, 420, "l"), (520, 620, "l")],
                    },
                    {
                        "closed": 1,
                        "nodes": [(760, 540, "l"), (880, 540, "l"), (820, 660, "l"), (880, 660, "l"), (820, 780, "l"), (700, 620, "l")],
                    },
                ]
            ),
        },
        {
            "name": "dev_json",
            "unicode": 0xE80B,
            "shapes": file_icon(
                [
                    {
                        "closed": 1,
                        "nodes": [
                            (360, 400, "l"),
                            (500, 400, "l"),
                            (480, 520, "l"),
                            (600, 620, "l"),
                            (480, 720, "l"),
                            (500, 840, "l"),
                            (360, 840, "l"),
                            (320, 700, "l"),
                            (380, 620, "l"),
                            (320, 540, "l"),
                        ],
                    },
                    {
                        "closed": 1,
                        "nodes": [
                            (1000, 400, "l"),
                            (860, 400, "l"),
                            (880, 520, "l"),
                            (760, 620, "l"),
                            (880, 720, "l"),
                            (860, 840, "l"),
                            (1000, 840, "l"),
                            (1040, 700, "l"),
                            (980, 620, "l"),
                            (1040, 540, "l"),
                        ],
                    },
                ]
            ),
        },
        {
            "name": "fa_file_text",
            "unicode": 0xF15C,
            "shapes": file_icon(
                [
                    {"closed": 1, "nodes": [(320, 340, "l"), (1020, 340, "l"), (1020, 420, "l"), (320, 420, "l")]},
                    {"closed": 1, "nodes": [(320, 540, "l"), (1020, 540, "l"), (1020, 620, "l"), (320, 620, "l")]},
                    {"closed": 1, "nodes": [(320, 740, "l"), (920, 740, "l"), (920, 820, "l"), (320, 820, "l")]},
                ]
            ),
        },
        {
            "name": "cod_symbol_method",
            "unicode": 0xEA8C,
            "shapes": badge
            + [
                {"closed": 1, "nodes": [(540, 460, "l"), (660, 460, "l"), (660, 820, "l"), (540, 820, "l")]},
                {"closed": 1, "nodes": [(540, 860, "l"), (660, 860, "l"), (660, 940, "l"), (540, 940, "l")]},
            ],
        },
        {
            "name": "md_function",
            "unicode": 0xF0295,
            "shapes": badge
            + [
                {
                    "closed": 1,
                    "nodes": [
                        (460, 420, "l"),
                        (540, 420, "l"),
                        (720, 880, "l"),
                        (640, 880, "l"),
                        (580, 720, "l"),
                        (520, 880, "l"),
                        (440, 880, "l"),
                        (540, 620, "l"),
                    ],
                }
            ],
        },
        {
            "name": "cod_symbol_variable",
            "unicode": 0xEA88,
            "shapes": badge
            + [
                {
                    "closed": 1,
                    "nodes": [(460, 520, "l"), (520, 460, "l"), (740, 680, "l"), (680, 740, "l")],
                },
                {
                    "closed": 1,
                    "nodes": [(460, 740, "l"), (520, 680, "l"), (740, 460, "l"), (680, 400, "l")],
                },
            ],
        },
        {
            "name": "cod_symbol_class",
            "unicode": 0xEB5B,
            "shapes": badge
            + [
                {"closed": 1, "nodes": [(410, 480, "l"), (790, 480, "l"), (790, 540, "l"), (410, 540, "l")]},
                {"closed": 1, "nodes": [(410, 620, "l"), (790, 620, "l"), (790, 680, "l"), (410, 680, "l")]},
                {"closed": 1, "nodes": [(410, 760, "l"), (790, 760, "l"), (790, 820, "l"), (410, 820, "l")]},
            ],
        },
        {
            "name": "cod_symbol_interface",
            "unicode": 0xEB61,
            "shapes": badge
            + [
                {"closed": 1, "nodes": [(440, 560, "l"), (520, 560, "l"), (520, 640, "l"), (440, 640, "l")]},
                {"closed": 1, "nodes": [(680, 560, "l"), (760, 560, "l"), (760, 640, "l"), (680, 640, "l")]},
                {"closed": 1, "nodes": [(520, 580, "l"), (680, 580, "l"), (680, 620, "l"), (520, 620, "l")]},
            ],
        },
        {
            "name": "cod_symbol_property",
            "unicode": 0xEB65,
            "shapes": badge
            + [
                {"closed": 1, "nodes": [(420, 600, "l"), (760, 600, "l"), (760, 680, "l"), (420, 680, "l")]},
                {"closed": 1, "nodes": [(760, 560, "l"), (880, 560, "l"), (880, 720, "l"), (760, 720, "l")]},
                {"closed": 1, "nodes": [(880, 600, "l"), (940, 600, "l"), (940, 680, "l"), (880, 680, "l")]},
            ],
        },
        {
            "name": "cod_symbol_enum",
            "unicode": 0xEA95,
            "shapes": badge
            + [
                {"closed": 1, "nodes": [(470, 500, "l"), (550, 500, "l"), (550, 580, "l"), (470, 580, "l")]},
                {"closed": 1, "nodes": [(470, 640, "l"), (550, 640, "l"), (550, 720, "l"), (470, 720, "l")]},
                {"closed": 1, "nodes": [(470, 780, "l"), (550, 780, "l"), (550, 860, "l"), (470, 860, "l")]},
                {"closed": 1, "nodes": [(640, 580, "l"), (820, 580, "l"), (820, 660, "l"), (640, 660, "l")]},
                {"closed": 1, "nodes": [(640, 740, "l"), (820, 740, "l"), (820, 820, "l"), (640, 820, "l")]},
            ],
        },
        {
            "name": "cod_symbol_constant",
            "unicode": 0xEB5D,
            "shapes": badge
            + [
                {
                    "closed": 1,
                    "nodes": [(500, 460, "l"), (700, 460, "l"), (760, 560, "l"), (700, 660, "l"), (500, 660, "l"), (440, 560, "l")],
                },
                {
                    "closed": 1,
                    "nodes": [(540, 600, "l"), (660, 600, "l"), (700, 660, "l"), (660, 720, "l"), (540, 720, "l"), (500, 660, "l")],
                },
            ],
        },
        {
            "name": "cod_symbol_namespace",
            "unicode": 0xEA8B,
            "shapes": badge
            + [
                {
                    "closed": 1,
                    "nodes": [(420, 460, "l"), (520, 460, "l"), (520, 520, "l"), (480, 520, "l"), (480, 840, "l"), (520, 840, "l"), (520, 900, "l"), (420, 900, "l")],
                },
                {
                    "closed": 1,
                    "nodes": [(780, 460, "l"), (680, 460, "l"), (680, 520, "l"), (720, 520, "l"), (720, 840, "l"), (680, 840, "l"), (680, 900, "l"), (780, 900, "l")],
                },
            ],
        },
        {
            "name": "cod_symbol_parameter",
            "unicode": 0xEA92,
            "shapes": badge
            + [
                {"closed": 1, "nodes": [(540, 520, "l"), (600, 520, "l"), (600, 580, "l"), (540, 580, "l")]},
                {"closed": 1, "nodes": [(540, 720, "l"), (600, 720, "l"), (600, 780, "l"), (540, 780, "l")]},
                {"closed": 1, "nodes": [(660, 620, "l"), (780, 620, "l"), (780, 680, "l"), (660, 680, "l")]},
            ],
        },
    ]
    return icons


def main():
    icons = build_icons()
    roman_dir = Path("sources/GoogleSansCode.glyphspackage/glyphs")
    italic_dir = Path("sources/GoogleSansCode-Italic.glyphspackage/glyphs")
    write_glyphs(roman_dir, icons)
    write_italic_glyphs(italic_dir, icons)
    names = [icon["name"] for icon in icons]
    ensure_orders(Path("sources/GoogleSansCode.glyphspackage/order.plist"), names)
    ensure_orders(Path("sources/GoogleSansCode-Italic.glyphspackage/order.plist"), names)
    ensure_glyph_order(Path("sources/GoogleSansCode.glyphspackage/fontinfo.plist"), names)
    ensure_glyph_order(Path("sources/GoogleSansCode-Italic.glyphspackage/fontinfo.plist"), names)


if __name__ == "__main__":
    main()
