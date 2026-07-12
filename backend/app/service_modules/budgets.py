import pandas as pd

from app.database import (
    add_audit_log,
    delete_rows,
    insert_row,
    select_rows,
    update_rows,
)
from app.service_modules.cleaning import clean_category
from app.service_modules.transactions import get_all_transactions


def create_budget(budget, user_id):
    row = {
        "user_id": user_id,
        "month": budget.month,
        "monthly_income": budget.monthly_income,
        "category": clean_category(budget.category),
        "budget_amount": budget.budget_amount,
        "source": "manual",
    }

    inserted = insert_row("budgets", row)
    record_id = inserted["id"] if inserted else None

    add_audit_log(
        action="CREATE",
        record_type="budget",
        user_id=user_id,
        record_id=record_id,
        source="manual",
        details=f"Budget added for {budget.category}",
    )

    return {
        "message": "Budget saved successfully",
        "id": record_id,
    }


def update_budget(budget_id, budget_update, user_id):
    existing_rows = select_rows(
        table_name="budgets",
        filters={
            "id": budget_id,
            "user_id": user_id,
        },
    )

    if not existing_rows:
        raise ValueError("Budget category was not found for this account.")

    update_data = {}

    if budget_update.category is not None:
        update_data["category"] = clean_category(budget_update.category)

    if budget_update.budget_amount is not None:
        update_data["budget_amount"] = budget_update.budget_amount

    if budget_update.monthly_income is not None:
        update_data["monthly_income"] = budget_update.monthly_income

    if not update_data:
        raise ValueError("No budget values were provided for update.")

    updated_rows = update_rows(
        table_name="budgets",
        filters={
            "id": budget_id,
            "user_id": user_id,
        },
        row=update_data,
    )

    updated = updated_rows[0] if updated_rows else None

    category_name = update_data.get(
        "category",
        existing_rows[0].get("category", "Unknown category"),
    )

    add_audit_log(
        action="UPDATE",
        record_type="budget",
        user_id=user_id,
        record_id=budget_id,
        source="manual",
        details=f"Budget updated for {category_name}",
    )

    return {
        "message": "Budget category updated successfully.",
        "id": budget_id,
        "budget": updated,
    }


def delete_budget(budget_id, user_id):
    existing_rows = select_rows(
        table_name="budgets",
        filters={
            "id": budget_id,
            "user_id": user_id,
        },
    )

    if not existing_rows:
        raise ValueError("Budget category was not found for this account.")

    category_name = existing_rows[0].get("category", "Unknown category")

    delete_rows(
        table_name="budgets",
        filters={
            "id": budget_id,
            "user_id": user_id,
        },
    )

    add_audit_log(
        action="DELETE",
        record_type="budget",
        user_id=user_id,
        record_id=budget_id,
        source="manual",
        details=f"Budget deleted for {category_name}",
    )

    return {
        "message": "Budget category deleted successfully.",
        "id": budget_id,
    }


def get_budget_summary(user_id):
    df = get_all_transactions(user_id)

    budgets = select_rows(
        table_name="budgets",
        filters={"user_id": user_id},
        order="month.desc",
    )

    budgets_df = pd.DataFrame(budgets)

    if budgets_df.empty:
        return {
            "monthly_income": 0,
            "total_budget": 0,
            "spent_so_far": 0,
            "remaining_money": 0,
            "safe_daily_spending": 0,
            "budget_groups": [],
            "message": "No manual budget has been added yet for your account.",
        }

    budgets_df["monthly_income"] = pd.to_numeric(
        budgets_df["monthly_income"],
        errors="coerce",
    ).fillna(0)

    budgets_df["budget_amount"] = pd.to_numeric(
        budgets_df["budget_amount"],
        errors="coerce",
    ).fillna(0)

    budgets_df["category"] = budgets_df["category"].apply(clean_category)

    if df.empty:
        expense_df = pd.DataFrame(columns=["month", "category", "amount"])
    else:
        expense_df = df[df["transaction_type"] == "expense"].copy()

    budget_groups = []
    months = sorted(budgets_df["month"].unique(), reverse=True)

    total_income_all_months = 0
    total_budget_all_months = 0
    total_spent_all_months = 0
    total_remaining_all_months = 0

    for month in months:
        month_budget_df = budgets_df[budgets_df["month"] == month].copy()

        monthly_income = float(month_budget_df["monthly_income"].max())
        total_budget = float(month_budget_df["budget_amount"].sum())

        if expense_df.empty:
            month_expense_df = pd.DataFrame(columns=["month", "category", "amount"])
        else:
            month_expense_df = expense_df[expense_df["month"] == month].copy()

        spent_so_far = float(month_expense_df["amount"].sum())
        remaining_money = monthly_income - spent_so_far
        safe_daily_spending = remaining_money / 30 if remaining_money > 0 else 0

        category_spending = (
            month_expense_df.groupby("category")["amount"]
            .sum()
            .reset_index()
            .rename(columns={"amount": "spent"})
        )

        merged = month_budget_df.merge(
            category_spending,
            on="category",
            how="left",
        )

        merged["spent"] = merged["spent"].fillna(0)
        merged["remaining"] = merged["budget_amount"] - merged["spent"]

        def budget_status(row):
            if row["spent"] > row["budget_amount"]:
                return "Over budget"

            if row["spent"] >= row["budget_amount"] * 0.8:
                return "Close to limit"

            return "Healthy"

        merged["status"] = merged.apply(budget_status, axis=1)

        category_budgets = merged[
            [
                "id",
                "month",
                "monthly_income",
                "category",
                "budget_amount",
                "spent",
                "remaining",
                "status",
            ]
        ].to_dict(orient="records")

        budget_groups.append(
            {
                "month": month,
                "monthly_income": round(monthly_income, 2),
                "total_budget": round(total_budget, 2),
                "spent_so_far": round(spent_so_far, 2),
                "remaining_money": round(remaining_money, 2),
                "safe_daily_spending": round(safe_daily_spending, 2),
                "category_budgets": category_budgets,
            }
        )

        total_income_all_months += monthly_income
        total_budget_all_months += total_budget
        total_spent_all_months += spent_so_far
        total_remaining_all_months += remaining_money

    latest_safe_daily = budget_groups[0]["safe_daily_spending"] if budget_groups else 0

    return {
        "monthly_income": round(total_income_all_months, 2),
        "total_budget": round(total_budget_all_months, 2),
        "spent_so_far": round(total_spent_all_months, 2),
        "remaining_money": round(total_remaining_all_months, 2),
        "safe_daily_spending": round(latest_safe_daily, 2),
        "budget_groups": budget_groups,
        "message": "All budgets are grouped by month, newest month first.",
    }