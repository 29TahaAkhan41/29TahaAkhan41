"""FTB Quests (1.21.1 / 2101.x) görev dosyalarını üretir.

Kullanım:  python3 modpack/tools/generate.py
Çıktı:     modpack/overrides/config/ftbquests/quests/
"""
import hashlib
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quests import CHAPTERS, FINAL  # noqa: E402
import quests_en as EN  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "overrides", "config", "ftbquests", "quests")
FILE_ID = "0000000000000001"
NAMES_EN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "item_names_en.json")
SPACING = 1.5


def qid(*parts):
    """Yeniden üretimde değişmeyen 16 haneli hex kimlik."""
    return hashlib.sha1("/".join(parts).encode()).hexdigest()[:16].upper()


class Raw:
    def __init__(self, text):
        self.text = text


def s(v):
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def snbt(v, ind=0):
    pad = "\t" * ind
    if isinstance(v, Raw):
        return v.text
    if isinstance(v, dict):
        if not v:
            return "{ }"
        lines = [f"{pad}\t{k}: {snbt(val, ind + 1)}" for k, val in v.items()]
        return "{\n" + "\n".join(lines) + f"\n{pad}}}"
    if isinstance(v, list):
        if not v:
            return "[ ]"
        return "[\n" + "\n".join(f"{pad}\t{snbt(x, ind + 1)}" for x in v) + f"\n{pad}]"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return f"{v}d"
    if isinstance(v, int):
        return str(v)
    return s(v)


def item_reward(rid, item, count):
    out = {"id": rid, "item": {"count": 1, "id": item}, "type": "item"}
    if count > 1:
        out["count"] = count
    return out


def make_task(key, item, count):
    t_id = qid("task", key)
    if item == "checkmark":
        return {"id": t_id, "type": "checkmark"}
    task = {"id": t_id, "item": {"count": 1, "id": item}, "type": "item"}
    if count > 1:
        task["count"] = Raw(f"{count}L")
    return task


def chapter_file(cid, key, icon, order, quests):
    return {
        "default_hide_dependency_lines": False,
        "default_quest_shape": "",
        "filename": key,
        "group": "",
        "icon": {"id": icon},
        "id": cid,
        "order_index": order,
        "quest_links": [],
        "quests": quests,
    }


