# -*- coding: utf-8 -*-
"""בדיקת קובץ תיוג-ראייה ומיזוג.
    python check_vision.py 07          # בדיקת חלק
    python check_vision.py --merge     # כל החלקים -> tags.json (תיאור+תגיות) ו-review.json (ok, או bad אם יש סימון)"""
import glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
NIK = re.compile(r"[֑-ׇ]")
FLAGS = {"women", "text", "church", "dome", "other"}


def check(k):
    job = [r["id"] for r in json.load(open(os.path.join(D, "visionjobs", k + ".json"), encoding="utf-8"))]
    part = json.load(open(os.path.join(D, "visionparts", k + ".json"), encoding="utf-8"))
    err = []
    for i in job:
        t = part.get(i)
        if not t:
            err.append("חסר: " + i); continue
        if not t.get("he_title") or NIK.search(t["he_title"]):
            err.append("כותרת: " + i)
        if not (4 <= len(t.get("he_tags", [])) <= 13):
            err.append("תגיות: " + i)
        if not isinstance(t.get("flags"), list) or set(t["flags"]) - FLAGS:
            err.append("flags: %s %s" % (i, t.get("flags")))
    return err


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1:] == ["--merge"]:
        tp, rp = os.path.join(D, "tags.json"), os.path.join(D, "review.json")
        tags = json.load(open(tp, encoding="utf-8")) if os.path.exists(tp) else {}
        rev = json.load(open(rp, encoding="utf-8")) if os.path.exists(rp) else {}
        bad = []
        for f in sorted(glob.glob(os.path.join(D, "visionparts", "*.json"))):
            for i, t in json.load(open(f, encoding="utf-8")).items():
                tags[i] = {"he_title": t["he_title"], "he_tags": t["he_tags"]}
                if rev.get(i, {}).get("by") == "user":      # החלטה של המשתמש גוברת
                    continue
                st = "bad" if t["flags"] else "ok"
                rev[i] = {"status": st, "flags": t["flags"], "note": t.get("note", ""), "by": "agent-vision"}
                if t["flags"]:
                    bad.append((i, t["flags"], t["he_title"]))
        json.dump(tags, open(tp, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        json.dump(rev, open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print("merged; excluded:", len(bad))
        json.dump(bad, open(os.path.join(D, "vision_excluded.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        return
    err = check(sys.argv[1])
    print("\n".join(err[:40]) or "OK")
    sys.exit(1 if err else 0)


if __name__ == "__main__":
    main()
