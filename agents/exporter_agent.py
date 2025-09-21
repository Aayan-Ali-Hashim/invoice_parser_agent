import uuid
import os
import pandas as pd
from typing import Dict, Any


class ExporterAgent:
    """
    ExporterAgent
    -------------
    Handles exporting invoices to CSV, XLSX, or Google Sheets.
    Communicates with other agents using A2A messages.
    """

    def __init__(self, export_dir: str = "exports"):
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)

    # ----------------------
    # Export Helpers
    # ----------------------
    def export_csv(self, invoice: Dict[str, Any], filename: str) -> str:
        filepath = f"{self.export_dir}/{filename}.csv"
        df = pd.DataFrame(invoice["line_items"])
        df.to_csv(filepath, index=False)
        return filepath

    def export_xlsx(self, invoice: Dict[str, Any], filename: str) -> str:
        filepath = f"{self.export_dir}/{filename}.xlsx"
        df = pd.DataFrame(invoice["line_items"])

        with pd.ExcelWriter(filepath, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Line Items", index=False)

            # Write summary on second sheet
            summary = writer.book.add_worksheet("Summary")
            summary.write(0, 0, "Invoice Number")
            summary.write(0, 1, invoice["invoice_number"])
            summary.write(1, 0, "Vendor")
            summary.write(1, 1, invoice["vendor"])
            summary.write(2, 0, "Date")
            summary.write(2, 1, invoice["date"])
            summary.write(3, 0, "Subtotal")
            summary.write(3, 1, invoice["subtotal"])
            summary.write(4, 0, "Tax")
            summary.write(4, 1, invoice["tax"])
            summary.write(5, 0, "Total")
            summary.write(5, 1, invoice["total"])

        return filepath

    def export_gsheets(self, invoice: Dict[str, Any], sheet_name: str) -> str:
        """Export invoice to Google Sheets (returns sheet URL)"""
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials

        scope = ["https://spreadsheets.google.com/feeds",
                 "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)

        # Create new sheet
        spreadsheet = client.create(sheet_name)

        # Fill Line Items
        worksheet = spreadsheet.add_worksheet(title="Line Items", rows="100", cols="20")
        df = pd.DataFrame(invoice["line_items"])
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())

        # Fill Summary
        summary = spreadsheet.add_worksheet(title="Summary", rows="10", cols="2")
        summary.update([
            ["Invoice Number", invoice["invoice_number"]],
            ["Vendor", invoice["vendor"]],
            ["Date", invoice["date"]],
            ["Subtotal", invoice["subtotal"]],
            ["Tax", invoice["tax"]],
            ["Total", invoice["total"]]
        ])

        return f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"

    # ----------------------
    # A2A Message Handler
    # ----------------------
    def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming A2A messages and return structured responses.
        """
        msg_type = message.get("type")
        msg_id = message.get("id", str(uuid.uuid4()))
        sender = message.get("from", "unknown")

        response = {
            "id": f"resp-{msg_id}",
            "type": f"{msg_type}.response",
            "from": "exporter-agent",
            "to": sender,
            "body": {}
        }

        if msg_type == "export.invoice":
            body = message.get("body", {})
            invoice = body.get("invoice")
            fmt = body.get("format", "csv").lower()

            if not invoice:
                response["body"] = {"status": "FAIL", "error": "Missing invoice payload"}
                return response

            try:
                filename = invoice.get("invoice_number", "invoice").replace(" ", "_")

                if fmt == "csv":
                    filepath = self.export_csv(invoice, filename)
                    response["body"] = {"status": "PASS", "file": filepath}

                elif fmt in ["xls", "xlsx", "excel"]:
                    filepath = self.export_xlsx(invoice, filename)
                    response["body"] = {"status": "PASS", "file": filepath}

                elif fmt in ["gsheets", "google", "sheets"]:
                    url = self.export_gsheets(invoice, filename)
                    response["body"] = {"status": "PASS", "url": url}

                else:
                    response["body"] = {"status": "FAIL", "error": f"Unsupported format {fmt}"}

                return response

            except Exception as e:
                response["body"] = {"status": "FAIL", "error": str(e)}
                return response

        # Unknown message type
        response["body"] = {"status": "FAIL", "error": f"Unsupported type {msg_type}"}
        return response
