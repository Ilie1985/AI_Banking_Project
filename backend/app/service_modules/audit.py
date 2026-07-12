from app.database import select_rows


def get_audit_log(user_id):
    rows = select_rows(
        table_name="audit_log",
        filters={"user_id": user_id},
        order="created_at.desc",
        limit=100,
    )

    return rows