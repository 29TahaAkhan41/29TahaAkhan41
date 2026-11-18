"""Oyun dil/yerelleştirme dosyalarını Türkçeye çevirir.

Desteklenen biçimler:
  .json                  (iç içe JSON; tüm metin değerleri - Minecraft, Unity, RPG Maker...)
  .lang .properties .cfg .ini   (anahtar=değer)
  .po .pot               (gettext: msgid -> msgstr)
  .csv .tsv              (ilk sütun anahtar sayılır, diğer metin hücreleri çevrilir)
  .yml .yaml             (iç içe YAML - Ren'Py dışı, Paradox oyunları vb.)
  .xml .resx             (metin düğümleri ve value/text öznitelikleri)
  .txt                   (satır satır)
"""
from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path
from typing import Callable

from .translator import Translator

Progress = Callable[[int, int], None] | None

SUPPORTED = (
    ".json", ".lang", ".properties", ".cfg", ".ini", ".po", ".pot",
    ".csv", ".tsv", ".yml", ".yaml", ".xml", ".resx", ".txt",
)

# Çevrilmemesi gereken değerler: dosya yolları, URL'ler, renk kodları, tanımlayıcılar
_SKIP_RE = re.compile(
    r"^(?:https?://\S+|[\w./\\-]+\.(?:png|jpg|ogg|wav|mp3|json|txt|dds|tga)"
    r"|#[0-9a-fA-F]{3,8}|[a-z0-9_]+(?:[.:][a-z0-9_]+)+|-?\d+(?:\.\d+)?|true|false)$"
)


def should_translate(value: str) -> bool:
    v = value.strip()
    return bool(v) and not _SKIP_RE.match(v) and any(c.isalpha() for c in v)


def default_output_path(path: Path) -> Path:
    """en_us.json -> tr_tr.json, english.txt -> turkish.txt, diğerleri -> ad_tr.uzantı"""
    name = path.name
    for pat, rep in (
        (r"en_us", "tr_tr"), (r"en_US", "tr_TR"), (r"en-US", "tr-TR"), (r"en_gb", "tr_tr"),
        (r"(?i)english", "turkish"), (r"(?<![a-z])en(?![a-z])", "tr"),
    ):
        new = re.sub(pat, rep, name, count=1)
        if new != name:
            return path.with_name(new)
    return path.with_name(f"{path.stem}_tr{path.suffix}")


def translate_file(
    src: Path, dst: Path, translator: Translator, progress: Progress = None
) -> int:
    """Dosyayı çevirip dst'ye yazar. Çevrilen metin sayısını döner."""
    ext = src.suffix.lower()
    raw = src.read_bytes()
    encoding = "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8"
    try:
        text = raw.decode(encoding)
    except UnicodeDecodeError:
        encoding = "cp1252"
        text = raw.decode(encoding)

    handler = {
        ".json": _json, ".lang": _keyvalue, ".properties": _keyvalue, ".cfg": _keyvalue,
        ".ini": _keyvalue, ".po": _po, ".pot": _po, ".csv": _csv, ".tsv": _csv,
        ".yml": _yaml, ".yaml": _yaml, ".xml": _xml, ".resx": _xml, ".txt": _txt,
    }.get(ext)
    if handler is None:
        raise ValueError(f"Desteklenmeyen dosya türü: {ext}")

    out, count = handler(text, translator, progress, ext)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(out, encoding="utf-8-sig" if encoding == "utf-8-sig" else "utf-8", newline="")
    return count


def translate_folder(
    folder: Path, out_folder: Path, translator: Translator,
    progress: Callable[[str, int, int], None] | None = None,
) -> list[tuple[Path, int | str]]:
    """Klasördeki tüm desteklenen dosyaları aynı yapıyla out_folder'a çevirir."""
    files = [p for p in sorted(folder.rglob("*")) if p.is_file() and p.suffix.lower() in SUPPORTED]
    report: list[tuple[Path, int | str]] = []
    for i, f in enumerate(files):
        if progress:
            progress(f.name, i, len(files))
        dst = out_folder / f.relative_to(folder)
        try:
            report.append((f, translate_file(f, dst, translator)))
        except Exception as e:  # bir dosya bozuksa diğerlerine devam et
            report.append((f, f"HATA: {e}"))
    if progress:
        progress("", len(files), len(files))
    return report


# --- Biçimler ------------------------------------------------------------

def _apply(values: list[str], translator: Translator, progress: Progress) -> dict[str, str]:
    wanted = [v for v in dict.fromkeys(values) if should_translate(v)]
    return dict(zip(wanted, translator.translate_many(wanted, progress)))


def _json(text, translator, progress, _ext):
    data = json.loads(text)
    strings: list[str] = []

    def collect(node):
        if isinstance(node, dict):
            for v in node.values():
                collect(v)
        elif isinstance(node, list):
            for v in node:
                collect(v)
        elif isinstance(node, str):
            strings.append(node)

    collect(data)
    table = _apply(strings, translator, progress)

    def rebuild(node):
        if isinstance(node, dict):
            return {k: rebuild(v) for k, v in node.items()}
        if isinstance(node, list):
            return [rebuild(v) for v in node]
        if isinstance(node, str):
            return table.get(node, node)
        return node

    indent = 2
    m = re.search(r"\n([ \t]+)\S", text)
    if m:
        indent = m.group(1) if "\t" in m.group(1) else len(m.group(1))
    out = json.dumps(rebuild(data), ensure_ascii=False, indent=indent)
    return out + ("\n" if text.endswith("\n") else ""), len(table)


