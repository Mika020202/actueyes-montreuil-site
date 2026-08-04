# Pipeline Actualités automatique — ACTU EYES

Instructions autonomes pour la tâche planifiée hebdomadaire de **contrôle qualité** de la publication autonome. Cette page est le point d'entrée : lis-la en entier avant d'agir, tu n'as aucune mémoire des sessions précédentes.

**Depuis le 02/08/2026, la veille et la publication sont exécutées par GitHub Actions, pas par toi.** Les étapes 1 à 4 bis restent la spécification de ce qu'un article doit être — c'est ce que `scripts/veille.py` met en œuvre dans le dépôt, et c'est la référence à consulter pour juger la qualité d'un article produit automatiquement, ou pour faire évoluer le générateur. **L'étape 5 décrit ton rôle réel : contrôler, en lecture seule.**

## Contexte

Le client (Mikhael, mikhael.saada@gmail.com) a demandé une veille automatique : surveiller des sites sources par thème, rédiger un article original (jamais une copie) quand il y a une vraie nouveauté, et le publier sur https://www.actueyes-montreuil.fr/ dans l'onglet Actualités, à un rythme de **1 à 2 articles par semaine au total** (pas par thème). Le client fait confiance par défaut à la publication automatique, sans validation préalable — mais veut être informé par email de ce qui se passe.

