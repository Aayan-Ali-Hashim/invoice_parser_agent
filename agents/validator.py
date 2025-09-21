import uuid
from typing import Dict, Any, List, Optional
import jsonschema
from datetime import datetime

class ValidatorAgent:
    """
    ValidatorAgent -- validates parsed invoice dicts against a schema,
    applies business rules, and normalizes data.
    """

    def __init__(self, schema: Optional[Dict[str, Any]] = None, rules: Optional[Dict[str, Any]] = None):
        self.schema = schema or self._default_schema()
        self.rules = rules or {}

    def _default_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["invoice_number", "date", "vendor", "line_items", "subtotal", "tax", "total"],
            "properties": {
                "invoice_number": {"type": "string"},
                "date": {"type": "string"},
                "vendor": {"type": "string"},
                "line_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["description", "quantity", "unit_price", "total"],
                        "properties": {
                            "description": {"type": "string"},
                            "quantity": {"type": ["number", "integer", "string"]},
                            "unit_price": {"type": ["number", "integer", "string"]},
                            "total": {"type": ["number", "integer", "string"]}
                        }
                    }
                },
                "subtotal": {"type": ["number", "integer", "string"]},
                "tax": {"type": ["number", "integer", "string"]},
                "total": {"type": ["number", "integer", "string"]}
            }
        }

    def validate_schema(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        validator = jsonschema.Draft7Validator(self.schema)
        errors: List[Dict[str, Any]] = []
        for error in validator.iter_errors(data):
            errors.append({
                "message": error.message,
                "path": list(error.path),
                "validator": error.validator
            })
        return errors

    def validate_business_rules(self, data: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        try:
            # Check line items
            for i, item in enumerate(data.get("line_items", [])):
                expected_total = float(item["quantity"]) * float(item["unit_price"])
                if float(item["total"]) != expected_total:
                    errors.append(
                        f"Line item {i}: total mismatch "
                        f"(expected {expected_total}, got {item['total']})"
                    )

            # Subtotal check
            subtotal_expected = sum(float(item["total"]) for item in data.get("line_items", []))
            if float(data.get("subtotal", 0)) != subtotal_expected:
                errors.append(
                    f"Subtotal mismatch (expected {subtotal_expected}, got {data.get('subtotal')})"
                )

            # Total check
            total_expected = float(data.get("subtotal", 0)) + float(data.get("tax", 0))
            if float(data.get("total", 0)) != total_expected:
                errors.append(
                    f"Total mismatch (expected {total_expected}, got {data.get('total')})"
                )

        except Exception as e:
            errors.append(f"Business rule validation error: {str(e)}")

        return errors

    def normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        normalized = data.copy()

        # Normalize date
        try:
            if "date" in normalized:
                parsed_date = datetime.fromisoformat(str(normalized["date"]).replace("/", "-"))
                normalized["date"] = parsed_date.strftime("%Y-%m-%d")
        except Exception:
            pass

        # Trim vendor
        if "vendor" in normalized and isinstance(normalized["vendor"], str):
            normalized["vendor"] = normalized["vendor"].strip()

        # Normalize numbers
        if "line_items" in normalized:
            for item in normalized["line_items"]:
                for field in ["quantity", "unit_price", "total"]:
                    if field in item:
                        item[field] = float(item[field])

        for field in ["subtotal", "tax", "total"]:
            if field in normalized:
                normalized[field] = float(normalized[field])

        return normalized

    def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = {
            "valid": True,
            "schema_errors": [],
            "business_errors": [],
            "normalized_data": self.normalize(data)
        }

        # Schema validation
        schema_errors = self.validate_schema(result["normalized_data"])
        if schema_errors:
            result["valid"] = False
            result["schema_errors"] = schema_errors
            return result

        # Business rules
        business_errors = self.validate_business_rules(result["normalized_data"])
        if business_errors:
            result["valid"] = False
            result["business_errors"] = business_errors

        return result
    def run_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = {
            "status": "success",
            "valid": True,
            "schema_errors": [],
            "business_errors": [],
            "date_errors": [],
            "custom_errors": [],
            "normalized_data": None
        }

        # 1. Normalize
        normalized = self.normalize(data)
        result["normalized_data"] = normalized

        # 2. Schema validation
        schema_errors = self.validate_schema(normalized)
        if schema_errors:
            result["status"] = "failed"
            result["valid"] = False
            result["schema_errors"] = schema_errors
            return result

        # 3. Date validation
        date_errors = self.validate_dates(normalized)
        if date_errors:
            result["status"] = "failed"
            result["valid"] = False
            result["date_errors"] = date_errors
            return result

        # 4. Business rules
        business_errors = self.validate_business_rules(normalized)
        if business_errors:
            result["status"] = "failed"
            result["valid"] = False
            result["business_errors"] = business_errors

        # 5. Custom rules
        custom_errors = self.validate_custom_rules(normalized)
        if custom_errors:
            result["status"] = "failed"
            result["valid"] = False
            result["custom_errors"] = custom_errors

        return result


    def validate_dates(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate invoice dates:
        - Must be valid format
        - Must not be in the future
        """
        errors: List[str] = []
        try:
            invoice_date = data.get("date")
            if not invoice_date:
                errors.append("Missing invoice date")
                return errors

            # Parse date (accepts YYYY-MM-DD or YYYY/MM/DD)
            parsed_date = None
            try:
                parsed_date = datetime.fromisoformat(invoice_date.replace("/", "-"))
            except Exception:
                errors.append(f"Invalid date format: {invoice_date}")
                return errors

            # Future date check
            today = datetime.now().date()
            if parsed_date.date() > today:
                errors.append(f"Invoice date {invoice_date} is in the future")

        except Exception as e:
            errors.append(f"Date validation error: {str(e)}")

        return errors
    def validate_custom_rules(self, data: Dict[str, Any]) -> List[str]:
        """
        Apply custom business rules.
        Rules can be extended by modifying self.rules.
        """
        errors: List[str] = []

        # Rule 1: Vendor must not be empty
        if not data.get("vendor"):
            errors.append("Vendor is missing or empty")

        # Rule 2: Tax must not exceed 20% of subtotal
        try:
            subtotal = float(data.get("subtotal", 0))
            tax = float(data.get("tax", 0))
            if subtotal > 0:
                tax_rate = tax / subtotal
                if tax_rate > 0.2:
                    errors.append(f"Tax rate too high: {tax_rate:.2%} (max 20%)")
        except Exception:
            errors.append("Error calculating tax rate")

        # Rule 3: Invoice number must start with 'INV-'
        invoice_number = str(data.get("invoice_number", ""))
        if not invoice_number.startswith("INV-"):
            errors.append(f"Invalid invoice number format: {invoice_number}")

        return errors
    def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an incoming A2A message and return a response message.
        """
        msg_type = message.get("type")
        msg_id = message.get("id", str(uuid.uuid4()))
        sender = message.get("from", "unknown")

        response: Dict[str, Any] = {
            "id": f"resp-{msg_id}",
            "type": f"{msg_type}.response",
            "from": "validator-agent",
            "to": sender,
            "body": {}
        }

        if msg_type == "validate.invoice":
            invoice = message.get("body", {}).get("invoice")
            if not invoice:
                response["body"] = {
                    "status": "FAIL",
                    "error": "Missing invoice payload"
                }
                return response

            # Run validation pipeline
            result = self.run_data(invoice)
            response["body"] = result
            return response

        # Unknown message type
        response["body"] = {"status": "FAIL", "error": f"Unsupported type {msg_type}"}
        return response