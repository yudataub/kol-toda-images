# -*- coding: utf-8 -*-
"""סורק את המקורות ובונה את data/items.json (נבנה מחדש בכל ריצה – התגיות והבדיקות בקבצים נפרדים).
    python ingest.py
תיבות החיתוך של הלוחות נמדדות פעם אחת ונשמרות ב-cache/boxes.json (לפי גודל וזמן שינוי של הקובץ)."""
import datetime, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))
import adapters  # noqa: E402

DATA = os.path.join(HERE, "data")
CACHE = os.path.join(HERE, "cache")


def panel_boxes(path, cache):
    """שלוש תיבות [l, t, r, b] בפיקסלים, משמאל לימין: הלוח בלי פס הכיתוב שמתחתיו."""
    st = os.stat(path)
    key = "%s|%d|%d" % (path, st.st_size, int(st.st_mtime))
    if key in cache:
        return cache[key]
    import numpy as np
    from PIL import Image
    if adapters.QUIZ not in sys.path:
        sys.path.insert(0, adapters.QUIZ)
    from recap import strip_box
    a = np.asarray(Image.open(path).convert("RGB"))
    h, w = a.shape[:2]
    boxes = []
    for i in range(3):
        x0, x1 = int(w * i / 3) + 4, int(w * (i + 1) / 3) - 4
        sb = strip_box(a, x0, x1)
        if sb:
            l, t, r, _ = sb
            boxes.append([int(l) + 4, int(h * .08), int(r) - 4, int(t) - 6])
        else:
            boxes.append(None)
    good = [b for b in boxes if b]
    if good:   # לוח שלא נמדד – לפי השאר
        top, bot = min(b[1] for b in good), max(b[3] for b in good)
        for i, b in enumerate(boxes):
            if not b:
                boxes[i] = [int(w * i / 3) + 20, top, int(w * (i + 1) / 3) - 20, bot]
    else:
        boxes = [[int(w * i / 3) + 20, int(h * .08), int(w * (i + 1) / 3) - 20, int(h * .78)] for i in range(3)]
    cache[key] = boxes
    return boxes


def main():
    os.makedirs(DATA, exist_ok=True); os.makedirs(CACHE, exist_ok=True)
    cpath = os.path.join(CACHE, "boxes.json")
    cache = json.load(open(cpath, encoding="utf-8")) if os.path.exists(cpath) else {}
    old_path = os.path.join(DATA, "items.json")
    old = {i["id"]: i for i in json.load(open(old_path, encoding="utf-8"))} if os.path.exists(old_path) else {}
    items = adapters.hq()
    by_id = {i["id"]: i for i in items}
    items += adapters.hb(by_id)
    today = datetime.date.today().isoformat()
    for it in items:
        if it["kind"] == "panel":
            boxes = panel_boxes(it["files"]["master"], cache)
            it["crop"] = boxes[2 - it["panel"]]          # אפשרות 0 = הלוח הימני
        it["added"] = old.get(it["id"], {}).get("added", today)
    json.dump(cache, open(cpath, "w", encoding="utf-8"))
    json.dump(items, open(old_path, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    new = [i for i in items if i["id"] not in old]
    gone = [k for k in old if k not in by_id and not k.startswith("hb/")]
    from collections import Counter
    print("items:", len(items), dict(Counter((i["source"], i["kind"]) for i in items)))
    print("new:", len(new), "| gone:", len(gone), "| reviewed:", sum(1 for i in items if i.get("reviewed")))


if __name__ == "__main__":
    main()
