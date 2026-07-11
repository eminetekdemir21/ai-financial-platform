"""
Kural tabanli kategorilendirme.
Islem aciklamasinda/satici adinda gecen anahtar kelimelere gore
hizli, kesin (deterministik) kategori atamasi yapar. Bu katman
embedding katmanindan ONCE calisir - cunku bilinen bir satici
adi (orn. "Migros") gorulduysa, tahmine gerek yok, dogrudan
eslesir. Boylece hem hiz hem dogruluk kazanilir.
"""

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "market": [
        "migros", "carrefour", "a101", "bim", "sok", "market",
        "hakmar", "macrocenter", "tarim kredi", "onur market", "happy center",
    ],
    "yemek": [
        "restoran", "restaurant", "yemek", "lokanta", "kebap", "pizza",
        "burger", "kahve", "cafe", "kafeterya", "getir yemek",
        "yemeksepeti", "trendyol yemek", "starbucks",
    ],
    "ulasim": [
        "benzin", "akaryakit", "otopark", "taksi", "uber", "bitaksi",
        "otobus", "metro", "iett", "istanbulkart", "tren bileti", "tcdd", "ucak",
        "pegasus", "thy", "shell", "opet", "petrol ofisi", "bp",
    ],
    "alisveris": [
        "trendyol", "hepsiburada", "amazon", "n11", "alisveris",
        "giyim", "ayakkabi", "zara", "lcw", "boyner", "teknosa",
        "mediamarkt", "defacto", "ikea",
    ],
    "abonelik": [
        "netflix", "spotify", "youtube premium", "disney", "disney+",
        "amazon prime", "blutv", "exxen", "gain", "storytel",
        "icloud", "google one", "playstation plus", "xbox game pass",
    ],
    "fatura": [
        "elektrik", "su faturasi", "dogalgaz", "internet faturasi",
        "telefon faturasi", "turkcell", "vodafone", "turk telekom",
        "fatura",
    ],
    "yatirim": [
        "borsa", "hisse", "fon", "yatirim", "altin", "kripto",
        "bitcoin", "btc", "forex", "bes", "emeklilik", "midas", "matriks",
    ],
    "saglik": [
        "eczane", "hastane", "doktor", "saglik", "klinik",
        "dis hekimi", "optik", "medikal", "hastanesi",
    ],
    "egitim": [
        "kurs", "egitim", "okul", "universite", "dershane",
        "udemy", "coursera", "kitap", "kitabevi",
    ],
    "gelir": [
        "maas", "maas yatti", "gelir", "havale geldi", "ucret yatti",
        "odeme alindi", "iade", "kira geliri",
    ],
}


def normalize(text: str) -> str:
    """
    Turkce karakterleri sadelestirip metni kucuk harfe cevirir.
    Bu sayede "Elektrik FaturasÄ±" ile "elektrik faturasi" ayni
    sekilde eslesir - encoding/harf farkliliklarina karsi dayaniklilik.
    """
    text = text.lower()
    replacements = {
        "Ä±": "i", "Ä°": "i", "ÅŸ": "s", "Ã§": "c",
        "ÄŸ": "g", "Ã¶": "o", "Ã¼": "u",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def match_rule(description: str, merchant: str | None = None) -> str | None:
    """
    Aciklama + satici adinda bilinen bir anahtar kelime arar.
    Eslesme bulunursa kategori adini, bulunamazsa None doner
    (bu durumda embedding katmani devreye girer).
    """
    haystack = normalize(f"{description or ''} {merchant or ''}")
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if normalize(kw) in haystack:
                return category
    return None

