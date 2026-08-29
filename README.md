## Google Sheets setup

The Django SQLite database remains enabled for Django's built-in auth and
session tables. Application records can be stored in Google Sheets through
`myapp.google_sheets.append_row()` and read with
`myapp.google_sheets.get_records()`.

To enable writes:

1. Create a Google Cloud service account and enable the Google Sheets API.
2. Share the target spreadsheet with the service account email as `Editor`.
3. Add the service-account JSON as one-line JSON in `.env` (never commit it):

```env
GOOGLE_SHEET_ID=your_spreadsheet_id
GOOGLE_SHEET_WORKSHEET=Client_Details
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
```

The first row of `Client_Details` should contain column headings. The helper
does not create application models or copy existing SQLite rows automatically;
call `append_row()` from the view that receives the form submission.

For public, read-only tables, the CSV settings below can still be used by a
separate reader, but public CSV export cannot write to Google Sheets.

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

The `Client_Details` tab can receive writes through the service-account helper
above. Do not place service-account credentials in a public CSV URL.

## Role dashboard workflow

The dashboard action endpoint expects the Google Apps Script web app to support
these JSON `action` values: `add_booking`, `update_booking`, `delete_booking`,
`add_report`, `update_report`, and `delete_report`. The read actions are
`get_admins`, `get_bookings`, and `get_reports`.

Create a `Reports` tab with this header row:

```text
ID,Booking_ID,Patient_Name,Patient_Email,Test_Name,Result,Report_File,Doctor,Doctor_Status,Manager_Status,Staff_Status,User_Status,Updated_By,Updated_At
```

Report workflow is sequential: a doctor creates the report, a manager approves
it, staff gives the final approval, and only then does it become visible in the
user dashboard. Admin can manage all records; other roles receive only their
role-specific actions and records.

The `Booking` tab should use this header row for the public booking form. `Timestamp` and `Status` are generated server-side and are not form fields:

```text
Timestamp,Name,Phone,Email,Address,Passport_Number,Lot_Number,Service,Country,Passport_Copy,Date,Message,Status
```

Passport copies are required and accept JPG, PNG, or PDF files up to 5 MB. They are stored under
the private media directory; the sheet records the internal file reference.
