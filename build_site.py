# -*- coding: utf-8 -*-
"""בונה את הגלריה docs/ (GitHub Pages: https://yudataub.github.io/kol-toda-images/).
    python build_site.py
רק תמונות שנבדקו נכנסות. תמונה מלאה – מהכתובת שכבר קיימת (ריפו kol-toda-halacha); ללוח בודד נשמר
קובץ חתוך ב-docs/f/. תמונות קטנות לגלריה ב-docs/t/.
מ-25.11.2026 (מגבלת 1GB של Pages): תמונה מלאה חדשה נשמרת בריפו השני image-library-2/f (kol-toda-images-2);
מה שכבר ב-docs/f נשאר שם. מקורות ב-data/hold.txt (שורה למקור) לא נכנסים לגלריה עד שמוציאים אותם משם. החיפוש: אותו נרמול כמו lib/hebrew.py (ב-app.js)."""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))
from hebrew import tokens  # noqa: E402

DATA, DOCS = os.path.join(HERE, "data"), os.path.join(HERE, "docs")
BASE = "https://yudataub.github.io/kol-toda-images/"
BASE2 = "https://yudataub.github.io/kol-toda-images-2/"
F2 = os.path.join(os.path.dirname(HERE), "image-library-2", "f")


def fname(iid):
    return re.sub(r"[^\w-]+", "_", iid) + ".webp"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    from PIL import Image
    items = json.load(open(os.path.join(DATA, "items.json"), encoding="utf-8"))
    tags = json.load(open(os.path.join(DATA, "tags.json"), encoding="utf-8")) if os.path.exists(os.path.join(DATA, "tags.json")) else {}
    review = json.load(open(os.path.join(DATA, "review.json"), encoding="utf-8")) if os.path.exists(os.path.join(DATA, "review.json")) else {}
    lex = json.load(open(os.path.join(DATA, "lexicon.json"), encoding="utf-8"))
    for d in ("t", "f"):
        os.makedirs(os.path.join(DOCS, d), exist_ok=True)
    os.makedirs(F2, exist_ok=True)
    hp = os.path.join(DATA, "hold.txt")
    hold = {l.strip() for l in open(hp, encoding="utf-8") if l.strip() and not l.startswith("#")} if os.path.exists(hp) else set()
    out, made = [], 0
    for it in items:
        if it["source"] in hold:
            continue
        st = review.get(it["id"], {}).get("status")
        if st == "bad" or (not it.get("reviewed") and st != "ok"):
            continue
        fn = fname(it["id"])
        tp, fp = os.path.join(DOCS, "t", fn), os.path.join(DOCS, "f", fn)
        need_full = it["kind"] == "panel" or not it["files"].get("web_url")
        fbase = BASE
        if need_full and not os.path.exists(fp):
            fp, fbase = os.path.join(F2, fn), BASE2
        if not os.path.exists(tp) or (need_full and not os.path.exists(fp)):
            f = it["files"]
            src = (f.get("clean") or f["master"]) if it["kind"] in ("triptych", "panel") else f["master"]
            if not os.path.exists(src):
                src = f["master"]
            im = Image.open(src).convert("RGB")
            if it["kind"] == "panel" and it.get("crop"):
                im = im.crop(tuple(it["crop"]))
            if need_full:
                full = im.copy()
                if full.width > 1200:
                    full = full.resize((1200, round(full.height * 1200 / full.width)))
                full.save(fp, quality=80)
            im.thumbnail((360, 260))
            im.save(tp, quality=68)
            made += 1
        t = tags.get(it["id"], {})
        c = it.get("he_ctx") or {}
        ctx = " ".join(str(v) if not isinstance(v, list) else " ".join(map(str, v)) for k, v in c.items())
        rec = {"id": it["id"], "k": it["kind"][0], "s": it["source"],
               "t": t.get("he_title") or "", "g": t.get("he_tags") or [],
               "p": " › ".join(it.get("topic", [])[1:]), "en": it.get("en", "")[:220],
               "u": fbase + "f/" + fn if need_full else it["files"]["web_url"], "th": "t/" + fn,
               "q": it.get("quiz_page", ""),
               # מילים מנורמלות לחיפוש (כולל גרסאות בלי תחיליות/רבים), לפי משקל
               "x": [" ".join(sorted(tokens(" ".join(t.get("he_tags") or [])))), " ".join(sorted(tokens(t.get("he_title", "")))),
                     " ".join(sorted(tokens(c.get("caption", "") + " " + " ".join(c.get("captions", []))))),
                     " ".join(sorted(tokens(" ".join(it.get("topic", []))))), " ".join(sorted(tokens(ctx)))]}
        out.append(rec)
    json.dump({"items": out, "lex": lex}, open(os.path.join(DOCS, "lib.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    open(os.path.join(DOCS, ".nojekyll"), "w").close()
    print(len(out), "items in the gallery,", made, "new pictures ->", DOCS)


if __name__ == "__main__":
    main()
