# -*- coding: utf-8 -*-
"""נרמול עברית לחיפוש: בלי ניקוד, גרשיים ומקף, אותיות סופיות כרגילות, ותחיליות/רבים כגרסאות נוספות.
אותו היגיון בדיוק נמצא ב-docs/app.js (החיפוש בגלריה) – שינוי כאן מחייב שינוי שם."""
import re

NIK = re.compile(r"[֑-ׇ]")
FIN = str.maketrans("ךםןףץ", "כמנפצ")
PREF2 = ("וה", "וב", "ול", "ומ", "וש", "שה", "שב", "של", "מה", "כש", "לה", "בה", "וכ")
PREF1 = "והבלמשכ"


def norm(s):
    s = NIK.sub("", str(s or ""))
    s = s.replace("״", '"').replace("׳", "'").replace("־", " ").replace("–", " ").replace("-", " ")
    s = s.translate(FIN).lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def variants(tok):
    """גרסאות של מילה אחת: המילה, בלי תחילית, בלי סיומת רבים."""
    out = {tok}
    if re.match(r"^[א-ת]+$", tok):
        bases = {tok}
        if len(tok) >= 5 and tok[:2] in PREF2:
            bases.add(tok[2:])
        if len(tok) >= 4 and tok[0] in PREF1:
            bases.add(tok[1:])
        for b in list(bases):
            out.add(b)
            if len(b) >= 5 and b.endswith(("ימ", "ות")):
                out.add(b[:-2])
            if len(b) >= 4 and b.endswith("ה"):
                out.add(b[:-1])
    return out


def tokens(s):
    """קבוצת המילים (עם הגרסאות) של טקסט מנורמל."""
    out = set()
    for t in norm(s).split():
        if len(t) >= 2:
            out |= variants(t)
    return out
