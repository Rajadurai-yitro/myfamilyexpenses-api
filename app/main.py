from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.application.categories.category_usecases import SeedCategoriesUseCase
from app.core.config import settings
from app.core.logging import logger
from app.infrastructure.database.repositories.sqlalchemy_category_repo import (
    SqlAlchemyCategoryRepository,
)
from app.infrastructure.database.session import SessionLocal, init_db
from app.presentation.api.middleware.error_handler import register_error_handlers
from app.presentation.api.middleware.request_id import RequestIdMiddleware
from app.presentation.api.routes import (
    auth,
    categories,
    expenses,
    exports,
    health,
    reports,
    users,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database tables and seed default categories
    logger.info("Starting up Expense Tracker API...")
    init_db()

    # Seed categories if database is empty
    db = SessionLocal()
    try:
        cat_repo = SqlAlchemyCategoryRepository(db)
        seed_usecase = SeedCategoriesUseCase(cat_repo)
        seeded = seed_usecase.execute()
        logger.info(f"Verified {len(seeded)} default expense categories in database.")
    except Exception as e:
        logger.error(f"Error during category seeding: {e}", exc_info=True)
    finally:
        db.close()

    yield

    # Shutdown
    logger.info("Shutting down Expense Tracker API...")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description="Clean Architecture Expense Tracker Backend API",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(RequestIdMiddleware)

    # CORS configuration
    origins = settings.CORS_ORIGINS
    if origins == ["*"] or "*" in origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Register standardized error handlers
    register_error_handlers(app)

    # Include routers
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(categories.router)
    app.include_router(expenses.router)
    app.include_router(reports.router)
    app.include_router(exports.router)
    app.include_router(users.router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
