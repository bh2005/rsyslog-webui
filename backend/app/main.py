import logging

from fastapi import FastAPI

from .audit import router as audit_router
from .auth import router as auth_router
from .groups import router as groups_router
from .log_buffer import install as install_log_buffer
from .manuals import router as manuals_router
from .stats import router as stats_router
from .config import settings
from .exceptions import register_exception_handlers
from .models import fake_users_db
from .rsyslog import router as rsyslog_router
from .security import hash_password
from .settings import router as settings_router
from .syslogs import router as syslogs_router
from .users import router as users_router

# basicConfig first so root logger level = INFO, then ring-buffer handler
logging.basicConfig(level=logging.INFO)
install_log_buffer()
logger = logging.getLogger(__name__)


def initialize_users() -> None:
    if fake_users_db["admin"]["hashed_password"] == "":
        fake_users_db["admin"]["hashed_password"] = hash_password(settings.admin_password)
    if fake_users_db["operator"]["hashed_password"] == "":
        fake_users_db["operator"]["hashed_password"] = hash_password("operator123")
    if fake_users_db["viewer"]["hashed_password"] == "":
        fake_users_db["viewer"]["hashed_password"] = hash_password("viewer123")


app = FastAPI(title=settings.app_name)
register_exception_handlers(app)
app.include_router(auth_router)
app.include_router(audit_router)
app.include_router(groups_router)
app.include_router(manuals_router)
app.include_router(stats_router)
app.include_router(rsyslog_router)
app.include_router(settings_router)
app.include_router(syslogs_router)
app.include_router(users_router)


@app.on_event("startup")
async def startup_event() -> None:
    initialize_users()
    logger.info("rsyslog-manager-api started (version: %s)", settings.app_name)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "rsyslog-manager-api"}
