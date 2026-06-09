import json
import urllib.error
import urllib.request
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Header, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.database import initialise_database
from app.schemas import TransactionCreate, BudgetCreate
from app.services import (
    create_manual_transaction,
    create_budget,
    get_dashboard,
    get_budget_summary,
    get_forecast,
    get_insights,
    get_spending_analysis,
    get_transactions,
    upload_csv_transactions,
    get_audit_log,
    get_data_status,
    switch_dataset_mode,
)


ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"


def clean_env_value(value):
    value = value.strip()
    value = value.strip('"')
    value = value.strip("'")
    value = value.rstrip(";")
    return value.strip()


def read_env_value(key):
    if not ENV_PATH.exists():
        return None

    with ENV_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                continue

            env_key, env_value = line.split("=", 1)

            if env_key.strip() == key:
                return clean_env_value(env_value)

    return None


SUPABASE_URL = read_env_value("SUPABASE_URL")
SUPABASE_ANON_KEY = read_env_value("SUPABASE_ANON_KEY")


app = FastAPI(
    title="AI Banking API",
    description="FastAPI backend for the AI Banking personal finance prototype.",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DatasetModeRequest(BaseModel):
    mode: str


def verify_supabase_token(access_token):
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise HTTPException(
            status_code=500,
            detail=(
                "Supabase is not configured on the backend. "
                "Check SUPABASE_URL and SUPABASE_ANON_KEY in your .env file."
            ),
        )

    if not SUPABASE_URL.startswith("https://"):
        raise HTTPException(
            status_code=500,
            detail="SUPABASE_URL must start with https://",
        )

    request = urllib.request.Request(
        url=f"{SUPABASE_URL}/auth/v1/user",
        headers={
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {access_token}",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response_body = response.read().decode("utf-8")
            user_data = json.loads(response_body)

    except urllib.error.HTTPError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired Supabase session. Please log in again.",
        )

    except Exception as error:
        raise HTTPException(
            status_code=401,
            detail=f"Could not verify Supabase session: {str(error)}",
        )

    user_id = user_data.get("id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Supabase user ID was not found in the session.",
        )

    return user_id


def get_current_user_id(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Please log in.",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format.",
        )

    access_token = authorization.replace("Bearer ", "").strip()

    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Missing access token.",
        )

    return verify_supabase_token(access_token)


@app.on_event("startup")
def startup_event():
    initialise_database()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "AI Banking backend is running",
    }


@app.get("/data-status")
def data_status(user_id: str = Depends(get_current_user_id)):
    return get_data_status(user_id)


@app.post("/dataset-mode")
def dataset_mode(
    request: DatasetModeRequest,
    user_id: str = Depends(get_current_user_id),
):
    try:
        return switch_dataset_mode(request.mode, user_id)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.get("/dashboard")
def dashboard(user_id: str = Depends(get_current_user_id)):
    return get_dashboard(user_id)


@app.get("/budget")
def budget(user_id: str = Depends(get_current_user_id)):
    return get_budget_summary(user_id)


@app.post("/budget")
def create_new_budget(
    budget_data: BudgetCreate,
    user_id: str = Depends(get_current_user_id),
):
    return create_budget(budget_data, user_id)


@app.post("/transactions")
def create_new_transaction(
    transaction_data: TransactionCreate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        return create_manual_transaction(transaction_data, user_id)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.get("/transactions")
def transactions(
    limit: int = 100,
    user_id: str = Depends(get_current_user_id),
):
    return get_transactions(user_id, limit)


@app.get("/analysis")
def analysis(user_id: str = Depends(get_current_user_id)):
    return get_spending_analysis(user_id)


@app.get("/forecast")
def forecast(user_id: str = Depends(get_current_user_id)):
    return get_forecast(user_id)


@app.get("/insights")
def insights(user_id: str = Depends(get_current_user_id)):
    return get_insights(user_id)


@app.get("/audit-log")
def audit_log(user_id: str = Depends(get_current_user_id)):
    return get_audit_log(user_id)


@app.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    date_column: str = Form(...),
    description_column: str = Form(...),
    amount_column: str = Form(...),
    category_column: str = Form(...),
    type_column: str = Form(""),
    payment_method_column: str = Form(""),
    user_id: str = Depends(get_current_user_id),
):
    try:
        file_bytes = await file.read()

        result = upload_csv_transactions(
            file_bytes=file_bytes,
            date_column=date_column,
            description_column=description_column,
            amount_column=amount_column,
            type_column=type_column,
            category_column=category_column,
            payment_method_column=payment_method_column,
            user_id=user_id,
        )

        return result

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))