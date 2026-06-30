from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from dotenv import dotenv_values
import yaml
import os

app = FastAPI()

# Allow every origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Helper function
# -----------------------------
def to_bool(value):
    return str(value).lower() in ["true", "1", "yes", "on"]


def coerce(key, value):
    if key in ["port", "workers"]:
        return int(value)

    if key == "debug":
        return to_bool(value)

    return str(value)


# -----------------------------
# Defaults
# -----------------------------
defaults = {
    "port": 8318,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):

    # Start with defaults
    config = defaults.copy()

    # -------------------------
    # YAML
    # -------------------------
    with open("config.development.yaml") as f:
        yaml_data = yaml.safe_load(f)

    for k, v in yaml_data.items():
        config[k] = coerce(k, v)

    # -------------------------
    # .env
    # -------------------------
    env_data = dotenv_values(".env")

    for k, v in env_data.items():

        if k == "NUM_WORKERS":
            k = "workers"

        key = k.lower()

        config[key] = coerce(key, v)

    # -------------------------
    # OS Environment Variables
    # -------------------------
    mapping = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env_name, config_name in mapping.items():

        if env_name in os.environ:
            config[config_name] = coerce(
                config_name,
                os.environ[env_name],
            )

    # -------------------------
    # CLI Overrides
    # -------------------------
    for item in set:

        if "=" not in item:
            continue

        key, value = item.split("=", 1)

        config[key] = coerce(key, value)

    # -------------------------
    # Mask secret
    # -------------------------
    config["api_key"] = "****"

    return config