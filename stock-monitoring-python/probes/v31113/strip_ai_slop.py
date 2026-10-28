#!/usr/bin/env python3
"""v3.11.13 — HILANGKAN AI SLOP dari UI (permintaan user).

Strip emoji dekoratif + glyph prefix dari RUNTIME string literals di
src/ui/*.py + test_ui_redesign.py + test_mock.py (docstring & comment
TIDAK disentuh — itu riwayat versi, bukan UI).

Aturan:
- STRIP_ALWAYS : emoji/glyph dekoratif — dibuang dari literal apa pun.
- PREFIX_ONLY  : ✕ ☑ — dibuang HANYA bila literal punya konten lain
                 (glif berdiri sendiri = tombol close/checkbox → KEEP).
- KEEPed        : ✓ ✗ ⚠ ● • → ↗ ↘ ↑ ↓ ↳ ▸ ▲ ▼ ☐ · — … × Σ Δ (fungsional).
- Edge-aware    : spasi/newline hanya dibuang BILA menempel emoji yang
                  dibuang (pemisah " 🚀 " → " "), spasi tepi yang memang
                  bagian nilai TIDAK disentuh — aman utk implicit-concat
                  multi-baris & chunk f-string.
- Literal utuh yang jadi KOSONG (icon-only, mis. "📊") TIDAK diubah —
  dilaporkan sbg FLAG utk penanganan manual. Chunk f-string yang jadi
  kosong ("📊 " di f"📊 {x}") AMAN diganti "".
AST-based: posisi byte-akurat (utf-8), rewrite urut mundur, file
di-parse ulang sbg verifikasi sintaks.
"""
import ast
import re
import sys

STRIP_ALWAYS = set(
    "⚙🚀📊📦🧩📤📋🧮🛒💾🧹📂🎯✏🗑⚖💰🚨🏆🧭♻🔎📉📈📭⚡🫵🔄📌🔍📥🏪📅"
    "⛶◱◫▦↺↻↕↔⏳⏹ℹ⤢⤡⧩"
) | {"\ufe0f"}
PREFIX_ONLY = set("☑✕")
ALL_TARGET = STRIP_ALWAYS | PREFIX_ONLY

RE_FIX_PUNCT = re.compile(r" +([.,;:!?%)])")
RE_OPEN_PAREN = re.compile(r"\( +")
RE_MULTI_SPACE = re.compile(r"  +")


def _class(has_other: bool) -> str:
    chars = STRIP_ALWAYS | (PREFIX_ONLY if has_other else set())
    return "".join(re.escape(c) for c in chars)


def _part_clean(seg: str, cls: str) -> str:
    """Bersihkan SATU bagian teks: buang emoji + spasi MENEMPEL saja."""
    if not any(c in ALL_TARGET for c in seg):
        return seg
    # cluster emoji di tepi (+spasi menempel) → hilangkan
    seg = re.sub(r"^[ \t]*(?:[" + cls + "])+[ \t]*", "", seg)
    seg = re.sub(r"[ \t]*(?:[" + cls + "])+$", "", seg)
    # cluster di tengah: "a 📊 b" → "a b" · "b 📊." → "b."
    def _mid(m):
        left, right = m.group(1), m.group(2)
        if left and right:
            return " "
        return ""
    seg = re.sub(r"([ \t]*)[" + cls + "]+([ \t]*)", _mid, seg)
    return seg


def _docstring_ids(tree):
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                docs.add(id(body[0].value))
    return docs


