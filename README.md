# Invoice Parser Agent

A multi-agent system for extracting, validating, and exporting invoice data from images or PDFs. Users can upload invoice images, extract key information, validate business rules, and export results to Excel or Google Sheets.

## Features

- **OCR Agent**: Extracts text from invoice images using OCR.
- **Parser Agent**: Parses extracted text to identify names, emails, phone numbers, and dates.
- **Validator Agent**: Validates parsed invoice data against schema and business rules.
- **Exporter Agent**: Exports validated invoices to CSV, XLSX, or Google Sheets.

## Setup

1. **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

2. **Google Sheets Export:**
    - Go to [Google Cloud Console](https://console.cloud.google.com/).
    - Create a Service Account, enable Google Sheets API and Google Drive API.
    - Download your JSON key file and save it as `credentials.json` in the project root.
    - Share your target Google Sheets with the service account email.

3. **Environment Variables:**
    - For OCR agent, set your API key in a `.env` file:
      ```
      API_KEY=your_aimlapi_key
      ```

## Usage

- **Start Agents:**
    - Run each agent as a separate process:
      ```sh
      python [ocr_agent.py](http://_vscodecontentref_/8)
      python [parser_agent.py](http://_vscodecontentref_/9)
      # ...and so on
      ```

- **Test Parsing:**
    - Use `test_client.py` to send a sample request to the parser agent:
      ```sh
      python [test_client.py](http://_vscodecontentref_/10)
      ```

- **Exporting:**
    - Export validated invoices using the exporter agent to CSV, XLSX, or Google Sheets.

## License

MIT License. See [LICENSE](LICENSE) for details.

