from contextlib import asynccontextmanager

from fastapi import FastAPI

from payment_service.bootstrap.provider import SqlalchemyUseCaseProvider
from payment_service.config import get_settings
from payment_service.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
)
from payment_service.presentation.api.exception_handlers import (
    register_exception_handlers,
)
from payment_service.presentation.api.routers import router as router_payments


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine = create_database_engine(url=settings.postgres.url)
    app.state.provider = SqlalchemyUseCaseProvider(
        session_factory=create_session_factory(engine=engine)
    )
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

register_exception_handlers(app)

app.include_router(router_payments)
