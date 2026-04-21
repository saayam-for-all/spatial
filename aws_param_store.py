import os
import json
from typing import Dict, Optional
import boto3

_CACHE: Dict[str, Dict[str, str]] = {}


def _as_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_json_parameter_value(raw_value: str) -> Dict[str, str]:
    parsed = json.loads(raw_value)
    if not isinstance(parsed, dict):
        raise ValueError("JSON parameter value must be an object")

    # Strict read for the JSON shape currently used in Parameter Store.
    resolved = {
        "host": str(parsed.get("HOST")) if parsed.get("HOST") is not None else None,
        "port": str(parsed.get("PORT")) if parsed.get("PORT") is not None else None,
        "user": str(parsed.get("USERNAME")) if parsed.get("USERNAME") is not None else None,
        "password": str(parsed.get("PASSWORD")) if parsed.get("PASSWORD") is not None else None,
        "dbname": str(parsed.get("DATABASE NAME")) if parsed.get("DATABASE NAME") is not None else None,
        "sslmode": str(parsed.get("SSL")) if parsed.get("SSL") is not None else None,
    }

    resolved = {k: v for k, v in resolved.items() if v is not None}
    return resolved


def get_db_config_from_parameter_name(name: str, region: Optional[str] = None) -> Dict[str, str]:
    cache_key = f"{region or ''}:name:{name}"
    if cache_key in _CACHE:
        return dict(_CACHE[cache_key])

    client = boto3.client("ssm", region_name=region)
    response = client.get_parameter(Name=name, WithDecryption=True)
    value = response["Parameter"]["Value"]

    resolved = _parse_json_parameter_value(value)
    _CACHE[cache_key] = dict(resolved)
    return resolved


def load_db_config() -> Dict[str, str]:
    """
    Load DB config from AWS Parameter Store only.

    Environment variables:
    - PARAM_STORE_PARAM_NAME=/dev/saayam/db/Virginia/Spatial/user (optional, default used if missing)
    - AWS_REGION=us-east-1 (optional)
    - PARAM_STORE_STRICT=true|false (default true)
    """
    param_name = os.environ.get("PARAM_STORE_PARAM_NAME", "/dev/saayam/db/Virginia/Spatial/user")
    region = os.environ.get("AWS_REGION")
    strict = _as_bool(os.environ.get("PARAM_STORE_STRICT"), default=True)

    try:
        config = get_db_config_from_parameter_name(name=param_name, region=region)
    except Exception:
        if strict:
            raise
        return {}

    required = ["host", "dbname", "user", "password"]
    missing = [field for field in required if not config.get(field)]
    if strict and missing:
        missing_str = ", ".join(missing)
        raise RuntimeError(f"Missing required DB config values: {missing_str}")

    return config
