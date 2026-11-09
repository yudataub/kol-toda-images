# -*- coding: utf-8 -*-
"""9.11.2026 (the user: "the rest – derive tags"): tags from text, without looking, for the untagged items of new.json
(except bk/tanach-*, tagged by eye). Title = the Hebrew caption, else the topic; tags = lexicon matches in `en` + topic + caption words.
Marked "derived": true, so a look-based tagging can replace them later. Writes data/tagjobs/dr.json + data/tagparts/dr.json."""
import json, os, re
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
NIK = re.compile(r"[֑-ׇ]")
BAD = {"אישה", "אשה", "נשים", "ילדה", "ילדות", "בחורה", "אמא", "סבתא", "בת"}
STOP = {"של", "על", "עם", "את", "אל", "מה", "מי", "זה", "זו", "הוא", "היא", "הם", "כל", "לא", "או", "גם", "יש", "אין", "כמו", "בין", "אחרי", "לפני", "עד", "רק", "כי", "אם", "איזה", "איך", "למה"}
ENSTOP = {"with", "from", "that", "this", "they", "them", "their", "have", "near", "into", "over", "under", "very", "some", "many", "male",
          "people", "person", "standing", "sitting", "holding", "looking", "wearing", "small", "large", "little", "white", "long", "front", "around"}
lex = json.load(open(os.path.join(D, "lexicon.json"), encoding="utf-8"))
jobs = [x for x in json.load(open(os.path.join(D, "tagjobs", "new.json"), encoding="utf-8")) if not x["id"].startswith("bk/tanach-")]
clean = lambda s: re.sub(r"\s+", " ", re.sub(r"[^\u05d0-\u05ea0-9\s׳״\"'\-]", " ", NIK.sub("", s or ""))).strip()
out = {}
for x in jobs:
    en = (x.get("en") or "").lower()
    en = re.sub(r"\bno (women|text|girls|people)\b", " ", en)
    tags = []
    def add(t):
        t = clean(t)
        if t and t not in tags and t not in BAD and t not in STOP and len(t) >= 2 and len(t.split()) <= 2:
            tags.append(t)
    for he, v in lex.items():   # only real words: the lexicon's English lists also hold "of", "and", "to", "old", "men"…
        if any(re.search(r"\b" + re.escape(w) + r"\b", en) for w in v.get("en", []) if len(w) >= 4 and w not in ENSTOP):
            add(he)
    topic = [clean(p) for p in re.split(r"[›:–\-]", x.get("topic", "")) if clean(p)]
    for p in topic: add(p)
    cap = clean(x.get("caption", ""))
    for w in cap.split():
        if len(tags) >= 11: break
        add(w)
    if "no people" in (x.get("en") or "").lower() or "בלי אנשים" in cap: add("בלי אנשים")
    for filler in ("איור", "לימוד", "יהדות", "חינוך", "תורה"):
        if len(tags) >= 6: break
        add(filler)
    # a panel's caption is sometimes a quiz answer ("נשים פטורות…"), not what is seen: then the topic
    title = cap if cap and not (set(cap.split()) & BAD) and len(cap.split()) <= 12 else ("איור: " + (topic[-1] if topic else "חומר לימוד"))
    title = " ".join(title.split()[:12])
    out[x["id"]] = {"he_title": title, "he_tags": tags[:12], "derived": True}
json.dump([{"id": x["id"]} for x in jobs], open(os.path.join(D, "tagjobs", "dr.json"), "w", encoding="utf-8"), ensure_ascii=False)
json.dump(out, open(os.path.join(D, "tagparts", "dr.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("derived:", len(out), "| sample:", list(out.items())[:2])
