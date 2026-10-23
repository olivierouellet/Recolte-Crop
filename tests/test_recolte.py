"""Tests for the Récolte integration: parsing, flows and sensors."""

from __future__ import annotations

import copy
import json
from datetime import date, timedelta
from pathlib import Path

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import async_fire_time_changed
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.recolte.api import AgClimateApiError, Reading, parse_identify, parse_latest, parse_value
from custom_components.recolte.const import DOMAIN
from custom_components.recolte.products import DEFAULT_PRODUCTS, PRODUCTS

from .conftest import OTTAWA, SERVICES, load_json, serve_recorded

INTEGRATION = Path(__file__).parent.parent / "custom_components" / DOMAIN
NOW = "2026-10-23T14:00:00+00:00"


# ---------- parsing ----------


def test_parse_value() -> None:
    assert parse_value("142.884") == 142.884
    assert parse_value("NoData") is None
    assert parse_value("1.13427e+38") is None
    assert parse_value(None) is None


def test_parse_latest() -> None:
    latest = parse_latest(load_json("accumulated_precipitation_query.json"))
    assert {k: v.date() for k, v in latest.items()} == {
        "ac_07": date(2026, 10, 22),
        "ac_gs": date(2026, 10, 22),
        "ac_wi": date(2026, 3, 31),
    }
    with pytest.raises(AgClimateApiError, match="Service error"):
        parse_latest({"error": {"code": 400, "message": "Invalid query"}})


def test_parse_identify_takes_the_newest_valid_value() -> None:
    payload = load_json("precipitation_percentile_identify.json")
    # Published as a fraction; the sensor is a percentage.
    assert parse_identify(payload, ["pe_gs"]) == {"pe_gs": Reading(99.7365, date(2026, 10, 21))}

    # The newest raster reads NoData while it is being replaced: fall back to the previous one.
    payload = copy.deepcopy(payload)
    payload["properties"]["Values"][0] = "1.13427e+38"
    assert parse_identify(payload, ["pe_gs"]) == {"pe_gs": Reading(99.7721, date(2026, 10, 19))}


def test_parse_identify_several_products_and_outside_grid() -> None:
    readings = parse_identify(load_json("accumulated_precipitation_identify.json"), ["ac_07", "ac_gs", "ac_wi"])
    assert readings["ac_07"] == Reading(21.0217, date(2026, 10, 22))
    assert readings["ac_gs"] == Reading(761.411, date(2026, 10, 22))
    assert readings["ac_wi"] == Reading(307.374, date(2026, 3, 31))
    assert parse_identify(load_json("covers_ocean.json"), ["ch_gs"]) == {}


def test_products_are_consistent() -> None:
    assert set(DEFAULT_PRODUCTS) <= set(PRODUCTS)
    for key, product in PRODUCTS.items():
        assert key == product.key
        assert product.device_class in (None, "precipitation", "temperature")


def test_translations_match_strings() -> None:
    """en.json is a copy of strings.json, fr.json has exactly the same keys, and every product is named."""

    def keys(node, path=""):
        if isinstance(node, dict):
            return {k for key, value in node.items() for k in keys(value, f"{path}.{key}")}
        return {path}

    strings = json.loads((INTEGRATION / "strings.json").read_text(encoding="utf-8"))
    for language in ("en", "fr"):
        translation = json.loads((INTEGRATION / "translations" / f"{language}.json").read_text(encoding="utf-8"))
        assert keys(translation) == keys(strings), language
    assert json.loads((INTEGRATION / "translations" / "en.json").read_text(encoding="utf-8")) == strings
    assert set(strings["entity"]["sensor"]) == set(PRODUCTS)
    assert set(strings["selector"]["product"]["options"]) == set(PRODUCTS)


# ---------- config and options flows ----------


async def _setup(hass: HomeAssistant, products: list[str] = DEFAULT_PRODUCTS) -> config_entries.ConfigEntry:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": "Ferme", "location": {"latitude": OTTAWA[0], "longitude": OTTAWA[1]}, "products": products},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    return result["result"]


@pytest.mark.freeze_time(NOW)
async def test_user_flow_defaults_to_home(ottawa_home, aafc_api) -> None:
    hass = ottawa_home
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    defaults = result["data_schema"]({})
    assert defaults["name"] == "Ferme expérimentale"
    assert defaults["location"] == {"latitude": OTTAWA[0], "longitude": OTTAWA[1]}
    assert defaults["products"] == DEFAULT_PRODUCTS

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": " ", "location": {"latitude": 45.38894, "longitude": -75.71523}, "products": ["ac_gs", "ch_gs"]},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Ferme expérimentale"
    assert result["data"] == {"latitude": 45.3889, "longitude": -75.7152}
    assert result["result"].options == {"products": ["ch_gs", "ac_gs"]}  # catalog order
    assert result["result"].unique_id == "45.389,-75.715"


async def test_user_flow_errors(ottawa_home, aioclient_mock: AiohttpClientMocker) -> None:
    hass = ottawa_home
    covers = f"{SERVICES}/crop_heat_units/ImageServer/identify"
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    location = {"latitude": 45.0, "longitude": -50.0}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "Large", "location": location, "products": []}
    )
    assert result["errors"] == {"products": "no_product"}

    aioclient_mock.get(covers, status=503)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "Large", "location": location, "products": ["ch_gs"]}
    )
    assert result["errors"] == {"base": "cannot_connect"}

    aioclient_mock.clear_requests()
    aioclient_mock.get(covers, json=load_json("covers_ocean.json"))
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "Large", "location": location, "products": ["ch_gs"]}
    )
    assert result["errors"] == {"location": "outside_coverage"}
    assert aioclient_mock.mock_calls[-1][1].query["geometry"] == '{"x":-50.0,"y":45.0,"spatialReference":{"wkid":4326}}'


