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
# מקור חיים (מדור נפרד /mekor-haim-quiz/, 5.11): התמונות עברו ל-kol-toda-img. ליד כל תמונה יש <שם>.json (gen_images.write_meta):
# origin "library" = הורכבה/הועתקה מפריטים שכבר בספרייה – לא נקלטת שוב; origin "generated" = תמונה חדשה (engine: gemini/codex).
MK_PUB = r"C:\kol-toda-build\kol\out\img-files"
MK_URL = "https://yudataub.github.io/kol-toda-img/"
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
                meta = {}
                if series == "mekorhaim":
                    mp = master[:-4] + ".json"
                    meta = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
                    if meta.get("origin") != "generated":
                        continue          # הורכבה או הועתקה מהספרייה – הפריטים המקוריים כבר בה
                    pub = os.path.join(MK_PUB, "mekor-haim-quiz", "img", "%s-%s.webp" % (qid, stem))
                    web = MK_URL + "mekor-haim-quiz/img/%s-%s.webp" % (qid, stem)
                else:
                    pub = os.path.join(PUB, "halacha-quiz", "img", "%s-%s.webp" % (qid, stem))
                    web = PUB_URL + "halacha-quiz/img/%s-%s.webp" % (qid, stem)
                ctx = {"book": plain(q.get("book")), "quiz_title": plain(q.get("title")), "subtitle": plain(q.get("subtitle")),
                       "question": plain(x.get("prompt")), "chapter_title": chap}
                base = dict(source="hq", engine=meta.get("engine") or "gemini", style="cartoon", topic=topic, topic_key="%s:%s" % (series, ch or ""),
                            quiz=qid, quiz_page="https://www.kol-toda.co.il/%s/%s.html" % ("mekor-haim-quiz" if meta else "halacha-quiz", qid),
                            reviewed=bool(meta.get("reviewed")) if meta else os.path.exists(pub), has_text=False)
                if not x.get("art") and (L["key"] == "b" or qid.endswith("-mk")):   # חידוני מושגים (-mk): תמונות מועתקות מחידונים אחרים / לוחות מורכבים – נקלטות ב-hq_cx()
                    continue
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
    return items + hq_cx(series_title)


def _cx_jobs():
    """תיאורי התמונות (באנגלית) מסקריפטי cx_*_images.py של החידונים: {שם: תיאור}. רק קבצים עם JOBS ו-__main__."""
    import importlib.util
    jobs = {}
    for f in glob.glob(os.path.join(QUIZ, "cx_*_images.py")):
        src = open(f, encoding="utf-8").read()
        if "JOBS" not in src or "__main__" not in src:
            continue
        spec = importlib.util.spec_from_file_location(os.path.basename(f)[:-3], f)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
            for k, v in getattr(mod, "JOBS", {}).items():
                jobs.setdefault(k, v)
        except Exception:
            pass
    return jobs


def hq_cx(series_title):
    """תמונות בודדות שנוצרו לחידוני המושגים (img/<quiz>/cx-*.png|jpg, Codex/Gemini) – בלי כיתוב, לשימוש חוזר."""
    jobs, items = _cx_jobs(), []
    for f in sorted(glob.glob(os.path.join(QUIZ, "img", "*", "cx-*.*"))):
        if not f.lower().endswith((".png", ".jpg")):
            continue
        qid, name = os.path.basename(os.path.dirname(f)), os.path.basename(f)[3:-4]
        if f.lower().endswith(".jpg") and os.path.exists(f[:-4] + ".png"):
            continue
        qf = os.path.join(QUIZ, "quizzes", qid + ".json")
        q = json.load(open(qf, encoding="utf-8")) if os.path.exists(qf) else {}
        series = q.get("series") or qid.rsplit("-", 1)[0]
        items.append(dict(source="hq", engine="codex" if f.endswith(".png") else "gemini", style="watercolor",
                          topic=[t for t in ("הלכה", series_title.get(series, series)) if t], topic_key="%s:" % series,
                          quiz=qid, quiz_page="https://www.kol-toda.co.il/halacha-quiz/%s.html" % qid,
                          reviewed=False, has_text=False, id="hq/%s/cx-%s" % (qid, name), kind="scene",
                          en=jobs.get(name, name.replace("_", " ")),
                          he_ctx={"book": plain(q.get("book")), "quiz_title": plain(q.get("title"))},
                          files={"master": f, "web_url": ""}))
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


OG = r"C:\og-ai"
TN = r"C:\YUDA\איורי סיפורי התנאים"


