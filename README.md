# AI Financial Platform

Bankacılık sektörüne yönelik, yapay zekâ destekli kişisel finans analiz platformu. Kullanıcılar banka ekstrelerini (CSV/Excel) yükleyerek işlemlerini otomatik kategorilendirebilir, şüpheli işlemleri tespit ettirebilir, finansal sağlık skorlarını görebilir, gelecek ay tahminleri alabilir, finansal hedefler belirleyip yapay zekâdan kişiselleştirilmiş planlar isteyebilir, farklı finansal senaryoları simüle edebilir ve kendi verileriyle sohbet edebilir.

Bu proje bir yazılım/AI mühendisliği stajı kapsamında, sıfırdan uçtan uca geliştirilmiştir.

---

## Özellikler

### Backend AI Modülleri
- **Kimlik Doğrulama** — JWT (Bearer token) tabanlı kayıt/giriş sistemi
- **Hesap ve İşlem Yönetimi** — Çoklu banka hesabı desteği, CSV/Excel ekstre yükleme, mükerrer kayıt koruması
- **AI Kategorilendirme** — Kural tabanlı + TF-IDF embedding hibrit sınıflandırma (market, fatura, abonelik, ulaşım vb.)
- **Fraud Detection** — Büyük tutar sapması, alışılmadık saat, mükerrer işlem ve yüksek frekans sinyalleriyle şüpheli işlem tespiti
- **Financial Health Score** — Tasarruf oranı, gider çeşitliliği, fraud riski, gelir istikrarı ve harcama trendinden hesaplanan 0-100 arası skor
- **Time Series Forecasting** — Geçmiş verilere dayanarak gelecek ayın net nakit akışı tahmini (doğrusal trend + düşük güven rozeti)
- **RAG + AI Finansal Asistan** — pgvector tabanlı semantik arama + Google Gemini ile kullanıcının gerçek işlem verisine dayanan doğal dil sohbeti
- **AI Goal Planner** — Finansal hedef tanımlama, aylık tasarruf hesabı, ulaşılabilirlik analizi ve kişiselleştirilmiş öneri
- **What-If Simulation Engine** — Gelir değişikliği, kategori bazlı harcama azaltma ve tek seferlik harcama senaryolarını 12 aylık projeksiyon ile simüle etme
- **AI Savings Coach** — Harcama trend analizi, kişiselleştirilmiş tasarruf önerileri ve yıllık tasarruf potansiyeli hesabı

### Frontend
- Dark tema dashboard (Revolut/Robinhood tarzı)
- 2 sütunlu grid layout
- Recharts ile kategori pasta grafiği ve aylık gelir/gider bar chart
- Financial Health Score gauge
- What-If Simülatör (slider, preset senaryolar, 12 aylık grafik)
- AI Savings Coach kartı (trend analizi, öneri kartları)
- AI Goal Planner (hedef oluşturma, AI analizi)
- AI Finansal Asistan chatbot
- İşlem tablosu (sayfalama, 20 satır/sayfa)

### Altyapı
- **CI/CD** — GitHub Actions ile her push'ta backend (pytest) ve frontend (vitest) testleri paralel çalışır
- **pgvector** — PostgreSQL üzerinde vektör benzerlik araması
- **Demo modu** — 5 banka seçeneği ile otomatik demo hesabı oluşturma

---

## Teknoloji Yığını

| Katman | Teknolojiler |
|--------|-------------|
| **Backend** | FastAPI, SQLAlchemy 2.0, PostgreSQL + pgvector, Alembic, Pydantic, JWT |
| **AI/ML** | Google Gemini API, TF-IDF embedding, scikit-learn, RAG pipeline |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS v4, Recharts |
| **Altyapı** | Docker, Docker Compose, Redis, GitHub Actions CI/CD |
| **Test** | pytest (71 backend testi), Vitest (8 frontend testi) |

---

## Proje Yapısı

```
ai-financial-platform/
├── backend/
│   ├── app/
│   │   ├── core/                  # Config, database, security
│   │   ├── domains/
│   │   │   ├── auth/              # Kimlik doğrulama
│   │   │   ├── transactions/      # Hesaplar, işlemler, CSV/Excel parser
│   │   │   ├── categorization/    # AI kategorilendirme (kural + TF-IDF)
│   │   │   ├── fraud/             # Fraud detection
│   │   │   ├── financial_health/  # Health score (0-100)
│   │   │   ├── forecasting/       # Gelecek ay tahmini
│   │   │   ├── assistant/
│   │   │   │   └── rag/           # pgvector + LLM asistan
│   │   │   ├── goal_planner/      # AI hedef planlayıcı
│   │   │   ├── simulation/        # What-If senaryo motoru
│   │   │   └── savings_coach/     # AI tasarruf koçu
│   │   └── main.py
│   ├── alembic/                   # Veritabanı migration'ları
│   ├── tests/                     # 71 pytest testi
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/                   # Backend API istemcileri
│       ├── components/            # Charts, GoalPlanner, WhatIfSimulator,
│       │                          # SavingsCoach, AssistantChat...
│       ├── pages/                 # Login, Register, Dashboard
│       └── test/                  # Vitest testleri
├── .github/workflows/             # CI/CD (backend + frontend paralel)
├── docker-compose.yml
└── generate_demo_data.py          # 200 işlemlik demo verisi üretici
```

---

## Kurulum

### Gereksinimler
- Docker ve Docker Compose
- Node.js v18+

### Backend

```bash
# .env dosyasını oluştur
cp backend/.env.example backend/.env
# SECRET_KEY ve LLM_API_KEY değerlerini doldur

# Container'ları başlat
docker compose up --build -d

# API dokümantasyonu
# http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# http://localhost:5173
```

### Demo Hesabı

Sistemi hızlıca denemek için:
- **E-posta:** test@example.com
- **Şifre:** Sifre123

Ya da "Bankamı Bağla" butonuyla 5 demo bankasından birini seçip otomatik hesap oluşturabilirsiniz.

---

## Testler

```bash
# Backend testleri (71 test)
docker exec afp_backend python -m pytest -v

# Frontend testleri (8 test)
cd frontend && npm test
```

---

## LLM Özellikleri Hakkında

AI Finansal Asistan, What-If Simulation ve Savings Coach modülleri Google Gemini API kullanır. `backend/.env` dosyasındaki `LLM_API_KEY` alanına [Google AI Studio](https://aistudio.google.com/apikey) üzerinden alınan ücretsiz API anahtarı girilmelidir.

Anahtar girilmezse bu uç noktalar `503 Service Unavailable` döner; sistemin geri kalanı bundan etkilenmez.

---

## Lisans

Bu proje eğitim/staj amaçlı geliştirilmiştir.
