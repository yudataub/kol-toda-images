# -*- coding: utf-8 -*-
"""תיוג הצבר (data/tagjobs/new.json) בראייה, בגיליונות של 12 תמונות. לא מתייג בעצמו – רק מכין, בודק וממזג.
    python vision_batch.py make            # בונה גיליונות data/visionjobs/v-<סדרה>-pNNN|sNNN.(jpg|json) למה שעוד לא תויג
    python vision_batch.py list [סדרה]     # שמות הגיליונות שעוד אין להם visionparts תקין
    python vision_batch.py check <שם> ...  # בדיקת חלק(ים)
    python vision_batch.py merge           # רק חלקי v-* תקינים -> tags.json + review.json (מסומנים: bad, בלי תגיות)
    python vision_batch.py status          # כמה תויגו / נשארו לפי סדרה
ההנחיות לסוכן: TAG_VISION_BATCH.md"""
import glob, json, os, re, sys
from collections import defaultdict, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
VJ, VP = os.path.join(D, "visionjobs"), os.path.join(D, "visionparts")
NIK = re.compile(r"[֑-ׇ]")
BAD = re.compile(r"(?:^|\s)(?:אישה|אשה|נשים|ילדה|ילדות|בחורה|אמא|סבתא|בת)(?=\s|$)")
FLAGS = {"women", "text", "church", "statue", "dome", "other"}
EMO = re.compile(r"[^\w\s׳״'\"\-–›,.()]+", re.U)


def jl(p, default=None):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def series(i):
    p = i.split("/")
    return re.sub(r"-\d+[a-z]?$", "", p[1]) if p[0] == "hq" else "misc"


def done_ids():
    out = set()
    for f in glob.glob(os.path.join(VP, "v-*.json")):
        k = os.path.basename(f)[:-5]
        if os.path.exists(os.path.join(VJ, k + ".json")) and not check(k):
            out.update(jl(f))
    return out


