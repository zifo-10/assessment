from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.router.assessment_router import assessment_router
from app.router.dashboard_router import dashboard_router
from app.router.job_router import job_router
from app.router.training_router import training_router
from app.router.user_router import user_router

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Catch-all for unexpected errors
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "detail": str(exc),
        },
    )

app.include_router(assessment_router, tags=["Assessment"])
app.include_router(dashboard_router, tags=["Dashboard"])
app.include_router(job_router, tags=["Job"])
app.include_router(training_router, tags=["Training"])
app.include_router(user_router, tags=["User"])
