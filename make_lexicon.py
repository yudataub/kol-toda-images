# -*- coding: utf-8 -*-
"""מילון המושגים: מושג בעברית -> מילים נרדפות בעברית + מילים באנגלית שמופיעות בתיאורי התמונות.
    python make_lexicon.py   -> data/lexicon.json
מוסיפים מושגים כאן (ולא בקובץ ה-json), ומריצים שוב."""
import json, os

L = {
 # אנשים
 "ילד": ("ילדים בן נער תלמיד", "boy boys child children kid kids son sons student"),
 "אבא": ("אב הורה", "father dad parent"),
 "סבא": ("זקן סב", "grandfather elderly old man"),
 "רב": ("רבי מורה מלמד חכם", "rabbi teacher sage"),
 "חזן": ("שליח ציבור שץ", "cantor chazan prayer leader"),
 "כהן": ("כהנים ברכת כהנים", "kohen kohanim priest priests"),
 "לוי": ("לויים", "levite levites"),
 "משפחה": ("בני משפחה", "family"),
 "חבר": ("חברים חברותא", "friend friends classmate neighbor"),
 "אורח": ("אורחים הכנסת אורחים", "guest guests visitor"),
 "עני": ("עניים קבצן", "poor beggar needy"),
 "חולה": ("חולים רופא", "sick ill doctor patient hospital"),
 "תינוק": ("תינוקות", "baby infant"),
 "חייל": ("חיילים צבא", "soldier soldiers army"),
 # מקומות
 "בית כנסת": ("בית הכנסת ארון קודש בימה", "synagogue ark bima shul"),
 "בית מדרש": ("ישיבה לימוד", "study hall yeshiva beit midrash"),
 "בית המקדש": ("מקדש היכל משכן", "holy temple temple sanctuary tabernacle"),
 "ירושלים": ("העיר העתיקה", "jerusalem old city"),
 "כותל": ("הכותל המערבי", "western wall kotel"),
 "בית": ("בבית חדר סלון", "home house living room"),
 "מטבח": ("כיריים תנור", "kitchen stove oven counter"),
 "חדר שינה": ("מיטה שינה", "bedroom bed pajamas"),
 "בית ספר": ("כיתה מורה", "school classroom schoolyard teacher desk"),
 "רחוב": ("כביש מדרכה", "street road sidewalk"),
 "גינה": ("חצר גן", "garden yard park"),
 "שדה": ("שדות חקלאי חיטה", "field fields farmer wheat"),
 "מדבר": ("", "desert"),
 "חנות": ("מכולת שוק קניות", "shop store grocery market"),
 "פארק": ("טיול", "park hike trip"),
 # תפילה
 "תפילה": ("מתפלל מתפללים להתפלל", "prayer praying pray prays"),
 "סידור": ("סידורים", "siddur prayer book"),
 "מניין": ("עשרה מנין", "minyan ten men"),
 "תפילין": ("הנחת תפילין", "tefillin phylacteries"),
 "טלית": ("טלית גדול", "tallit prayer shawl"),
 "ציצית": ("טלית קטן", "tzitzit fringes"),
 "כיפה": ("", "kippa kippot yarmulke"),
 "מזוזה": ("מזוזות", "mezuzah mezuza doorpost"),
 "ספר תורה": ("תורה קריאת התורה", "torah scroll sefer torah"),
 "שמע ישראל": ("קריאת שמע שמע", "shema covering eyes"),
 "ברכת כהנים": ("נשיאת כפיים", "priestly blessing raised hands"),
 "עמידה": ("שמונה עשרה", "amidah standing prayer"),
 # ברכות ואוכל
 "ברכה": ("ברכות מברך לברך", "blessing bless blessings"),
 "נטילת ידיים": ("נטילה נוטל ליטול ספל נטלה", "washing hands washing cup two handled cup netilat"),
 "לחם": ("פת המוציא כיכר", "bread loaf"),
 "חלה": ("חלות", "challah braided"),
 "מצה": ("מצות", "matza matzah matzot"),
 "יין": ("כוס יין גפן", "wine cup of wine goblet"),
 "ענבים": ("ענב גפן", "grape grapes vine"),
 "פירות": ("פרי עץ", "fruit fruits tree"),
 "תפוח": ("תפוחים", "apple apples"),
 "תמר": ("תמרים", "date dates palm"),
 "זית": ("זיתים", "olive olives"),
 "רימון": ("רימונים", "pomegranate"),
 "תאנה": ("תאנים", "fig figs"),
 "ירקות": ("ירק אדמה מלפפון עגבניה", "vegetable vegetables cucumber tomato carrot"),
 "עוגה": ("עוגיה עוגיות מזונות", "cake cookie cookies pastry"),
 "מים": ("כוס מים", "water"),
 "חלב": ("חלבי", "milk dairy cheese"),
 "בשר": ("בשרי עוף", "meat chicken"),
 "דגים": ("דג", "fish"),
 "מרק": ("", "soup"),
 "ממתקים": ("סוכריות שוקולד", "candy sweets chocolate"),
 "ארוחה": ("סעודה ארוחת ערב שולחן", "meal dinner lunch feast table"),
 "ברכת המזון": ("זימון", "grace after meals birkat hamazon"),
 "כשרות": ("כשר הכשר", "kosher kashrut"),
 "שבעת המינים": ("חיטה שעורה", "seven species wheat barley"),
 # שבת
 "שבת": ("שבתות שבת קודש", "shabbat sabbath"),
 "נרות שבת": ("נרות הדלקת נרות פמוטים", "shabbat candles candlesticks candle lighting"),
 "קידוש": ("כוס קידוש", "kiddush goblet"),
 "הבדלה": ("נר הבדלה בשמים", "havdalah braided candle spice box"),
 "חמין": ("פלטה טשולנט", "cholent hot plate blech"),
 "מוקצה": ("", "muktzeh"),
 # חגים ומועדים
 "ראש השנה": ("ראש השנה שופר תפוח בדבש", "rosh hashana honey"),
 "שופר": ("תקיעת שופר", "shofar horn ram"),
 "יום כיפור": ("יום הכיפורים כיפור", "yom kippur"),
 "סוכה": ("סוכות סכך", "sukkah sukka schach booth"),
 "ארבעת המינים": ("לולב אתרוג הדס ערבה", "lulav etrog myrtle willow four species"),
 "שמחת תורה": ("הקפות", "simchat torah dancing"),
 "חנוכה": ("חנוכיה נרות חנוכה פך שמן", "hanukkah chanukah menorah hanukkiah oil"),
 "פורים": ("מגילה משלוח מנות מתנות לאביונים", "purim megillah scroll mishloach costume"),
 "פסח": ("ליל הסדר הגדה קערה", "passover pesach seder haggadah"),
 "חמץ": ("בדיקת חמץ ביעור", "chametz candle feather"),
 "ספירת העומר": ("עומר", "omer counting"),
 "ראש חודש": ("ירח חודש", "rosh chodesh new moon moon"),
 "תשעה באב": ("חורבן צום", "tisha bav destruction fast"),
 "שבועות": ("ביכורים", "shavuot first fruits"),
 # בין אדם לחברו וערכים
 "צדקה": ("קופת צדקה מטבעות", "charity tzedakah coins box"),
 "כיבוד הורים": ("הורים", "honoring parents mother father"),
 "חסד": ("עזרה עוזר גמילות חסדים", "kindness helping help"),
 "שלום": ("השכנת שלום", "peace reconciling"),
 "לשון הרע": ("רכילות דיבור", "gossip whispering speech"),
 "אמת": ("שקר", "truth honest lie"),
 "גניבה": ("גנב", "stealing theft thief"),
 "אבדה": ("השבת אבדה מציאה", "lost found lost and found"),
 "צער בעלי חיים": ("בעלי חיים", "animal animals kindness to animals"),
 "בעלי חיים": ("כלב חתול פרה סוס ציפור", "dog cat cow horse bird sheep animal"),
 "לימוד תורה": ("לומד לימוד ספר", "learning studying reading book books"),
 # זמנים ואור
 "בוקר": ("שחרית זריחה", "morning sunrise dawn"),
 "ערב": ("שקיעה מעריב", "evening sunset dusk"),
 "לילה": ("ירח כוכבים", "night moon stars dark"),
 "גשם": ("גשמים חורף", "rain rainy"),
 "קשת": ("קשת בענן", "rainbow"),
 # חפצים
 "נר": ("נרות", "candle candles"),
 "ספר": ("ספרים", "book books"),
 "שעון": ("שעה", "clock watch"),
 "טלפון": ("נייד", "phone"),
 "חשמל": ("מתג אור מנורה", "electric switch lamp light"),
 "כסף": ("מטבעות", "money coins"),
 "מתנה": ("מתנות", "gift present"),
 "בגדים": ("בגד חולצה נעליים", "clothes shirt shoes coat"),
 "כלים": ("צלחת כוס סיר", "dishes plate cup pot bowl"),
}


def main():
    out = {k: {"he": [w for w in he.split() if w] + [k], "en": en.split()} for k, (he, en) in L.items()}
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "lexicon.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(out), "concepts ->", p)


if __name__ == "__main__":
    main()
