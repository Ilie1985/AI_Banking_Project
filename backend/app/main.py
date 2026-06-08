from fastapi import FastAPI, UploadFile, File, Form, HTTPException
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
def data_status():
    return get_data_status()


@app.post("/dataset-mode")
def dataset_mode(request: DatasetModeRequest):
    try:
        return switch_dataset_mode(request.mode)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.get("/dashboard")
def dashboard():
    return get_dashboard()


@app.get("/budget")
def budget():
    return get_budget_summary()


@app.post("/budget")
def create_new_budget(budget_data: BudgetCreate):
    return create_budget(budget_data)


@app.post("/transactions")
def create_new_transaction(transaction_data: TransactionCreate):
    try:
        return create_manual_transaction(transaction_data)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.get("/transactions")
def transactions(limit: int = 100):
    return get_transactions(limit)


@app.get("/analysis")
def analysis():
    return get_spending_analysis()


@app.get("/forecast")
def forecast():
    return get_forecast()


@app.get("/insights")
def insights():
    return get_insights()


@app.get("/audit-log")
def audit_log():
    return get_audit_log()


@app.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    date_column: str = Form(...),
    description_column: str = Form(...),
    amount_column: str = Form(...),
    category_column: str = Form(...),
    type_column: str = Form(""),
    payment_method_column: str = Form(""),
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
        )

        return result

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))