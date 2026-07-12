import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

from app.service_modules.budgets import get_budget_summary
from app.service_modules.dataset import get_active_dataset_mode
from app.service_modules.transactions import get_all_transactions


def get_dashboard(user_id):
    df = get_all_transactions(user_id)
    active_dataset = get_active_dataset_mode(user_id)

    if df.empty:
        return {
            "active_dataset": active_dataset,
            "total_income": 0,
            "total_expenses": 0,
            "net_savings": 0,
            "transaction_count": 0,
            "spending_by_category": [],
            "monthly_spending_trend": [],
            "source_summary": [],
            "message": "No transaction data is available for the selected data mode.",
        }

    income_df = df[df["transaction_type"] == "income"]
    expense_df = df[df["transaction_type"] == "expense"]

    total_income = float(income_df["amount"].sum())
    total_expenses = float(expense_df["amount"].sum())
    net_savings = total_income - total_expenses

    spending_by_category = (
        expense_df.groupby("category")["amount"]
        .sum()
        .reset_index()
        .sort_values("amount", ascending=False)
        .to_dict(orient="records")
    )

    monthly_spending_trend = (
        expense_df.groupby("month")["amount"]
        .sum()
        .reset_index()
        .sort_values("month")
        .to_dict(orient="records")
    )

    source_summary = (
        df.groupby("source")
        .size()
        .reset_index(name="count")
        .to_dict(orient="records")
    )

    return {
        "active_dataset": active_dataset,
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net_savings": round(net_savings, 2),
        "transaction_count": int(len(df)),
        "spending_by_category": spending_by_category,
        "monthly_spending_trend": monthly_spending_trend,
        "source_summary": source_summary,
        "message": f"Dashboard generated using {active_dataset} data mode.",
    }


def get_spending_analysis(user_id):
    df = get_all_transactions(user_id)
    active_dataset = get_active_dataset_mode(user_id)

    if df.empty:
        return {
            "active_dataset": active_dataset,
            "average_monthly_spending": 0,
            "highest_spending_month": None,
            "lowest_spending_month": None,
            "top_categories": [],
            "monthly_analysis": [],
            "source_summary": [],
            "message": "No spending analysis is available because the selected data mode has no transactions.",
        }

    expense_df = df[df["transaction_type"] == "expense"]

    monthly = (
        expense_df.groupby("month")["amount"]
        .sum()
        .reset_index()
        .sort_values("month")
    )

    if monthly.empty:
        highest_month = None
        lowest_month = None
        average_monthly_spending = 0
    else:
        highest_row = monthly.loc[monthly["amount"].idxmax()]
        lowest_row = monthly.loc[monthly["amount"].idxmin()]

        highest_month = {
            "month": highest_row["month"],
            "amount": round(float(highest_row["amount"]), 2),
        }

        lowest_month = {
            "month": lowest_row["month"],
            "amount": round(float(lowest_row["amount"]), 2),
        }

        average_monthly_spending = round(float(monthly["amount"].mean()), 2)

    top_categories = (
        expense_df.groupby("category")["amount"]
        .sum()
        .reset_index()
        .sort_values("amount", ascending=False)
        .head(10)
        .to_dict(orient="records")
    )

    source_summary = (
        df.groupby("source")
        .agg(
            transaction_count=("amount", "count"),
            total_amount=("amount", "sum"),
        )
        .reset_index()
        .to_dict(orient="records")
    )

    return {
        "active_dataset": active_dataset,
        "average_monthly_spending": average_monthly_spending,
        "highest_spending_month": highest_month,
        "lowest_spending_month": lowest_month,
        "top_categories": top_categories,
        "monthly_analysis": monthly.to_dict(orient="records"),
        "source_summary": source_summary,
        "message": f"Spending analysis generated using {active_dataset} data mode.",
    }


