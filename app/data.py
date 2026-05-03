from app.models import AdherentUser, ChatMessage, CoachContext


ADHERENT_USER = AdherentUser(
    id="adh-001",
    name="Amina S.",
    avatar="AS",
    currentStep=2,
    currentStepLabel="Etape 2",
    deadline="TOEIC dans 18 jours",
)

COACH_CONTEXT = CoachContext(
    etape="Listening",
    score=615,
    objectif=785,
    deadline="J-18",
    weakZones="Part 3, Part 7",
)

CHAT_HISTORY: list[ChatMessage] = [
    ChatMessage(
        id="chat-1",
        role="assistant",
        content="Tu es en etape Listening. La priorite est la precision avant la vitesse brute.",
        timestamp="2026-05-02T20:30:00.000Z",
    ),
    ChatMessage(
        id="chat-2",
        role="user",
        content="Quelle est ma priorite cette semaine ?",
        timestamp="2026-05-02T20:31:00.000Z",
    ),
    ChatMessage(
        id="chat-3",
        role="assistant",
        content="Stabiliser Part 3, consolider la prise de notes, puis refaire un retest court.",
        timestamp="2026-05-02T20:31:30.000Z",
    ),
]

DASHBOARD_DATA = {
    "score": 615,
    "scoreStart": 520,
    "scoreObjectif": 785,
    "listening": 325,
    "reading": 290,
    "regularite": 86,
    "regulariteLabel": "6 jours actifs sur 7",
    "risquePrincipal": "Part 3",
    "risqueDetail": "Perte de precision sur questions implicites et cadence audio.",
    "missionDuJour": [
        {"num": "01", "title": "Neuro training Listening", "sub": "25 min ciblees sur concentration et vitesse.", "priority": "urgent"},
        {"num": "02", "title": "Relecture des notes", "sub": "Corriger les erreurs recurrentes des deux derniers tests.", "priority": "warn"},
        {"num": "03", "title": "Question au Coach IA", "sub": "Valider le protocole des prochaines 48 h.", "priority": "info"},
    ],
    "progression": [
        {"num": 1, "name": "Embarquement", "status": "Completee", "percent": 100},
        {"num": 2, "name": "Listening", "status": "Active", "percent": 62},
        {"num": 3, "name": "Reading", "status": "Verrouillee"},
        {"num": 4, "name": "Deep Boost 2.0", "status": "Verrouillee"},
        {"num": 5, "name": "Anti Derangement", "status": "Verrouillee"},
    ],
    "progressionPercent": 32,
    "recentActivity": [
        {"date": "2026-05-02 20:10", "action": "Retest Listening", "type": "Score"},
        {"date": "2026-05-02 18:40", "action": "Ajout d'une note Part 3", "type": "Notes"},
        {"date": "2026-05-01 21:05", "action": "Message envoye au support", "type": "Support"},
    ],
    "coachTip": "Stabilise la prise de notes en Listening avant d'augmenter le volume de tests blancs.",
}

PROGRAMME = [
    {
        "num": "1",
        "name": "Embarquement",
        "status": "Completee",
        "statusTone": "badge-success",
        "desc": "Cadre d'execution, outils et tableau de bord.",
        "items": [
            {"label": "Conditions de performance", "color": "var(--accent)"},
            {"label": "Guide d'astuces", "color": "var(--gold)"},
        ],
        "progress": "100%",
        "progressDetail": "Etape terminee.",
    },
    {
        "num": "2",
        "name": "Listening",
        "status": "Active",
        "statusTone": "badge-accent",
        "desc": "Travail de cadence, precision et endurance audio.",
        "items": [
            {"label": "Consignes speciales", "color": "var(--accent)"},
            {"label": "Neuro training", "color": "#0098cc"},
            {"label": "Challenge mode", "color": "var(--gold)"},
        ],
        "progress": "62%",
        "progressDetail": "Bon rythme, encore instable sur les implicites.",
        "active": True,
    },
    {
        "num": "3",
        "name": "Reading",
        "status": "Verrouillee",
        "statusTone": "",
        "desc": "Lecture business, pression du temps et grammaire en contexte.",
        "items": [
            {"label": "Resume de grammaire", "color": "var(--gold)"},
            {"label": "Business reading", "color": "var(--accent)"},
        ],
        "locked": True,
    },
]

SCORES = {
    "current": 615,
    "currentStart": 520,
    "listening": 325,
    "listeningStart": 260,
    "reading": 290,
    "readingStart": 260,
    "objectif": 785,
    "history": [
        {"date": "2026-04-12", "listening": 260, "reading": 260, "total": 520, "format": "Diagnostic"},
        {"date": "2026-04-19", "listening": 285, "reading": 270, "total": 555, "format": "Retest"},
        {"date": "2026-04-26", "listening": 305, "reading": 280, "total": 585, "format": "Retest"},
        {"date": "2026-05-02", "listening": 325, "reading": 290, "total": 615, "format": "Retest", "isCurrent": True},
    ],
    "analysis": [
        {"part": "Part 1", "percent": 82, "level": "Bon"},
        {"part": "Part 2", "percent": 76, "level": "Bon"},
        {"part": "Part 3", "percent": 49, "level": "Faible"},
        {"part": "Part 4", "percent": 58, "level": "Moyen"},
        {"part": "Part 5", "percent": 71, "level": "Bon"},
        {"part": "Part 6", "percent": 54, "level": "Moyen"},
        {"part": "Part 7", "percent": 51, "level": "Moyen"},
    ],
    "coachTip": "Ne cherche pas encore le volume maximal. Verrouille d'abord les erreurs recurrentes de Part 3 et Part 7.",
}

NOTES = [
    {
        "id": "note-1",
        "title": "Erreurs Part 3",
        "meta": "Mise a jour le 2026-05-02",
        "etape": "Listening",
        "content": "Je perds le fil quand deux distracteurs se ressemblent. Revenir au mot-cle de la question avant les choix.",
        "words": [{"word": "shipment", "state": "review"}, {"word": "delay", "state": "mastered"}],
        "tag": "Prioritaire",
    },
    {
        "id": "note-2",
        "title": "Routine avant session",
        "meta": "Mise a jour le 2026-05-01",
        "etape": "Embarquement",
        "content": "Casque, timer, feuille de notes, pas de telephone.",
        "words": [],
    },
]

RESOURCES = [
    {
        "id": "res-1",
        "title": "Resume de grammaire",
        "meta": "Support fondamental pour Reading",
        "category": "Methode",
        "statuses": ["Disponible", "Essentiel"],
        "tones": ["badge-accent", "badge-gold"],
        "icon": "GR",
        "toneClass": "badge-accent",
    },
    {
        "id": "res-2",
        "title": "Feuille de prise de notes",
        "meta": "A utiliser pendant les sessions Listening",
        "category": "Methode",
        "statuses": ["Disponible"],
        "tones": ["badge-success"],
        "icon": "NT",
        "toneClass": "badge-success",
    },
]

MESSAGES = [
    {
        "id": "msg-1",
        "sender": "Coach support",
        "senderAvatar": "CS",
        "time": "2026-05-02 21:00",
        "read": False,
        "content": "J'ai bien recu ton dernier score. Continue le protocole Listening sur 48 h avant un nouveau retest.",
        "borderColor": "#22d3ff",
    },
    {
        "id": "msg-2",
        "sender": "Equipe Deep Training",
        "senderAvatar": "DT",
        "time": "2026-05-01 10:15",
        "read": True,
        "content": "Tes acces de l'etape 2 sont actifs. Pense a utiliser la feuille de notes pendant chaque session.",
        "borderColor": "#f5a623",
    },
]
