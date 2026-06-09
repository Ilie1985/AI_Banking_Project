import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"


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


def clean_env_value(value):
    value = value.strip()
    value = value.strip('"')
    value = value.strip("'")
    value = value.rstrip(";")
    return value.strip()


SUPABASE_URL = read_env_value("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = read_env_value("SUPABASE_SERVICE_ROLE_KEY")


def check_supabase_config():
    if not SUPABASE_URL:
        raise ValueError("SUPABASE_URL is missing from .env")

    if not SUPABASE_URL.startswith("https://"):
        raise ValueError("SUPABASE_URL must start with https://")

    if not SUPABASE_URL.endswith(".supabase.co"):
        raise ValueError("SUPABASE_URL must end with .supabase.co")

    if not SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY is missing from .env")


def initialise_database():
    check_supabase_config()


def build_query(params):
    if not params:
        return ""

    return "?" + urllib.parse.urlencode(params)


def supabase_request(method, table_name, params=None, payload=None):
    check_supabase_config()

    url = f"{SUPABASE_URL}/rest/v1/{table_name}{build_query(params)}"

    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "return=representation",
    }

    data = None

    if payload is not None:
      data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url=url,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            response_body = response.read().decode("utf-8")

            if not response_body:
                return []

            return json.loads(response_body)

    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8")
        raise ValueError(
            f"Supabase request failed: {error.code} {error.reason} {error_body}"
        )

    except Exception as error:
        raise ValueError(f"Supabase request failed: {str(error)}")


def select_rows(
    table_name,
    filters=None,
    columns="*",
    order=None,
    limit=None,
):
    params = {
        "select": columns,
    }

    if filters:
        for key, value in filters.items():
            params[key] = f"eq.{value}"

    if order:
        params["order"] = order

    if limit:
        params["limit"] = str(limit)

    return supabase_request(
        method="GET",
        table_name=table_name,
        params=params,
    )


def insert_row(table_name, row):
    result = supabase_request(
        method="POST",
        table_name=table_name,
        payload=row,
    )

    if result:
        return result[0]

    return None


def insert_rows(table_name, rows):
    if not rows:
        return []

    return supabase_request(
        method="POST",
        table_name=table_name,
        payload=rows,
    )


def delete_rows(table_name, filters):
    params = {}

    for key, value in filters.items():
        params[key] = f"eq.{value}"

    return supabase_request(
        method="DELETE",
        table_name=table_name,
        params=params,
    )


def upsert_row(table_name, row, conflict_column):
    params = {
        "on_conflict": conflict_column,
    }

    check_supabase_config()

    url = f"{SUPABASE_URL}/rest/v1/{table_name}{build_query(params)}"

    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation",
    }

    data = json.dumps(row).encode("utf-8")

    request = urllib.request.Request(
        url=url,
        data=data,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            response_body = response.read().decode("utf-8")

            if not response_body:
                return None

            result = json.loads(response_body)

            if result:
                return result[0]

            return None

    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8")
        raise ValueError(
            f"Supabase upsert failed: {error.code} {error.reason} {error_body}"
        )


def add_audit_log(
    action,
    record_type,
    user_id,
    record_id=None,
    source=None,
    details=None,
):
    row = {
        "user_id": user_id,
        "action": action,
        "record_type": record_type,
        "record_id": record_id,
        "source": source,
        "details": details,
    }

    insert_row("audit_log", row)