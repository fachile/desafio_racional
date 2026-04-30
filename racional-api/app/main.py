from fastapi import FastAPI
from app.routers import users, wallets, portfolios

app = FastAPI(
    title="Investment API",
    description="API for managing user investments, portfolios, and stock orders.",
    version="1.0.0",
)

app.include_router(users.router)
app.include_router(wallets.router)
app.include_router(portfolios.router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
