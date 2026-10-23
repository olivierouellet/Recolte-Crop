"""The AAFC agroclimate products Récolte offers, keyed by the service's `tType` code.

Mirrored in Récolte Crop Card's `src/products.ts`: change one, change the other.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    """One raster series: a product type over a period, ending on the raster's date."""

    key: str  # the service's tType, e.g. "ac_gs"
    service: str  # ImageServer under agclimate/
    unit: str | None
    precision: int
    icon: str
    device_class: str | None = None
    scale: float = 1.0  # applied to the pixel value (percentiles are published as fractions)


# Period codes: 01 is 24 hours; numbers are days before the raster's date; gs April 1 to October 31,
# ay September 1 to August 31, wi November 1 to March 31; cc consecutive days; im instantaneous; mo month.
_ROLLING = ("30", "60", "90")
_SEASONS = ("gs", "ay")


def _series(prefix: str, periods: tuple[str, ...], **kwargs) -> list[Product]:
    return [Product(key=f"{prefix}_{period}", **kwargs) for period in periods]


PRODUCTS: dict[str, Product] = {
    p.key: p
    for p in [
        Product("ch_gs", "crop_heat_units", None, 0, "mdi:corn"),
        *_series(
            "gd", ("0", "5", "10", "15"), service="growing_degree_days", unit=None, precision=0, icon="mdi:sprout"
        ),
        *_series(
            "ac",
            ("01", "07", "14", *_ROLLING, *_SEASONS, "wi"),
            service="accumulated_precipitation",
            unit="mm",
            precision=1,
            icon="mdi:weather-rainy",
            device_class="precipitation",
        ),
        *_series(
            "av",
            (*_ROLLING, *_SEASONS),
            service="percent_of_average_precipitation",
            unit="%",
            precision=0,
            icon="mdi:water-percent",
        ),
        *_series(
            "pe",
            (*_ROLLING, *_SEASONS),
            service="precipitation_percentile",
            unit="%",
            precision=1,
            icon="mdi:chart-bell-curve",
            scale=100.0,
        ),
        *_series(
            "dnp",
            (*_ROLLING, *_SEASONS),
            service="departure_from_average_precipitation",
            unit="mm",
            precision=1,
            icon="mdi:plus-minus-variant",
        ),
        Product("ds_cc", "dry_spell", "d", 0, "mdi:water-off"),
        *_series("ds", ("gs", *_ROLLING), service="dry_spell", unit="d", precision=0, icon="mdi:water-off-outline"),
        *[
            Product(f"hw{t}_{period}", "heat_wave", "d", 0, "mdi:weather-sunny-alert")
            for t in ("25", "30", "32")
            for period in ("cc", "gs")
        ],
        *_series(
            "tx",
            ("01", "07"),
            service="maximum_temperature",
            unit="°C",
            precision=1,
            icon="mdi:thermometer-chevron-up",
            device_class="temperature",
        ),
        *_series(
            "ti",
            ("01", "07"),
            service="minimum_temperature",
            unit="°C",
            precision=1,
            icon="mdi:thermometer-chevron-down",
            device_class="temperature",
        ),
        # A difference, not a temperature: no device class, or °F users would get a converted offset.
        *_series(
            "dntm",
            ("28", "mo"),
            service="difference_from_normal_temperature",
            unit="°C",
            precision=1,
            icon="mdi:thermometer-lines",
        ),
        *_series(
            "spi",
            ("30", "90", "180", "365"),
            service="standardized_precipitation_index",
            unit=None,
            precision=2,
            icon="mdi:chart-bell-curve-cumulative",
        ),
        *_series(
            "spei",
            ("30", "90", "180", "365"),
            service="standardized_precipitation_evapotranspiration_index",
            unit=None,
            precision=2,
            icon="mdi:chart-bell-curve-cumulative",
        ),
        *[
            Product(f"{index}_im", "palmer_drought_index", None, 2, "mdi:gauge")
            for index in ("pdsi", "phdi", "pmdi", "mai")
        ],
        Product("tsm_im", "versatile_soil_moisture_budget", "mm", 0, "mdi:water-outline"),
        Product("pnm_im", "versatile_soil_moisture_budget", "%", 0, "mdi:water-percent"),
        Product("dnm_im", "versatile_soil_moisture_budget", "mm", 0, "mdi:plus-minus-variant"),
        *[Product(f"{index}_im", "blended_index", None, 2, "mdi:gauge") for index in ("bist", "bilt")],
    ]
}

# What a new location follows: heat for the crop, this season's rain and how it compares, and dryness.
DEFAULT_PRODUCTS = ["ch_gs", "gd_5", "ac_07", "ac_gs", "av_gs", "pe_gs", "ds_cc", "pnm_im"]
