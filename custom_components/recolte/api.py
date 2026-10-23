"""Client for Agriculture and Agri-Food Canada's agroclimate image services (AgClimate).

Each service is a mosaic of daily, weekly (Mondays) and monthly rasters. Every raster has a product code
(`tType`, e.g. "ac_gs") and the date its period ends (`dateEnd`, noon UTC). Without a mosaic rule, a point
query returns the service's default product, so Récolte always names the products it wants.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

import aiohttp

from .products import PRODUCTS

_LOGGER = logging.getLogger(__name__)

SERVICES_URL = "https://agriculture.canada.ca/imagery-images/rest/services/agclimate"
TIMEOUT = aiohttp.ClientTimeout(total=30)

# The newest daily raster can read NoData while it is being replaced: look back this far from each
# product's latest date for a value.
LOOKBACK = timedelta(days=14)

_LATEST_DATE = '[{"statisticType":"max","onStatisticField":"dateEnd","outStatisticFieldName":"latest"}]'

# Pixels outside the grid read "NoData"; inside, missing values are float32's 1.13427e+38.
_MISSING = 1e30


class AgClimateApiError(Exception):
    """The service could not be reached or returned something unexpected."""


@dataclass(frozen=True)
class Reading:
    """A product's value at a point, and the date its period ends."""

    value: float
    date: date


def _url(service: str, operation: str) -> str:
    return f"{SERVICES_URL}/{service}/ImageServer/{operation}"


def _point(latitude: float, longitude: float) -> str:
    return f'{{"x":{longitude},"y":{latitude},"spatialReference":{{"wkid":4326}}}}'


def _timestamp(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("timestamp '%Y-%m-%d %H:%M:%S'")


def parse_value(text: Any) -> float | None:
    """A pixel value, or None for NoData."""
    try:
        value = float(text)
    except (TypeError, ValueError):
        return None
    return value if abs(value) < _MISSING else None


def _from_epoch(ms: Any) -> datetime:
    return datetime.fromtimestamp(int(ms) / 1000, UTC)


def _checked(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise AgClimateApiError("Unexpected response")
    if "error" in payload:
        raise AgClimateApiError(f"Service error: {payload['error'].get('message', payload['error'])}")
    return payload


def parse_latest(payload: Any) -> dict[str, datetime]:
    """Each product's latest raster date, from a statistics query."""
    try:
        return {
            f["attributes"]["tType"]: _from_epoch(f["attributes"]["latest"])
            for f in _checked(payload)["features"]
            if f["attributes"].get("latest") is not None
        }
    except (KeyError, TypeError, ValueError) as err:
        raise AgClimateApiError(f"Unexpected statistics: {err}") from err


def parse_identify(payload: Any, keys: Iterable[str]) -> dict[str, Reading]:
    """The newest valid value of each product, from a point query that returns its catalog items."""
    data = _checked(payload)
    wanted = set(keys)
    try:
        items = (data.get("catalogItems") or {}).get("features") or []
        values = (data.get("properties") or {}).get("Values") or []
        newest: dict[str, tuple[datetime, float]] = {}
        for item, raw in zip(items, values, strict=False):
            key = item["attributes"]["tType"]
            value = parse_value(raw)
            if key not in wanted or value is None:
                continue
            moment = _from_epoch(item["attributes"]["dateEnd"])
            if key not in newest or moment > newest[key][0]:
                newest[key] = (moment, value)
    except (KeyError, TypeError, ValueError) as err:
        raise AgClimateApiError(f"Unexpected identify result: {err}") from err
    return {
        key: Reading(round(value * PRODUCTS[key].scale, 6), moment.date()) for key, (moment, value) in newest.items()
    }


class AgClimateClient:
    """Reads products at a point: two small requests per service involved."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def _async_get(self, service: str, operation: str, params: dict[str, str]) -> Any:
        try:
            async with self._session.get(
                _url(service, operation), params={**params, "f": "json"}, timeout=TIMEOUT
            ) as resp:
                resp.raise_for_status()
                return await resp.json(content_type=None)
        except TimeoutError as err:
            raise AgClimateApiError(f"{service} timed out") from err
        except (aiohttp.ClientError, ValueError) as err:
            raise AgClimateApiError(f"{service}: {err}") from err

    async def _async_latest(self, service: str, keys: list[str]) -> dict[str, datetime]:
        quoted = ",".join(f"'{k}'" for k in keys)
        payload = await self._async_get(
            service,
            "query",
            {
                "where": f"tType IN ({quoted})",
                "groupByFieldsForStatistics": "tType",
                "outStatistics": _LATEST_DATE,
            },
        )
        # Only codes we asked for go into the next where clause.
        return {k: v for k, v in parse_latest(payload).items() if k in keys}

    async def _async_service(self, service: str, keys: list[str], latitude: float, longitude: float) -> dict:
        latest = await self._async_latest(service, keys)
        if not latest:
            return {}
        where = " OR ".join(
            f"(tType = '{key}' AND dateEnd >= {_timestamp(moment - LOOKBACK)})"
            for key, moment in sorted(latest.items())
        )
        mosaic = (
            '{"mosaicMethod":"esriMosaicAttribute","sortField":"dateEnd","sortValue":"3000","ascending":true,'
            f'"where":"{where}"}}'
        )
        payload = await self._async_get(
            service,
            "identify",
            {
                "geometry": _point(latitude, longitude),
                "geometryType": "esriGeometryPoint",
                "mosaicRule": mosaic,
                "returnGeometry": "false",
                "returnCatalogItems": "true",
                "returnPixelValues": "true",
            },
        )
        return parse_identify(payload, keys)

    async def async_readings(self, latitude: float, longitude: float, keys: Iterable[str]) -> dict[str, Reading]:
        """The newest value of each product at a point; products with no value there are left out."""
        by_service: dict[str, list[str]] = {}
        for key in sorted(set(keys)):
            by_service.setdefault(PRODUCTS[key].service, []).append(key)
        readings: dict[str, Reading] = {}
        errors: list[AgClimateApiError] = []
        # One service at a time: the server answers about two requests at once and lets the others time out.
        for service, service_keys in by_service.items():
            try:
                readings.update(await self._async_service(service, service_keys, latitude, longitude))
            except AgClimateApiError as err:
                # One service down shouldn't take the others with it.
                _LOGGER.debug("AgClimate service failed: %s", err)
                errors.append(err)
        if errors and len(errors) == len(by_service):
            raise errors[0]
        return readings

    async def async_covers(self, latitude: float, longitude: float) -> bool:
        """Whether the point is on the agroclimate grid (Canada's agricultural regions)."""
        payload = _checked(
            await self._async_get(
                "crop_heat_units",
                "identify",
                {
                    "geometry": _point(latitude, longitude),
                    "geometryType": "esriGeometryPoint",
                    "returnGeometry": "false",
                    "returnCatalogItems": "false",
                },
            )
        )
        return parse_value(payload.get("value")) is not None
