import base64
import os

from fastapi import APIRouter

from app.schemas import TraderProfile

router = APIRouter(prefix="/traders", tags=["traders"])

AVATAR_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "static", "avatars")


def _load_avatar_base64(filename: str) -> str:
    path = os.path.join(AVATAR_DIR, filename)
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except FileNotFoundError:
        return ""


TRADERS: list[dict] = [
    {
        "key": "buffett",
        "name": "Warren Buffett",
        "emoji": "\U0001F3A9",
        "title": "Value Investor",
        "bio": "Kaufe nur, was du verstehst. Suche nach dauerhaftem Wettbewerbsvorteil (Burggraben). Bewerte den inneren Wert und kaufe mit Sicherheitsmarge. Halte langfristig – Volatilität ist dein Freund. Meide Spekulation.",
        "color": "#f0a500",
        "avatar_url": "/static/avatars/buffett.png",
        "traits": ["Innerer Wert", "Burggraben", "Langfrist-Horizont"],
    },
    {
        "key": "lynch",
        "name": "Peter Lynch",
        "emoji": "\U0001F981",
        "title": "Growth Investor",
        "bio": "Investiere in das, was du kennst. Suche nach starkem Wachstum zu fairem Preis (GARP). Nischen-Wachstumsstories, die Institutionelle ignorieren. Pragmatisch und bodenständig.",
        "color": "#00b09b",
        "avatar_url": "/static/avatars/lynch.png",
        "traits": ["Wachstum + Wert", "Nischen-Fokus", "PEG-Ratio"],
    },
    {
        "key": "soros",
        "name": "George Soros",
        "emoji": "\U0001F405",
        "title": "Makro-Trader",
        "bio": "Reflexivitätstheorie: Märkte beeinflussen Fundamentaldaten. Suche nach asymmetrischen Setups. Gegen den Strom schwimmen wenn die Logik stimmt. Makro-Faktoren wie Zinsen, Währungen, Geopolitik.",
        "color": "#9b59b6",
        "avatar_url": "/static/avatars/soros.png",
        "traits": ["Reflexivität", "Asymmetrische Wetten", "Konträr"],
    },
    {
        "key": "wood",
        "name": "Cathie Wood",
        "emoji": "\U0001F680",
        "title": "Innovation Investor",
        "bio": "Größte Chancen durch disruptive Technologien: KI, Genomik, Robotik, Blockchain. 5–10 Jahre Horizont. Kurzfristige Volatilität ist der Preis für transformative Renditen.",
        "color": "#3498db",
        "avatar_url": "/static/avatars/wood.png",
        "traits": ["Disruptive Tech", "5–10 Jahre", "Exponentiell"],
    },
    {
        "key": "saylor",
        "name": "Michael Saylor",
        "emoji": "\u20BF",
        "title": "Digital Asset Stratege",
        "bio": "Bitcoin ist das härteste Geld der Geschichte. Fixes Angebot, dezentral, exponentiell wachsendes Netzwerk. Altcoin-skeptisch. Denkt in Jahrzehnten, nicht Quartalen.",
        "color": "#f7931a",
        "avatar_url": "/static/avatars/saylor.png",
        "traits": ["Digitales Gold", "Fixes Angebot", "BTC-Maximalist"],
    },
]


@router.get("", response_model=list[TraderProfile])
async def list_traders():
    result = []
    for t in TRADERS:
        entry = dict(t)
        filename = os.path.basename(t["avatar_url"])
        entry["avatar_base64"] = _load_avatar_base64(filename)
        result.append(entry)
    return result