def write(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        f.write(snbt(obj) + "\n")


def main():
    chapters_dir = os.path.join(OUT, "chapters")
    shutil.rmtree(chapters_dir, ignore_errors=True)
    os.makedirs(chapters_dir)
    os.makedirs(os.path.join(OUT, "lang"), exist_ok=True)

    import json
    names = json.load(open(NAMES_EN, encoding="utf-8")) if os.path.exists(NAMES_EN) else {}
    missing_en = set()
    lang = {f"file.{FILE_ID}.title": "Yıldız Yolu"}
    en = {f"file.{FILE_ID}.title": EN.FILE_TITLE}

    def en_title(item, tr):
        if tr in EN.TITLES:
            return EN.TITLES[tr]
        if item in names:
            return names[item]
        missing_en.add(("başlık", tr))
        return tr

    def en_desc(tr):
        if tr not in EN.DESCS:
            missing_en.add(("açıklama", tr))
        return EN.DESCS.get(tr, tr)

    capstones, creative_ids = [], []
    seen_items = {}
    total = 0

    for order, ch in enumerate(CHAPTERS):
        cid = qid("chapter", ch["key"])
        lang[f"chapter.{cid}.title"] = ch["title"]
        en[f"chapter.{cid}.title"] = EN.CHAPTERS.get(ch["title"], ch["title"])
        tier = ch["tier"]
        quests = []
        root_id = None
        for r, row in enumerate(ch["rows"]):
            prev = None
            for i, (item, count, title, desc) in enumerate(row):
                key = f"{ch['key']}/{r}/{i}"
                if item != "checkmark":
                    dup = seen_items.get((item, count))
                    assert dup is None, f"aynı görev iki kez: {item} ({dup} ve {key})"
                    seen_items[(item, count)] = key
                q_id = qid("quest", key)
                deps = []
                if prev:
                    deps.append(prev)
                elif r > 0:
                    deps.append(root_id)
                rewards = [{"id": qid("reward", key, "xp"), "type": "xp", "xp": 10 * tier * (1 + i // 3)}]
                last_in_row = i == len(row) - 1
                if last_in_row:
                    rewards.append(item_reward(qid("reward", key, "item"), *ch["reward"]))
                quest = {"id": q_id}
                if deps:
                    quest["dependencies"] = deps
                if r == 0 and (i == 0 or last_in_row):
                    quest["shape"] = "hexagon"
                    quest["size"] = 1.5
                quest["rewards"] = rewards
                quest["tasks"] = [make_task(key, item, count)]
                quest["x"] = float(i * SPACING)
                quest["y"] = float(r * SPACING * (1.4 if r else 1))
                quests.append(quest)

                lang[f"quest.{q_id}.title"] = title
                en[f"quest.{q_id}.title"] = en_title(item, title)
                if desc:
                    lang[f"quest.{q_id}.quest_desc"] = [desc]
                    en[f"quest.{q_id}.quest_desc"] = [en_desc(desc)]
                if r == 0 and i == 0:
                    root_id = q_id
                if r == 0 and last_in_row:
                    capstones.append(q_id)
                if ch["key"] == "yaratici" and r > 0:
                    creative_ids.append(q_id)
                prev = q_id
                total += 1
        write(os.path.join(chapters_dir, ch["key"] + ".snbt"),
              chapter_file(cid, ch["key"], ch["icon"], order, quests))

    # Final bölümü
    cid = qid("chapter", FINAL["key"])
    lang[f"chapter.{cid}.title"] = FINAL["title"]
    en[f"chapter.{cid}.title"] = EN.CHAPTERS[FINAL["title"]]
    key = "final/0/0"
    q_id = qid("quest", key)
    tellraw = ('/tellraw @a [{"text":"\\u2726 ","color":"gold"},'
               '{"translate":"message.kubejs.pack_complete","color":"gold",'
               '"with":[{"text":"{p}","color":"light_purple","bold":true}]},{"text":" \\u2726","color":"gold"}]')
    title_cmd = '/title {p} title {"translate":"title.kubejs.pack_complete","color":"gold","bold":true}'
    firework = ('/execute at {p} run summon firework_rocket ~ ~1 ~ {LifeTime:20,FireworksItem:{id:"minecraft:firework_rocket",count:1,'
                'components:{"minecraft:fireworks":{flight_duration:1,explosions:[{shape:"star",colors:[I;16766720,11141290],'
                'has_trail:true,has_twinkle:true}]}}}}')
    rewards = [item_reward(qid("reward", key, "medal"), "kubejs:completion_medal", 1),
               {"id": qid("reward", key, "xp"), "type": "xp", "xp": 5000}]
    for n, cmd in enumerate([tellraw, title_cmd, firework]):
        rewards.append({"id": qid("reward", key, f"cmd{n}"), "type": "command", "command": cmd,
                        "elevate_perms": True, "silent": True, "player_command": False})
    final_q = {
        "id": q_id,
        "dependencies": capstones + creative_ids,
        "shape": "gear",
        "size": 3.0,
        "rewards": rewards,
        "tasks": [make_task(key, FINAL["item"], 1)],
        "x": 0.0,
        "y": 0.0,
    }
    lang[f"quest.{q_id}.title"] = FINAL["quest_title"]
    lang[f"quest.{q_id}.quest_desc"] = [FINAL["desc"]]
    en[f"quest.{q_id}.title"] = en_title(FINAL["item"], FINAL["quest_title"])
    en[f"quest.{q_id}.quest_desc"] = [en_desc(FINAL["desc"])]
    total += 1
    write(os.path.join(chapters_dir, "final.snbt"),
          chapter_file(cid, FINAL["key"], FINAL["icon"], len(CHAPTERS), [final_q]))

    write(os.path.join(OUT, "data.snbt"), {
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
    })

    # tr_tr: Türkçe, en_us: İngilizce (diğer diller en_us'a düşer).
    write(os.path.join(OUT, "lang", "tr_tr.snbt"), lang)
    write(os.path.join(OUT, "lang", "en_us.snbt"), en)
    for kind, text in sorted(missing_en):
        print(f"  ! İngilizcesi yok ({kind}): {text}")

    print(f"{len(CHAPTERS) + 1} bölüm, {total} görev yazıldı -> {OUT}")
    for ch in CHAPTERS:
        print(f"  {ch['key']:<12} {sum(len(r) for r in ch['rows'])}")


if __name__ == "__main__":
    main()
