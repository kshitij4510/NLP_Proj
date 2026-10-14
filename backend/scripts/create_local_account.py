"""Create a local researcher account. Never overwrite an existing password."""
import asyncio
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from dotenv import load_dotenv
load_dotenv(BACKEND / ".env.local")
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///" + (BACKEND / "researchmind_local.db").as_posix()

async def main():
    from app.database.session import AsyncSessionLocal, engine
    from app.models.base import Base
    import app.models
    from app.services.auth_service import AuthService
    from app.repositories.user_repo import UserRepository
    from app.schemas.auth import UserRegister, UserLogin
    email = os.environ.get("LOCAL_ACCOUNT_EMAIL", "researcher@example.com")
    password = os.environ["LOCAL_ACCOUNT_PASSWORD"]
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        svc = AuthService(db)
        if not await UserRepository(db).get_by_email(email):
            await svc.register(UserRegister(email=email, username="researcher", password=password, full_name="Researcher"))
            await db.commit()
        await svc.login(UserLogin(email=email, password=password))
        print(f"Verified working account: {email}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
