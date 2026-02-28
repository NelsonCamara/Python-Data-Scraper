# ⚽ SofaScore Football Data Scraper

Outil de **web scraping** développé en **Python** pour extraire automatiquement les statistiques de joueurs de football depuis **SofaScore**. Le scraper parcourt **9 championnats européens**, collecte les profils de plus de **2000 joueurs**, extrait leurs statistiques détaillées (attributs, valeur marchande, forces/faiblesses, postes) et exporte le tout dans un fichier **Excel** structuré. Le projet intègre une architecture modulaire, une gestion robuste des erreurs, et un pipeline CLI complet.

---

## 📖 À propos du projet

Ce scraper automatise la collecte de données footballistiques à grande échelle depuis SofaScore, une des plateformes de statistiques sportives les plus complètes. Il gère les pages dynamiques rendues en JavaScript via **Selenium**, contourne les protections anti-bot avec rotation de **User-Agents** via l'API ScrapeOps, et traite les données brutes à travers un pipeline de nettoyage, formatage et export. Le projet couvre 9 compétitions : Premier League, La Liga, Bundesliga, Serie A, Ligue 1, Liga Portugal, Eredivisie, Champions League et Europa League.

---

## 🏗️ Architecture & Structure

```
Python-Data-Scraper/
├── main.py                      → Point d'entrée CLI (argparse, 6 commandes)
├── config.py                    → Configuration centralisée (ligues, chemins, clés API)
├── requirements.txt             → Dépendances Python
├── scraper/
│   ├── __init__.py
│   ├── browser.py               → Configuration Selenium + rotation User-Agent
│   ├── player_scraper.py        → Collecte des liens et scraping des stats
│   └── search_scraper.py        → Re-scraping par recherche de joueurs
├── processing/
│   ├── __init__.py
│   ├── formatter.py             → Nettoyage des données brutes (regex, normalisation)
│   ├── parser.py                → Parsing structuré et export Excel (pandas)
│   └── deduplicator.py          → Déduplication et détection des scrapes manquants
└── output/                      → Fichiers générés (liens, stats, Excel)
```

**8 fichiers Python** | **Architecture modulaire en packages** | **Pipeline CLI complet**

---

## 🔧 Compétences techniques démontrées

### Web Scraping avancé (Selenium)

- **Navigation de pages dynamiques** — Selenium WebDriver pour interagir avec le contenu JavaScript rendu côté client par SofaScore (Single Page Application React)
- **Waits explicites** — `WebDriverWait` + `expected_conditions` (`presence_of_element_located`, `element_to_be_clickable`) pour synchroniser le scraping avec le chargement asynchrone du DOM
- **Sélecteurs CSS multiples** — Stratégie de fallback avec plusieurs sélecteurs CSS par élément (`nationality_selectors`, `club_selectors`, `champ_selectors`) pour gérer les variations de structure HTML
- **Pagination automatique** — Parcours de jusqu'à 46 pages par championnat avec `ActionChains.move_to_element().click()` sur les boutons de navigation
- **Gestion des popups** — `dismiss_cookie_popup()` pour fermer automatiquement les bannières de consentement
- **Gestion d'exceptions robuste** — `try/except` sur `TimeoutException`, `NoSuchElementException`, `StaleElementReferenceException` pour un scraping résilient sans crash

### Anti-détection & Contournement

- **Rotation de User-Agents** — Intégration de l'API ScrapeOps (`headers.scrapeops.io`) pour récupérer une liste de User-Agents réalistes et en sélectionner un aléatoirement à chaque session
- **Configuration du driver** — `page_load_strategy = "none"` pour ne pas attendre le chargement complet, `--ignore-certificate-errors`, `--allow-running-insecure-content` pour éviter les blocages
- **Variables d'environnement** — Clé API stockée dans `.env` via `python-dotenv`, jamais en dur dans le code

### Architecture logicielle & Design Patterns

- **Architecture modulaire** — Séparation en 2 packages (`scraper/`, `processing/`) avec responsabilités distinctes : collecte, nettoyage, parsing, export
- **Configuration centralisée** — `config.py` regroupe les URLs des 9 ligues, les chemins de sortie, les paramètres du navigateur, facilitant la maintenance et l'extension
- **Pattern Command** — Interface CLI avec `argparse` et sous-commandes (`collect-links`, `scrape-stats`, `rescrape`, `format`, `export`, `pipeline`), dispatch via dictionnaire de fonctions
- **Pipeline composable** — La commande `pipeline` chaîne les 4 étapes dans l'ordre : collecte → scraping → formatage → export, chaque étape pouvant être exécutée indépendamment
- **Logging structuré** — Module `logging` avec format horodaté et niveaux (INFO, WARNING, DEBUG) dans chaque module

### Traitement de données (Processing)

