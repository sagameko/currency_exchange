from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILE = PROJECT_ROOT / "config" / "settings.yaml"


@dataclass(frozen=True)
class Settings:
    api_base_url: str
    api_timeout: int
    base_currency: str
    currencies: list[str]
    initial_start_date: date
    lookback_days: int
    raw_dir: Path
    clean_dir: Path
    database: Path
    log_dir: Path
    max_bad_ratio: float


def load_settings(config_file: Path = CONFIG_FILE) -> Settings:
    if not config_file.exists():
        raise FileNotFoundError(f"Config file cant be found: {config_file}")

    with open(config_file, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    api, rates, incremental, paths = (
        cfg["api"],
        cfg["rates"],
        cfg["incremental"],
        cfg["paths"],
    )

    start = incremental["initial_start_date"]
    if isinstance(start, str):  # in case someone writes it in quotes
        start = date.fromisoformat(start)

    return Settings(
        api_base_url=api["base_url"],
        api_timeout=api["timeout_seconds"],
        base_currency=rates["base_currency"],
        currencies=rates["currencies"],
        initial_start_date=start,
        lookback_days=incremental["lookback_days"],
        raw_dir=PROJECT_ROOT / paths["raw_dir"],
        clean_dir=PROJECT_ROOT / paths["clean_dir"],
        database=PROJECT_ROOT / paths["database"],
        log_dir=PROJECT_ROOT / paths["log_dir"],
        max_bad_ratio=cfg["quality"]["max_bad_ratio"],
    )
