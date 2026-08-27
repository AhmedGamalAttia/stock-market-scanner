"""EGX tickers with their Yahoo Finance symbols and Sharia classification.

Yahoo lists Egyptian Exchange stocks under the ``.CA`` suffix (Cairo), e.g.
``COMI.CA``. Verified 2026-08-27: 5 years of daily OHLCV for every symbol below.

Sharia status values:
  - "halal"   : النشاط الأساسى متوافق مع الشريعة
  - "haram"   : نشاط محرّم بإجماع/أغلبية (ربا، خمر، تبغ، إلخ)
  - "mixed"   : مختلط/يحتاج مراجعة شخصية (نسب ديون، أنشطة فرعية)

⚠️ تنبيه: هذا تصنيف اجتهادى مبدئى بناءً على النشاط الرئيسى. النسب المالية
(الديون، الإيرادات الفرعية) متغيرة سنوياً ويُفضّل المراجعة مع هيئة شرعية
موثوقة قبل اتخاذ قرار تداول حقيقى.
"""

# (symbol, yahoo_symbol, name_ar, name_en, sector, sharia_status)
EGX_TICKERS: list[tuple[str, str, str, str, str, str]] = [
    ("COMI",  "COMI.CA",  "البنك التجارى الدولى",        "Commercial International Bank", "Banks",       "haram"),
    ("HRHO",  "HRHO.CA",  "المجموعة المالية هيرميس",     "EFG Hermes Holding",            "Financials",  "haram"),
    ("EFIH",  "EFIH.CA",  "إى فاينانس للاستثمارات",      "e-Finance Investment",          "Technology",  "mixed"),
    ("FWRY",  "FWRY.CA",  "فورى لتكنولوجيا البنوك",      "Fawry",                         "Technology",  "mixed"),
    ("ETEL",  "ETEL.CA",  "المصرية للاتصالات",            "Telecom Egypt",                 "Telecom",     "halal"),
    ("SWDY",  "SWDY.CA",  "السويدى اليكتريك",             "El Sewedy Electric",            "Industrial",  "halal"),
    ("EAST",  "EAST.CA",  "الشرقية للدخان",               "Eastern Tobacco",               "Consumer",    "haram"),
    ("TMGH",  "TMGH.CA",  "مجموعة طلعت مصطفى",            "Talaat Moustafa Group",         "Real Estate", "halal"),
    ("PHDC",  "PHDC.CA",  "بالم هيلز للتعمير",            "Palm Hills Developments",       "Real Estate", "halal"),
    ("ORHD",  "ORHD.CA",  "أوراسكوم للتنمية مصر",         "Orascom Development Egypt",     "Real Estate", "mixed"),
    ("HELI",  "HELI.CA",  "مصر الجديدة للاسكان",          "Heliopolis Housing",            "Real Estate", "halal"),
    ("EGTS",  "EGTS.CA",  "المصرية للمنتجعات السياحية",   "Egyptian Tourism Resorts",      "Real Estate", "mixed"),
    ("ORWE",  "ORWE.CA",  "النساجون الشرقيون",            "Oriental Weavers",              "Industrial",  "halal"),
    ("JUFO",  "JUFO.CA",  "جهينة للصناعات الغذائية",      "Juhayna Food Industries",       "Consumer",    "halal"),
    ("DOMT",  "DOMT.CA",  "دومتى",                         "Domty",                         "Consumer",    "halal"),
    ("OLFI",  "OLFI.CA",  "أوبور لاند",                    "Obour Land",                    "Consumer",    "halal"),
    ("ABUK",  "ABUK.CA",  "أبو قير للاسمدة",              "Abu Qir Fertilizers",           "Materials",   "halal"),
    ("MFPC",  "MFPC.CA",  "مصر للاسمدة (موبكو)",          "Misr Fertilizers (MOPCO)",      "Materials",   "halal"),
    ("EFIC",  "EFIC.CA",  "المالية والصناعية",             "Egyptian Financial & Industrial","Materials",  "halal"),
    ("SKPC",  "SKPC.CA",  "سيدى كرير للبتروكيماويات",     "Sidi Kerir Petrochemicals",     "Materials",   "halal"),
    ("AMOC",  "AMOC.CA",  "الاسكندرية للزيوت المعدنية",   "Alexandria Mineral Oils",       "Energy",      "halal"),
    ("ISPH",  "ISPH.CA",  "ابن سينا فارما",                "Ibnsina Pharma",                "Healthcare",  "halal"),
    ("CIEB",  "CIEB.CA",  "كريدى أجريكول مصر",            "Credit Agricole Egypt",         "Banks",       "haram"),
    ("HDBK",  "HDBK.CA",  "بنك التعمير والاسكان",         "Housing & Development Bank",    "Banks",       "haram"),
    ("ADIB",  "ADIB.CA",  "مصرف ابوظبى الاسلامى",         "ADIB Egypt",                    "Banks",       "halal"),
    ("CANA",  "CANA.CA",  "بنك قناة السويس",              "Suez Canal Bank",               "Banks",       "haram"),
    ("MASR",  "MASR.CA",  "مدينة مصر للاسكان",            "Madinet Masr Housing",          "Real Estate", "halal"),
    ("RMDA",  "RMDA.CA",  "راميدا",                        "Rameda Pharma",                 "Healthcare",  "halal"),
    ("CIRA",  "CIRA.CA",  "كايرو للاستثمار التعليمى",     "CIRA Education",                "Education",   "halal"),
    ("OCDI",  "OCDI.CA",  "السادس من أكتوبر للتنمية",     "SODIC",                         "Real Estate", "halal"),
    ("EFID",  "EFID.CA",  "إديتا للصناعات الغذائية",      "Edita Food Industries",         "Consumer",    "halal"),
    ("RAYA",  "RAYA.CA",  "راية القابضة",                  "Raya Holding",                  "Industrial",  "halal"),
    ("PRDC",  "PRDC.CA",  "بايونيرز",                      "Pioneers Holding",              "Financials",  "mixed"),
    ("ALCN",  "ALCN.CA",  "الاسكندرية للحاويات",          "Alexandria Containers",         "Industrial",  "halal"),
    ("UEFM",  "UEFM.CA",  "صعيد مصر لمطاحن الدقيق",       "Upper Egypt Flour Mills",       "Consumer",    "halal"),
    ("MCQE",  "MCQE.CA",  "مصر لانتاج الاسمنت قنا",       "Misr Cement Qena",              "Materials",   "halal"),
    ("CCAP",  "CCAP.CA",  "قلعة القابضة",                  "Qalaa Holdings",                "Financials",  "mixed"),
    ("OIH",   "OIH.CA",   "أوراسكوم للاستثمار القابضة",   "Orascom Investment Holding",    "Financials",  "mixed"),
    ("FAITA", "FAITA.CA", "فيصل الاسلامى المصرى",         "Faisal Islamic Bank Egypt",     "Banks",       "halal"),
    ("MTIE",  "MTIE.CA",  "إم إم جروب للصناعة",           "MM Group for Industry",         "Industrial",  "halal"),
    ("EXPA",  "EXPA.CA",  "بنك تنمية الصادرات",           "Export Development Bank Egypt", "Banks",       "haram"),
    ("ATQA",  "ATQA.CA",  "مصر الوطنية للصلب",            "Misr National Steel",           "Materials",   "halal"),
]
# Dropped: ESRS (Ezz Steel) — delisted, no Yahoo data.


def list_symbols() -> list[str]:
    return [t[0] for t in EGX_TICKERS]


def yahoo_for(symbol: str) -> str:
    for s, y, *_ in EGX_TICKERS:
        if s == symbol:
            return y
    return f"{symbol}.CA"


def sharia_for(symbol: str) -> str:
    for s, *_, sh in EGX_TICKERS:
        if s == symbol:
            return sh
    return "mixed"


def stock_info(symbol: str) -> dict | None:
    for row in metadata_rows():
        if row["symbol"] == symbol:
            return row
    return None


def metadata_rows() -> list[dict]:
    return [
        {
            "symbol": s,
            "yahoo_symbol": y,
            "name_ar": ar,
            "name_en": en,
            "sector": sec,
            "sharia_status": sh,
            "is_active": True,
        }
        for (s, y, ar, en, sec, sh) in EGX_TICKERS
    ]
