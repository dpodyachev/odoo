T = {
    "meta_title": 'Odoo : architecture, développement et migration pour la région DACH – Goldberg Odoo Services',
    "meta_desc": 'Odoo pour les entreprises en Allemagne, Autriche et Suisse : architecture, développement de modules, intégrations (DATEV, facture électronique, Shopware, JTL, DHL, DPD), migrations et performance. Prix fixes, à distance depuis Stuttgart.',
    "nav": {"services": "Services", "dach": "DATEV & e-facture", "bot": "Supervision", "prices": "Tarifs",
            "about": "À propos", "blog": 'Blog & guides', "contact": "Contact"},
    "kicker": 'Architecture Odoo · Développement · Intégration · Migration · Performance',
    "h1": 'Un Odoo <span>qui fonctionne, tout simplement.</span>',
    "sub": "Architecture, développement, intégrations, migrations et performance pour Odoo Community et Enterprise – à distance depuis Stuttgart pour l'Allemagne, l'Autriche et la Suisse, à prix fixes et avec un interlocuteur unique.",
    "cta_book": "Prendre rendez-vous – 30 min offertes",
    "badges": ["Prix fixes, sans surprise", "Supervision 24 h/24", "Mises à jour sans interruption", "Odoo 14 à 19",
               "Conforme RGPD avec contrat de sous-traitance"],
    "hero_card": ["Odoo accessible", "Sauvegarde réussie", "Disque – alerte", "Erreurs dans le journal aujourd'hui",
                  "Votre serveur surveillé jour et nuit"],
    "services_title": "Services",
    "services_intro": "De l'architecture aux évolutions – le travail technique sur votre Odoo, sans les frais d'une agence. Licences : directement chez Odoo S.A. · Support utilisateurs : via des partenaires.",
    "services": [('install', 'Architecture et mise en place', 'Un concept pour les modules, les flux de données et les serveurs – puis la réalisation : Odoo sur votre serveur (contrat à votre nom), Docker, PostgreSQL, SSL, sauvegardes. Documenté proprement et remis entre vos mains.'), ('support', 'Développement et adaptation', 'Modules et extensions sur mesure en Python et OWL, rapports, automatisations – versionnés dans Git, testés sur une copie, avec retour arrière.'), ('fix', 'Analyse des pannes', 'Odoo ne démarre pas, est lent, une mise à jour échoue, les e-mails ne partent pas ? Analyse des journaux et de la base, cause claire, solution durable.'), ('update', 'Mises à jour et migration', "Les mises à jour comme projet planifié : d'abord sur une copie de test, puis en production avec retour arrière. Changements de version (p. ex. 14 → 17), adaptation des modules sur mesure comprise."), ('integration', 'Intégration et interfaces', 'DATEV, facture électronique, boutiques en ligne, transporteurs, banques et interfaces sur mesure (REST, XML-RPC) – conçues, développées et testées.'), ('server', 'Performance et sécurité', 'Réglage de PostgreSQL et des workers, tests de charge, analyse des requêtes lentes, sécurisation des serveurs et des accès – mesuré avant et après chaque mesure.')],
    "dach_title": "Ce qu'Odoo doit savoir faire en Allemagne, en Autriche et en Suisse",
    "dach_intro": "Une installation standard suffit rarement ici. Je mets ces points en place pour vous – et les tiens à jour.",
    "dach": [
        ('Comptabilité', 'Plans comptables, clôture & DATEV', 'La comptabilité allemande dans Odoo – configurée pour que votre conseiller fiscal reprenne sans retouches.', ['Plans comptables SKR03 / SKR04, codes et taux de TVA', 'Bilan et compte de résultat selon le HGB ; BWA via DATEV ou en rapport dédié', 'Export DATEV (EXTF) avec pièces jointes, export de test avant la clôture mensuelle']),
        ('Obligatoire depuis 2025', 'Facture électronique : XRechnung & ZUGFeRD', "Depuis le 1er janvier 2025, les entreprises en Allemagne doivent pouvoir recevoir des factures électroniques ; à partir de 2027/2028 (selon le chiffre d'affaires), elles devront aussi en émettre en B2B. Odoo le permet – s'il est bien configuré.", ['ZUGFeRD / Factur-X (PDF avec XML) et XRechnung (UBL/CII)', 'Leitweg-ID pour les administrations, contrôle par validateur', 'Réception et saisie automatique des factures électroniques entrantes']),
        ('Impôts & paiements', 'ELSTER, SEPA et prélèvement', 'De la déclaration de TVA au lot de paiements – moins de travail manuel en comptabilité.', ["Déclaration de TVA (USt-VA) depuis Odoo, transmission à ELSTER (selon l'édition par module ou via DATEV)", 'Virements SEPA et prélèvements SEPA avec gestion des mandats', 'GiroCode (QR EPC) sur les factures, relevés bancaires au format CAMT']),
        ('GoBD', 'Tenue des comptes conforme aux GoBD', 'Exploiter Odoo de façon auditable : écritures inaltérables et traçables, données exportables pour le contrôle fiscal.', ["Verrouillage des écritures validées, dates de clôture, piste d'audit", 'Export des données pour le contrôle fiscal (accès Z3)', 'Durées de conservation, aide à la documentation des procédures']),
        ('RGPD', "Hébergement en Allemagne ou dans l'UE", 'Vos données restent en Europe – sur le serveur de votre choix, sécurisé et documenté.', ["Serveur et base de données en Allemagne ou dans l'UE (p. ex. Hetzner, IONOS)", "Sauvegardes chiffrées dans l'UE, restaurations testées", 'Contrat de sous-traitance (art. 28 RGPD), accès limités au nécessaire']),
        ('Commerce', 'E-commerce & logistique', 'Commandes, stocks et expéditions circulent automatiquement entre votre boutique, Odoo et le transporteur.', ['Shopware, JTL-Wawi, WooCommerce', 'DHL, DPD, GLS : étiquettes et suivi', 'Synchronisation des prix, stocks et factures']),
        ('AT · CH', 'Autriche & Suisse', 'Les exigences locales, sans détour.', ["Autriche : factures électroniques à l'État fédéral (ebInterface / PEPPOL)", 'Suisse : QR-facture, TVA (MWST), CHF et EUR en parallèle', 'Documents multilingues (DE / FR / EN)']),
    ],
    "dach_note": "Remarque : aucun logiciel n'est « certifié GoBD » en soi – ce qui compte, c'est la configuration, les processus et la documentation des procédures. Je m'occupe de la partie technique, en accord avec votre conseiller fiscal.",
    "impl_title": "Mise en place d'Odoo étape par étape",
    "impl_intro": "Le projet commence par une analyse approfondie de votre activité et la conception de l'architecture, passe par le développement, les tests et la formation de votre équipe, et se termine par un démarrage progressif et un suivi continu.",
    "impl": [
        ('Lancement & analyse', 'Cartographier les processus, vérifier les exigences de la comptabilité allemande, fixer objectifs et périmètre.'),
        ('Concept & architecture', 'Modules, interfaces, reprise de données et serveurs – un plan clair à prix fixe ou avec budget.'),
        ('Installation & localisation', 'Installation et localisation allemande : TVA, SKR03/04, XRechnung/ZUGFeRD, DATEV et ELSTER.'),
        ('Ateliers & développement', 'Adapter CRM, stock, production, ventes et comptabilité à votre entreprise – développements là où le standard ne suffit pas.'),
        ('Tests', 'Tests sur des cas réels : circuit des documents, écritures correctes, factures, interfaces.'),
        ('Formation', 'Formation des utilisateurs et utilisateurs clés, guides courts pour le quotidien.'),
        ('Démarrage & suivi', 'Mise en production progressive, puis supervision, mises à jour en tant que projet et évolutions.'),
    ],
    "yearly": 'Paiement annuel : {p} / an – 2 mois offerts',
    "bot_title": "Bot de supervision : votre Odoo d'un coup d'œil – directement dans Telegram",
    "bot_intro": "Chaque forfait de suivi technique inclut mon bot de supervision. Il vérifie votre serveur en continu et signale les problèmes avant que vos équipes ne les remarquent. Sur demande, je l'installe aussi comme instance dédiée pour votre équipe.",
    "bot_points": [
        ("Disponibilité :", "Odoo, base de données, serveur web, certificat SSL, espace disque."),
        ("Erreurs :", "journaux Odoo et nginx résumés – l'essentiel, sans bruit."),
        ("Tâches de fond :", "actions planifiées (cron) et files d'attente, tâches bloquées."),
        ("Sauvegardes :", "chaque nuit – avec contrôle qu'elles sont réellement restaurables."),
        ("Mises à jour en un clic :", "récupérer le code → mettre à jour les modules → redémarrer, avec retour à l'état précédent."),
        ('Utilisateurs & activité :', "/users montre qui travaille dans Odoo aujourd'hui, qui est en ligne et qui est le plus actif – une base pour les licences et le ménage des anciens comptes."),
        ('Analyse IA avec /analyze :', 'logs, temps de réponse et charge serveur sont résumés, une IA explique la cause en clair et propose la solution. Mots de passe et clés sont masqués au préalable ; utilisée seulement avec votre accord.'),
    ],
    "bot_note": "Données d'exemple – noms et adresses masqués.",
    "bot_online": "bot · en ligne",
    "chat_caption": "Le bot au quotidien (exemple).",
    "chat": [
        {"who": "me", "html": "/status"},
        {"who": "bot", "html": "<b>PROD</b> · ▒▒▒▒▒.de<br>✅ Odoo actif, 200 OK en 0,21 s<br>✅ PostgreSQL · 2,4 Go<br>"
                               "⚠️ Disque 86 % (12 Go libres)<br>✅ SSL valide jusqu'au 23/02<br>✅ Sauvegarde 03:00 · 1,1 Go"},
        {"who": "me", "html": "/errors"},
        {"who": "bot", "html": "<b>Erreurs aujourd'hui : 2</b><br>• sale.order: Expected singleton (2×)<br>"
                               "<i>Conflits de sérialisation masqués : 14</i>"},
        {"who": "me", "html": "/update"},
        {"who": "bot", "html": "<b>/update PROD</b> · ▒▒▒▒<br>Modules modifiés (3) : sale_custom, stock_report, l10n_de_datev",
         "buttons": ["▶️ Mettre à jour 3 modules", "Annuler"]},
        {"who": "bot", "html": "✅ Terminé en 1 min 40 s, 0 erreur<br>Redémarrer Odoo pour charger le nouveau code.",
         "buttons": ["🔄 Redémarrer Odoo"]},
    ],
    "process_title": "Comment nous travaillons ensemble",
    "process": [
        ("Premier échange", "30 minutes en visio ou sur Telegram – gratuit. Vous m'expliquez ce qui coince."),
        ("Bilan ou devis", "J'examine votre système et vous propose un prix fixe ou une formule adaptée."),
        ("Mise en œuvre", "D'abord sur une copie de test, puis en production – au moment qui vous convient."),
        ('Suivi technique', 'Analyse régulière, mises à jour en tant que projet testé et évolutions – avec rapport et coûts mensuels prévisibles.'),
    ],
    "prices_title": "Tarifs",
    "prices_intro": "Transparents et prévisibles. Petites tâches au temps passé, projets à prix fixe après un bilan.",
    "offer": {"title": 'Offre de découverte', "text": 'Nouveaux clients : les {h} premières heures à {p}/h au lieu de 65 € – valable jusqu’au {d}. Idéal pour faire connaissance : petite correction, mise à jour ou bilan.', "cta": 'En profiter', "date": '%d/%m/%Y'},
    "per_month": "/ mois",
    "incl_hours": "{h} h de travail incluses",
    "reaction": {"2": "Réponse sous 2 jours ouvrés", "1": "Réponse le jour ouvré suivant",
                 "4h": "Réponse sous 4 h (lun–ven 9 h–18 h)"},
    "plans": {'basic': {'name': 'Basic', 'desc': 'Surveillance technique pour les petits systèmes.', 'features': ['Bot de supervision et analyse mensuelle avec rapport', 'Mises à jour de sécurité en tant que projet testé', 'Concept de sauvegarde avec test de restauration']}, 'business': {'name': 'Business', 'desc': 'Surveillance et évolutions pour les entreprises qui travaillent chaque jour avec Odoo.', 'features': ['Tout le contenu de Basic', "Adaptations et modules sur le contingent d'heures", 'Rapport trimestriel : performance, base de données, risques']}, 'premium': {'name': 'Premium', 'desc': 'Pour les systèmes critiques.', 'features': ['Tout le contenu de Business', "Revue d'architecture et feuille de route chaque trimestre", 'Test de charge annuel avec rapport']}},
    "plans_note": 'Heures supplémentaires : 65 € / h. Résiliable chaque mois. Travaux le week-end sur accord : 95 € / h. Licences : directement chez Odoo S.A. · Support utilisateurs : via des partenaires.',
    "table_title": "Prestations à l'unité",
    "table_head": ["Prestation", "Prix"],
    "units": {"h": "/ h", "fix": "prix fixe", "from": "à partir de", "pct": 'du projet'},
    "price_names": {
        "hourly_support": ('Développement et travaux techniques', 'adaptations, analyses, travaux planifiés – facturés par tranches de 15 minutes'),
        "hourly_urgent": ('Analyse de panne urgente', "incident ou interruption – analyse et correction dans l'urgence, week-end compris"),
        "healthcheck": ("Bilan de santé Odoo", "serveur, sauvegardes, modules, performances, sécurité – rapport écrit et plan d'action"),
        "diagnosis": ("Premier diagnostic d'incident", "jusqu'à 2 h de recherche, ensuite au temps passé (95 € / h)"),
        "install": ('Mise en place selon concept', 'Odoo + PostgreSQL sous Docker sur votre serveur, SSL, sauvegardes, e-mail, supervision'),
        "module_update": ("Mise à jour de modules avec retour arrière", "git pull, mise à jour sur copie de test, puis en production"),
        "migration": ("Migration de version", "p. ex. Odoo 14 → 17, avec essai sur une copie"),
        "datev": ("Export DATEV", "configuration, correspondance des comptes, export de test avec votre cabinet"),
        "einvoice": ("Facture électronique (XRechnung / ZUGFeRD)", "émission et réception, validation, Leitweg-ID"),
        "shop": ("Connexion boutique", "Shopware, JTL-Wawi, WooCommerce"),
        "shipping": ("Connexion transporteur", "DHL, DPD, GLS – étiquettes, suivi"),
        "qrbill": ("QR-facture suisse", "QR-IBAN, références, TVA"),
        "monitoring": ('Mise en place Grafana & Prometheus', 'Exporters serveur, PostgreSQL, Docker, nginx ; tableaux de bord et alertes'),
        "loadtest": ('Test de charge avec Locust', 'scénarios, copie de test, mesures, rapport avec recommandations'),
        "replica": ('Réplique PostgreSQL en lecture pour Odoo 18/19', 'réplication en streaming, db_replica_host, mesures avec/sans réplique, revue des modules maison'),
        "bot": ("Bot de supervision pour votre équipe", "votre propre instance, configurée pour votre serveur"),
    },
    "vat_note": "Tous les prix en EUR. Selon le § 19 UStG (régime des petites entreprises), aucune TVA n'est facturée. Facturation mensuelle au temps passé par tranche de 15 min ou au prix fixe convenu.",
    "kleinunternehmer": "Petite entreprise selon le § 19 UStG – TVA non applicable.",
    "cases_title": "Cas typiques à prix fixe",
    "cases": [
        ("« Odoo est en panne après une mise à jour du serveur »",
         "Premier diagnostic, cause (paquet Python, base de données, proxy), correction et court rapport pour éviter la récidive.",
         "en général 190 € + 1–2 h × 95 €"),
        ("« Il nous faut des e-factures avant la fin de l'année »",
         "Mise en place de ZUGFeRD/XRechnung, contrôle des données de base, validation de factures de test, formation de l'équipe.",
         "à partir de 900 € prix fixe"),
        ("« Notre Odoo tourne – mais personne ne s'en occupe »", 'Bilan de santé, puis suivi technique dans la formule Business : supervision, mises à jour en tant que projet, rapport trimestriel.', '490 € une fois + 690 € / mois'),
    ],
    "about_job": "Développeur et consultant Odoo",
    "exp_title": "Expérience : de la production à l'ERP",
    "exp_alt": "Système d'inspection par rayons X GE Phoenix PCBA Analyzer 160 pour cartes électroniques",
    "exp_caption": "Auparavant : production électronique – contrôle des cartes électroniques par rayons X (GE Phoenix PCBA Analyzer 160). C'est pourquoi je connais la production, le contrôle qualité et l'entrepôt pas seulement par la documentation d'Odoo.",
    "about_title": "À propos",
    "about": [
        "Je développe et exploite des systèmes Odoo depuis de nombreuses années – de l'architecture aux modules sur mesure, jusqu'aux systèmes de production comptant des centaines de modules.",
        "Je travaille sur des projets Odoo pour des entreprises du commerce, de la logistique, des services et des centres d'appels : architecture, développement, intégrations, migrations et performance. J'habite à Stuttgart et je travaille à distance pour des clients dans toute la région DACH – rendez-vous sur place dans la région de Stuttgart sur demande.",
        "Pour les projets plus importants, je m'appuie sur une équipe de développement rodée : développeurs Odoo (Python, OWL), analystes et testeurs. Nouveaux modules, interfaces et migrations suivent un processus clair, du besoin aux tests – et je reste votre interlocuteur unique.",
        "Vous avez un interlocuteur unique qui connaît votre système – pas de file de tickets, pas de transferts.",
    ],
    "about_facts": ['Diplôme universitaire (spécialiste) : automatisation des processus technologiques et de la production, électromécanique (université d’État, Ukraine ; anabin H+)', "Odoo 14 – 19, Community et Enterprise", "Linux · Docker · PostgreSQL · nginx",
                    "Python, OWL, XML-RPC / REST", "Déploiements Git avec retour arrière",
                    "Langues : ukrainien, russe (langue maternelle) · anglais (B2) · grec, allemand (notions)",
                    'Équipe dédiée : développement, analyse, QA'],
    "faq_title": "Questions fréquentes",
    "faq": [
        ("Community ou Enterprise ?", "Les deux. Je vous aide aussi à choisir – Community avec quelques modules OCA suffit souvent."),
        ("Travaillez-vous uniquement à distance ?", "Oui, via SSH ou VPN – en toute sécurité et sans frais de déplacement. Sur place dans la région de Stuttgart."),
        ("Comment l'accès à nos données est-il encadré ?",
         "Par un contrat de sous-traitance (RGPD, art. 28). Accès limité au strict nécessaire, et dans le temps sur demande."),
        ("Et si une mise à jour se passe mal ?",
         "Les mises à jour passent d'abord sur une copie. En production, l'état précédent du code est sauvegardé – le retour arrière prend quelques minutes."),
        ('Nous avons déjà un partenaire Odoo.', "Aucun problème – je prends volontiers en charge l'architecture, le développement, la performance et les serveurs, pendant que votre partenaire s'occupe des processus métier."),
        ("Vendez-vous des licences ou de l'hébergement ?", "Non. Vous achetez les licences directement chez Odoo S.A. ; le serveur est à votre nom chez l'hébergeur de votre choix (p. ex. Hetzner). Le support utilisateurs au quotidien est assuré par des partenaires – je vous indique volontiers des contacts."),
        ("Comment se passe la facturation ?", "Chaque mois au temps passé par tranche de 15 min ou au prix fixe convenu, par virement."),
    ],
    "contact_title": "Parlons-en",
    "contact_text": "Indiquez-moi brièvement votre version d'Odoo et ce qui coince – je réponds en général le jour ouvré même.",
    "contact_note": "Pas de formulaire, pas de cookies – simplement Telegram, e-mail ou rendez-vous.",
    "footer_tag": "Architecture, développement, intégration, migration et performance Odoo pour l'Allemagne, l'Autriche et la Suisse.",
    "footer_note": "Ce site n'utilise ni cookies ni suivi.",
    "impressum": "Mentions légales",
    "privacy": "Confidentialité",
    "legal_note": "Traduction pour information. Seule la version allemande fait foi :",
    "impressum_page": {
        "title": "Mentions légales (Impressum)",
        "html": """
<h2>Informations selon le § 5 DDG</h2>
<p>{name}<br>{street}<br>{city}<br>{country}</p>
<h2>Contact</h2>
<p>E-mail : {email}<br>Telegram : {telegram}<br>Tél. : {phone}<br>WhatsApp : {whatsapp}</p>
<h2>TVA</h2>
<p>{vat}</p>
<h2>Responsable du contenu selon le § 18 al. 2 MStV</h2>
<p>{name}, adresse ci-dessus</p>
<h2>Règlement des litiges de consommation</h2>
<p>Je ne suis ni disposé ni tenu de participer à une procédure de règlement des litiges devant un organisme de médiation
de la consommation. Mes services s'adressent aux entreprises.</p>
<h2>Responsabilité pour les liens</h2>
<p>Ce site contient des liens vers des sites tiers (p. ex. Telegram, Cal.com) dont je ne contrôle pas le contenu.
Le fournisseur concerné en est responsable.</p>
""",
    },
    "privacy_page": {
        "title": "Politique de confidentialité",
        "html": """
<h2>1. Responsable du traitement</h2>
<p>{name}, {street}, {city}, {country}<br>E-mail : {email}</p>
<h2>2. En bref</h2>
<p>Ce site <b>ne dépose aucun cookie</b>, n'utilise <b>aucun suivi</b>, aucun outil d'analyse, aucun pixel publicitaire,
aucun contenu tiers intégré ni police chargée de l'extérieur. Il n'y a pas de formulaire de contact.
Le stockage local du navigateur (Local Storage) n'est pas utilisé non plus.</p>
<h2>3. Hébergement et journaux du serveur</h2>
<p>Le site est servi via Cloudflare Pages (Cloudflare, Inc., 101 Townsend St, San Francisco, CA 94107, USA).
Lors de votre visite, Cloudflare traite des données techniquement nécessaires (adresse IP, date et heure, page demandée,
type de navigateur) pour délivrer le site et le protéger contre les attaques. Base légale : art. 6, par. 1, f) RGPD
(intérêt légitime à un fonctionnement sûr et stable). Cloudflare est certifié selon le EU-US Data Privacy Framework ;
un contrat de sous-traitance avec clauses contractuelles types est en place. Je n'analyse pas moi-même ces données.</p>
<h2>4. Contact par e-mail ou Telegram</h2>
<p>Si vous m'écrivez, je traite vos données (nom, coordonnées, contenu du message) pour répondre à votre demande
(art. 6, par. 1, b) RGPD – mesures précontractuelles, sinon f)). Les données sont supprimées une fois la demande traitée,
sauf obligation légale de conservation. Les e-mails passent par Google Gmail (Google Ireland Ltd., Dublin).
Telegram est exploité par Telegram Messenger Inc. (Dubaï, EAU) ; son utilisation est facultative et soumise à la politique
de confidentialité de Telegram – vous pouvez toujours écrire par e-mail.</p>
<h2>5. Prise de rendez-vous (Cal.com)</h2>
<p>Le bouton « Prendre rendez-vous » mène à Cal.com (Cal.com, Inc., USA). Ce n'est que si vous réservez un créneau que Cal.com
traite vos données (nom, e-mail, horaire) selon sa propre politique de confidentialité. Base légale : art. 6, par. 1, b) RGPD.</p>
<h2>6. Vos droits</h2>
<p>Vous disposez d'un droit d'accès (art. 15), de rectification (art. 16), d'effacement (art. 17), de limitation du traitement
(art. 18), de portabilité (art. 20) et d'opposition (art. 21 RGPD). Un simple e-mail suffit.</p>
<h2>7. Droit de réclamation</h2>
<p>Vous pouvez introduire une réclamation auprès d'une autorité de contrôle, p. ex. le délégué à la protection des données et à
la liberté d'information du Bade-Wurtemberg, Lautenschlagerstraße 20, 70173 Stuttgart, Allemagne.</p>
<h2>8. Sous-traitance pour les clients</h2>
<p>Si j'accède à des données personnelles de votre entreprise dans le cadre du support Odoo, nous concluons un contrat de
sous-traitance distinct (art. 28 RGPD).</p>
<p class="small">Mise à jour : novembre 2026</p>
""",
    },
    "mon_title": 'Supervision avec Grafana & Prometheus',
    "mon_intro": 'Quand les alertes Telegram ne suffisent plus : tableaux de bord avec historique, métriques et alertes pour votre Odoo – sur votre propre serveur, vos données restent chez vous.',
    "mon": [
        ('node_exporter', 'Serveur', "CPU, mémoire, disques, réseau et charge – avec des semaines d'historique."),
        ('postgres_exporter', 'PostgreSQL', 'Connexions, requêtes lentes, verrous, taille de la base, réplication.'),
        ('cAdvisor', 'Docker', 'Ressources par conteneur : Odoo, workers, base de données, services annexes.'),
        ('blackbox · nginx', 'Disponibilité', "Temps de réponse vus de l'extérieur, erreurs HTTP, expiration des certificats SSL."),
        ('Odoo · Loki', 'Application', "Workers, durée des crons, files d'attente (queue_job) et erreurs des logs."),
        ('Alertmanager', 'Alertes', 'Notifications par Telegram ou e-mail – avec des seuils adaptés à votre activité.'),
    ],
    "mon_note": 'Fonctionne avec le bot de supervision ou seul. Mise en place à prix fixe, analyse continue dans un forfait de suivi technique.',
    "lt_title": 'Tests de charge avec Locust',
    "lt_intro": 'Votre Odoo tient-il 50, 100 ou 300 utilisateurs simultanés – et que se passe-t-il à la clôture du mois ? Je simule des processus réels avec Locust, je mesure les limites et je montre où ça bloque. Toujours sur une copie de test, jamais en production.',
    "lt_types_title": 'Quels tests – et ce qu’ils montrent',
    "lt_types": [('Test de performance', 'Terme général : à quelle vitesse et avec quelle stabilité Odoo répond dans des conditions définies – la performance réelle plutôt que des estimations.'), ('Test de charge', 'Le nombre d’utilisateurs attendu au quotidien : les objectifs sont-ils tenus, p. ex. p95 sous 1 seconde ?'), ('Test de stress', 'Au-delà de la limite : où le système casse-t-il, comment, et se rétablit-il seul ?'), ('Pic de charge (spike)', 'Afflux soudain : clôture mensuelle, newsletter, journée promo – Odoo encaisse-t-il le saut ?'), ('Test d’endurance (soak)', 'Charge normale pendant des heures : fuites mémoire, files qui grossissent, redémarrages de workers.'), ('Test de volume', 'Gros volumes de données : millions d’écritures, grands entrepôts, longues listes et rapports.'), ('Test de scalabilité', 'Ce qu’apportent vraiment plus de workers, de CPU, de RAM ou un second serveur – mesuré, pas estimé.')],
    "lt": [('locust', 'Scénarios selon vos processus', 'Les commerciaux créent des devis, l’entrepôt valide des livraisons, la comptabilité émet des factures, les clients commandent en ligne – pondérés, avec des pauses réalistes.'), ('JSON-RPC · HTTP', 'De vrais appels Odoo', 'Connexion, recherche, listes et formulaires, création, confirmation, rapports PDF – via la même interface que le navigateur. Données de test générées automatiquement.'), ('ramp-up', 'Paliers & pics de charge', 'Progressivement de 10 à 50, 100, 300 utilisateurs ; charge continue sur des heures (fuites mémoire) et pics comme la clôture ou les jours de promotion.'), ('p95 · p99', 'Indicateurs mesurables', 'Temps de réponse (médiane, p95, p99), taux d’erreurs et requêtes par seconde – en direct dans Locust et dans Grafana, à côté du CPU, de la RAM et de PostgreSQL.'), ('workers · pg', 'Trouver les goulots', 'Nombre de workers et limites mémoire, requêtes SQL lentes et index manquants, verrous, connexions (pgbouncer), nginx, modules et champs calculés lents.'), ('report', 'Rapport avant/après', 'Combien d’utilisateurs le système supporte aujourd’hui, où est la limite, ce que chaque mesure apporte – à chaque fois remesuré. Vous gardez les scénarios pour les futures mises à jour.')],
    "lt_code": 'Exemple de scénario (locustfile.py)',
    "lt_note": 'Idéal avant la mise en production, avant une migration de version ou quand Odoo est « parfois lent ». Prix fixe après un court échange sur les scénarios.',
    "lt_shots": {"caps": ['Interface web Locust : statistiques par requête (médiane, 95 %, 99 %, erreurs)', 'Graphiques : requêtes/s, temps de réponse p50/p95 et nombre d’utilisateurs en montée jusqu’à 80'], "note": 'Un vrai test Locust (80 utilisateurs virtuels : ventes, entrepôt, comptabilité) sur un environnement de démo – aucune donnée client. Cliquez pour agrandir.', "full": 'Plein écran'},
    "slides_title": 'Exemples de projets',
    "slides_intro": 'Extraits de réalisations réelles – données clients rendues méconnaissables.',
    "slide_alt": 'Exemple {n}',
    "slides_prev": 'Exemple précédent',
    "slides_next": 'Exemple suivant',
    "slides_goto": "Afficher l'exemple {n}",
    "theme_toggle": 'Thème clair / sombre',
    "echeck": {'hero_link': 'Check e-facture gratuit pour Odoo – 2 minutes', 'title': 'Check e-facture pour Odoo', 'kicker': 'Gratuit · 5 questions · 2 minutes', 'intro': 'Votre Odoo est-il prêt pour la facture électronique obligatoire en Allemagne ? Répondez à cinq questions – vous voyez tout de suite où vous en êtes et quoi faire.', 'privacy': "Vos réponses restent dans votre navigateur. Rien n'est enregistré ni transmis – sauf si vous m'envoyez vous-même le résultat.", 'answers': ['Oui', 'En partie', 'Non / je ne sais pas'], 'q': [('Réception', 'Pouvez-vous recevoir des factures XRechnung et ZUGFeRD et lire leurs données XML – pas seulement afficher le PDF ?', 'Obligatoire pour toutes les entreprises depuis le 1er janvier 2025.', 'Mettre en place la réception : boîte mail ou import dans Odoo, saisie automatique du XML en facture fournisseur.'), ('Émission', 'Votre Odoo produit-il les factures clients en ZUGFeRD/Factur-X ou XRechnung ?', 'Obligatoire dès le 1er janvier 2027 au-delà de 800 000 € de CA, dès le 1er janvier 2028 pour tous (B2B).', "Définir le format par client (ZUGFeRD pour les entreprises, XRechnung pour les administrations) et l'activer dans la mise en page."), ('Données de base', 'Les n° de TVA, adresses complètes et – pour les administrations – Leitweg-ID ou référence acheteur sont-ils renseignés ?', 'Les champs obligatoires manquants sont la première cause de rejet des factures électroniques.', "Vérifier et nettoyer les données ; configurer Odoo pour repérer les manques avant l'envoi."), ('Validation', "Vos factures électroniques sont-elles validées avant l'envoi (p. ex. avec le validateur KoSIT) ?", "Un PDF correct à l'œil peut être une facture électronique invalide.", 'Valider des factures de test et corriger les erreurs typiques dans Odoo (catégories de TVA, unités, arrondis).'), ('Archivage', "Les factures électroniques reçues et émises sont-elles conservées en XML d'origine, conformément aux GoBD ?", "Pour une e-facture, l'original est le XML – pas le PDF. Conservation : 8 ans.", 'Archiver les XML de façon inaltérable dans Odoo, garantir sauvegardes et export pour le contrôle fiscal.')], 'submit': 'Voir le résultat', 'need_all': 'Merci de répondre aux cinq questions.', 'score': 'Votre résultat : {s} sur 10 points', 'levels': [('Action urgente', "Votre Odoo n'est pas encore prêt pour la facture électronique. Bonne nouvelle : bien configuré, c'est réglé en quelques jours."), ('Bonne base – avec des lacunes', "Une partie fonctionne déjà, mais les points ouverts peuvent entraîner des rejets ou des soucis lors d'un contrôle fiscal."), ('Très bien préparé', "Votre Odoo est en grande partie prêt. Un regard extérieur reste utile – pour la validation et l'archivage.")], 'todo': 'À traiter :', 'cta_title': 'Audit gratuit de 30 minutes', 'cta_text': "La facture électronique dans Odoo, c'est exactement mon domaine. J'examine votre système avec vous – 30 minutes, gratuit et sans engagement. Vous repartez avec une liste claire de ce qui manque et de son coût.", 'cta_book': 'Prendre rendez-vous – avec le résultat', 'cta_mail': 'Envoyer le résultat par e-mail', 'cta_tg': 'Envoyer le résultat via Telegram', 'copied': 'Résultat copié – collez-le simplement dans le chat Telegram.', 'mail_subject': "Check e-facture : {s}/10 – demande d'audit gratuit", 'mail_intro': 'Bonjour, voici mon résultat du check e-facture :', 'mail_outro': "Version d'Odoo :\nEntreprise :\nDate souhaitée :"},
    "bot_more_title": 'Rapports dynamiques, bots pratiques',
    "bot_more_intro": 'Au lieu de chercher dans des tableaux de bord, demandez au bot – la réponse arrive en quelques secondes, sur mobile comme au bureau.',
    "chat2": [{'caption': "Qui travaille dans Odoo aujourd'hui ? (exemple, noms modifiés)", 'msgs': [{'who': 'me', 'html': '/users'}, {'who': 'bot', 'html': '<b>▒▒▒ PROD : utilisateurs sur 24 h</b><br>Dans le client web Odoo : 88<br>En ligne : 37<br>Connexions : 398 (47 utilisateurs)<br>Utilisateurs internes actifs : 147<br>Actions aujourd&#x27;hui (depuis 00:00), utilisateurs : 74<pre>modif. chatter\n  568      9  Taras Wendel\n  534     67  Oleh Brandt\n  499     54  Lukas Feld\n  495    115  Daria Moos\n  481     60  Sofia Kern</pre>Dernière action :<pre>🟢 13.11 16:43  Ivan Roth\n🟢 13.11 16:43  Marta Lind\n🟢 13.11 16:42  Olena Weiss\n🟢 13.11 16:41  Anna Berg\n🟢 13.11 16:40  Irina Falk</pre>'}]}, {'caption': 'La cause en clair au lieu de 5 000 lignes de log (exemple).', 'msgs': [{'who': 'me', 'html': '/analyze shop.▒▒▒.de'}, {'who': 'bot', 'html': "🔎 <b>Analyse shop.▒▒▒.de</b> · 24 h<br>✅ HTTP 200 en 0,24 s · SSL jusqu'au 14/02<br>CPU 31 % · RAM 62 % · Disque 71 %<br>Log Odoo : ERROR 12 · WARNING 40<br>• SerializationFailure 9× – cron « Stocks »<br>• nginx 502 3× à 03:12<br>🤖 <b>Synthèse IA :</b> les erreurs 502 coïncident avec la sauvegarde nocturne – tous les workers étaient occupés. Recommandation : décaler la sauvegarde à 04:00, augmenter la limite de temps du cron.", 'buttons': ['📋 Détails', '🛠 Créer un ticket']}]}],
    "lb": {"close": 'Fermer', "zoom_in": 'Agrandir', "zoom_out": 'Réduire', "full": 'Plein écran'},
    "map": {'title': 'Projets en Allemagne, en Suisse et en Ukraine', 'caption': "Villes où j'ai accompagné des projets Odoo.", 'home': 'Stuttgart – ma base', 'c': {'frankfurt': 'Francfort', 'berlin': 'Berlin', 'stuttgart': 'Stuttgart', 'ulm': 'Ulm', 'luzern': 'Lucerne', 'kyiv': 'Kyiv', 'poltava': 'Poltava', 'dnipro': 'Dnipro', 'odesa': 'Odessa', 'kherson': 'Kherson'}},
}

# пакеты часов (config.PACKS) – сравнение с Odoo Success Packs
T.update({'packs_title': "Forfaits d'heures – moins chers que les Success Packs d'Odoo", 'packs_intro': "Heures prépayées pour l'analyse, la conception, le développement, l'intégration, la migration, la performance et la formation – les mêmes tailles de forfaits qu'Odoo, à un prix inférieur. Possible parce que le travail de routine (sauvegardes, supervision, copies de test, mises à jour) est automatisé chez nous.", 'packs_head': ['Forfait', 'Heures', 'Prix', 'par heure', 'Odoo Success Pack¹'], 'packs_note': "Valable 12 mois, décompte par tranches de 15 minutes, relevé mensuel des heures restantes. Sans frais supplémentaires pour la maintenance de vos propres modules. Sur site : temps et frais de déplacement selon le réel. ¹ Prix catalogue d'Odoo S.A. pour les nouveaux clients (remise de 15 %) selon odoo.com/pricing-packs, au 19/11/2026 ; les prix d'Odoo varient selon le pays, hors TVA. Nos prix : sans TVA (§ 19 UStG, franchise allemande)."})
