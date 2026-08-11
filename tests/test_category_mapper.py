import pytest

from app.normalization.category_mapper import map_category


def test_map_category_returns_mapped_value() -> None:
    assert map_category("concert", {"concert": "muzik"}) == "muzik"


def test_map_category_raises_for_unmapped_category() -> None:
    with pytest.raises(KeyError):
        map_category("unknown", {"concert": "muzik"})
