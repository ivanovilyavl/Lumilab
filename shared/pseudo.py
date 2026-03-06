import hashlib
import hmac
import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ClientAlias

ADJECTIVES = [
    "неосознанный", "задумчивый", "стремительный", "пушистый",
    "загадочный", "искренний", "рассеянный", "бодрый", "тихий",
    "решительный", "мечтательный", "осторожный", "весёлый",
    "спокойный", "дерзкий", "нежный", "строгий", "ленивый",
    "вдумчивый", "порывистый", "сонный", "внимательный",
    "озорной", "серьёзный", "любопытный", "флегматичный",
    "харизматичный", "задорный", "молчаливый", "импульсивный",
]

ANIMALS = [
    "опоссум", "капибара", "енот", "выдра", "тапир", "аксолотль",
    "ламантин", "утконос", "квокка", "фенек", "окапи", "нарвал",
    "броненосец", "галаго", "тарсир", "лемур", "вомбат", "манул",
    "дикобраз", "тушканчик", "бобёр", "байбак", "секретарь",
    "фламинго", "пеликан", "тукан", "какаду", "иволга", "скунс",
]


def generate_pseudo() -> str:
    """Generate a random pseudonym like 'задумчивый аксолотль'."""
    return f"{random.choice(ADJECTIVES)} {random.choice(ANIMALS)}"


def hash_client_id(telegram_id: int, secret: str) -> str:
    """HMAC-SHA256 — irreversible but stable for the same ID."""
    return hmac.new(
        secret.encode(),
        str(telegram_id).encode(),
        hashlib.sha256,
    ).hexdigest()


async def get_or_create_pseudo(tg_hash: str, master_id: int, db: AsyncSession) -> str:
    """Get existing pseudonym or create a new one for this client+master pair."""
    result = await db.execute(
        select(ClientAlias).where(
            ClientAlias.tg_hash == tg_hash,
            ClientAlias.master_id == master_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing.pseudo

    pseudo = generate_pseudo()
    db.add(ClientAlias(tg_hash=tg_hash, master_id=master_id, pseudo=pseudo))
    await db.flush()
    return pseudo
