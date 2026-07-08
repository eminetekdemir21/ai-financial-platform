"""
Embedding (vektor benzerligi) tabanli kategorilendirme katmani.

Neden agir bir dil modeli (orn. sentence-transformers) yerine TF-IDF:
- Internet'ten buyuk bir model indirmeye gerek kalmiyor (Docker build
  hizli kalir, offline calisir).
- Az veriyle (birkac ornek cumleyle) bile mantikli sonuc verir.
- Gercek fintech MVP'lerinde de siklikla ilk asama tam olarak budur:
  "once basit vektor benzerligiyle basla, yeterli veri toplaninca
  gercek bir derin ogrenme modeline gec."

Mantik: Her kategori icin birkac "ornek cumle" tanimlanir. Butun
ornek cumleler TF-IDF vektorlerine cevrilir, her kategorinin
vektorlerinin ortalamasi alinarak bir "merkez nokta" (centroid)
cikarilir. Yeni bir islem geldiginde, onun vektoru bu merkez
noktalara ne kadar yakinsa (cosine similarity), o kategoriye
en yakin sayilir.
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.domains.categorization.rules import normalize

# Her kategori icin, o kategoriyi temsil eden ornek/tipik ifadeler.
# Bunlar gercek islem degil, sadece "bu kategori boyle konusulur"
# ornekleri - vektor uzayinda kategorinin bulundugu bolgeyi tanimlar.
SEED_PHRASES: dict[str, list[str]] = {
    "market": ["gunluk market alisverisi", "bakkal gida urunleri", "supermarket odemesi"],
    "yemek": ["disarida yemek yeme", "restoranda hesap odeme", "kahve ve atistirmalik"],
    "ulasim": ["yakit ve akaryakit odemesi", "toplu tasima bilet ucreti", "otopark ve ulasim gideri"],
    "alisveris": ["online alisveris siparisi", "giyim ve aksesuar alimi", "elektronik urun satin alma"],
    "fatura": ["aylik fatura odemesi", "elektrik su dogalgaz odemesi", "internet ve telefon aboneligi"],
    "yatirim": ["borsa ve hisse senedi islemi", "altin ve doviz yatirimi", "emeklilik fonu odemesi"],
    "saglik": ["eczane ve ilac alimi", "hastane ve doktor muayenesi", "saglik sigortasi odemesi"],
    "egitim": ["kurs ve egitim ucreti", "okul ve universite harci", "kitap ve egitim materyali"],
    "gelir": ["maas odemesi hesaba gecti", "gelir yatirildi", "havale ile odeme alindi"],
}

_CATEGORIES = list(SEED_PHRASES.keys())
_ALL_PHRASES = [normalize(p) for cat in _CATEGORIES for p in SEED_PHRASES[cat]]

# Vektorizer, tum ornek cumleler uzerinde bir kere egitilir (fit),
# modul yuklendiginde bellekte tutulur (tekrar egitmeye gerek yok).
_vectorizer = TfidfVectorizer()
_phrase_matrix = _vectorizer.fit_transform(_ALL_PHRASES)

# Her kategorinin kendi cumlelerinin ortalama vektoru = merkez nokta.
_centroids = {}
_idx = 0
for cat in _CATEGORIES:
    n = len(SEED_PHRASES[cat])
    rows = _phrase_matrix[_idx: _idx + n]
    _centroids[cat] = np.asarray(rows.mean(axis=0))
    _idx += n

# Bu esigin altinda kalan benzerlik skorlari "hicbir kategoriye
# yeterince benzemiyor" sayilir, "diger" olarak birakilir.
SIMILARITY_THRESHOLD = 0.10


def classify(description: str, merchant: str | None = None) -> tuple[str | None, float]:
    """
    Aciklama + satici adini vektore cevirir, en yakin kategori
    merkezini bulur. (kategori, benzerlik_skoru) doner.
    Hicbir kategori esik degerini gecemezse (None, skor) doner.
    """
    text = normalize(f"{description or ''} {merchant or ''}")
    vec = _vectorizer.transform([text])

    best_category = None
    best_score = 0.0
    for cat, centroid in _centroids.items():
        score = float(cosine_similarity(vec, centroid)[0][0])
        if score > best_score:
            best_score = score
            best_category = cat

    if best_score < SIMILARITY_THRESHOLD:
        return None, best_score
    return best_category, best_score
