"""EGX tickers with their investing.com instrument IDs and Sharia classification.

Sharia status values:
  - "halal"   : النشاط الأساسى متوافق مع الشريعة
  - "haram"   : نشاط محرّم بإجماع/أغلبية (ربا، خمر، تبغ، إلخ)
  - "mixed"   : مختلط/يحتاج مراجعة شخصية (نسب ديون، أنشطة فرعية)

⚠️ تنبيه: هذا تصنيف اجتهادى مبدئى بناءً على النشاط الرئيسى. النسب المالية
(الديون، الإيرادات الفرعية) متغيرة سنوياً ويُفضّل المراجعة مع هيئة شرعية
موثوقة قبل اتخاذ قرار تداول حقيقى.
"""

# (symbol, investing_id, name_ar, name_en, sector, sharia_status)
EGX_TICKERS: list[tuple[str, int, str, str, str, str]] = [
    ("COMI",  12865,   "البنك التجارى الدولى",        "Commercial International Bank", "Banks",       "haram"),
    ("HRHO",  12875,   "المجموعة المالية هيرميس",     "EFG Hermes Holding",            "Financials",  "haram"),
    ("EFIH",  1178529, "إى فاينانس للاستثمارات",      "e-Finance Investment",          "Technology",  "mixed"),
    ("FWRY",  1152800, "فورى لتكنولوجيا البنوك",      "Fawry",                         "Technology",  "mixed"),
    ("ETEL",  12874,   "المصرية للاتصالات",            "Telecom Egypt",                 "Telecom",     "halal"),
    ("SWDY",  12888,   "السويدى اليكتريك",             "El Sewedy Electric",            "Industrial",  "halal"),
    ("EAST",  12986,   "الشرقية للدخان",               "Eastern Tobacco",               "Consumer",    "haram"),
    ("TMGH",  12889,   "مجموعة طلعت مصطفى",            "Talaat Moustafa Group",         "Real Estate", "halal"),
    ("PHDC",  12883,   "بالم هيلز للتعمير",            "Palm Hills Developments",       "Real Estate", "halal"),
    ("ORHD",  40620,   "أوراسكوم للتنمية مصر",         "Orascom Development Egypt",     "Real Estate", "mixed"),
    ("HELI",  12922,   "مصر الجديدة للاسكان",          "Heliopolis Housing",            "Real Estate", "halal"),
    ("EGTS",  12867,   "المصرية للمنتجعات السياحية",   "Egyptian Tourism Resorts",      "Real Estate", "mixed"),
    ("ORWE",  12943,   "النساجون الشرقيون",            "Oriental Weavers",              "Industrial",  "halal"),
    ("JUFO",  40604,   "جهينة للصناعات الغذائية",      "Juhayna Food Industries",       "Consumer",    "halal"),
    ("DOMT",  969108,  "دومتى",                         "Domty",                         "Consumer",    "halal"),
    ("OLFI",  994418,  "أوبور لاند",                    "Obour Land",                    "Consumer",    "halal"),
    ("ABUK",  12964,   "أبو قير للاسمدة",              "Abu Qir Fertilizers",           "Materials",   "halal"),
    ("MFPC",  997882,  "مصر للاسمدة (موبكو)",          "Misr Fertilizers (MOPCO)",      "Materials",   "halal"),
    ("EFIC",  12910,   "المالية والصناعية",             "Egyptian Financial & Industrial","Materials",  "halal"),
    ("SKPC",  12886,   "سيدى كرير للبتروكيماويات",     "Sidi Kerir Petrochemicals",     "Materials",   "halal"),
    ("AMOC",  12971,   "الاسكندرية للزيوت المعدنية",   "Alexandria Mineral Oils",       "Energy",      "halal"),
    ("ESRS",  12873,   "حديد عز",                      "Ezz Steel",                     "Materials",   "halal"),
    ("ISPH",  1056341, "ابن سينا فارما",                "Ibnsina Pharma",                "Healthcare",  "halal"),
    ("CIEB",  12979,   "كريدى أجريكول مصر",            "Credit Agricole Egypt",         "Banks",       "haram"),
    ("HDBK",  12921,   "بنك التعمير والاسكان",         "Housing & Development Bank",    "Banks",       "haram"),
    ("ADIB",  40917,   "مصرف ابوظبى الاسلامى",         "ADIB Egypt",                    "Banks",       "halal"),
    ("CANA",  12977,   "بنك قناة السويس",              "Suez Canal Bank",               "Banks",       "haram"),
    ("MASR",  12932,   "مدينة مصر للاسكان",            "Madinet Masr Housing",          "Real Estate", "halal"),
    ("RMDA",  1156268, "راميدا",                        "Rameda Pharma",                 "Healthcare",  "halal"),
    ("CIRA",  40580,   "كايرو للاستثمار التعليمى",     "CIRA Education",                "Education",   "halal"),
    ("OCDI",  12880,   "السادس من أكتوبر للتنمية",     "SODIC",                         "Real Estate", "halal"),
    ("EFID",  992622,  "إديتا للصناعات الغذائية",      "Edita Food Industries",         "Consumer",    "halal"),
    ("RAYA",  12948,   "راية القابضة",                  "Raya Holding",                  "Industrial",  "halal"),
    ("PRDC",  1178528, "بايونيرز",                      "Pioneers Holding",              "Financials",  "mixed"),
    ("ALCN",  40563,   "الاسكندرية للحاويات",          "Alexandria Containers",         "Industrial",  "halal"),
    ("UEFM",  13005,   "صعيد مصر لمطاحن الدقيق",       "Upper Egypt Flour Mills",       "Consumer",    "halal"),
    ("MCQE",  12966,   "مصر لانتاج الاسمنت قنا",       "Misr Cement Qena",              "Materials",   "halal"),
    ("CCAP",  12864,   "قلعة القابضة",                  "Qalaa Holdings",                "Financials",  "mixed"),
    ("OIH",   40621,   "أوراسكوم للاستثمار القابضة",   "Orascom Investment Holding",    "Financials",  "mixed"),
    ("FAITA", 40594,   "فيصل الاسلامى المصرى",         "Faisal Islamic Bank Egypt",     "Banks",       "halal"),
    ("MTIE",  1010530, "إم إم جروب للصناعة",           "MM Group for Industry",         "Industrial",  "halal"),
    ("EXPA",  13001,   "بنك تنمية الصادرات",           "Export Development Bank Egypt", "Banks",       "haram"),
    ("ATQA",  40574,   "مصر الوطنية للصلب",            "Misr National Steel",           "Materials",   "halal"),
]


def list_symbols() -> list[str]:
    return [t[0] for t in EGX_TICKERS]


def id_for(symbol: str) -> int | None:
    for s, i, *_ in EGX_TICKERS:
        if s == symbol:
            return i
    return None


def sharia_for(symbol: str) -> str:
    for s, *_, sh in EGX_TICKERS:
        if s == symbol:
            return sh
    return "mixed"


def metadata_rows() -> list[dict]:
    return [
        {
            "symbol": s,
            "name_ar": ar,
            "name_en": en,
            "sector": sec,
            "sharia_status": sh,
            "is_active": True,
        }
        for (s, _, ar, en, sec, sh) in EGX_TICKERS
    ]