def process(path: str, apply: bool):
    with open(path, encoding="utf-8") as f:
        src = f.read()
    tree = ast.parse(src)
    docs = _docstring_ids(tree)
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[id(child)] = node

    data = src.encode("utf-8")
    line_starts = [0]
    for i, b in enumerate(data):
        if b == 0x0A:
            line_starts.append(i + 1)

    edits = []   # (byte_start, byte_end, replacement_bytes)
    flags = []   # icon-only → manual
    changed = [] # (lineno, before, after)

    def has_other_content(val: str) -> bool:
        return any(c not in ALL_TARGET and not c.isspace() for c in val)

    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant)
                and isinstance(node.value, str)):
            continue
        if id(node) in docs:
            continue
        if not any(c in ALL_TARGET for c in node.value):
            continue
        start = line_starts[node.lineno - 1] + node.col_offset
        end = (line_starts[node.end_lineno - 1] + node.end_col_offset)
        seg = data[start:end].decode("utf-8")
        cls = _class(has_other_content(node.value))

        in_fstr = isinstance(parents.get(id(node)), ast.JoinedStr)
        if in_fstr:
            # chunk literal f-string: raw text tanpa prefix/quote.
            # Chunk yang jadi kosong (mis. "📊 ") AMAN diganti "".
            stripped = "".join(
                ch for ch in seg
                if ch not in STRIP_ALWAYS and ch != "\ufe0f")
            if not stripped.strip():
                edits.append((start, end, b""))
                changed.append((node.lineno, seg, "<f-chunk kosong>"))
                continue
            new = _part_clean(seg, cls)
            if new != seg:
                edits.append((start, end, new.encode("utf-8")))
                changed.append((node.lineno, seg, new))
            continue

        m = re.match(r"^([fFrRbBuU]{0,2})('''|\"\"\"|'|\")", seg)
        if not m or not seg.endswith(m.group(2)):
            flags.append((node.lineno, seg))
            continue
        prefix, quote = m.group(1), m.group(2)
        content = seg[m.end():len(seg) - len(quote)]
        if not has_other_content(node.value):
            # literal icon-only (mis. "📊" / "✕") → jangan otomatis
            flags.append((node.lineno, seg))
            continue
        if (len(quote) == 1
                and re.search(rf"(?<!\\){re.escape(quote)}", content)):
            # implicit-concat multi-baris: bersihkan PER-BAGIAN,
            # boundary (newline/indent/komentar) dipertahankan.
            boundary = re.compile(
                rf"((?:#[^\n]*\n|\n)+[ \t]*(?={re.escape(quote)}))")
            segs = boundary.split(content)
            parts = []
            for i, s in enumerate(segs):
                if i % 2 == 1 or not s:
                    parts.append(s)
                    continue
                lead = trail = ""
                if s.startswith(quote):
                    lead, s = s[0], s[1:]
                if s.endswith(quote):
                    trail, s = s[-1], s[:-1]
                parts.append(lead + _part_clean(s, cls) + trail)
            new = "".join(parts)
        else:
            new = _part_clean(content, cls)
            new = RE_MULTI_SPACE.sub(" ", new)
            new = RE_FIX_PUNCT.sub(r"\1", new)
            new = RE_OPEN_PAREN.sub("(", new)
        if new != content:
            new_seg = f"{prefix}{quote}{new}{quote}"
            edits.append((start, end, new_seg.encode("utf-8")))
            changed.append((node.lineno, content, new))

    print(f"== {path}: {len(edits)} edit, {len(flags)} flag icon-only")
    for ln, before, after in changed:
        b = " ".join(before.split())[:88]
        a = " ".join(str(after).split())[:88]
        print(f"   L{ln}: {b!r} -> {a!r}")
    for ln, seg in flags:
        print(f"   FLAG L{ln}: {seg[:60]!r}")

    if apply and edits:
        for s, e, rep in sorted(edits, reverse=True):
            data = data[:s] + rep + data[e:]
        out = data.decode("utf-8")
        ast.parse(out)  # verifikasi sintaks
        with open(path, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"   >> WRITTEN ({len(edits)} edits)")
    return len(edits), len(flags)


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    files = [f for f in sys.argv[1:] if not f.startswith("--")]
    tot_e = tot_f = 0
    for p in files:
        e, fl = process(p, apply)
        tot_e += e
        tot_f += fl
    print(f"\nTOTAL: {tot_e} edits, {tot_f} flags "
          f"({'APPLY' if apply else 'DRY-RUN'})")