def get_forecast(user_id):
    df = get_all_transactions(user_id)
    active_dataset = get_active_dataset_mode(user_id)

    if df.empty:
        return {
            "message": "No transaction data is available for the selected data mode.",
            "prediction": None,
            "mae": None,
            "r2_score": None,
            "chart_data": [],
            "active_dataset": active_dataset,
            "forecast_ready": False,
        }

    expense_df = df[df["transaction_type"] == "expense"]

    monthly = (
        expense_df.groupby("month")["amount"]
        .sum()
        .reset_index()
        .sort_values("month")
    )

    if len(monthly) < 6:
        chart_data = []

        for _, row in monthly.iterrows():
            chart_data.append(
                {
                    "month": row["month"],
                    "actual": round(float(row["amount"]), 2),
                    "predicted": None,
                }
            )

        return {
            "message": (
                f"The selected data mode is '{active_dataset}', but it only has "
                f"{len(monthly)} month(s) of expense history. At least 6 months "
                "are recommended for a more meaningful ML forecast."
            ),
            "prediction": None,
            "mae": None,
            "r2_score": None,
            "chart_data": chart_data,
            "active_dataset": active_dataset,
            "forecast_ready": False,
        }

    monthly["month_number"] = np.arange(len(monthly))

    X = monthly[["month_number"]]
    y = monthly["amount"]

    model = LinearRegression()
    model.fit(X, y)

    monthly["predicted"] = model.predict(X)

    next_month_number = np.array([[len(monthly)]])
    next_prediction = float(model.predict(next_month_number)[0])

    mae = float(mean_absolute_error(y, monthly["predicted"]))
    r2 = float(r2_score(y, monthly["predicted"])) if len(monthly) > 1 else 0.0

    chart_data = []

    for _, row in monthly.iterrows():
        chart_data.append(
            {
                "month": row["month"],
                "actual": round(float(row["amount"]), 2),
                "predicted": round(float(row["predicted"]), 2),
            }
        )

    chart_data.append(
        {
            "month": "Next month",
            "actual": None,
            "predicted": round(next_prediction, 2),
        }
    )

    return {
        "message": (
            f"The app is using '{active_dataset}' data mode. The model predicts "
            f"that next month's spending may be around £{next_prediction:.2f}. "
            f"The MAE is £{mae:.2f}."
        ),
        "prediction": round(next_prediction, 2),
        "mae": round(mae, 2),
        "r2_score": round(r2, 3),
        "chart_data": chart_data,
        "active_dataset": active_dataset,
        "forecast_ready": True,
    }


def get_insights(user_id):
    dashboard = get_dashboard(user_id)
    budget = get_budget_summary(user_id)
    forecast = get_forecast(user_id)
    analysis = get_spending_analysis(user_id)
    active_dataset = get_active_dataset_mode(user_id)

    insights = []

    if dashboard["transaction_count"] == 0:
        insights.append(
            "No transactions are available in the selected data mode. Choose mock data, upload a CSV, or add manual transactions."
        )
    elif dashboard["total_expenses"] > dashboard["total_income"]:
        insights.append(
            "Your expenses are currently higher than your income. Consider reducing non-essential spending."
        )
    else:
        insights.append(
            "Your income is higher than your expenses, which is a positive sign for savings."
        )

    if dashboard["spending_by_category"]:
        top_category = dashboard["spending_by_category"][0]
        insights.append(
            f"Your highest spending category is {top_category['category']} at £{top_category['amount']:.2f}."
        )

    for group in budget.get("budget_groups", []):
        for category in group.get("category_budgets", []):
            if category["status"] == "Over budget":
                insights.append(f"You are over budget in {category['category']}.")
            elif category["status"] == "Close to limit":
                insights.append(
                    f"You are close to your budget limit in {category['category']}."
                )

    if budget.get("safe_daily_spending", 0) > 0:
        insights.append(
            f"Your safe daily spending allowance is about £{budget['safe_daily_spending']:.2f}."
        )

    if forecast.get("forecast_ready") is True:
        insights.append(
            f"Based on the selected dataset, next monthly spending may be around £{forecast['prediction']:.2f}."
        )
    else:
        insights.append(forecast.get("message"))

    if analysis.get("average_monthly_spending", 0) > 0:
        insights.append(
            f"Your average monthly spending is £{analysis['average_monthly_spending']:.2f}."
        )

    return {
        "active_dataset": active_dataset,
        "insights": insights,
        "summary": f"These insights are generated using {active_dataset} data mode.",
    }