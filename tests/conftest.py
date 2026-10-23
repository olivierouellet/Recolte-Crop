"""Fixtures for the Récolte tests."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

FIXTURES = Path(__file__).parent / "fixtures"

# Recorded 2026-10-23 at the Central Experimental Farm in Ottawa (scripts/record_fixtures.py): ch_gs 3516.92 and
# gd_5 2133.8 on 10-19, ac_07 21.0217 and ac_gs 761.411 on 10-22, ac_wi 307.374 on 03-31, av_gs 136.719 and
# pe_gs 0.997365 on 10-21 (both NoData on 10-20), ds_cc 5 on 10-21, pnm_im 138.66 on 10-19.
OTTAWA = (45.3889, -75.7152)
SERVICES = "https://agriculture.canada.ca/imagery-images/rest/services/agclimate"


def load_json(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Load custom_components/ in every test."""
    yield


@pytest.fixture
async def ottawa_home(hass):
    """Home Assistant located at the Central Experimental Farm."""
    await hass.config.async_set_time_zone("America/Toronto")
    hass.config.latitude, hass.config.longitude = OTTAWA
    hass.config.location_name = "Ferme expérimentale"
    hass.config.country = "CA"
    return hass


def serve_recorded(aioclient_mock: AiohttpClientMocker) -> AiohttpClientMocker:
    """Serve every recorded response; the coverage check answers from Ottawa's."""
    for path in sorted(FIXTURES.glob("*_query.json")) + sorted(FIXTURES.glob("*_identify.json")):
        service, operation = path.stem.rsplit("_", 1)
        aioclient_mock.get(
            re.compile(rf"{re.escape(SERVICES)}/{service}/ImageServer/{operation}\?.*returnCatalogItems=true")
            if operation == "identify"
            else re.compile(rf"{re.escape(SERVICES)}/{service}/ImageServer/{operation}"),
            json=load_json(path.name),
        )
    aioclient_mock.get(
        re.compile(rf"{re.escape(SERVICES)}/crop_heat_units/ImageServer/identify"), json=load_json("covers_ottawa.json")
    )
    return aioclient_mock


@pytest.fixture
def aafc_api(aioclient_mock: AiohttpClientMocker) -> AiohttpClientMocker:
    return serve_recorded(aioclient_mock)
