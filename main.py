from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import yaml
import os

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load .env
load_dotenv()

# Default configuration
DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def load_yaml():
    """Load config.development.yaml if it exists."""
    try:
        with open("config.development.yaml", "r") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def load_dotenv_config():
    """Read values from .env (already loaded into os.environ)."""
    config = {}

    mapping = {
        "PORT": "port",
        "DEBUG": "debug",
        "LOG_LEVEL": "log_level",
        "API_KEY": "api_key",
    }

    for env_key, config_key in mapping.items():
        value = os.getenv(env_key)
        if value is not None:
            config[config_key] = value

    # Special alias
    num_workers = os.getenv("NUM_WORKERS")
    if num_workers is not None:
        config["workers"] = num_workers

    return config


def load_os_config():
    """Read APP_* environment variables."""
    config = {}

    mapping = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env_key, config_key in mapping.items():
        value = os.getenv(env_key)
        if value is not None:
            config[config_key] = value

    return config


def coerce_types(config):
    """Convert values to required types."""

    if "port" in config:
        config["port"] = int(config["port"])

    if "workers" in config:
        config["workers"] = int(config["workers"])

    if "debug" in config:
        config["debug"] = str(config["debug"]).lower() in (
            "true",
            "1",
            "yes",
            "on",
        )

    if "log_level" in config:
        config["log_level"] = str(config["log_level"])

    return config


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    # Merge configuration layers
    config = DEFAULTS.copy()
    config.update(load_yaml())
    config.update(load_dotenv_config())
    config.update(load_os_config())

    # Apply CLI overrides
    overrides = {}
    for item in set:
        if "=" in item:
            key, value = item.split("=", 1)
            overrides[key] = value

    config.update(overrides)

    # Convert types
    config = coerce_types(config)

    # Mask API key
    config["api_key"] = "****"

    return config