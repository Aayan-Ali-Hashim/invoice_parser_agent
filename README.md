# Invoice Parser Agent 
This is a Multi Agent system
Users can upload the image of invoice or pdf of it and extract all important info from it in a excel file.

## Google Sheets Setup

To enable exporting invoices to Google Sheets:

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a Service Account, enable Google Sheets API + Google Drive API.
3. Download your JSON key file and save it as `credentials.json` in the project root.
4. Share your target Google Sheets with the service account email.
