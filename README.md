# Task Coach

Task Coach est une application de bureau libre de gestion de tâches. Elle aide à organiser des projets complexes comme des listes simples, avec des tâches imbriquées, des échéances et le suivi du temps passé. L'application peut être utilisée à son niveau le plus simple ou avec ses fonctions avancées.

## Fonctionnalités

- Organiser les tâches en projets et sous-tâches, avec prérequis et priorités.
- Suivre les dates de début et d'échéance, les rappels et les tâches récurrentes.
- Enregistrer le temps consacré aux tâches.
- Regrouper les tâches avec des catégories et leur associer des notes ou des pièces jointes.
- Enregistrer les données dans des fichiers Task Coach (`.tsk`) et importer ou exporter des données dans plusieurs formats.

## Architecture

Task Coach est une application Python bien architecturée avec une séparation nette entre les couches :

```
taskcoachlib/
  ├── domain/            # Modèles métier (Task, Effort, Category, etc.)
  ├── persistence/       # Persistance XML, import/export
  ├── guitk/             # Interface Tkinter (interface principale)
  ├── gui/               # [LEGACY] Interface wxPython (en cours de phase out)
  ├── application/       # Logique applicative, contrôle
  ├── config/            # Configuration, arguments CLI
  ├── widgets/           # Composants GUI réutilisables
  ├── widgetstk/         # Composants Tkinter
  ├── changes/           # Gestion de l'historique d'undo/redo
  ├── command/           # Pattern Command pour les actions
  ├── patterns/          # Observer, Composite, etc.
  ├── filesystem/        # I/O, monitoring de fichiers
  ├── syncml/            # Synchronisation
  └── [...autres]        # i18n, mailer, notify, powermgt, speak, etc.
```

### Note sur la transition wxPython → Tkinter

Les répertoires `gui/` et `widgets/` contiennent l'ancienne implémentation wxPython et sont **voués à disparaître**. Le code est progressivement migré vers `guitk/` et `widgetstk/`. Durant la transition, les deux interfaces coexistent, Tkinter étant le choix par défaut.

### État de l'avancement (novembre 2026)

- Le point d'entrée `python taskcoach/taskcoach.py` atteint la boucle principale Tkinter lors d'un test de démarrage sur Linux.
- Plusieurs problèmes bloquants de démarrage ont été corrigés : compatibilité syntaxique avec Python 3.11, conversion de certaines polices historiques, dépendances manquantes et initialisation de la commande d'arrondi des efforts.
- La commande `AlwaysRoundUp` et son réglage `effortviewer.alwaysroundup` ont été vérifiés avec un widget Tkinter.
- Le démarrage produit encore des erreurs répétées de formatage dans les messages de journalisation (`TypeError: not all arguments converted during string formatting`). Les vues et interactions doivent encore être validées ; ce test de démarrage ne remplace pas une campagne de tests fonctionnels.
- La migration vers Tkinter est toujours en cours : wxPython et l'ancienne interface restent présents pour compatibilité.

## Prérequis

- **Python 3.8 à 3.13** (3.11+ recommandé pour performance)
- Les dépendances Python listées dans `requirements.txt`
- Un environnement graphique de bureau. L'interface Tkinter est utilisée par défaut; wxPython n'est plus recommandé (legacy).

## Installation et lancement

### Depuis la racine du dépôt

1. **Créez un environnement virtuel :**
   ```bash
   python -m venv .venv
   ```

2. **Activez l'environnement virtuel :**
   ```bash
   # Linux / macOS
   source .venv/bin/activate

   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   ```

3. **Installez les dépendances et lancez l'application :**
   ```bash
   python -m pip install -r requirements.txt
   python taskcoach/taskcoach.py
   ```

### Sélection explicite de l'interface (par compatibilité)

```bash
python taskcoach/taskcoach.py --gui tk    # Tkinter (par défaut, recommandé)
python taskcoach/taskcoach.py --gui wx    # wxPython (legacy, ne pas utiliser pour du nouveau code)
```

### Options disponibles

