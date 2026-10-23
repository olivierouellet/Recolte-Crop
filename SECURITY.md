# Sécurité · Security Policy

**[Français](#français) · [English](#english)**

---

## Français

### Signaler une vulnérabilité

**N’ouvrez pas d’issue publique.** Signalez-la en privé par GitHub :

* [Signaler une vulnérabilité](https://github.com/olivierouellet/Recolte-Crop/security/advisories/new)
  dans l’onglet **Security** du dépôt, visible seulement par le responsable, ou
* écrivez directement à [@olivierouellet](https://github.com/olivierouellet).

Utile à inclure : la version, ce qu’il faut pour exploiter le problème, et une façon de le reproduire.

C’est un projet à un seul responsable, fait sur son temps libre. Comptez un accusé de réception
d’ici deux semaines; vous saurez où en est la correction. Vous serez crédité dans les notes de
version si vous le souhaitez.

### Versions prises en charge

| Version | Prise en charge |
| --- | --- |
| Dernière version publiée | ✅ |
| `main` | ✅ Les correctifs y arrivent d’abord |
| Versions antérieures | ❌ Mettez à jour avec HACS |

### Surface d’attaque

* L’intégration ne fait que des GET vers les services d’imagerie d’Agriculture et Agroalimentaire Canada (`agriculture.canada.ca`), sans clé. Chaque point de requête envoie la position de l’endroit configuré, arrondie à quatre décimales (une dizaine de mètres) : choisissez un point au milieu du champ plutôt que la maison si vous préférez.
* La position est conservée dans l’entrée de configuration de Home Assistant, comme celle du domicile.
* Les réponses sont traitées comme des données non fiables : seuls des nombres, des dates et des codes de produit connus en sont extraits.

---

## English

### Reporting a vulnerability

**Don't open a public issue.** Report privately through GitHub:

* [Report a vulnerability](https://github.com/olivierouellet/Recolte-Crop/security/advisories/new)
  from the repository's **Security** tab, visible only to the maintainer, or
* contact [@olivierouellet](https://github.com/olivierouellet) directly.

Useful to include: the version, what an attacker needs, and a way to reproduce it.

This is a one-maintainer, spare-time project. Expect acknowledgement within 2 weeks, and you'll
be told where the fix stands. Credit in the release notes if you'd like it.

### Supported versions

| Version | Supported |
| --- | --- |
| Latest release | ✅ |
| `main` | ✅ Fixes land here first |
| Earlier releases | ❌ Update through HACS |

### Attack surface

* The integration only makes GET requests to Agriculture and Agri-Food Canada’s imagery services (`agriculture.canada.ca`), with no key. Each point query sends the configured location, rounded to four decimals (about ten metres): pick a point in the middle of the field rather than the house if you prefer.
* The location is stored in the Home Assistant config entry, like the home location.
* Responses are treated as untrusted data: only numbers, dates and known product codes are taken from them.
