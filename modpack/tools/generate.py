"""FTB Quests (1.21.1 / 2101.x) görev dosyalarını üretir.

Kullanım:  python3 modpack/tools/generate.py
Çıktı:     modpack/overrides/config/ftbquests/quests/
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quests import CHAPTERS  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "overrides", "config", "ftbquests", "quests")
FILE_ID = "0000000000000001"


def qid(*parts):
    """Yeniden üretimde değişmeyen 16 haneli hex kimlik."""
    return hashlib.sha1("/".join(parts).encode()).hexdigest()[:16].upper()


def s(v):
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def snbt(v, ind=0):
    pad = "\t" * ind
    if isinstance(v, dict):
        if not v:
            return "{ }"
        lines = [f"{pad}\t{k}: {snbt(val, ind + 1)}" for k, val in v.items()]
        return "{\n" + "\n".join(lines) + f"\n{pad}}}"
    if isinstance(v, list):
        if not v:
            return "[ ]"
        if all(isinstance(x, str) for x in v):
            return "[\n" + "\n".join(f"{pad}\t{s(x)}" for x in v) + f"\n{pad}]"
        return "[\n" + "\n".join(f"{pad}\t{snbt(x, ind + 1)}" for x in v) + f"\n{pad}]"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return f"{v}d"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, Raw):
        return v.text
    return s(v)


class Raw:
    def __init__(self, text):
        self.text = text


def reward(qkey, i, r):
    rid = qid("reward", qkey, str(i))
    if r[0] == "xp":
        return {"id": rid, "type": "xp", "xp": r[1]}
    if r[0] == "item":
        out = {"id": rid, "item": {"count": 1, "id": r[1]}, "type": "item"}
        if r[2] > 1:
            out["count"] = r[2]
        return out
    if r[0] == "cmd":
        return {"id": rid, "type": "command", "command": r[1], "elevate_perms": True, "silent": True, "player_command": False}
    raise ValueError(r)


def main():
    os.makedirs(os.path.join(OUT, "chapters"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "lang"), exist_ok=True)
    keys = {q[0] for ch in CHAPTERS for q in ch["quests"]}
    lang = {f"file.{FILE_ID}.title": "Yıldız Yolu"}

    for order, ch in enumerate(CHAPTERS):
        cid = qid("chapter", ch["key"])
        lang[f"chapter.{cid}.title"] = ch["title"]
        quests = []
        for (key, title, desc, item, count, deps, rewards, x, y) in ch["quests"]:
            for d in deps:
                assert d in keys, f"bilinmeyen bağımlılık: {d}"
            q_id = qid("quest", key)
            t_id = qid("task", key)
            if item == "checkmark":
                task = {"id": t_id, "type": "checkmark"}
            else:
                task = {"id": t_id, "item": {"count": 1, "id": item}, "type": "item"}
                if count > 1:
                    task["count"] = Raw(f"{count}L")
            quest = {"id": q_id}
            if deps:
                quest["dependencies"] = [qid("quest", d) for d in deps]
            if key == "fn_kalp":
                quest["shape"] = "gear"
                quest["size"] = 2.0
            quest["rewards"] = [reward(key, i, r) for i, r in enumerate(rewards)]
            quest["tasks"] = [task]
            quest["x"] = float(x)
            quest["y"] = float(y)
            quests.append(quest)
            lang[f"quest.{q_id}.title"] = title
            lang[f"quest.{q_id}.quest_desc"] = [desc]

        chapter = {
            "default_hide_dependency_lines": False,
            "default_quest_shape": "",
            "filename": ch["key"],
            "group": "",
            "icon": {"id": ch["icon"]},
            "id": cid,
            "order_index": order,
            "quest_links": [],
            "quests": quests,
        }
        with open(os.path.join(OUT, "chapters", ch["key"] + ".snbt"), "w", encoding="utf-8") as f:
            f.write(snbt(chapter) + "\n")

    data = {
        "default_autoclaim_rewards": "disabled",
        "default_consume_items": False,
        "default_quest_disable_jei": False,
        "default_quest_shape": "circle",
        "default_reward_team": False,
        "disable_gui": False,
        "drop_loot_crates": False,
        "emergency_items_cooldown": 300,
        "grid_scale": 0.5,
        "icon": {"id": "ftbquests:book"},
        "lock_message": "",
        "pause_game": False,
        "progression_mode": "linear",
        "version": 13,
    }
    with open(os.path.join(OUT, "data.snbt"), "w", encoding="utf-8") as f:
        f.write(snbt(data) + "\n")

    # Türkçe metinler hem tr_tr hem en_us'a yazılır (oyun dili ne olursa olsun görünsün).
    for code in ("tr_tr", "en_us"):
        with open(os.path.join(OUT, "lang", code + ".snbt"), "w", encoding="utf-8") as f:
            f.write(snbt(lang) + "\n")

    n = sum(len(c["quests"]) for c in CHAPTERS)
    print(f"{len(CHAPTERS)} bölüm, {n} görev yazıldı -> {OUT}")


if __name__ == "__main__":
    main()
