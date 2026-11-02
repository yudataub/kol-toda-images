# -*- coding: utf-8 -*-
"""בדיקת קובץ תיוג ומיזוג:  python check_tags.py 03   |   python check_tags.py --merge  (כל החלקים -> data/tags.json)"""
import glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
NIK = re.compile(r"[֑-ׇ]")
BAD = re.compile(r"(?:^|\s)(?:אישה|אשה|נשים|ילדה|ילדות|בחורה|אמא|סבתא|בת)(?=\s|$)")


def check(k):
    job = [r["id"] for r in json.load(open(os.path.join(D, "tagjobs", k + ".json"), encoding="utf-8"))]
    part = json.load(open(os.path.join(D, "tagparts", k + ".json"), encoding="utf-8"))
    err = []
    for i in job:
        t = part.get(i)
        if not t:
            err.append("חסר: " + i); continue
        ti, tg = t.get("he_title", ""), t.get("he_tags", [])
        if not ti or NIK.search(ti) or len(ti.split()) > 14:
            err.append("כותרת: %s | %s" % (i, ti))
        if not (5 <= len(tg) <= 13) or any(NIK.search(x) for x in tg):
            err.append("תגיות: %s | %s" % (i, tg))
        if BAD.search(ti + " " + " ".join(tg)):
            err.append("אישה/ילדה בתיוג: %s | %s" % (i, ti))
    extra = set(part) - set(job)
    if extra:
        err.append("מזהים מיותרים: %d" % len(extra))
    return err


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1:] == ["--merge"]:
        out = {}
        p = os.path.join(D, "tags.json")
        if os.path.exists(p):
            out = json.load(open(p, encoding="utf-8"))
        for f in sorted(glob.glob(os.path.join(D, "tagparts", "*.json"))):
            out.update(json.load(open(f, encoding="utf-8")))
        json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(len(out), "tags ->", p)
        return
    err = check(sys.argv[1])
    print("\n".join(err[:40]) or "OK")
    sys.exit(1 if err else 0)


if __name__ == "__main__":
    main()
