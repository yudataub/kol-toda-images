# -*- coding: utf-8 -*-
"""סורקי המקורות – קוראים בלבד, אף פעם לא כותבים לתיקיות המקור.

hq – חידוני ההלכה (torah-game/halacha-quiz): תמונת סצנה לכל שאלה ברמה ב׳, ותמונת שלושה לוחות ברמה א׳
     (נשמרת כפריט אחד + פריט לכל לוח, עם תיבת החיתוך שלו). נבדקו בעין; "ok" = התמונה כבר באתר.
hb – ספר ההלכה לחגים (torah-game/halacha-book-b): 88 תמונות משלו, ותמונות חידונים שהוא משתמש בהן
     (אלה לא פריט חדש – הכותרת של הסעיף בספר נוספת להקשר של פריט החידון)."""
import glob, json, os, re, sys

QUIZ = r"C:\Users\User\torah-game\halacha-quiz"
BOOK = r"C:\Users\User\torah-game\halacha-book-b"
PUB = r"C:\kol-toda-build\kol\out\halacha-files"          # העותק של ריפו התמונות (kol/offload.py)
PUB_URL = "https://yudataub.github.io/kol-toda-halacha/"
NIK = re.compile(r"[\u0591-\u05C7]")


def plain(s):
    return NIK.sub("", str(s or "")).strip()


def _quiz_mods():
    if QUIZ not in sys.path:
        sys.path.insert(0, QUIZ)
    from map_halachot import parse_src          # noqa
    from build import SERIES, SEFER            # noqa
    return parse_src, SERIES, SEFER


def hq():
    parse_src, SERIES, SEFER = _quiz_mods()
    series_title = {p: plain(t) for p, t, _ in SERIES}
    titles = json.load(open(os.path.join(QUIZ, "learn_titles.json"), encoding="utf-8"))
    items = []
    for f in sorted(glob.glob(os.path.join(QUIZ, "quizzes", "*.json"))):
        q = json.load(open(f, encoding="utf-8"))
        qid, series = q["id"], q.get("series") or q["id"].rsplit("-", 1)[0]
        book = SEFER.get(series, "")
        for L in q["levels"]:
            for x in L["questions"]:
                if not x.get("image") or L["key"] not in ("a", "b"):
                    continue
                stem = x["image"][:-4]
                master = os.path.join(QUIZ, "img", qid, x["image"])
                if not os.path.exists(master):
                    continue
                keys = parse_src(x.get("src", "")) or []
                ch = keys[0][0] if keys else None
                chap = plain(titles.get("%s:%d" % (book, ch), "")) if ch else ""
                topic = [t for t in ("הלכה", series_title.get(series, series), chap) if t]
                pub = os.path.join(PUB, "halacha-quiz", "img", "%s-%s.webp" % (qid, stem))
                web = PUB_URL + "halacha-quiz/img/%s-%s.webp" % (qid, stem)
                ctx = {"book": plain(q.get("book")), "quiz_title": plain(q.get("title")), "subtitle": plain(q.get("subtitle")),
                       "question": plain(x.get("prompt")), "chapter_title": chap}
                base = dict(source="hq", engine="gemini", style="cartoon", topic=topic, topic_key="%s:%s" % (series, ch or ""),
                            quiz=qid, quiz_page="https://www.kol-toda.co.il/halacha-quiz/%s.html" % qid,
                            reviewed=os.path.exists(pub), has_text=False)
                if L["key"] == "b":
                    art = x["art"] if isinstance(x["art"], str) else " ".join(x["art"])
                    items.append(dict(base, id="hq/%s/%s" % (qid, stem), kind="scene", en=art,
                                      he_ctx=dict(ctx, options=[plain(o) for o in x.get("options", [])]),
                                      files={"master": master, "web_url": web if os.path.exists(pub) else ""}))
                else:
                    art, caps = x.get("art") or [], x.get("captions") or []
                    orig = master[:-4] + ".orig.jpg"
                    tid = "hq/%s/%s" % (qid, stem)
                    items.append(dict(base, id=tid, kind="triptych", en=" | ".join(art[0::2]),
                                      he_ctx=dict(ctx, captions=[plain(c) for c in caps]), has_text=True,
                                      files={"master": master, "clean": orig if os.path.exists(orig) else "",
                                             "web_url": web if os.path.exists(pub) else ""}))
                    for k in range(min(3, len(art) // 2)):
                        items.append(dict(base, id="%s/p%d" % (tid, k), parent=tid, kind="panel", panel=k,
                                          en=art[2 * k] + (" (" + art[2 * k + 1] + ")" if len(art) > 2 * k + 1 else ""),
                                          he_ctx={"caption": plain(caps[k]) if k < len(caps) else "",
                                                  "quiz_title": ctx["quiz_title"], "chapter_title": chap, "question": ctx["question"]},
                                          files={"master": master, "clean": orig if os.path.exists(orig) else ""}))
    return items


TAIL = re.compile(r"\s*(Single scene|Warm, friendly|A bright, warm|Absolutely NO text|People:).*$", re.S)


def hb(by_id):
    """תמונות ספר החגים. by_id: פריטי hq לפי מזהה – אליהם מתווסף ההקשר של תמונות חידון שהספר משתמש בהן."""
    jobs = {j["id"]: j for j in json.load(open(os.path.join(BOOK, "jobs.json"), encoding="utf-8"))}
    items = []
    for f in sorted(glob.glob(os.path.join(BOOK, "chapters", "*.json"))):
        c = json.load(open(f, encoding="utf-8"))
        kids = c.get("kids") or {}
        secs = kids.get("sections") or []
        ctitle = plain(c.get("title_plain") or c.get("title"))
        for k, iid in (kids.get("images") or {}).items():
            k = int(k)
            sec = next((s for s in secs if k in (s.get("h") or [])), secs[k - 1] if 0 < k <= len(secs) else {})
            stitle, stext = plain(sec.get("title")), plain(sec.get("text"))[:300]
            own = os.path.join(BOOK, "img", iid + ".webp")
            if iid in jobs and os.path.exists(own):
                src_jpg = os.path.join(BOOK, "img_new", iid + ".jpg")
                pub = os.path.join(PUB, "halacha-book-chagim", "img", iid + ".webp")
                items.append(dict(id="hb/" + iid, source="hb", engine="gemini", style="cartoon", kind="scene",
                                  en=TAIL.sub("", jobs[iid]["prompt"]),
                                  he_ctx={"book": plain(c.get("book_name")), "chapter_title": ctitle,
                                          "section_title": stitle, "section_text": stext},
                                  topic=["חגים", plain(c.get("book_name")), ctitle], topic_key=c.get("topic", ""),
                                  reviewed=True, has_text=False,
                                  files={"master": src_jpg if os.path.exists(src_jpg) else own,
                                         "web_url": PUB_URL + "halacha-book-chagim/img/%s.webp" % iid if os.path.exists(pub) else ""}))
            else:   # תמונת חידון שהספר משתמש בה: chanuka-01-b7 -> hq/chanuka-01/b7
                m = re.match(r"^(.+-\d+)-([ab]\d+)$", iid)
                it = by_id.get("hq/%s/%s" % m.groups()) if m else None
                if it is not None:
                    it["he_ctx"].setdefault("book_sections", [])
                    if stitle and stitle not in it["he_ctx"]["book_sections"]:
                        it["he_ctx"]["book_sections"].append(stitle)
    return items
