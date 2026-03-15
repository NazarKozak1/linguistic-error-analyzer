import asyncio
import os
from src.db.models import Sentence, ParsedError, User, UserRole
from src.db.database import AsyncSessionLocal
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.texts import SUPPORTED_LANGUAGES


async def get_or_create_user(
        session: AsyncSession,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        language_code: str | None = None
) -> tuple[User, bool]:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    today = date.today()

    if user:
        # reset limits if it is a new day
        if user.last_request_date != today:
            user.daily_requests = 0
            user.daily_tokens = 0
            user.last_request_date = today
            await session.commit()
        return user, False

    # assign OWNER role if the ID matches the environment variable
    owner_id = int(os.getenv("OWNER_ID", 0))
    assigned_role = UserRole.OWNER if telegram_id == owner_id else UserRole.REGULAR

    # set default language using short codes from texts.py
    pref_lang = language_code if language_code in SUPPORTED_LANGUAGES else "en"

    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        language_code=language_code,
        preferred_language=pref_lang,
        role=assigned_role,
        last_request_date=today
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user, True

async def save_sentence_with_errors(
        session: AsyncSession,
        user_id: int,
        telegram_message_id: int,
        original_text: str,
        corrected_text: str,
        translation: str,
        tokens_used: int,
        errors_data: list[dict]
) -> Sentence:
    """save sentence and linked errors in one transaction."""
    sentence = Sentence(
        user_id=user_id,
        telegram_message_id=telegram_message_id,
        original_text=original_text,
        corrected_text=corrected_text,
        translation=translation,
        tokens_used=tokens_used
    )
    session.add(sentence)
    await session.flush()

    for err in errors_data:
        parsed_error = ParsedError(
            sentence_id=sentence.id,
            error_fragment=err["error_fragment"],
            correction=err["correction"],
            category=err["category"],
            subcategory=err["subcategory"],
            cefr_level=err["cefr_level"],
            explanation=err["explanation"]
        )
        session.add(parsed_error)

    await session.commit()
    await session.refresh(sentence)

    return sentence


async def delete_user(session: AsyncSession, telegram_id: int) -> bool:
    """delete user and cascade delete all their sentences and errors."""
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if user:
        await session.delete(user)
        await session.commit()
        return True
    return False




async def update_user_language(session: AsyncSession, telegram_id: int, new_language: str) -> bool:
    """update user preferred output language."""
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if user:
        user.preferred_language = new_language
        await session.commit()
        return True
    return False


async def main():
    """run test execution."""
    async with AsyncSessionLocal() as session:
        # 1. test user creation
        test_tg_id = 123456789
        user = await get_or_create_user(
            session,
            telegram_id=test_tg_id,
            first_name="Test User"
        )
        print(f"user created/fetched: id={user.id}")

        # 2. test saving sentence and errors
        mock_errors = [{
            "error_fragment": "getern",
            "correction": "gestern",
            "category": "1_orthography",
            "subcategory": "spelling",
            "cefr_level": "A1.1",
            "explanation": "test explanation"
        }]

        sentence = await save_sentence_with_errors(
            session=session,
            user_id=user.id,
            telegram_message_id=999,
            original_text="Ich kaufe ein Apfel getern",
            corrected_text="Ich habe gestern einen Apfel gekauft.",
            translation="Я вчора купив яблуко.",
            tokens_used=150,
            errors_data=mock_errors
        )
        print(f"sentence saved: id={sentence.id} with {len(mock_errors)} error(s)")

"""        # 3. test cascading delete (cleans up DB after test)
        is_deleted = await delete_user(session, telegram_id=test_tg_id)
        print(f"user deleted (with cascading data): {is_deleted}")"""




if __name__ == "__main__":
    asyncio.run(main())