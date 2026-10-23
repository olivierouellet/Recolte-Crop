# Contribuer · Contributing

**[Français](#français) · [English](#english)**

---

## Français

Merci de votre intérêt! En participant, vous acceptez le [code de conduite](CODE_OF_CONDUCT.md). Vous utilisez l’IA? Lisez la [politique sur l’IA](AI_POLICY.md).
Les issues et les demandes de tirage sont bienvenues en français ou en anglais.

### Installation

```bash
uv venv --python 3.13
uv pip install -r requirements_test.txt
pytest
ruff check && ruff format --check
```

Les tests n’appellent jamais le vrai service : ils utilisent des réponses enregistrées dans
`tests/fixtures/`, à la Ferme expérimentale centrale d’Ottawa. Pour les renouveler, avec le client de
l’intégration :

```bash
python scripts/record_fixtures.py
```

Les valeurs attendues dans `tests/conftest.py` et `tests/test_recolte.py` changent alors aussi.

### Conventions

* **Le français d’abord.** Toute documentation est bilingue, avec la section française en premier.
* **Textes de l’interface** : `strings.json` (anglais), copié tel quel dans `translations/en.json`, et
  `translations/fr.json`. Un test vérifie que les trois ont les mêmes clés et que chaque produit a un nom.
* **Le catalogue des produits** est dans `custom_components/recolte/products.py` et dans `src/products.ts` de
  [Récolte Crop Card](https://github.com/olivierouellet/Recolte-Crop-Card) : changer l’un, c’est changer l’autre.
* **Une requête à la fois.** Le serveur d’AAC répond à environ deux requêtes simultanées et laisse les autres
  expirer.
* **Commits** : `[Sujet] Ce qui a changé`, un sujet par commit (par exemple `[Integration]`, `[Docs]`, `[Tooling]`).
* **Les valeurs restent celles d’AAC.** Récolte ne corrige ni n’interpole les valeurs publiées.

---

## English

Thanks for your interest! By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md). Using AI tools? Read the [AI policy](AI_POLICY.md).
Issues and pull requests are welcome in French or English.

### Setup

```bash
uv venv --python 3.13
uv pip install -r requirements_test.txt
pytest
ruff check && ruff format --check
```

Tests never call the real service: they use responses recorded in `tests/fixtures/`, at the Central
Experimental Farm in Ottawa. To renew them, through the integration’s own client:

```bash
python scripts/record_fixtures.py
```

The expected values in `tests/conftest.py` and `tests/test_recolte.py` then change too.

### Conventions

* **French first.** All documentation is bilingual, with the French section first.
* **Interface text**: `strings.json` (English), copied as is to `translations/en.json`, and
  `translations/fr.json`. A test checks that all three have the same keys and that every product is named.
* **The product catalog** is in `custom_components/recolte/products.py` and in
  [Récolte Crop Card](https://github.com/olivierouellet/Recolte-Crop-Card)’s `src/products.ts`: change one,
  change the other.
* **One request at a time.** AAFC’s server answers about two simultaneous requests and lets the others time out.
* **Commits**: `[Topic] What changed`, one topic each (for example `[Integration]`, `[Docs]`, `[Tooling]`).
* **The values stay AAFC’s.** Récolte never corrects or interpolates the published values.
