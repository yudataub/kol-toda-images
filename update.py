# -*- coding: utf-8 -*-
"""עדכון הספרייה: סריקת המקורות, רשימת פריטים שעוד לא תויגו, בניית הגלריה ופרסום.
    python update.py [--no-push] [--quiet]
פריטים חדשים בלי תגיות נכתבים ל-data/tagjobs/new.json – מתייגים לפי TAG.md (סוכן), ואז check_tags.py --merge."""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(*a):
    r = subprocess.run([sys.executable, *a], cwd=HERE, capture_output=True, text=True, encoding="utf-8",
                       env=dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8"))
    if r.returncode:
        raise SystemExit(r.stdout + r.stderr)
    return r.stdout.strip()


def main():
    quiet = "--quiet" in sys.argv
    say = (lambda *x: None) if quiet else print
    say(run("ingest.py"))
    items = json.load(open(os.path.join(HERE, "data", "items.json"), encoding="utf-8"))
    tp = os.path.join(HERE, "data", "tags.json")
    tags = json.load(open(tp, encoding="utf-8")) if os.path.exists(tp) else {}
    new = [i for i in items if i["kind"] in ("scene", "panel") and i["id"] not in tags]
    if new:
        os.makedirs(os.path.join(HERE, "data", "tagjobs"), exist_ok=True)
        json.dump([{"id": i["id"], "en": i["en"][:400], "topic": " › ".join(i.get("topic", [])[1:]),
                    "caption": (i.get("he_ctx") or {}).get("caption", ""), "question": (i.get("he_ctx") or {}).get("question", "")[:160],
                    "section": (i.get("he_ctx") or {}).get("section_title", "")} for i in new],
                  open(os.path.join(HERE, "data", "tagjobs", "new.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print("⚠️ %d פריטים חדשים בלי תגיות – data/tagjobs/new.json (לתייג לפי TAG.md)" % len(new))
    say(run("build_site.py"))
    if "--no-push" in sys.argv:
        return
    g = lambda *a: subprocess.run(["git", *a], cwd=HERE, capture_output=True, text=True, encoding="utf-8")
    g("add", "docs", "data", "lib", "*.py", "*.md")
    if g("status", "--porcelain").stdout.strip():
        g("commit", "-q", "-m", "image library: update (update.py)")
    r = g("push", "-q", "origin", "main")
    say("pushed" if r.returncode == 0 else "push failed: " + r.stderr[-300:])


if __name__ == "__main__":
    main()
