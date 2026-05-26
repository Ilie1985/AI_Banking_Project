from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    date: str = Field(..., example="2026-05-26")
    description: str = Field(..., example="Tesco groceries")
    amount: float = Field(..., example=45.50)
    transaction_type: str = Field(..., example="expense")
    category: str = Field(..., example="Groceries")
    payment_method: str = Field(default="Manual", example="Debit Card")


class BudgetCreate(BaseModel):
    month: str = Field(..., example="2026-05")
    monthly_income: float = Field(..., example=2200)
    category: str = Field(..., example="Groceries")
    budget_amount: float = Field(..., example=350)
    