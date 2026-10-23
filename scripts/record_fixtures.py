"""Record the AgClimate responses the tests replay, through the integration's own client.

Run from the repository root: `python scripts/record_fixtures.py`. It writes `tests/fixtures/<service>_<operation>.json`
for the Central Experimental Farm in Ottawa, and the coverage checks for Ottawa and the open Atlantic.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import aiohttp

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from custom_components.recolte import api  # noqa: E402
from custom_components.recolte.products import DEFAULT_PRODUCTS  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"
OTTAWA = (45.3889, -75.7152)  # Central Experimental Farm
OCEAN = (45.0, -50.0)
# The defaults, plus a product out of season (winter precipitation, last raster on March 31).
PRODUCTS = [*DEFAULT_PRODUCTS, "ac_wi"]


async def main() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    async with aiohttp.ClientSession() as session:
        client = api.AgClimateClient(session)
        original = client._async_get

        async def recording(service: str, operation: str, params: dict[str, str]):
            payload = await original(service, operation, params)
            name = f"{service}_{operation}.json"
            if operation == "identify" and params.get("returnCatalogItems") == "false":
                name = f"covers_{'ocean' if params['geometry'].startswith('{"x":-50') else 'ottawa'}.json"
            (FIXTURES / name).write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
            return payload

        client._async_get = recording
        readings = await client.async_readings(*OTTAWA, PRODUCTS)
        await client.async_covers(*OTTAWA)
        await client.async_covers(*OCEAN)
    for key, reading in sorted(readings.items()):
        print(f"{key:8} {reading.value:>10} {reading.date}")


asyncio.run(main())
