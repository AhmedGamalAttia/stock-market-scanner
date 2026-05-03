"""EGX tickers with their investing.com instrument IDs.

Discovered via api.investing.com/api/search/v2/search?q={symbol}.
If a stock stops fetching, re-run discover_ids() and update.
"""

# (symbol, investing_id, name_ar, name_en, sector)
EGX_TICKERS: list[tuple[str, int, str, str, str]] = [
    ("COMI", 12865, "البنك التجارى الدولى", "Commercial International Bank", "Banks"),
    ("HRHO", 12875, "المجموعة المالية هيرميس", "EFG Hermes Holding", "Financials"),
    ("EFIH", 1178529, "إى فاينانس للاستثمارات", "e-Finance Investment", "Technology"),
    ("FWRY", 1152800, "فوري لتكنولوجيا البنوك", "Fawry", "Technology"),
    ("ETEL", 12874, "المصرية للاتصالات", "Telecom Egypt", "Telecom"),
    ("SWDY", 12888, "السويدى اليكتريك", "El Sewedy Electric", "Industrial"),
    ("EAST", 12986, "الشرقية للدخان", "Eastern Tobacco", "Consumer"),
    ("TMGH", 12889, "مجموعة طلعت مصطفى", "Talaat Moustafa Group", "Real Estate"),
    ("PHDC", 12883, "بالم هيلز للتعمير", "Palm Hills Developments", "Real Estate"),
    ("ORHD", 40620, "أوراسكوم للتنمية مصر", "Orascom Development Egypt", "Real Estate"),
    ("HELI", 12922, "مصر الجديدة للاسكان", "Heliopolis Housing", "Real Estate"),
    ("EGTS", 12867, "المصرية للمنتجعات السياحية", "Egyptian Tourism Resorts", "Real Estate"),
    ("ORWE", 12943, "النساجون الشرقيون", "Oriental Weavers", "Industrial"),
    ("JUFO", 40604, "جهينة للصناعات الغذائية", "Juhayna Food Industries", "Consumer"),
    ("DOMT", 969108, "دومتى", "Domty", "Consumer"),
    ("OLFI", 994418, "أوبر فينانس", "Obour Land", "Consumer"),
    ("ABUK", 12964, "أبو قير للاسمدة", "Abu Qir Fertilizers", "Materials"),
    ("MFPC", 997882, "مصر للاسمدة (موبكو)", "Misr Fertilizers (MOPCO)", "Materials"),
    ("EFIC", 12910, "المالية والصناعية", "Egyptian Financial & Industrial", "Materials"),
    ("SKPC", 12886, "سيدى كرير للبتروكيماويات", "Sidi Kerir Petrochemicals", "Materials"),
    ("AMOC", 12971, "الاسكندرية للزيوت المعدنية", "Alexandria Mineral Oils", "Energy"),
    ("ESRS", 12873, "حديد عز", "Ezz Steel", "Materials"),
    ("ISPH", 1056341, "ابن سينا فارما", "Ibnsina Pharma", "Healthcare"),
    ("CIEB", 12979, "كريدى أجريكول مصر", "Credit Agricole Egypt", "Banks"),
    ("HDBK", 12921, "بنك التعمير والاسكان", "Housing & Development Bank", "Banks"),
    ("ADIB", 40917, "مصرف ابوظبى الاسلامى", "ADIB Egypt", "Banks"),
    ("CANA", 12977, "بنك قناة السويس", "Suez Canal Bank", "Banks"),
    ("MASR", 12932, "مدينة مصر للاسكان", "Madinet Masr Housing", "Real Estate"),
    ("RMDA", 1156268, "راميدا", "Rameda Pharma", "Healthcare"),
    ("CIRA", 40580, "كايرو للاستثمار التعليمى", "CIRA Education", "Education"),
    ("OCDI", 12880, "السادس من أكتوبر للتنمية", "SODIC", "Real Estate"),
    ("EFID", 992622, "إديتا للصناعات الغذائية", "Edita Food Industries", "Consumer"),
    ("RAYA", 12948, "راية القابضة", "Raya Holding", "Industrial"),
    ("PRDC", 1178528, "بايونيرز", "Pioneers Holding", "Financials"),
    ("ALCN", 40563, "الاسكندرية للحاويات", "Alexandria Containers", "Industrial"),
    ("UEFM", 13005, "صعيد مصر لمطاحن الدقيق", "Upper Egypt Flour Mills", "Consumer"),
    ("MCQE", 12966, "مصر لانتاج الاسمنت قنا", "Misr Cement Qena", "Materials"),
    ("CCAP", 12864, "قلعة القابضة", "Qalaa Holdings", "Financials"),
    ("OIH", 40621, "أوراسكوم للاستثمار القابضة", "Orascom Investment Holding", "Financials"),
    ("FAITA", 40594, "فيصل الاسلامى المصرى", "Faisal Islamic Bank Egypt", "Banks"),
    ("MTIE", 1010530, "إم إم جروب للصناعة", "MM Group for Industry", "Industrial"),
    ("EXPA", 13001, "بنك تنمية الصادرات", "Export Development Bank Egypt", "Banks"),
    ("ATQA", 40574, "مصر الوطنية للصلب", "Misr National Steel", "Materials"),
]


def list_symbols() -> list[str]:
    return [t[0] for t in EGX_TICKERS]


def id_for(symbol: str) -> int | None:
    for s, i, *_ in EGX_TICKERS:
        if s == symbol:
            return i
    return None


def metadata_rows() -> list[dict]:
    return [
        {"symbol": s, "name_ar": ar, "name_en": en, "sector": sec, "is_active": True}
        for (s, _, ar, en, sec) in EGX_TICKERS
    ]
