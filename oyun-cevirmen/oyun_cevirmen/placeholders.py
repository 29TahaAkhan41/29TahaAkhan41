"""Oyun metinlerindeki yer tutucuları (placeholder) çeviri sırasında korur.

Örnekler: %s, %1$d, {0}, {player}, §a (Minecraft renk kodu), <b>, [color=red],
\\n, $VAR$, {{count}}. Bunlar çevirmene gönderilmeden önce ⟦0⟧, ⟦1⟧ ... gibi
işaretlere dönüştürülür, çeviriden sonra geri konur.
"""
from __future__ import annotations

import re

PLACEHOLDER_RE = re.compile(
    r"""
    \{\{[^{}]*\}\}                     # {{count}}
  | \{[A-Za-z0-9_.:,\-#]*\}            # {0} {name} {0:N2}
  | %(?:\d+\$)?[-+ 0#]*\d*(?:\.\d+)?[sdifuxXeEgGcopn%]   # %s %1$s %.2f %%
  | [§&][0-9a-fk-orA-FK-OR]            # Minecraft renk/biçim kodları
  | </?[A-Za-z][^<>]*>                 # <b> </color> <color=#fff>
  | \[/?[A-Za-z][^\[\]]*\]             # [b] [/color] [color=red]
  | \$[A-Za-z0-9_]+\$                  # $VAR$
  | \\[nrt]                            # kaçış dizileri \n \t
  | \r?\n                              # gerçek satır sonları
  """,
    re.VERBOSE,
)

TOKEN_RE = re.compile(r"⟦\s*(\d+)\s*⟧")


def protect(text: str) -> tuple[str, list[str]]:
    """Yer tutucuları ⟦n⟧ işaretleriyle değiştirir."""
    found: list[str] = []

    def repl(m: re.Match) -> str:
        found.append(m.group(0))
        return f"⟦{len(found) - 1}⟧"

    return PLACEHOLDER_RE.sub(repl, text), found


def restore(text: str, found: list[str]) -> str | None:
    """İşaretleri geri koyar. İşaretlerden biri kaybolduysa None döner."""
    seen: set[int] = set()

    def repl(m: re.Match) -> str:
        i = int(m.group(1))
        if i >= len(found):
            return m.group(0)
        seen.add(i)
        return found[i]

    out = TOKEN_RE.sub(repl, text)
    if len(seen) != len(found) or TOKEN_RE.search(out):
        return None
    return out


def split_segments(text: str) -> list[tuple[bool, str]]:
    """Metni (çevrilecek_mi, parça) listesine böler. Yedek yöntem için."""
    parts: list[tuple[bool, str]] = []
    pos = 0
    for m in PLACEHOLDER_RE.finditer(text):
        if m.start() > pos:
            parts.append((True, text[pos:m.start()]))
        parts.append((False, m.group(0)))
        pos = m.end()
    if pos < len(text):
        parts.append((True, text[pos:]))
    return parts


def has_letters(text: str) -> bool:
    """Çevrilecek gerçek bir kelime var mı (yalnızca sayı/simge değil)?"""
    stripped = PLACEHOLDER_RE.sub("", text)
    return any(ch.isalpha() for ch in stripped)
