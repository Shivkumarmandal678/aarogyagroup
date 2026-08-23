## Google Sheets setup

The worker and employer dashboards load their table data from the configured Google Sheet.

1. Open the sheet's Share dialog and set General access to `Anyone with the link` / `Viewer`.
2. Add these values to `.env`:

```env
GOOGLE_SHEET_ID=1iRNlkAgDdrfET5DEqKG_ZeCwQiUqmoge4emB_2cbWQg
GOOGLE_SHEET_GID=
```

Set `GOOGLE_SHEET_GID` to a tab's numeric `gid` when the spreadsheet has multiple tabs. If the sheet cannot be made public, provide an authenticated CSV proxy URL instead:

```env
GOOGLE_SHEET_CSV_URL=https://your-domain.example/sheet.csv
```

The first row is used as the table header and every following row is displayed on both dashboards.

The `Employee_Login_System` tab supplies employee `Username`, `Password`, and `Status`. The `Client_Details` tab is currently read-only through CSV export. Writing back to Google Sheets requires a Google Sheets API service account or a protected Apps Script endpoint; do not place those credentials in the public CSV URL.
