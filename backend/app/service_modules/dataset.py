from app.database import (
    add_audit_log,
    select_rows,
    upsert_row,
)


def get_active_dataset_setting_name(user_id):
    return f"active_dataset:{user_id}"


def get_active_dataset_mode(user_id):
    setting_name = get_active_dataset_setting_name(user_id)

    rows = select_rows(
        table_name="app_settings",
        filters={"setting_name": setting_name},
    )

    if not rows:
        return "mock"

    return rows[0]["setting_value"]


def set_active_dataset_mode(mode, user_id):
    allowed_modes = ["mock", "uploaded", "manual", "combined"]

    if mode not in allowed_modes:
        raise ValueError(
            "Invalid dataset mode. Choose one of: mock, uploaded, manual, combined."
        )

    setting_name = get_active_dataset_setting_name(user_id)

    upsert_row(
        table_name="app_settings",
        row={
            "setting_name": setting_name,
            "user_id": user_id,
            "setting_value": mode,
        },
        conflict_column="setting_name",
    )

    add_audit_log(
        action="SWITCH",
        record_type="dataset_mode",
        user_id=user_id,
        record_id=None,
        source=mode,
        details=f"Application switched to {mode} data mode.",
    )

    return {
        "message": f"The app is now using {mode} data mode.",
        "active_dataset": mode,
        "changed": True,
    }


def switch_dataset_mode(mode, user_id):
    from app.service_modules.transactions import (
        count_manual_transactions,
        count_uploaded_transactions,
    )

    mode = str(mode).strip().lower()

    if mode == "uploaded" and count_uploaded_transactions(user_id) == 0:
        return {
            "message": "No uploaded CSV data is available for your account. Upload a CSV before using uploaded mode.",
            "active_dataset": get_active_dataset_mode(user_id),
            "changed": False,
        }

    if mode == "manual" and count_manual_transactions(user_id) == 0:
        return {
            "message": "No manual transactions are available for your account. Add manual transactions before using manual mode.",
            "active_dataset": get_active_dataset_mode(user_id),
            "changed": False,
        }

    return set_active_dataset_mode(mode, user_id)


def get_data_status(user_id):
    from app.service_modules.transactions import (
        count_manual_transactions,
        count_mock_transactions,
        count_uploaded_transactions,
    )

    active_dataset = get_active_dataset_mode(user_id)

    messages = {
        "mock": "The app is using the original mock/demo dataset.",
        "uploaded": "The app is using your uploaded CSV data only.",
        "manual": "The app is using your manually added transactions only.",
        "combined": "The app is using mock data, your uploaded CSV data and your manual transactions together.",
    }

    return {
        "active_dataset": active_dataset,
        "mock_transactions": count_mock_transactions(),
        "uploaded_transactions": count_uploaded_transactions(user_id),
        "manual_transactions": count_manual_transactions(user_id),
        "available_modes": ["mock", "uploaded", "manual", "combined"],
        "message": messages.get(active_dataset, "Unknown data mode."),
    }