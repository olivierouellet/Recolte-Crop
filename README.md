<p align="center">
  <img src="https://raw.githubusercontent.com/olivierouellet/Recolte-Crop/main/assets/icon.svg" alt="Logo de Récolte" width="128" height="128">
</p>

<h1 align="center">Récolte</h1>

<p align="center">Les données agroclimatiques d’Agriculture et Agroalimentaire Canada dans Home Assistant · Agriculture and Agri-Food Canada’s agroclimate data in Home Assistant</p>

<p align="center"><b><a href="#français">Français</a> · <a href="#english">English</a></b></p>

---

## Français

Agriculture et Agroalimentaire Canada (AAC) publie chaque jour des cartes agroclimatiques des régions agricoles du Canada : unités thermiques de croissance, degrés-jours, précipitations et leur comparaison à la moyenne, jours secs, vagues de chaleur, humidité du sol et indices de sécheresse. Récolte lit ces valeurs **à l’endroit de votre choix**, votre domicile ou une autre terre, et en fait des capteurs Home Assistant.

Le projet comporte deux parties :

| Partie | Dépôt | Rôle |
|---|---|---|
| **Intégration Récolte** (`recolte`) | ce dépôt | Choisissez un endroit sur la carte et les produits à suivre. Crée un capteur par produit, avec l’historique et les statistiques à long terme de Home Assistant. |
| **Récolte Crop Card** | [Récolte Crop Card](https://github.com/olivierouellet/Recolte-Crop-Card) | Une carte de tableau de bord : les valeurs en tuiles, leur interprétation (sec, normal, humide), la progression vers les UTC de votre hybride. En français et en anglais. |

### Fonctionnalités

- **Configuration dans l’interface** : *Paramètres → Appareils et services → Ajouter une intégration → Récolte*. L’emplacement de votre domicile est proposé; déplacez le repère sur la carte pour une autre terre. Ajoutez l’intégration de nouveau pour suivre un autre endroit.
- **63 produits** au choix (voir plus bas); huit sont cochés au départ.
- **Changer les produits plus tard** avec *Configurer*. Les capteurs des produits retirés sont supprimés.
- Les valeurs sont vérifiées toutes les 3 heures. Si le service est injoignable, les dernières valeurs sont conservées : plus besoin de capteurs gabarits « Dernière valeur ».
- Chaque capteur indique dans son attribut `date` la date de fin de la période mesurée : les produits quotidiens sont à jour d’hier, les hebdomadaires du lundi.
- Interface en français et en anglais.

### Produits

Chaque produit combine un type et une période, avec le code d’AAC (`tType`) entre parenthèses dans la liste :

| Type | Périodes | Unité |
|---|---|---|
| Unités thermiques de croissance (maïs) | saison de croissance (`ch_gs`) | UTC |
| Degrés-jours de croissance | base 0, 5, 10, 15 (`gd_5`…) | degrés-jours |
| Précipitations | 24 h, 7, 14, 30, 60, 90 jours, saison de croissance, année agricole, hiver (`ac_07`, `ac_gs`…) | mm |
| Précipitations en % de la moyenne, centile, écart | 30, 60, 90 jours, saison, année agricole (`av_gs`, `pe_gs`, `dnp_gs`…) | %, %, mm |
| Jours secs (moins de 0,5 mm) | consécutifs, saison, 30, 60, 90 jours (`ds_cc`…) | jours |
| Jours au-dessus de 25, 30 ou 32 °C | consécutifs, saison (`hw30_gs`…) | jours |
| Températures maximale et minimale | 24 heures, 7 jours (`tx_01`, `ti_01`…) | °C |
| Écart de température à la normale | 28 jours, mois dernier (`dntm_28`, `dntm_mo`) | °C |
| Indices SPI et SPEI | 30, 90, 180, 365 jours (`spi_90`…) | |
| Indices de Palmer, indices mixtes | (`pdsi_im`, `mai_im`, `bist_im`…) | |
| Humidité du sol | totale, % de la normale, écart (`tsm_im`, `pnm_im`, `dnm_im`) | mm, %, mm |

La saison de croissance va du 1er avril au 31 octobre, l’année agricole du 1er septembre au 31 août, l’hiver du 1er novembre au 31 mars. Hors de sa période, un produit garde sa dernière valeur (par exemple celle du 31 octobre pour la saison de croissance), avec sa date.

### Capteurs

Les identifiants dépendent du nom de l’endroit et de la langue de Home Assistant au moment de l’ajout. Pour un endroit nommé « Ferme », en français :

| Entité | État | Attributs |
|---|---|---|
| `sensor.ferme_unites_thermiques_de_croissance_mais` | UTC cumulées depuis le 1er avril | `product` : `ch_gs`, `date` : date des données |
| `sensor.ferme_precipitations_saison_de_croissance` | mm depuis le 1er avril | `product` : `ac_gs`, `date` |
| `sensor.ferme_jours_secs_consecutifs` | jours | `product` : `ds_cc`, `date` |

En anglais : `sensor.ferme_crop_heat_units_corn`, `sensor.ferme_precipitation_growing_season`, `sensor.ferme_dry_days_in_a_row`.

### Vous utilisiez des capteurs RESTful?

Une requête `identify` sans `mosaicRule` renvoie le produit **par défaut** du service, pas celui que vous pensez : pour les précipitations accumulées, c’est l’année agricole (depuis le 1er septembre), pas la saison de croissance. Récolte demande toujours le produit par son code.

### Installation

**Avec HACS (recommandé)**

[![Ouvrir votre instance Home Assistant et ce dépôt dans HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=olivierouellet&repository=Recolte-Crop&category=integration)

1. Dans Home Assistant, ouvrez **HACS** → **⋮** (en haut à droite) → **Dépôts personnalisés**.
2. Dépôt : `https://github.com/olivierouellet/Recolte-Crop`, type : **Intégration**, puis **Ajouter**. (Le bouton ci-dessus fait les étapes 1 et 2 pour vous.)
3. Cherchez **Récolte**, ouvrez-la et cliquez sur **Télécharger**.
4. Redémarrez Home Assistant.
5. Ajoutez l’intégration : *Paramètres → Appareils et services → Ajouter une intégration → Récolte*.

**Manuellement** : copiez `custom_components/recolte` dans le dossier `config/custom_components/` de Home Assistant, redémarrez, puis ajoutez l’intégration comme à l’étape 5.

**La carte** : installez [Récolte Crop Card](https://github.com/olivierouellet/Recolte-Crop-Card) de la même façon, comme dépôt personnalisé HACS de type **Dashboard**.

### Et Environnement Canada?

Les services [GeoMet](https://eccc-msc.github.io/open-data/msc-geomet/readme_fr/) et [api.weather.gc.ca](https://api.weather.gc.ca) d’Environnement et Changement climatique Canada offrent les observations des stations, les normales climatiques et les prévisions. Les produits d’AAC s’appuient sur les observations des stations et sont déjà interpolés sur une grille, ce qui donne une valeur à n’importe quelle terre plutôt qu’à la station la plus proche. Pour les prévisions et les alertes, l’intégration [Environnement Canada](https://www.home-assistant.io/integrations/environment_canada/) de Home Assistant fait déjà le travail.

### Développement

- Tests : `uv venv --python 3.13 && uv pip install -r requirements_test.txt`, puis `pytest`. Ils utilisent des réponses enregistrées du service dans `tests/fixtures` (`python scripts/record_fixtures.py` pour les renouveler).
- Style : `ruff check` et `ruff format`.
- L’icône est dans `custom_components/recolte/brand/` (Home Assistant 2026.3 ou plus récent l’affiche). Sa source est `assets/icon.svg`; après l’avoir modifiée, exportez `icon@2x.png` en 512 × 512 et `icon.png` en 256 × 256.
- Voir [CONTRIBUTING.md](CONTRIBUTING.md).

Données : [Agroclimat](https://agriculture.canada.ca/fr/production-agricole/meteo), Agriculture et Agroalimentaire Canada, sur le [Portail du gouvernement ouvert](https://ouvert.canada.ca/data/fr/dataset/07875f11-c342-4450-bdaa-0cdeaf43c0c9) ([Licence du gouvernement ouvert – Canada](https://ouvert.canada.ca/fr/licence-du-gouvernement-ouvert-canada)). Récolte n’est pas affilié au gouvernement du Canada.

---

## English

Agriculture and Agri-Food Canada (AAFC) publishes agroclimate maps of Canada’s agricultural regions every day: crop heat units, growing degree days, precipitation and how it compares with the average, dry days, heat waves, soil moisture and drought indices. Récolte (French for *harvest*) reads those values **at the location you choose**, your home or another field, and turns them into Home Assistant sensors.

It has two parts:

| Part | Repository | What it does |
|---|---|---|
| **Récolte integration** (`recolte`) | this one | Pick a location on the map and the products to follow. Creates one sensor per product, with Home Assistant’s history and long-term statistics. |
| **Récolte Crop Card** | [Récolte Crop Card](https://github.com/olivierouellet/Recolte-Crop-Card#english) | A dashboard card: the values as tiles, what they mean (dry, normal, wet), progress toward your hybrid’s CHU rating. In French and English. |

### Features

- **Set up from the UI**: *Settings → Devices & services → Add integration → Récolte*. Your home location is suggested; move the pin on the map for another field. Add the integration again to follow another location.
- **63 products** to choose from (see below); eight are ticked to start with.
- **Change the products later** under *Configure*. Sensors of removed products are deleted.
- Values are checked every 3 hours. If the service can’t be reached, the last values are kept: no more “last value” template sensors.
- Each sensor’s `date` attribute is the date the measured period ends: daily products are as of yesterday, weekly ones as of Monday.
- Interface in French and English.

### Products

Each product is a type over a period, with AAFC’s code (`tType`) in parentheses in the list:

| Type | Periods | Unit |
|---|---|---|
| Crop heat units (corn) | growing season (`ch_gs`) | CHU |
| Growing degree days | base 0, 5, 10, 15 (`gd_5`…) | degree days |
| Precipitation | 24 h, 7, 14, 30, 60, 90 days, growing season, agricultural year, winter (`ac_07`, `ac_gs`…) | mm |
| Precipitation as % of average, percentile, departure | 30, 60, 90 days, season, agricultural year (`av_gs`, `pe_gs`, `dnp_gs`…) | %, %, mm |
| Dry days (under 0.5 mm) | in a row, season, 30, 60, 90 days (`ds_cc`…) | days |
| Days above 25, 30 or 32 °C | in a row, season (`hw30_gs`…) | days |
| Maximum and minimum temperature | 24 hours, 7 days (`tx_01`, `ti_01`…) | °C |
| Temperature departure from normal | 28 days, last month (`dntm_28`, `dntm_mo`) | °C |
| SPI and SPEI | 30, 90, 180, 365 days (`spi_90`…) | |
| Palmer indices, blended indices | (`pdsi_im`, `mai_im`, `bist_im`…) | |
| Soil moisture | total, % of normal, departure (`tsm_im`, `pnm_im`, `dnm_im`) | mm, %, mm |

The growing season runs April 1 to October 31, the agricultural year September 1 to August 31, winter November 1 to March 31. Outside its period, a product keeps its last value (October 31’s for the growing season, say), with its date.

### Sensors

Entity IDs depend on the location’s name and on Home Assistant’s language when the integration is added. For a location named “Ferme”, in English:

| Entity | State | Attributes |
|---|---|---|
| `sensor.ferme_crop_heat_units_corn` | CHU accumulated since April 1 | `product`: `ch_gs`, `date`: data date |
| `sensor.ferme_precipitation_growing_season` | mm since April 1 | `product`: `ac_gs`, `date` |
| `sensor.ferme_dry_days_in_a_row` | days | `product`: `ds_cc`, `date` |

In French: `sensor.ferme_unites_thermiques_de_croissance_mais`, `sensor.ferme_precipitations_saison_de_croissance`, `sensor.ferme_jours_secs_consecutifs`.

### Were you using RESTful sensors?

An `identify` request without a `mosaicRule` returns the service’s **default** product, not the one you may expect: for accumulated precipitation, that’s the agricultural year (since September 1), not the growing season. Récolte always asks for the product by its code.

### Installation

**With HACS (recommended)**

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=olivierouellet&repository=Recolte-Crop&category=integration)

1. In Home Assistant, open **HACS** → **⋮** (top right) → **Custom repositories**.
2. Repository: `https://github.com/olivierouellet/Recolte-Crop`, type: **Integration**, then **Add**. (The button above does steps 1 and 2 for you.)
3. Search for **Récolte**, open it and click **Download**.
4. Restart Home Assistant.
5. Add the integration: *Settings → Devices & services → Add integration → Récolte*.

**Manually:** copy `custom_components/recolte` into your Home Assistant `config/custom_components/` folder, restart, and add the integration as in step 5.

**The card:** install [Récolte Crop Card](https://github.com/olivierouellet/Recolte-Crop-Card#english) the same way, as a HACS custom repository of type **Dashboard**.

### What about Environment Canada?

Environment and Climate Change Canada’s [GeoMet](https://eccc-msc.github.io/open-data/msc-geomet/readme_en/) and [api.weather.gc.ca](https://api.weather.gc.ca) services offer station observations, climate normals and forecasts. AAFC’s products build on station observations and are already interpolated onto a grid, which gives a value for any field rather than for the nearest station. For forecasts and alerts, Home Assistant’s [Environment Canada](https://www.home-assistant.io/integrations/environment_canada/) integration already does the job.

### Development

- Tests: `uv venv --python 3.13 && uv pip install -r requirements_test.txt`, then `pytest`. They use recorded service responses in `tests/fixtures` (`python scripts/record_fixtures.py` renews them).
- Style: `ruff check` and `ruff format`.
- The icon lives in `custom_components/recolte/brand/` (Home Assistant 2026.3 or later shows it). Its source is `assets/icon.svg`; after editing it, export `icon@2x.png` at 512×512 and `icon.png` at 256×256.
- See [CONTRIBUTING.md](CONTRIBUTING.md).

Data: [AgClimate](https://agriculture.canada.ca/en/agricultural-production/weather), Agriculture and Agri-Food Canada, on the [Open Government Portal](https://open.canada.ca/data/en/dataset/07875f11-c342-4450-bdaa-0cdeaf43c0c9) ([Open Government Licence – Canada](https://open.canada.ca/en/open-government-licence-canada)). Récolte is not affiliated with the Government of Canada.
