from typing import Any, Protocol


class SourceAdapter(Protocol):
    def fetch_raw_events(self) -> list[dict[str, Any]]:
        """Her dict su alanlari icermeli: external_id, title, category_raw,
        location_name, address, starts_at (datetime), ve opsiyonel olarak
        description, source_url, image_url. app.normalization.normalizer bu
        sozlesmeye gore raw veriyi EventPayload'a cevirir.

        Kaynak konumu dogrudan (lat, lng) olarak biliyorsa (ornegin API
        zaten koordinat donuyorsa), raw dict'e ayrica latitude/longitude
        eklenebilir; bu durumda normalizer address'i geocode etmeden
        koordinatlari oldugu gibi kullanir."""
        ...
