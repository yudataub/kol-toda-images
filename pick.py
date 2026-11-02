# -*- coding: utf-8 -*-
"""מעתיק תמונות שנבחרו מהספרייה לתיקייה של ספר.
    python pick.py 3 7 11 --to "<תיקיית הספר>\\img" [--prefix sukkot] [--fmt webp|jpg|png] [--max-width 1600] [--html]
    python pick.py hq/berachot-01/b8 hb/chanuka-11-s1 --to ...
מספרים = מהגיליון האחרון (sheets/last.json). תמונת שלושה לוחות נלקחת בלי הכיתובים (הקובץ המקורי),
ולוח בודד נחתך בלי פס הכיתוב. כל בחירה נרשמת ב-<to>/picks.json וב-data/usage.json."""
import argparse, datetime, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("picks", nargs="+")
    ap.add_argument("--to", required=True)
    ap.add_argument("--prefix", default="")
    ap.add_argument("--fmt", default="webp", choices=["webp", "jpg", "png"])
    ap.add_argument("--max-width", type=int, default=1600)
    ap.add_argument("--html", action="store_true")
    a = ap.parse_args()
    from PIL import Image
    items = {i["id"]: i for i in json.load(open(os.path.join(DATA, "items.json"), encoding="utf-8"))}
    tags = json.load(open(os.path.join(DATA, "tags.json"), encoding="utf-8")) if os.path.exists(os.path.join(DATA, "tags.json")) else {}
    last = json.load(open(os.path.join(HERE, "sheets", "last.json"), encoding="utf-8")) if os.path.exists(os.path.join(HERE, "sheets", "last.json")) else {}
    os.makedirs(a.to, exist_ok=True)
    rec_p = os.path.join(a.to, "picks.json")
    rec = json.load(open(rec_p, encoding="utf-8")) if os.path.exists(rec_p) else []
    use_p = os.path.join(DATA, "usage.json")
    usage = json.load(open(use_p, encoding="utf-8")) if os.path.exists(use_p) else {}
    for p in a.picks:
        iid = last.get(p, p)
        it = items.get(iid)
        if not it:
            print("!! לא נמצא:", p); continue
        f = it["files"]
        src = (f.get("clean") or f["master"]) if it["kind"] in ("triptych", "panel") else f["master"]
        if not os.path.exists(src):
            src = f["master"]
        im = Image.open(src).convert("RGB")
        if it["kind"] == "panel" and it.get("crop"):
            im = im.crop(tuple(it["crop"]))
        if im.width > a.max_width:
            im = im.resize((a.max_width, round(im.height * a.max_width / im.width)))
        name = (a.prefix + "-" if a.prefix else "") + re.sub(r"[^\w-]+", "-", iid.split("/", 1)[1]) + "." + a.fmt
        out = os.path.join(a.to, name)
        im.save(out, quality=88) if a.fmt != "png" else im.save(out)
        title = tags.get(iid, {}).get("he_title", "")
        rec.append({"id": iid, "file": name, "date": datetime.date.today().isoformat()})
        usage.setdefault(iid, []).append(os.path.abspath(a.to))
        print("✓", iid, "->", out)
        if a.html:
            print('<div class="pic"><img src="img/%s" alt="%s" loading="lazy"></div>' % (name, title.replace('"', "")))
    json.dump(rec, open(rec_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(usage, open(use_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
