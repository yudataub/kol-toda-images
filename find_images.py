# -*- coding: utf-8 -*-
"""חיפוש בספריית התמונות.
    python find_images.py "נטילת ידיים" [--n 12] [--kind scene|panel|triptych|any] [--source hq,hb] [--json]
    python find_images.py --text פרק.txt          # מילות מפתח מתוך טקסט של פרק בספר
מדפיס רשימה ממוספרת וכותב גיליון תמונות: sheets/<תאריך>-<חיפוש>.jpg, ו-sheets/last.json (מספר -> מזהה)
כדי שאפשר יהיה לבחור במספרים: python pick.py 3 7 --to <תיקייה>."""
import argparse, datetime, json, os, re, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))
from hebrew import norm, tokens  # noqa: E402

DATA = os.path.join(HERE, "data")
SHEETS = os.path.join(HERE, "sheets")
EN_WORD = re.compile(r"[a-z]+")
# משקל לכל שדה
W = {"tags": 3.0, "title": 2.5, "caption": 2.0, "topic": 1.5, "en": 1.5, "ctx": 0.7}


def load(name, default):
    p = os.path.join(DATA, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def fields(it, tag):
    c = it.get("he_ctx") or {}
    ctx = " ".join(str(v) if not isinstance(v, list) else " ".join(map(str, v)) for k, v in c.items() if k != "caption")
    return {"tags": " ".join(tag.get("he_tags", [])), "title": tag.get("he_title", ""),
            "caption": c.get("caption", "") + " " + " ".join(c.get("captions", []) if it["kind"] != "panel" else []),
            "topic": " ".join(it.get("topic", [])), "en": it.get("en", ""), "ctx": ctx}


def expand(q, lex):
    """מילות החיפוש + מילים נרדפות ואנגלית מהמילון (במשקל נמוך יותר)."""
    qt = tokens(q)
    qn = " " + norm(q) + " "
    he_extra, en = set(), set(EN_WORD.findall(q.lower()))
    for k, v in lex.items():
        keys = [k] + v["he"]
        if any((" " + norm(s) + " ") in qn or (len(norm(s)) >= 3 and norm(s) in qt) for s in keys):
            for s in keys:
                he_extra |= tokens(s)
            en |= {w.lower() for w in v["en"]}
    return qt, he_extra - qt, en


def search(q, n=12, kind="scene", sources=None, lex=None, items=None, tags=None, review=None):
    lex = lex if lex is not None else load("lexicon.json", {})
    items = items if items is not None else load("items.json", [])
    tags = tags if tags is not None else load("tags.json", {})
    review = review if review is not None else load("review.json", {})
    qt, extra, en = expand(q, lex)
    qn = norm(q)
    res = []
    for it in items:
        if sources and it["source"] not in sources:
            continue
        if kind != "any" and it["kind"] != kind and not (kind == "scene" and it["kind"] == "scene"):
            continue
        if (review.get(it["id"], {}).get("status") == "bad") or (not it.get("reviewed") and review.get(it["id"], {}).get("status") != "ok"):
            continue
        tag = tags.get(it["id"], {})
        f = fields(it, tag)
        s = 0.0
        for name, txt in f.items():
            if name == "en":
                words = set(EN_WORD.findall(txt.lower()))
                s += W["en"] * len(en & words)
                continue
            tk = tokens(txt)
            s += W[name] * (len(qt & tk) + 0.5 * len(extra & tk))
            if qn and len(qn) >= 3 and qn in norm(txt):
                s += W[name] * 1.5
        if s > 0:
            res.append((s, it))
    res.sort(key=lambda x: -x[0])
    out, per = [], defaultdict(int)
    for s, it in res:   # גיוון: עד 3 תמונות מאותו חידון/פרק
        g = it.get("quiz") or it.get("topic_key") or it["id"]
        if per[g] >= 3:
            continue
        per[g] += 1
        out.append((round(s, 1), it))
        if len(out) >= n:
            break
    return out


def thumb(it, w=420, h=282):
    from PIL import Image
    f = it["files"]
    src = f.get("clean") or f["master"] if it["kind"] in ("triptych", "panel") else f["master"]
    if not src or not os.path.exists(src):
        src = f["master"]
    im = Image.open(src).convert("RGB")
    if it["kind"] == "panel" and it.get("crop"):
        im = im.crop(tuple(it["crop"]))
    im.thumbnail((w, h))
    return im


def sheet(found, title):
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(SHEETS, exist_ok=True)
    W_, H_, C = 420, 300, 4
    rows = (len(found) + C - 1) // C or 1
    S = Image.new("RGB", (W_ * C, H_ * rows), "white")
    d = ImageDraw.Draw(S)
    try:
        F = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 22)
    except OSError:
        F = ImageFont.load_default()
    for k, (sc, it) in enumerate(found):
        x, y = (k % C) * W_, (k // C) * H_
        try:
            t = thumb(it)
            S.paste(t, (x + (W_ - t.width) // 2, y + 4))
        except Exception as e:   # noqa
            d.text((x + 10, y + 100), "?? " + str(e)[:40], fill="red", font=F)
        d.rectangle([x + 4, y + 4, x + 46, y + 34], fill=(220, 30, 60))
        d.text((x + 10, y + 6), str(k + 1), fill="white", font=F)
        d.text((x + 6, y + H_ - 26), it["id"][-34:], fill=(60, 60, 60), font=ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 15))
    slug = re.sub(r"[^\w]+", "-", norm(title))[:30] or "search"
    p = os.path.join(SHEETS, "%s-%s.jpg" % (datetime.date.today().isoformat(), slug))
    S.save(p, quality=80)
    json.dump({str(k + 1): it["id"] for k, (_, it) in enumerate(found)},
              open(os.path.join(SHEETS, "last.json"), "w", encoding="utf-8"), ensure_ascii=False)
    return p


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", default="")
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--kind", default="scene", choices=["scene", "panel", "triptych", "any"])
    ap.add_argument("--source", default="")
    ap.add_argument("--text", default="", help="קובץ טקסט/HTML: מחפשים לפי מושגי המילון שמופיעים בו")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    q = a.query
    if a.text:
        lex = load("lexicon.json", {})
        t = norm(re.sub(r"<[^>]+>", " ", open(a.text, encoding="utf-8").read()))
        hits = [k for k, v in lex.items() if any(" " + norm(s) + " " in " " + t + " " for s in [k] + v["he"] if len(norm(s)) >= 3)]
        q = (q + " " + " ".join(hits)).strip()
        print("מושגים מהטקסט:", ", ".join(hits) or "-")
    found = search(q, a.n, a.kind, set(a.source.split(",")) if a.source else None)
    if a.json:
        print(json.dumps([{"n": k + 1, "score": s, "id": it["id"], "en": it["en"], "topic": it.get("topic"),
                           "master": it["files"]["master"]} for k, (s, it) in enumerate(found)], ensure_ascii=False, indent=1))
    else:
        tags = load("tags.json", {})
        for k, (s, it) in enumerate(found):
            print("%2d. [%s] %s | %s | %s" % (k + 1, s, it["id"], tags.get(it["id"], {}).get("he_title") or it["en"][:70],
                                              " › ".join(it.get("topic", [])[1:])))
    if found:
        print("גיליון:", sheet(found, q))
    else:
        print("לא נמצאו תמונות")


if __name__ == "__main__":
    main()
