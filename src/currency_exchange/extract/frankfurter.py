import requests
import json
import logging
import time
from datetime import date, datetime, timezone
from pathlib import Path

from currency_exchange.config import Settings

logger = logging.getLogger(__name__)

RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 3

class ExtractError(Exception):
    """Raised when exchange rates could not be fetched"""

def fetch_rates(start: date, end: date, settings: Settings) -> dict:

    url = f"{settings.api_base_url}/{start}..{end}"
    params = {"base": settings.base_currency, "symbols": ",".join(settings.currencies)}

    error = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(url, params= params, timeout= settings.api_timeout)
        except (requests.ConnectionError, requests.Timeout) as e:
            error = f"{type(e).__name__} : {e}"
        else:
            if response.status_code == 200:
                return response.json()
            if response.status_code not in RETRY_STATUS_CODES:
                raise ExtractError(
                    f"{start} to {end}: HTTP {response.status_code} - {response.text[:200]}"
                )

            error = f"HTTP {response.status_code}"

        if attempt < MAX_ATTEMPTS:
            wait_seconds = 2 ** attempt                        # 2s, then 4s
            logger.warning("%s to %s: attempt %d/%d failed (%s). Retrying in %ds",
                           start, end, attempt, MAX_ATTEMPTS, error, wait_seconds)
            time.sleep(wait_seconds)

    raise ExtractError(f"{start} to {end}: failed after {MAX_ATTEMPTS} attempts ({error})")

def raw_path(settings: Settings, start: date, end: date) -> Path:
    return settings.raw_dir / "frankfurter" / f"{start}_{end}.json"

def save_raw(payload: dict, start: date, end: date, settings: Settings) -> Path:
    path = raw_path(settings, start, end)
    path.parent.mkdir(parents= True, exist_ok= True)

    record = {
        "source": "frankfurter",
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "requested_start_date": start.isoformat(),
        "requested_end_date": end.isoformat(),
        "base_currency": settings.base_currency,
        "currencies": settings.currencies,
        "payload": payload,                                    # the API response, unchanged
    }

    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(record, indent=2), encoding= "utf-8")
    tmp_path.replace(path)
    return path

def check_currencies(payload: dict, settings: Settings) -> None:
    """Fail if the API silently left out any requested currency."""
    returned = set()
    for day_rates in payload.get("rates", {}).values():
        returned.update(day_rates.keys())

    missing = set(settings.currencies) - returned
    if missing:
        raise ExtractError(
            f"API returned no rates for: {', '.join(sorted(missing))}. "
            f"Check the currency codes in config/settings.yaml"
        )

    
def extract(settings: Settings, start: date, end: date) -> Path:
    """Fetch one date range and save it as a raw file."""
    logger.info("Extracting %s rates for %s from %s to %s",
                settings.base_currency, ", ".join(settings.currencies), start, end)
    payload = fetch_rates(start, end, settings)
    check_currencies(payload, settings)

    days = len(payload.get("rates", {}))
    returned_start = payload.get("start_date")
    if returned_start and date.fromisoformat(returned_start) < start:
        logger.warning("API returned data from %s, earlier than the requested %s "
                       "(the requested start was not a publishing day)", returned_start, start)

    path = save_raw(payload, start, end, settings)
    logger.info("Saved %d days of rates to %s", days, path)
    return path