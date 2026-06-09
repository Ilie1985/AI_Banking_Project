from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
CONFIG_PATH = BASE_DIR / "frontend" / "config.js"


def read_env_file():
    values = {}

    if not ENV_PATH.exists():
        raise FileNotFoundError(
            "No .env file found. Create a .env file in the AI_Banking folder first."
        )

    with ENV_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                continue

            key, value = line.split("=", 1)

            value = value.strip()
            value = value.strip('"')
            value = value.strip("'")
            value = value.rstrip(";").strip()

            values[key.strip()] = value

    return values


def main():
    env_values = read_env_file()

    supabase_url = env_values.get("SUPABASE_URL")
    supabase_anon_key = env_values.get("SUPABASE_ANON_KEY")
    api_base = env_values.get("API_BASE", "http://127.0.0.1:8000")

    if not supabase_url or not supabase_anon_key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_ANON_KEY must both exist in your .env file."
        )

    config_content = f"""window.APP_CONFIG = {{
  SUPABASE_URL: "{supabase_url}",
  SUPABASE_ANON_KEY: "{supabase_anon_key}",
  API_BASE: "{api_base}",
}};
"""

    CONFIG_PATH.write_text(config_content, encoding="utf-8")

    print("frontend/config.js created successfully from .env")


if __name__ == "__main__":
    main()