Fichiers de ce dossier :
- `sources.json` — sites à surveiller, par thème (fourni par le client le 26/07/2026, **refondu le 02/08/2026** après test individuel des 38 sources d'origine : voir `_revision_note` en tête du fichier).
- `state.json` — mémoire persistante entre les exécutions (dernier item vu par source, articles déjà publiés, slugs déjà utilisés, file d'attente).
- `pending/` — dossier où stocker un article déjà rédigé mais pas encore mis en ligne, si le déploiement échoue une semaine donnée.

Le site est généré par `/home/claude/build.py` (liste `ARTICLES`, fonction `article_url()`, JSON-LD, etc. — voir le fichier directement, il est trop long pour être résumé ici). Le doc de référence complet du projet est `/home/claude/project_doc.md` (et sa copie dans le Projet Claude `claude/site-maison-mikis-recap.md`) — le lire si le contexte général du site est nécessaire (structure des pages, historique, contraintes techniques).

## Étape 0 — Premier passage seulement (baseline)

**La baseline a été enregistrée manuellement le 02/08/2026 : `state.json` est déjà en `"baseline_done": true`.** Tu passes donc directement à l'étape 1 — il n'y a plus de passage à blanc à faire.

(Pour mémoire, si un jour `baseline_done` repassait à `false` : ne publie aucun article, enregistre seulement pour chaque source l'item le plus récent affiché — titre + URL — dans `last_seen_title`/`last_seen_url`, remets `"baseline_done": true`, sauvegarde et termine avec un message expliquant que la veille est réarmée.)

Quatre sources ont une baseline vide (`null`) parce qu'elles n'ont pas pu être relevées le 02/08 : `jj-vision`, `coopervision`, `ophtalmic`, `eye-see-mag`. Au premier passage, enregistre leur item le plus récent, mais ne le publie que s'il respecte la règle de fraîcheur ci-dessous.

## Étape 1 — Vérifier les sources

Pour chaque thème de `sources.json`, récupère (WebFetch) la page indiquée et regarde l'item le plus récent (titre, date si disponible, URL). Compare avec `last_seen_title`/`last_seen_url` dans `state.json` pour cette source :
- Si c'est identique → rien de neuf, mets juste à jour `last_checked`.
- Si c'est différent → nouvel item détecté, à ajouter à la liste des candidats de la semaine.

**RÈGLE DE FRAÎCHEUR — impérative :** ne retiens jamais comme candidat un item daté de **plus de 3 mois**, même s'il est "nouveau" par rapport à `last_seen_title`. Certaines sources sont dormantes (leur dernier article date de 2020 ou 2023) : leur item le plus récent doit être enregistré dans `last_seen_*` mais jamais publié. Si la liste n'affiche pas de date (Audio Infos 365, Marchon), ouvre l'item pour le dater avant de le retenir. Un article daté publié comme s'il était neuf est la pire erreur possible sur ce site.

**Thème "Mode & tendances" — plus de rotation depuis le 02/08/2026 :** les 19 pages de marques d'origine étaient des vitrines rendues en JavaScript et ne renvoyaient jamais rien. Elles sont remplacées par 9 fils de presse des groupes qui fabriquent réellement ces lunettes (Thélios, Kering Eyewear, Marcolin, Marchon, Safilo, EssilorLuxottica) plus deux titres de presse française et la page Prada. La liste est courte : **vérifie-les toutes chaque semaine**, il n'y a plus de `mode_rotation_index` ni de `mode_rotation_batch_size` dans `state.json`. Le champ `covers` de chaque source indique quelles marques du magasin elle couvre — c'est l'angle à privilégier dans l'article (« Fendi », pas « Thélios », pour la clientèle).

**Sources marquées `ok_faible_valeur`** (Safilo, EssilorLuxottica) : ce sont des fils financiers et réglementaires. Ignore systématiquement les déclarations de capital, droits de vote, résultats, assemblées, nominations. Ne retiens que les rares annonces produit ou collection.

**Sources en anglais** (Alcon, Johnson & Johnson Vision, et tous les fils de groupes lunetiers) : le contenu retenu doit être traduit/adapté en français dans l'article, pas publié en anglais.

**Source CRAMIF** : flux généraliste — ne retenir un item que s'il concerne concrètement l'optique, le remboursement de lunettes ou le 100% Santé. Ignorer tout le reste (ce n'est pas un manque de veille, juste hors-sujet).

**Sources en échec :** si un WebFetch renvoie une erreur (403, 404, page vide), note-le dans `last_checked` et passe à la source suivante sans bloquer le run. **Ne contourne jamais un blocage** par curl, python, un proxy, une archive ou un cache : si WebFetch est refusé, la source est simplement sautée cette semaine. Si une source échoue trois semaines de suite, déplace-la dans `disabled_sources` de `sources.json` avec le motif et la date.

**`disabled_sources` et `rejected_candidates_note` dans `sources.json` :** ces deux blocs listent des URL déjà testées et écartées le 02/08/2026, avec leur motif. Ne les réintroduis pas et ne les retente pas — elles ont coûté une session entière de tests.

## Étape 2 — Sélectionner 1 à 2 sujets

Parmi tous les items neufs détectés cette semaine (tous thèmes confondus) et ceux déjà en attente dans `state.json.queue` (voir plus bas), choisis les **1 à 2 plus pertinents** pour la clientèle d'une boutique d'optique de quartier à Montreuil — privilégie une vraie information utile (nouvelle techno de verre/lentille, nouvelle collection concrète, évolution de remboursement, conseil santé) plutôt qu'un simple communiqué corporate creux (nomination, résultats financiers, partenariat sans intérêt client).

Si plus de 2 sujets valables sont trouvés, garde les 2 meilleurs pour cette semaine et **ajoute les autres à `state.json.queue`** (avec thème, source, titre, URL) pour les semaines suivantes — ne les perds pas, mais ne dépasse jamais 2 publications dans la même semaine.

Si aucun sujet valable n'est trouvé cette semaine (queue vide et rien de neuf) : ne publie rien, mets à jour `last_checked` sur toutes les sources vérifiées, termine avec un message bref indiquant qu'il n'y a rien eu de neuf cette semaine (pas la peine d'être alarmiste, c'est normal certaines semaines).

## Étape 3 — Rédiger l'article (politique de citation obligatoire)

**Jamais de copie verbatim d'un article source, quelle que soit sa longueur** — c'est une règle stricte du projet (voir `project_doc.md`, section citation). Rédige un article **original**, dans les mots de Claude, à partir de l'information factuelle trouvée à la source (l'info elle-même n'est pas protégée, sa formulation l'est).

**Depuis le 31/07/2026, les 24 articles du site suivent un gabarit SEO commun. Tout nouvel article doit le suivre aussi, sans exception** — sinon il sera le seul du site à ne pas être structuré pour les moteurs de recherche et les moteurs de réponse (AI Overviews, ChatGPT…).

Le contrat de rédaction complet est dans `/home/claude/seo_briefs/_CONSIGNES.md` : **lis-le en entier avant de rédiger.** Les deux articles de référence, validés par le client, sont dans `/home/claude/new_bodies.py` (`FATIGUE` et `REMBOURSEMENTS`) — c'est le modèle de style, de ton et de densité à imiter.

Résumé du gabarit (le détail est dans `_CONSIGNES.md`) :

- **900 à 1 200 mots** de corps (et non 300-500 comme les articles de lancement d'origine).
- **Pas de `<h1>`** dans le corps. **4 à 6 `<h2>`, tous formulés comme une question d'internaute** (« Pourquoi… ? », « Combien coûte… ? »). Au moins **2 `<h3>`** en énoncés courts.
- Au moins **une liste numérotée `<ol>`** et **un tableau** au format `<div class="table-wrap"><table><thead>…</thead><tbody>…</tbody></table></div>` (2-3 colonnes, 4-6 lignes). Un article purement narratif « vie de la boutique » peut se dispenser du tableau.
- Le **dernier `<h2>` ramène naturellement à la boutique** (venir essayer, faire contrôler sa vue, prendre rendez-vous) sans argumentaire de vente. C'est là que se place l'**ancrage local**, mentionné **une ou deux fois maximum dans tout l'article** (centre Grand Angle, Cœur de Ville, cinéma Le Méliès, mairie de Montreuil…), jamais dans le `meta_title` ni dans un `<h2>`.
- **Signature « l'équipe ACTU EYES »** : jamais de nom de personne, jamais de diplôme, jamais de « je ». On écrit au « nous » quand on parle de la boutique.
- **N'invente aucun chiffre, aucune date, aucune étude, aucun prix.** Seules les données réellement trouvées à la source peuvent être chiffrées. Toute affirmation de fabricant (Essilor, Alcon, Hoya, Novacel, Ray-Ban…) doit être **explicitement attribuée à la marque** (« selon Essilor », « le fabricant annonce »), jamais présentée comme un fait démontré. C'est un site de santé : une imprécision qualitative est toujours préférable à un chiffre inventé.
- **Prudence médicale :** aucun diagnostic, aucune posologie. Renvoyer vers l'ophtalmologiste ou le médecin traitant, et distinguer ce qui relève de l'opticien.

Ton professionnel, chaleureux, honnête : on explique, on ne vend pas. Pas de superlatifs marketing, pas d'emojis, pas de points d'exclamation.

L'encart de sources en fin d'article est **désormais généré automatiquement** par `build.py` à partir du champ `sources` de l'article (voir étape 4). Ne l'écris plus à la main dans le corps : renseigne simplement `sources` avec la source réelle de l'actualité plus une ou deux références institutionnelles cohérentes.

## Étape 4 — Champs de l'article et intégration dans `build.py`

Détermine le champ `category` (slug) selon le thème d'où vient le sujet :
| Thème | `category` (slug) | Image à réutiliser par défaut |
|---|---|---|
| Santé visuelle | `sante-visuelle` | `/images/sante/conseils-fatigue-oculaire.jpg` |
| Santé auditive | `sante-auditive` | `/images/audition/signes-audition.jpg` |
| Mode & tendances | `mode-lunettes` | `/images/actualites/tendances-montures.jpg` |
| Technologies verres | `tech-verres` | `/images/actualites/tech-verres.jpg` |
| Technologies lentilles | `tech-lentilles` | `/images/actualites/tech-lentilles.jpg` |
| Remboursements & démarches | `remboursements` | `/images/audition/accompagnement.jpg` |

**Politique image :** en l'absence de nouvelle photo dédiée fournie par le client, réutilise l'image existante du thème (tableau ci-dessus) avec un `image_alt` réécrit pour rester honnête sur le contenu réel de l'article (l'alt-text doit rester descriptif de l'image elle-même, pas du sujet de l'article s'ils divergent). Ne génère jamais une image de synthèse et ne va jamais chercher une photo de stock externe sans validation du client — ce n'est pas le mandat ici. Si tu juges qu'un sujet mériterait vraiment sa propre photo, tu peux le signaler dans ton message de fin de session, mais publie quand même avec l'image de réutilisation par défaut plutôt que d'attendre.

Ajoute une nouvelle entrée dans la liste `ARTICLES` de `build.py` (à la fin, avant `]`) avec : `slug` (kebab-case unique — vérifie qu'il n'existe pas déjà dans `state.json.used_slugs`), `category`, `title`, `meta_title`, `meta_description`, `excerpt`, `image`/`image_alt` (tableau ci-dessus), `date_display` (date du jour en français, ex. "2 août 2026"), `date_iso` (AAAA-MM-JJ), `body` (variable Python contenant le HTML — définis-la juste avant `ARTICLES` comme les autres `ART_BODY_*`).

**Champs du gabarit SEO — obligatoires depuis le 31/07/2026.** `build.py` sait les rendre ; s'ils sont absents, l'article se génère quand même mais sans encadré « En bref », sans FAQ et sans encart de sources, et il détonnera avec les 24 autres. Copie la forme exacte d'un article existant (par exemple `100-pour-cent-sante-2026`) :

| Champ | Contenu attendu |
|---|---|
| `answer` | **40 à 60 mots**, une ou deux phrases. La réponse directe à la question du titre, affichée dans l'encadré « En bref » juste sous le `<h1>`. Elle doit se suffire à elle-même si un moteur la cite hors contexte. Pas de HTML, sauf `&nbsp;`. |
| `faq` | Liste de **4 ou 5 couples `(question, réponse)`**. Questions telles qu'un client les poserait, différentes des `<h2>`. Réponses de **40 à 60 mots**, autonomes, sans HTML. Rendues en clair dans la page, **volontairement sans balisage `FAQPage`** (voir ci-dessous). |
| `sources` | **2 ou 3 couples `(nom, URL)`**. Uniquement des URL dont l'existence est certaine — de préférence la racine du site (`https://www.ameli.fr/`, `https://www.asnav.org/`, `https://www.inrs.fr/`, `https://www.service-public.fr/`, le site officiel d'une marque citée…) plus l'URL réelle de l'actualité qui a déclenché l'article. **Ne fabrique jamais une URL profonde.** |
| `updated_display` / `updated_iso` | À renseigner **uniquement si tu modifies un article déjà publié** (ex. « 12 août 2026 » / « 2026-08-12 »). Pour un article nouveau, ne les mets pas : `dateModified` reprend alors `date_iso`. |

**Pourquoi pas de balisage `FAQPage` :** Google a déprécié les résultats enrichis FAQ (annonce du 8 mai 2026, documentation retirée le 15 juin 2026). La FAQ reste donc **visible dans le HTML** — elle sert aux lecteurs et aux moteurs de réponse — mais n'est plus balisée en JSON-LD. Le schéma d'article est `BlogPosting`, avec `dateModified`. Ne réintroduis pas de `FAQPage` ni de `HowTo` (déprécié depuis septembre 2023).

**Rappel important (piège déjà rencontré sur ce projet) :** `related_articles()` calcule le bloc "À lire aussi" en prenant d'abord les articles de la **même catégorie** (depuis le maillage du 31/07/2026 — ce n'est plus une rotation chronologique). Ajouter un article change donc les cartes "À lire aussi" affichées sur les autres pages de la même catégorie, déjà en ligne. Après `python3 build.py`, régénère et prévois de redéployer **toutes** les pages articles existantes en plus de la nouvelle, ainsi que `actualites.html` (grille d'index) et `sitemap.xml` (ajouter l'URL avec `<lastmod>` = date du jour).

## Étape 4 bis — Maillage interne (OBLIGATOIRE pour chaque nouvel article)

Depuis le 31/07/2026 le site a un maillage interne complet (voir la section "Maillage interne complet" du doc projet). **Une partie est automatique, une partie ne l'est pas — il faut la faire à la main à chaque publication, sinon le nouvel article sera le seul du site à ne pas être maillé.**

**Automatique, rien à faire :** le bloc "À lire aussi" en bas d'article (`related_articles()`, sélection par catégorie), la carte de l'article dans la grille `actualites.html`, le fil d'Ariane et le JSON-LD.

**À faire à la main dans `build.py`, dans la section `# MAILLAGE INTERNE`, pour chaque nouvel article :**

1. **`INLINE_LINKS`** — ajoute une entrée `"<slug-du-nouvel-article>": [ ... ]` avec **2 à 4 liens contextuels** sous la forme `("expression exacte présente dans le corps", "/cible.html")`, ou `("expression", "/cible.html", 2)` pour viser la 2ᵉ occurrence. Vise en priorité une page de service (`/espace-sante.html`, `/espace-audition.html`, `/nos-conseils.html`, `/marques.html`) ou une ancre précise (`/nos-conseils.html#type-verres`, `/index.html#examen-de-vue`…), et au moins un autre article existant. L'expression doit exister **telle quelle** dans le HTML du corps — vérifie après `python3 build.py` que le lien apparaît bien dans le fichier généré (`grep` sur la page). Les titres, les liens existants, les `<blockquote>` et les `<figcaption>` sont protégés automatiquement, inutile de les éviter à la main.

2. **`GO_FURTHER`** — ajoute une entrée `"<slug>": [(url, titre, description), ...]` avec **exactement 3 entrées**, en respectant le mélange utilisé partout ailleurs : une page de service, une ancre de page, un article existant. Titres courts (une ligne), descriptions d'une phrase. C'est ce qui produit l'encadré "Pour aller plus loin / À lire et à voir sur le site" en fin d'article.

3. **Réciprocité** — ajoute le nouvel article comme cible dans le `GO_FURTHER` (ou l'`INLINE_LINKS`) d'**au moins un article existant** du même thème, sinon le maillage ne va que dans un sens. Ces pages-là devront être redéployées de toute façon.

4. **`PAGE_ARTICLES`** — chaque page de service affiche 3 articles figés dans ce dictionnaire. Si le nouvel article est clairement plus pertinent ou plus récent qu'un des 3 en place pour sa page (`espace-sante.html` / `espace-audition.html` / `nos-conseils.html` / `marques.html` / `notre-histoire.html`), remplace le plus ancien des 3 par le nouveau. Sinon, laisse tel quel — mieux vaut 3 articles pertinents que 3 articles récents. Si tu modifies ce dictionnaire, la page concernée doit être redéployée elle aussi.

**Ne touche pas au CSS pour ça.** Les styles `.go-further`, `.answer-lead`, `.table-wrap`, `.article-faq` et `.article-source-note` existent déjà dans `SHARED_CSS`. Si `SHARED_CSS` n'est pas modifié, `CSS_VERSION` ne bouge pas et `site.css` n'a pas besoin d'être redéployé. Pour connaître la valeur courante, ne te fie pas à une valeur écrite ici : lance `python3 build.py` et lis le `?v=` dans une page générée. Si tu le modifies malgré tout, **il faut impérativement redéployer `site.css` en plus des pages HTML**, sinon les pages référenceront une feuille de style qui n'existe pas sur le serveur.

Contrôle final avant déploiement : sur la page générée du nouvel article, vérifie la présence de `class="answer-lead"` (encadré « En bref »), `class="article-faq"`, `class="article-source-note"`, `class="go-further"`, du texte "À lire aussi", de `"@type": "BlogPosting"`, et de **chacun** des liens contextuels déclarés dans `INLINE_LINKS` — sous la forme exacte `<a href="…">expression</a>`. Un lien qui ne ressort pas signifie que l'expression n'existe plus telle quelle dans le corps : c'est la régression la plus fréquente sur ce site, corrige le corps ou l'expression avant de déployer.

Mets à jour `state.json` : ajoute le slug à `used_slugs`, ajoute une entrée à `published_log` (slug, thème, source, date), retire l'item de `queue` s'il en venait.

## Étape 5 — Déploiement

**Depuis le 02/08/2026, ce n'est plus toi qui déploies.** La veille, la rédaction,
la régénération du site et la mise en ligne sur IONOS sont exécutées **deux fois
par semaine — le lundi ET le jeudi à 07:00 UTC** — par un workflow GitHub Actions
(`.github/workflows/publication.yml` dans le dépôt `Mika020202/actueyes-montreuil-site`),
sur les serveurs de GitHub, sans aucune intervention du client et sans son
ordinateur. C'est l'arbitrage explicite du client : **« 100 % automatique »**.

**Le passage du jeudi (`- cron: '0 7 * * 4'`) a été ajouté le 02/08/2026**, commit
`53e2331`, à la demande verbatim du client : *« je souhaite deux articles par
semaine, qui sont publiés automatiquement sans que je fasse quoi que ce soit et
sans avoir besoin d'etre connecté a ionos, github ou bien meme avoir l'ordinateur
allumé »*. Les deux passages sont **strictement identiques** : le `MODE` se
résout sur `github.event_name == 'schedule'`, pas sur la chaîne cron, donc les
deux tombent sur « Publication hebdomadaire (veille + mise en ligne) ». Le jeudi
n'est **pas** un rattrapage du lundi.

**Pourquoi deux passages ne peuvent pas produire de doublon** (vérifié en lisant
`scripts/veille.py`, 487 lignes, le 02/08/2026) : `veille.py` n'a **aucun
compteur hebdomadaire, aucun verrou de date, aucun plafond par semaine**. Une
exécution publie **au plus un** article. `run_weekly()` construit
`known_slugs = {a["slug"] for a in site.ARTICLES} | set(state["used_slugs"])` et
le passe à la fois dans le prompt **et** dans `validate()`, qui lève une
exception si `slug in known_slugs` (« jamais d'écrasement »). Un second cron est
donc sûr par construction.

**Conséquence assumée, à ne pas « corriger » en silence :** le client a choisi
« deux articles d'actualité » plutôt qu'un second article de fond evergreen. Le
seuil éditorial de `veille.py` reste volontairement strict (*« Dans le doute, tu
ne publies pas. Une semaine sans article est un bon résultat ; un article creux
abîme le site. »* → `{"no_novelty": true}`). **Certaines semaines ne donneront
donc qu'un article, parfois zéro.** Ce n'est pas une panne, c'est le
comportement attendu, et le client en a été informé explicitement avant de
choisir. Si le créneau du jeudi revient vide plusieurs semaines de suite, **le
signaler au client** — ne pas assouplir le seuil de sa propre initiative.

**Ne tente jamais de FTP/SFTP direct depuis le bash de cet environnement — c'est bloqué au niveau réseau (vérifié le 26/07/2026 puis re-vérifié le 02/08/2026 : `curl https://my.ionos.fr/` → HTTP 000). Ce n'est pas spécifique à IONOS, tout le trafic sortant passe par une liste d'autorisation restreinte. Ne cherche pas non plus à pousser sur GitHub depuis cet environnement : la lecture git par HTTPS fonctionne, l'écriture demanderait une clé d'accès personnelle que tu ne dois jamais détenir.**

### Ton rôle est désormais le contrôle qualité, en lecture seule

La tâche planifiée hebdomadaire tire à **`30 8 * * 1`**, soit une heure et demie
après le workflow GitHub, précisément pour vérifier son travail sans jamais
entrer en collision avec lui.

**Interdiction absolue : ne jamais exécuter de veille, ne jamais rédiger
d'article, ne jamais téléverser quoi que ce soit sur IONOS, ne jamais modifier le
dépôt.** Si le workflow a échoué, tu le signales — tu ne le remplaces pas.

Ce que tu fais :

1. Ouvrir la page des exécutions du workflow et lire le résultat de l'exécution du jour (lundi **ou jeudi**). **Les journaux sont lisibles** : naviguer l'onglet authentifié vers la page du job, puis lire `document.body.innerText` (l'endpoint `/actions/runs/<id>/job/<id>/logs` renvoie 404, ne pas l'utiliser).
2. Si un article a été publié, **vérifier son URL en production** avec `fetch(url, {cache:'no-store'})` — vérifier par le contenu réel, jamais seulement par l'interface.
3. Vérifier que le site est intact : `index.html` répond, `site.css?v=<hash>` sert bien la bonne feuille, le nombre de pages n'a pas chuté.
4. Journaliser le résultat et en informer le client en français, simplement.

**Ne jamais demander au client de recopier le contenu d'un secret**, quelle que
soit la nature de la panne. Le diagnostic passe par les journaux et par les
empreintes de forme déjà en place dans la recette (voir `project_doc.md`).

### Le relais est validé (`state.json["relais_github"]["actif"] == true` depuis le 02/08/2026)

Le drapeau est passé à `true` le **02/08/2026 à 22h01 UTC**, après vérification
externe réelle : le fichier `https://www.actueyes-montreuil.fr/_test-relais-github.txt`
a bien été écrit en ligne par le workflow (exécution #9, « Tester la connexion
IONOS »), lu depuis l'extérieur, puis une remise en ligne complète du site a
réussi (#10) et le fichier de test a été supprimé (#11). **La cause des huit
échecs précédents : le secret `IONOS_PASSWORD` contenait le NOM du secret et non
le mot de passe.**

Si une exécution (lundi ou jeudi) échoue malgré tout :

- Constate l'état, informe le client, **n'improvise pas de déploiement de secours**. Le site en place reste intact : les garde-fous du workflow (minimum 30 pages HTML, `index.html` obligatoire, aucun `.py` publié, `mirror` **sans `--delete`**) l'ont protégé pendant les huit essais qui ont échoué.
- Le diagnostic se lit dans les journaux du job. **Ne jamais demander au client le contenu d'un secret** — mais si le diagnostic converge sur « la valeur enregistrée est mauvaise », lui demander de montrer *la façon dont le champ a été rempli* (capture de la page, pas la valeur) : c'est ce qui a résolu le cas du 02/08 après huit essais inutiles.
- Si le client est présent et demande explicitement une mise en ligne manuelle, la voie navigateur IONOS reste utilisable (Webspace Explorer, `https://my.ionos.fr/webhosting/7eaa253a-5a62-4f79-b78c-46ee8bc522dd/webspace-explorer`) — **ne jamais saisir de mot de passe à sa place** ; si la session IONOS a expiré, le prévenir et attendre.

### Fabriquer une archive : cas résiduel seulement

`make_archive.py` reste utile pour **semer ou corriger le dépôt** (par exemple
pousser une nouvelle version de `build.py`), pas pour la publication
hebdomadaire, que le workflow assure seul.

```
cd /home/claude
python3 actualites_watch/make_archive.py <fichiers relatifs à la racine du site>
```

Le script vérifie l'existence de chaque fichier, refuse tout ce qui sort de la
racine du site ou porte une extension non web (le `.py` n'est toléré qu'à la
racine et dans `scripts/`, précisément pour `build.py` et `scripts/veille.py`), et
écrit `actualites_watch/pending/<date>/publication-<date>.zip` en conservant
l'arborescence.

**Le contenu de l'archive se déverse à la racine du dépôt, pas dans un
sous-dossier `public/`** : `build.py` vit à la racine et, comme
`OUT_DIR = os.path.dirname(os.path.abspath(__file__))`, il régénère le site
exactement là où il se trouve.

### Le fichier de recette côté GitHub

Il vit dans le dépôt du client. Sa copie de référence est
`/home/claude/github-relais/publication.yml`. Il ne sait qu'**ajouter ou
remplacer** des fichiers sur IONOS : aucune suppression, jamais. **Ne jamais
ajouter `--delete` au `mirror`** — `.htaccess` n'est pas dans le dépôt, ce serait
destructeur.

Le mode d'emploi client `/home/claude/github-relais/Guide-publication-autonome-Maison-Mikis.html`
est généré par `build_guide.py` à partir du YAML : **il est aujourd'hui largement
périmé**, toute évolution de la recette impose de relancer ce script.

## Étape 6 — Fin de session et notification

Cette tâche planifiée envoie un email au client à la fin de chaque exécution "notable". Le texte final de ta session EST le contenu qui sera résumé dans cette notification — écris-le donc clairement, en français, à destination du client (pas un rapport technique). Selon le cas :
- **Article publié :** dis quel article, sur quel thème, à partir de quelle source, et donne le lien direct de la page en ligne.
- **Publication automatique réussie :** dis quel article, sur quel thème, à partir de quelle source, et donne le lien direct de la page en ligne, vérifiée. Rappelle qu'il n'y a rien à faire de son côté.
- **Le workflow a échoué :** explique en une phrase simple ce qui a bloqué et ce qu'il reste à faire, en précisant que **le site en ligne n'a pas été touché** (les garde-fous l'en empêchent). Ne demande jamais le contenu d'un secret.
- **Rien de neuf cette semaine :** un message bref, pas d'inquiétude à avoir.
- **Baseline (premier passage) :** explique que la veille est maintenant active.

Termine toujours par la mise à jour de `state.json` (et régénère `project_doc.md` / le doc du Projet Claude avec une brève ligne dans le journal si un article a été publié — pas besoin d'une section complète à chaque fois, une ligne dans une section "Articles automatiques publiés" suffit, à créer si elle n'existe pas encore).

## Incident du 03/08/2026 — le déclencheur programmé n'a pas démarré

Premier lundi après la mise en place des deux crons (`0 7 * * 1` et `0 7 * * 4`,
commit `53e2331` poussé le 02/08 à 22h32 UTC). À 09h31 UTC le 03/08, **aucun
article n'avait été publié et surtout aucune exécution programmée n'avait eu
lieu** : `https://github.com/Mika020202/actueyes-montreuil-site/actions?query=event%3Aschedule`
affichait « 0 workflow run results », et les onze exécutions listées étaient
toutes des `workflow_dispatch` manuels. Le journal du dépôt le confirmait :
dernier commit `53e2331`, pas de « Publication automatique du 03/08 ».

**Ce n'était donc PAS le seuil éditorial.** Vérifications faites : la recette est
bien sur `main`, les deux lignes `cron` sont présentes dans le fichier déployé,
la branche par défaut est `main`, le dépôt est actif, les lancements manuels
fonctionnent. Cause probable : retard ou saut du tout premier passage côté
GitHub — comportement documenté sur l'infrastructure mutualisée, où les
`schedule` peuvent être retardés en période de charge, en particulier au début
d'une heure ronde.

**Décision du client (verbatim) :** *« ON ATTEND JEUDI MATIN JE PENSE QUE C4EST
MIEUX »*. Aucun lancement manuel n'a été fait : le passage du jeudi 06/08 sert de
test propre du mécanisme. S'il démarre, l'incident est classé comme un raté de
démarrage. **S'il ne démarre pas non plus, le problème est structurel** et il
faudra changer d'approche plutôt que de réessayer à l'identique.

**Leçon durable, à ne jamais oublier :** « aucun article ce matin » a DEUX causes
possibles, radicalement différentes — le seuil éditorial n'a rien laissé passer
(normal, attendu), ou le déclencheur n'a pas démarré (anomalie). **Ne jamais
conclure « c'est normal » sans avoir consulté le filtre `event:schedule`.** La
tâche de contrôle `trig_01ERuncHqs3tyKPZWHCpgxdX` a été réécrite le 03/08 pour
imposer cette vérification comme étape décisive avant tout rapport au client.

## Limites connues à ne pas essayer de contourner seul

- Pas de FTP/SFTP possible depuis cet environnement (réseau bloqué), et pas d'écriture possible vers GitHub depuis le conteneur (il faudrait une clé d'accès personnelle, interdite). La publication est assurée par GitHub Actions ; toute modification du dépôt passe par le navigateur authentifié du client — voir étape 5.
- Certaines sources (LCS, potentiellement SNOF/FNOF) peuvent être peu fiables à scraper — ne pas y passer un temps disproportionné, les ignorer temporairement si ça bloque est acceptable.
- Ne jamais dépasser 2 publications dans la même semaine, même si beaucoup de nouveautés sont détectées — mets le surplus en `queue`.
- Ne jamais publier une traduction non adaptée d'une source anglophone — toujours réécrire en français naturel.