def make():
    from PIL import Image, ImageDraw, ImageFont
    items = {x["id"]: x for x in jl(os.path.join(D, "items.json"))}
    tags = jl(os.path.join(D, "tags.json"), {})
    rev = jl(os.path.join(D, "review.json"), {})
    skip = done_ids()
    for f in glob.glob(os.path.join(VJ, "v-*.json")):          # גיליון שכבר נבנה – לא בונים שוב
        skip.update(r["id"] for r in jl(f))
    groups = defaultdict(list)
    for n in jl(os.path.join(D, "tagjobs", "new.json")):
        i = n["id"]
        if i in tags or i in skip or rev.get(i, {}).get("status") == "bad" or i not in items:
            continue
        groups[(series(i), "p" if items[i]["kind"] == "panel" else "s")].append(n)
    font = ImageFont.truetype("arialbd.ttf", 20)
    made = 0
    for (ser, kind), rows in sorted(groups.items()):
        cols, cw, ch = (6, 256, 450) if kind == "p" else (3, 512, 343)
        nrows = 12 // cols
        start = len(glob.glob(os.path.join(VJ, "v-%s-%s*.json" % (ser, kind))))
        for b in range(0, len(rows), 12):
            name = "v-%s-%s%03d" % (ser, kind, start + b // 12 + 1)
            sheet = Image.new("RGB", (cols * cw, nrows * (ch + 26)), "white")
            dr = ImageDraw.Draw(sheet)
            job = []
            for k, n in enumerate(rows[b:b + 12]):
                it = items[n["id"]]
                f = it["files"]
                src = f.get("clean") if f.get("clean") and os.path.exists(f["clean"]) else f["master"]
                im = Image.open(src).convert("RGB")
                if it.get("crop"):
                    im = im.crop(tuple(it["crop"]))
                im.thumbnail((cw - 4, ch))
                x, y = (k % cols) * cw, (k // cols) * (ch + 26)
                dr.rectangle([x, y, x + cw - 1, y + 25], fill="black")
                dr.text((x + 8, y + 2), str(k + 1), fill="yellow", font=font)
                sheet.paste(im, (x + (cw - im.width) // 2, y + 26))
                job.append({"n": k + 1, "id": n["id"], "topic": EMO.sub("", n.get("topic", "")).strip(),
                            "caption": n.get("caption", ""), "en": n.get("en", "")})
            sheet.save(os.path.join(VJ, name + ".jpg"), quality=88)
            json.dump(job, open(os.path.join(VJ, name + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
            made += 1
    print("sheets made:", made)


def check(k):
    job = [r["id"] for r in jl(os.path.join(VJ, k + ".json"))]
    try:
        part = jl(os.path.join(VP, k + ".json"))
    except Exception as e:
        return ["JSON לא תקין: %s" % e]
    if not isinstance(part, dict):
        return ["אין קובץ פלט / לא מילון"]
    err = []
    for i in job:
        t = part.get(i)
        if not isinstance(t, dict):
            err.append("חסר: " + i); continue
        fl = t.get("flags")
        if not isinstance(fl, list) or set(fl) - FLAGS:
            err.append("flags: %s %s" % (i, fl)); continue
        if fl:
            if not t.get("note"):
                err.append("מסומן בלי note: " + i)
            continue
        ti, tg = t.get("he_title", ""), t.get("he_tags", [])
        if not ti or NIK.search(ti) or len(ti.split()) > 14:
            err.append("כותרת: %s | %s" % (i, ti))
        if not isinstance(tg, list) or not (6 <= len(tg) <= 12) or any(NIK.search(x) or len(x.split()) > 3 for x in tg):
            err.append("תגיות (6-12, קצרות, בלי ניקוד): %s | %s" % (i, tg))
        if BAD.search(ti + " " + " ".join(tg if isinstance(tg, list) else [])):
            err.append("אישה/ילדה בתיוג (אם באמת יש – לסמן flags women): %s | %s" % (i, ti))
    if set(part) - set(job):
        err.append("מזהים מיותרים: %d" % len(set(part) - set(job)))
    return err


def names(todo_only=True, ser=None):
    out = []
    for f in sorted(glob.glob(os.path.join(VJ, "v-*.json"))):
        k = os.path.basename(f)[:-5]
        if ser and not k.startswith("v-%s-" % ser):
            continue
        if todo_only and os.path.exists(os.path.join(VP, k + ".json")) and not check(k):
            continue
        out.append(k)
    return out


def merge():
    tp, rp = os.path.join(D, "tags.json"), os.path.join(D, "review.json")
    tags, rev = jl(tp, {}), jl(rp, {})
    flagged, ok, badparts = jl(os.path.join(D, "vision_flagged_batch.json"), {}), 0, []
    for f in sorted(glob.glob(os.path.join(VP, "v-*.json"))):
        k = os.path.basename(f)[:-5]
        if not os.path.exists(os.path.join(VJ, k + ".json")) or check(k):
            badparts.append(k); continue
        for i, t in jl(f).items():
            if rev.get(i, {}).get("by") == "user":
                continue
            if t["flags"]:
                rev[i] = {"status": "bad", "flags": t["flags"], "note": t.get("note", ""), "by": "agent-vision"}
                flagged[i] = {"flags": t["flags"], "note": t.get("note", ""), "sheet": k}
                tags.pop(i, None)
            else:
                tags[i] = {"he_title": t["he_title"], "he_tags": t["he_tags"]}
                rev[i] = {"status": "ok", "flags": [], "note": "", "by": "agent-vision"}
                flagged.pop(i, None)
                ok += 1
    json.dump(tags, open(tp, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    json.dump(rev, open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    json.dump(flagged, open(os.path.join(D, "vision_flagged_batch.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("merged ok:", ok, "| flagged:", len(flagged), "| parts skipped (missing/invalid):", len(badparts))


def status():
    tags = jl(os.path.join(D, "tags.json"), {})
    rev = jl(os.path.join(D, "review.json"), {})
    c = OrderedDict()
    for n in jl(os.path.join(D, "tagjobs", "new.json")):
        s = c.setdefault(series(n["id"]), [0, 0, 0])
        if n["id"] in tags:
            s[0] += 1
        elif rev.get(n["id"], {}).get("status") == "bad":
            s[1] += 1
        else:
            s[2] += 1
    for k, (a, b, r) in sorted(c.items(), key=lambda t: -sum(t[1])):
        print("%-14s tagged %5d | flagged %4d | left %5d" % (k, a, b, r))
    print("TOTAL tagged %d | flagged %d | left %d" % tuple(sum(v[j] for v in c.values()) for j in range(3)))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    a = sys.argv[1:]
    if a[:1] == ["make"]:
        make()
    elif a[:1] == ["list"]:
        print("\n".join(names(True, a[1] if len(a) > 1 else None)))
    elif a[:1] == ["check"]:
        bad = 0
        for k in a[1:]:
            e = check(k)
            print(k + ":", "OK" if not e else "\n  " + "\n  ".join(e[:30]))
            bad += bool(e)
        sys.exit(1 if bad else 0)
    elif a[:1] == ["merge"]:
        merge()
    elif a[:1] == ["status"]:
        status()
    else:
        print(__doc__)