@pytest.mark.freeze_time(NOW)
async def test_same_location_twice(ottawa_home, aafc_api) -> None:
    hass = ottawa_home
    await _setup(hass)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": "Encore", "location": {"latitude": 45.38891, "longitude": -75.71519}, "products": ["ch_gs"]},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


# ---------- sensors ----------


@pytest.mark.freeze_time(NOW)
async def test_sensors(ottawa_home, aafc_api) -> None:
    hass = ottawa_home
    await _setup(hass, [*DEFAULT_PRODUCTS, "ac_wi"])

    chu = hass.states.get("sensor.ferme_crop_heat_units_corn")
    assert chu.state == "3516.92"
    assert chu.attributes["product"] == "ch_gs"
    assert chu.attributes["date"] == "2026-10-19"
    assert "unit_of_measurement" not in chu.attributes
    assert chu.attributes["attribution"].startswith("Agriculture et Agroalimentaire Canada")

    rain = hass.states.get("sensor.ferme_precipitation_growing_season")
    assert rain.state == "761.411"
    assert rain.attributes["unit_of_measurement"] == "mm"
    assert rain.attributes["device_class"] == "precipitation"
    assert hass.states.get("sensor.ferme_precipitation_winter").attributes["date"] == "2026-03-31"
    assert hass.states.get("sensor.ferme_precipitation_percentile_growing_season").state == "99.7365"
    assert hass.states.get("sensor.ferme_dry_days_in_a_row").state == "5.0"
    assert hass.states.get("sensor.ferme_soil_moisture_as_of_normal").state == "138.66"


@pytest.mark.freeze_time(NOW)
async def test_only_the_needed_services_are_asked(ottawa_home, aafc_api) -> None:
    hass = ottawa_home
    await _setup(hass, ["ac_07", "ac_gs"])
    # The coverage check, then one statistics query and one identify for the single service involved.
    urls = [str(call[1].with_query(None)) for call in aafc_api.mock_calls]
    assert urls[1:] == [
        f"{SERVICES}/accumulated_precipitation/ImageServer/query",
        f"{SERVICES}/accumulated_precipitation/ImageServer/identify",
    ]
    mosaic = json.loads(aafc_api.mock_calls[-1][1].query["mosaicRule"])
    assert mosaic["where"] == (
        "(tType = 'ac_07' AND dateEnd >= timestamp '2026-10-08 12:00:00') OR "
        "(tType = 'ac_gs' AND dateEnd >= timestamp '2026-10-08 12:00:00')"
    )


@pytest.mark.freeze_time(NOW)
async def test_options_change_products(ottawa_home, aafc_api) -> None:
    hass = ottawa_home
    entry = await _setup(hass, ["ch_gs", "ac_gs"])

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["data_schema"]({})["products"] == ["ch_gs", "ac_gs"]
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"products": []})
    assert result["errors"] == {"products": "no_product"}
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"products": ["pnm_im", "ch_gs"]})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    assert registry.async_get("sensor.ferme_precipitation_growing_season") is None
    assert hass.states.get("sensor.ferme_crop_heat_units_corn").state == "3516.92"
    assert hass.states.get("sensor.ferme_soil_moisture_as_of_normal").state == "138.66"


@pytest.mark.freeze_time(NOW)
async def test_service_down_keeps_last_values(
    ottawa_home, aioclient_mock: AiohttpClientMocker, freezer: FrozenDateTimeFactory
) -> None:
    hass = ottawa_home
    serve_recorded(aioclient_mock)
    await _setup(hass, ["ch_gs", "ac_gs"])

    # One service down: its sensor keeps its value, the other refreshes.
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{SERVICES}/accumulated_precipitation/ImageServer/query", status=503)
    serve_recorded(aioclient_mock)
    freezer.tick(timedelta(hours=3, minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.ferme_precipitation_growing_season").state == "761.411"
    assert hass.states.get("sensor.ferme_crop_heat_units_corn").state == "3516.92"

    # Everything down: still the last values.
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{SERVICES}/accumulated_precipitation/ImageServer/query", status=503)
    aioclient_mock.get(f"{SERVICES}/crop_heat_units/ImageServer/query", status=503)
    freezer.tick(timedelta(hours=3, minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert len(aioclient_mock.mock_calls) == 2
    assert hass.states.get("sensor.ferme_precipitation_growing_season").state == "761.411"
    assert hass.states.get("sensor.ferme_crop_heat_units_corn").state == "3516.92"


@pytest.mark.freeze_time(NOW)
async def test_french_entity_ids(ottawa_home, aafc_api) -> None:
    """The IDs the README gives for a Home Assistant set to French."""
    hass = ottawa_home
    hass.config.language = "fr"
    await _setup(hass, ["ch_gs", "ac_gs", "ds_cc"])

    chu = hass.states.get("sensor.ferme_unites_thermiques_de_croissance_mais")
    assert chu.attributes["friendly_name"] == "Ferme Unités thermiques de croissance (maïs)"
    assert hass.states.get("sensor.ferme_precipitations_saison_de_croissance") is not None
    assert hass.states.get("sensor.ferme_jours_secs_consecutifs") is not None
