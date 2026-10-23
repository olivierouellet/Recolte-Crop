"""Constants for the Récolte integration."""

from datetime import timedelta

DOMAIN = "recolte"

CONF_PRODUCTS = "products"

# Daily products come out each morning and weekly ones on Mondays: every 3 hours is plenty.
FETCH_INTERVAL = timedelta(hours=3)

ATTRIBUTION = "Agriculture et Agroalimentaire Canada (Licence du gouvernement ouvert – Canada)"
INFO_URL = "https://agriculture.canada.ca/fr/production-agricole/meteo"