def og():
    """og-ai: ציורי צבעי מים (Codex) שצוירו כתמונות שיתוף לעמודי האתר. אין תיאור של מה שמצויר – רק שם העמוד;
    התיאור, התגיות והבדיקה (נשים/טקסט) – בתיוג עם ראייה (TAG_VISION.md). נכנסים לגלריה רק אחרי review ok."""
    jobs = {j["key"]: j for j in json.load(open(os.path.join(OG, "jobs.json"), encoding="utf-8"))}
    items = []
    for f in sorted(glob.glob(os.path.join(OG, "img", "*.png"))):
        stem = os.path.basename(f)[:-4]
        j = jobs.get(stem, {})
        items.append(dict(id="og/" + stem, source="og", engine="codex", style="watercolor", kind="scene", en="",
                          he_ctx={"page_title": plain(j.get("title", "")), "page_desc": plain(j.get("desc", ""))[:200]},
                          topic=["צבעי מים"], topic_key="og", reviewed=False, has_text=False,
                          files={"master": f, "web_url": ""}))
    return items


def tn():
    """איורי סיפורי התנאים: פרומפטים.md – '## סיפור N — כותרת', '### N-NN.png', ואחריו הפרומפט בבלוק קוד."""
    md = open(os.path.join(TN, "פרומפטים.md"), encoding="utf-8").read()
    items, story, cur = [], "", None
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("## "):
            story = l[3:].strip()
        elif l.startswith("### ") and re.match(r"^###\s+(\S+\.png)", l):
            cur = re.match(r"^###\s+(\S+\.png)", l).group(1)
        elif l.startswith("```") and cur:
            j = i + 1
            buf = []
            while j < len(lines) and not lines[j].startswith("```"):
                if not lines[j].startswith("Style:"):
                    buf.append(lines[j])
                j += 1
            path = os.path.join(TN, cur)
            if os.path.exists(path):
                title = re.sub(r"^סיפור\s+\d+\s*[—–-]\s*", "", story)
                items.append(dict(id="tn/" + cur[:-4], source="tn", engine="gpt", style="cinematic", kind="scene",
                                  en=" ".join(buf).strip()[:600], he_ctx={"story_title": title},
                                  topic=["סיפורי התנאים", title], topic_key="tn", reviewed=False, has_text=False,
                                  files={"master": path, "web_url": ""}))
            cur, i = None, j
        i += 1
    return items


def bookgen():
    """תמונות שנוצרו לספרים (Gemini) ונבדקו בעין. הרשימה ב-data/book_images.json: [{id, file, en, book}]."""
    mp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "book_images.json")
    if not os.path.exists(mp):
        return []
    items = []
    for j in json.load(open(mp, encoding="utf-8")):
        if os.path.exists(j["file"]):
            items.append(dict(id="bk/" + j["id"], source="bk", engine="gemini", style="painterly", kind="scene", en=j["en"],
                              he_ctx={"book": j["book"]}, topic=["ספרים", j["book"]], topic_key="book", reviewed=False,
                              has_text=False, files={"master": j["file"], "web_url": j.get("web_url", "")}))   # 9.11: game pictures already on the site's image repo – the gallery links there, no second copy
    return items


SEDER = r"C:\Users\User\torah-game\seder-parasha"


def sp():
    """"סדרו את התמונות" (seder-parasha, 13.11.2026): 6 סצנות לכל פרשה, src/<key>-<n>.jpg (Gemini, ספר ילדים חם).
    התיאור באנגלית מ-prompts.py, הכיתוב המנוקד מ-scenes.json. תמונה פסולה כבר עברה ל-rejected/ ולא נקלטת."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("seder_prompts", os.path.join(SEDER, "prompts.py"))
    pm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pm)
    scenes = json.load(open(os.path.join(SEDER, "scenes.json"), encoding="utf-8"))
    items = []
    for key, v in scenes.items():
        for n, cap in enumerate(v["scenes"], 1):
            f = os.path.join(SEDER, "src", "%s-%d.jpg" % (key, n))
            if not os.path.exists(f):
                continue
            items.append(dict(id="sp/%s-%d" % (key, n), source="sp", engine="gemini", style="picturebook", kind="scene",
                              en=pm.PROMPTS[key][n - 1][:600],
                              he_ctx={"caption": plain(cap), "parasha": "פרשת " + v["name"], "book": v.get("book", "")},
                              topic=["פרשת השבוע", "ספר " + v.get("book", ""), "פרשת " + v["name"]], topic_key="sp/" + key,
                              reviewed=False, has_text=False, files={"master": f, "web_url": ""}))
    return items