```bash
python taskcoach/taskcoach.py --help
```

## Développement

Le code de l'application se trouve dans `taskcoach/`, notamment dans le paquet `taskcoach/taskcoachlib/`. 

### Structure des répertoires clés

- **`taskcoachlib/domain/`** : Modèles métier (Task, Effort, Note, etc.) — cœur de l'application
- **`taskcoachlib/persistence/`** : Lecteurs/écrivains XML, formats d'import/export
- **`taskcoachlib/guitk/` et `widgetstk/`** : Interface Tkinter en cours de migration
- **`taskcoachlib/application/`** : Initialisation, orchestration globale
- **`taskcoachlib/command/`** : Pattern Command pour undo/redo
- **`taskcoachlib/patterns/`** : Observer, Composite, etc.
- **`taskcoachlib/gui/` et `widgets/`** : [LEGACY] Ancienne interface wxPython — à ignorer pour nouveau code
- **`tests/`** : Tests unitaires et tests des composants ; la couverture des parcours Tkinter reste à renforcer

### Configuration du logging

Task Coach utilise le module Python `logging` pour la journalisation. Lors du démarrage, un fichier log rotatif est créé :

```
taskcoach_YYYYMMDDHHMM.log
```

Le niveau par défaut est `DEBUG`. Pour réduire la verbosité en production, modifiez :
```python
# Dans taskcoach.py, ligne 145
level=logging.INFO,  # au lieu de logging.DEBUG
```

### Priorités de développement

#### 🔴 Haute priorité

1. **Compléter la migration Tkinter** : Tous les fonctionnalités manquantes doivent être implémentées en Tkinter avant de supprimer wxPython
   - Audit des widgets manquants dans `widgetstk/`
   - Tester les cas limites et les parcours complets (drag & drop, impression, export)
   - Documenter les dépendances wxPython → Tkinter pour chaque feature

2. **Renforcer et automatiser les tests**
   - Étendre les tests ciblés aux parcours Tkinter et à la persistance
   - Ajouter ou compléter la CI avec GitHub Actions
   - Mesurer la couverture pour fixer des objectifs réalistes

3. **Audit des dépendances** : Mettre à jour ou remplacer
   - wxPython → suppression en fin de migration
   - Twisted → remplacer par asyncio natif (long terme)
   - Moderniser les versions de `requirements.txt`

4. **Fiabiliser le démarrage et le logging**
   - Corriger les appels de journalisation qui produisent des erreurs de formatage
   - Vérifier le chargement des fichiers de démarrage et les principales vues Tkinter

#### 🟡 Moyenne priorité

5. **Code quality** : Linter, type hints
   - Intégrer mypy pour vérifier les types
   - Appliquer black/isort pour formattage
   - Supprimer les `# pylint: disable` injustifiés

6. **Documentation** : Docstrings, architecture
   - Compléter les docstrings manquantes (notamment `VirtualListCtrl`)
   - Créer un diagramme UML à jour (`TCUML-*.puml`)

#### 🟢 Basse priorité

7. **Optimisations** : Performance, mémoire
   - Profiler pour identifier les goulots
   - Réduire la charge du logging en production

8. **Support multilingue** : Améliorer la couverture `i18n/`

## Licence

Task Coach est distribué sous licence [GNU GPL version 3 ou ultérieure](https://www.gnu.org/licenses/gpl-3.0.html).

## Contribution

Pour contribuer :

1. Consultez `taskcoach/HACKING.txt` pour la convention de code.
2. Les commits devraient être clairs et atomiques.
3. Ajoutez des tests pour toute nouvelle fonctionnalité (Tkinter uniquement).
4. **Ne pas ajouter du code wxPython** — priorité à la migration Tkinter.
5. Soumettez une PR contre la branche principale avec une description détaillée.

---

**Note :** L'application gère un historique complexe d'undo/redo via le pattern Command, de l'import/export multi-formats, et la synchronisation SyncML. La base de code est mature mais en phase de **transition vers Tkinter**. Les contributions doivent respecter cette feuille de route.
