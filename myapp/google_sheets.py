import csv
import io
import urllib.error
import urllib.parse
import urllib.request


class GoogleSheetError(Exception):
    """Raised when the configured Google Sheet cannot be read."""


def fetch_sheet_data(sheet_id, gid="", csv_url=""):
    if csv_url:
        export_url = csv_url
    elif sheet_id:
        query = {"format": "csv"}
        if gid:
            query["gid"] = gid
        export_url = (
            f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?"
            f"{urllib.parse.urlencode(query)}"
        )
    else:
        raise GoogleSheetError("GOOGLE_SHEET_ID is not configured.")

    request = urllib.request.Request(
        export_url,
        headers={"User-Agent": "AarogyaGroup/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8-sig")
    except (urllib.error.URLError, TimeoutError, UnicodeDecodeError) as error:
        raise GoogleSheetError(f"Could not connect to Google Sheets: {error}") from error

    if not body.strip():
        raise GoogleSheetError(
            "The sheet returned no data. Set sharing to 'Anyone with the link: Viewer' "
            "or configure a CSV URL with access."
        )

    rows = list(csv.reader(io.StringIO(body)))
    if not rows:
        raise GoogleSheetError("The Google Sheet is empty.")

    headers = [header.strip() or f"Column {index}" for index, header in enumerate(rows[0], 1)]
    data = []
    table_rows = []
    for row in rows[1:]:
        values = row + [""] * (len(headers) - len(row))
        values = values[:len(headers)]
        if not any(value.strip() for value in values):
            continue
        table_rows.append(values)
        data.append(dict(zip(headers, values)))

    return {"headers": headers, "rows": data, "table_rows": table_rows}
