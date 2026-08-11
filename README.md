# findyourbuddy-scraper

`findyourbuddy-backend`'e etkinlik verisi besleyen bağımsız scraper servisi.
Backend veritabanına doğrudan erişmez, sadece `POST /internal/events/ingest`
REST endpoint'i üzerinden konuşur.

## Kurulum

```bash
uv sync
cp .env.example .env   # BACKEND_API_URL, SCRAPER_API_KEY, GEOCODING_USER_AGENT doldurulmalı
```

## Çalıştırma

```bash
uv run python -m app.main
```

## Test

```bash
uv run pytest
```

Testler gerçek ağ isteği atmaz, `respx` ile mock'lanmış HTTP yanıtları kullanır.

## Proje yapısı

```
app/
├── config.py            # Settings (.env) + AppConfig (config.json)
├── sources/              # Her kaynak site için bir adapter (SourceAdapter Protocol)
├── normalization/        # raw dict -> EventPayload (schema, category_mapper, normalizer)
├── geocoding/             # Adres -> (lat, lon)
├── ingestion/             # Backend'e batch + retry ile gönderim
└── scheduler.py / main.py # APScheduler ile periyodik çalıştırma
tests/                     # Unit testler + fixtures
config.json                # Kategori eşlemesi + aktif kaynak listesi (kod değişmeden güncellenir)
```

## Durum

- Görev 1 (ortak contract, iskelet) tamamlandı.
- Görev 2 (kaynak site seçimi — robots.txt/ToS kontrolü) henüz yapılmadı.
  `app/main.py` içindeki `SOURCE_REGISTRY` şu an boş; `config.json`'daki
  `active_sources` listesi de boş.
