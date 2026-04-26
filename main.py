from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum

from src.auth.url import router as auth_router
from src.category.urls import router as category_router
from src.expense.urls import router as expense_router
from src.extras.urls import router as extras_router
from src.transaction.urls import router as transaction_router

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://",
]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(transaction_router)
app.include_router(expense_router)
app.include_router(category_router)
app.include_router(extras_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation error",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "message": str(exc),
        },
    )


@app.get("/", tags=["Root"])
async def root():
    """API root endpoint."""
    return {
        "success": True,
        "message": "Transaction & Expense Management API",
        "version": "1.0.0",
        "endpoints": {
            "transactions": "/transactions",
            "expenses": "/expenses",
            "health": "/health",
            "docs": "/docs",
        },
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"success": True, "status": "healthy", "message": "API is running"}


# Lambda handler
handler = Mangum(app)
