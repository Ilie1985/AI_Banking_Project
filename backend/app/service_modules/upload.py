import io

import pandas as pd

from app.database import (
    add_audit_log,
    delete_rows,
    insert_rows,
)
from app.service_modules.cleaning import (
    clean_amount,
    clean_category,
    clean_date,
    clean_description,
    standardise_transaction_type,
)
from app.service_modules.dataset import set_active_dataset_mode


def upload_csv_transactions(
    file_bytes,
    date_column,
    description_column,
    amount_column,
    type_column,
    category_column,
    user_id,
    payment_method_column=None,
):
    df = pd.read_csv(io.BytesIO(file_bytes))

    required_columns = [
        date_column,
        description_column,
        amount_column,
        category_column,
    ]

    for column in required_columns:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' was not found in the uploaded CSV.")

    cleaned_rows = []

    for _, row in df.iterrows():
        date_value = clean_date(row[date_column])

        if date_value is None:
            continue

        amount_value = clean_amount(row[amount_column])

        if type_column and type_column in df.columns:
            transaction_type =         standardise_transaction_type(
                row[type_column],
                amount_value,
            )
        else:
            transaction_type = "expense"

        if payment_method_column and payment_method_column in df.columns:
            payment_method = str(row[payment_method_column])
        else:
            payment_method = "Uploaded CSV"

        cleaned_rows.append(
            {
                "user_id": user_id,
                "date": date_value,
                "description": clean_description(row[description_column]),
                "amount": amount_value,
                "transaction_type": transaction_type,
                "category": clean_category(row[category_column]),
                "payment_method": payment_method,
                "source": "uploaded",
            }
        )

    if len(cleaned_rows) == 0:
        raise ValueError(
            "The uploaded CSV could not be used because no valid transaction rows were found."
        )

    delete_rows(
        table_name="uploaded_transactions",
        filters={"user_id": user_id},
    )

    insert_rows(
        table_name="uploaded_transactions",
        rows=cleaned_rows,
    )

    set_active_dataset_mode("uploaded", user_id)

    add_audit_log(
        action="UPLOAD",
        record_type="uploaded_transactions",
        user_id=user_id,
        record_id=None,
        source="uploaded",
        details=(
            f"{len(cleaned_rows)} transactions uploaded, cleaned, mapped and "
            f"set as the active dataset."
        ),
    )

    return {
        "message": "CSV uploaded, cleaned and set as the active dataset.",
        "rows_uploaded": len(cleaned_rows),
        "active_dataset": "uploaded",
    }