import json
from functools import lru_cache

from django.conf import settings
import gspread
from google.oauth2.service_account import Credentials


SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
]


class GoogleSheetsConfigurationError(RuntimeError):
    """Raised when Google Sheets credentials or identifiers are missing."""


def _credentials():
    if not settings.GOOGLE_SERVICE_ACCOUNT_JSON:
        raise GoogleSheetsConfigurationError(
            'GOOGLE_SERVICE_ACCOUNT_JSON is not configured.'
        )

    try:
        service_account_info = json.loads(settings.GOOGLE_SERVICE_ACCOUNT_JSON)
    except json.JSONDecodeError as error:
        raise GoogleSheetsConfigurationError(
            'GOOGLE_SERVICE_ACCOUNT_JSON must contain valid JSON.'
        ) from error

    return Credentials.from_service_account_info(
        service_account_info,
        scopes=SCOPES,
    )


@lru_cache(maxsize=1)
def _worksheet():
    if not settings.GOOGLE_SHEET_ID:
        raise GoogleSheetsConfigurationError(
            'GOOGLE_SHEET_ID is not configured.'
        )

    client = gspread.authorize(_credentials())
    spreadsheet = client.open_by_key(settings.GOOGLE_SHEET_ID)
    return spreadsheet.worksheet(settings.GOOGLE_SHEET_WORKSHEET)


def append_row(values):
    """Append one application record to the configured worksheet."""
    if not values:
        raise ValueError('values must contain at least one item.')
    _worksheet().append_row(list(values), value_input_option='USER_ENTERED')


def get_records():
    """Return worksheet records as dictionaries using the first row as headers."""
    return _worksheet().get_all_records()