from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes import auth, chat, collections, notion, telegram, vocabulary
from app.config.settings import get_settings
from app.db.session import engine

app = FastAPI(title="LexiShelf API", version="0.1.0")

settings = get_settings()

# Bearer tokens (not cookies) authenticate every request, so credentialed CORS is never needed;
# wildcard + credentials would violate the CORS spec anyway. Restrict origins once deployed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.app_web_url.rstrip("/")] if settings.environment == "production" else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(collections.router)
app.include_router(vocabulary.router)
app.include_router(notion.router)
app.include_router(chat.router)
app.include_router(telegram.router)


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception:
        return {"status": "degraded", "database": "unreachable"}