_KV_RE = re.compile(r"^(\s*[^#;!\s=:][^=:]*?\s*[=:]\s*)(.*?)(\r?)$")


def _keyvalue(text, translator, progress, _ext):
    lines = text.split("\n")
    values = []
    for line in lines:
        m = _KV_RE.match(line)
        if m and not line.lstrip().startswith("["):
            values.append(m.group(2))
    table = _apply(values, translator, progress)
    out = []
    for line in lines:
        m = _KV_RE.match(line)
        if m and not line.lstrip().startswith("[") and m.group(2) in table:
            line = m.group(1) + table[m.group(2)] + m.group(3)
        out.append(line)
    return "\n".join(out), len(table)


def _txt(text, translator, progress, _ext):
    lines = text.split("\n")
    stripped = [l.rstrip("\r") for l in lines]
    table = _apply(stripped, translator, progress)
    out = [
        table.get(s, s) + ("\r" if l.endswith("\r") else "") for l, s in zip(lines, stripped)
    ]
    return "\n".join(out), len(table)


def _po(text, translator, progress, _ext):
    # Basit gettext ayrıştırıcı: msgid "..." (+ devam satırları) / msgstr "..."
    entry_re = re.compile(
        r'(msgid\s+((?:"(?:[^"\\]|\\.)*"\s*)+))(msgstr\s+)((?:"(?:[^"\\]|\\.)*"\s*?)+)',
        re.MULTILINE,
    )

    def unquote(block: str) -> str:
        return "".join(json.loads(s) for s in re.findall(r'"(?:[^"\\]|\\.)*"', block))

    entries = list(entry_re.finditer(text))
    ids = [unquote(m.group(2)) for m in entries if unquote(m.group(2)) and not unquote(m.group(4))]
    table = _apply(ids, translator, progress)

    def repl(m):
        msgid = unquote(m.group(2))
        if msgid in table and not unquote(m.group(4)):
            return m.group(1) + m.group(3) + json.dumps(table[msgid], ensure_ascii=False)
        return m.group(0)

    return entry_re.sub(repl, text), len(table)


def _csv(text, translator, progress, ext):
    delim = "\t" if ext == ".tsv" else (csv.Sniffer().sniff(text[:4096], ",;").delimiter
                                         if text.strip() else ",")
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    values = [c for r in rows[1:] for c in r[1:]]
    table = _apply(values, translator, progress)
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=delim, lineterminator="\r\n" if "\r\n" in text else "\n")
    if rows:
        w.writerow(rows[0])
    for r in rows[1:]:
        w.writerow(r[:1] + [table.get(c, c) for c in r[1:]])
    return buf.getvalue(), len(table)


def _yaml(text, translator, progress, _ext):
    # Satır bazlı: yorumları ve düzeni korur.  anahtar: "değer"  /  anahtar: değer
    line_re = re.compile(r'^(\s*(?:- )?[^#\s][^:#]*:\d*\s+)(["\']?)(.*?)\2(\s*(?:#.*)?)(\r?)$')
    lines = text.split("\n")
    matches = [line_re.match(l) for l in lines]
    values = [m.group(3) for m in matches if m and m.group(3) and m.group(3)[0] not in "|>&*[{"]
    table = _apply(values, translator, progress)
    out = []
    for line, m in zip(lines, matches):
        if m and m.group(3) in table:
            val = table[m.group(3)]
            q = m.group(2)
            if q == '"':
                val = val.replace('\\"', '"').replace('"', '\\"')
            elif q == "'":
                val = val.replace("'", "''") if "''" not in val else val
            elif ": " in val or val.startswith(("#", "-", "'", '"')):
                q, val = '"', val.replace('"', '\\"')
            line = f"{m.group(1)}{q}{val}{q}{m.group(4)}{m.group(5)}"
        out.append(line)
    return "\n".join(out), len(table)


def _xml(text, translator, progress, _ext):
    # Metin düğümleri ve yaygın öznitelikler; yapıyı bozmamak için regex ile.
    import html

    node_re = re.compile(r">([^<>]+)<")
    attr_re = re.compile(r'(\b(?:value|text|title|label|tooltip|description)\s*=\s*")([^"]*)(")')
    texts = [html.unescape(m.group(1)) for m in node_re.finditer(text)]
    texts += [html.unescape(m.group(2)) for m in attr_re.finditer(text)]
    texts = [t for t in texts if t.strip()]
    table = _apply([t.strip() for t in texts], translator, progress)

    def tr(s: str, attr: bool) -> str:
        raw = html.unescape(s)
        key = raw.strip()
        if key not in table:
            return s
        new = raw.replace(key, table[key])
        return html.escape(new, quote=attr)

    out = node_re.sub(lambda m: ">" + tr(m.group(1), False) + "<", text)
    out = attr_re.sub(lambda m: m.group(1) + tr(m.group(2), True) + m.group(3), out)
    return out, len(table)
