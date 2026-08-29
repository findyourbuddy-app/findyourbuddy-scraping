# findyourbuddy-scraper

`findyourbuddy-backend`'e etkinlik verisi besleyen bağımsız scraper servisi.
Backend veritabanına doğrudan erişmez, sadece `POST /internal/events/ingest`
REST endpoint'i üzerinden konuşur. Sistemdeki yeri:
[findyourbuddy-backend/docs/mimari.md](../findyourbuddy-backend/docs/mimari.md) §8.

> ⚠️ `.env` `BACKEND_API_URL`, backend'in gerçekten dinlediği portla eşleşmeli.
> Native geliştirmede `run_server.py` sırayla `8001, 8000, ...` dener (genelde
> **8001**); port uyuşmazsa ingest sessizce başarısız olur.

## Kurulum

```bash
uv sync
cp .env.example .env   # BACKEND_API_URL, SCRAPER_API_KEY, GEOCODING_USER_AGENT doldurulmalı
                        # NOVITA_API_KEY / GEMINI_API_KEY opsiyonel; ikisi de boşsa AI enrichment atlanır
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
├── config.py                    # Settings (.env) + AppConfig (config.json)
├── sources/
│   ├── base.py                  # SourceAdapter Protocol
│   └── etkinlikio.py             # etkinlik.io API v2 adapter (sadece fiziksel venue'lu etkinlikler)
├── normalization/
│   ├── schema.py                 # EventPayload
│   ├── category_mapper.py        # kaynak kategorisi -> ortak kategori
│   ├── normalizer.py              # raw dict -> EventPayload (geocoding + AI enrichment dahil)
│   └── ai_enrichment.py           # Novita veya Gemini ile kategori/tag zenginleştirme (opsiyonel)
├── geocoding/
│   └── client.py                 # Adres -> (lat, lon), Nominatim üzerinden
├── ingestion/
│   └── backend_client.py         # Backend'e batch + retry ile gönderim
└── scheduler.py / main.py         # APScheduler (BlockingScheduler) ile periyodik çalıştırma
tests/                             # Unit testler + fixtures
config.json                        # Kategori eşlemesi + aktif kaynak listesi (kod değişmeden güncellenir)
```

## Durum

- `etkinlik_io` kaynağı aktif ve entegre (`config.json` → `active_sources`,
  `app/main.py` → `build_source_registry`). Sadece fiziksel venue'su olan
  etkinlikler alınır, ONLINE etkinlikler atlanır.
- Adres bazlı geocoding fallback'i var: venue'da lat/lng yoksa (VENUE veya MANUAL tipi fark etmeksizin)
  adres Nominatim ile geocode edilir; geocoding başarısız olursa etkinlik atlanır.
- AI zenginleştirme (`scheduler.build_enrich_fn`): `NOVITA_API_KEY` varsa Novita
  (`NOVITA_MODEL`, varsayılan `deepseek/deepseek-v4-flash`) kullanılır; yoksa
  `GEMINI_API_KEY` varsa Gemini (`GEMINI_MODEL`, varsayılan `gemini-flash-latest`);
  ikisi de boşsa bu adım sessizce atlanır.
- Scheduler `SCHEDULE_INTERVAL_HOURS` aralığında (varsayılan 6, örnekte 1) tüm aktif kaynakları çalıştırır;
  bir kaynak hata verirse loglanıp diğerlerine devam edilir. Açılışta hemen bir tur atar.
- **Artımlı çalışma:** her tur önce backend'den `known-ids`'i çeker; adapter
  zaten kayıtlı etkinlikleri impression ping / mapping / geocoding'den ÖNCE
  atlar. Restart / yeni tur yalnız yeni etkinlikleri işler.
- `start_r001` UTC ISO'dur; `_parse_starts_at` aware→UTC, naive→İstanbul(UTC+3)
  normalizasyonu yapıp tzinfo'yu düşürür (backend naive-UTC saklar).
- Tek seferlik tam yeniden çekiş için `run_once.py` (scheduler'sız tek tur).