- **Nettoyage regex** — `format_stats_file()` supprime les unités (`yrs`, `cm`), normalise les espaces, et insère des délimiteurs pipe (`|`) entre mots CamelCase via `re.sub(r"([a-z])([A-Z])", r"\1|\2")`
- **Parsing structuré** — `parse_stats_file()` tokenize chaque ligne et reconstruit les champs (nom, nationalité, club, postes, stats) avec une logique de détection positionnelle (codes de 1-2 lettres majuscules)
- **Déduplication multi-critères** — `remove_duplicates()` utilise un `set` de tuples `(Prenom, Nom, Age, Taille, Club)` pour éliminer les doublons
- **Détection des scrapes manquants** — `find_missing_scrapes()` compare les slugs des liens collectés avec ceux déjà scrapés pour identifier les joueurs à re-scraper
- **Export Excel** — Conversion en `DataFrame` pandas et export via `openpyxl` vers `.xlsx`

### Extraction de données spécialisée

- **Profils joueurs complets** — 15+ champs extraits par joueur : nom, nationalité, championnat, club, postes, âge, taille, 5 attributs de performance, valeur marchande, forces, faiblesses, pied préféré
- **Distinction gardien/joueur de champ** — Logique conditionnelle avec `attr_map` différent selon la position (`GK` → saves, anticipation, ball_distribution vs. `FW/MF/DF` → attacking, creativity, defending)
- **Extraction de la valeur marchande** — Filtrage de caractères avec `set("0123456789MK€.")` pour nettoyer les valeurs brutes (`€12.5M` → `125M€`)
- **Forces et faiblesses** — Extraction des spans HTML dans les containers SofaScore avec concaténation par pipe

### Re-scraping intelligent

- **Recherche par nom** — `search_scraper.py` utilise la barre de recherche SofaScore pour retrouver les joueurs manquants par leur slug converti en nom (`david-raya` → `david raya`)
- **Détection automatique** — `find_missing_scrapes()` identifie automatiquement les joueurs qui n'ont pas été scrapés avec succès
- **Reprise sur erreur** — Option `--start` pour reprendre le scraping à un index donné après une interruption

---

## ▶️ Installation & Lancement

### Prérequis
- **Python** ≥ 3.8
- **Google Chrome** installé
- **ChromeDriver** (géré automatiquement par `webdriver-manager`)

### Installation
```bash
git clone https://github.com/NelsonCamara/Python-Data-Scraper.git
cd Python-Data-Scraper
pip install -r requirements.txt
```

### Configuration
Créer un fichier `.env` à la racine du projet :
```env
SCRAPEOPS_API_KEY=votre_cle_api
```

### Commandes disponibles

| Commande | Description |
|----------|-------------|
| `python main.py collect-links` | Collecter les URLs des joueurs depuis les pages de championnats |
| `python main.py scrape-stats` | Scraper les statistiques de chaque joueur |
| `python main.py rescrape` | Re-scraper les joueurs manquants ou échoués |
| `python main.py format` | Nettoyer et formater le fichier de stats brut |
| `python main.py export` | Parser les stats et exporter en Excel |
| `python main.py pipeline` | Exécuter le pipeline complet (4 étapes) |

### Options
```bash
python main.py --headless scrape-stats --start 150   # Mode sans GUI, reprendre à l'index 150
python main.py rescrape --names david-raya nick-pope  # Re-scraper des joueurs spécifiques
python main.py format --input raw.txt --output clean.txt  # Fichiers personnalisés
```

---

## 📊 Données extraites

### Joueur de champ
| Champ | Exemple |
|-------|---------|
| Nom, Prénom | Mbappé, Kylian |
| Nationalité | FRA |
| Championnat | La Liga |
| Club | Real Madrid |
| Postes | FW ST RW |
| Âge | 26 |
| Taille | 178 |
| Attaque / Créativité / Technique / Défense / Tactique | 92 / 85 / 88 / 34 / 76 |
| Valeur marchande | 180M€ |
| Forces / Faiblesses | Key passes\|Dribbles / Aerial duels |
| Pied préféré | Right |

### Gardien
| Champ | Exemple |
|-------|---------|
| Saves / Anticipation / Tactique / Distribution / Jeu aérien | 88 / 82 / 75 / 70 / 85 |

---

## 🛠️ Technologies

| Technologie | Usage |
|-------------|-------|
| Python 3 | Langage principal |
| Selenium 4 | Automatisation du navigateur, scraping de pages dynamiques |
| pandas | Manipulation de données et export Excel |
| openpyxl | Écriture de fichiers `.xlsx` |
| requests | Appels API ScrapeOps pour les User-Agents |
| argparse | Interface en ligne de commande |
| python-dotenv | Gestion des variables d'environnement |
| regex (re) | Nettoyage et formatage des données |
| logging | Journalisation structurée |

---

## 📄 Championnats couverts

Premier League (46 pages) · La Liga (35) · Bundesliga (37) · Serie A (28) · Ligue 1 (30) · Liga Portugal (26) · Eredivisie (26) · Champions League (29) · Europa League (30)

---

## 👤 Auteur

**Nelson Camara** — Étudiant en Master Informatique

---

*Projet personnel — Scraper de données footballistiques à grande échelle avec pipeline de traitement automatisé.*
