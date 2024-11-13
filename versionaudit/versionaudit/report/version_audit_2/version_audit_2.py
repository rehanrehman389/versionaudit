# Copyright (c) 2024, Rehan and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.utils import get_datetime

def execute(filters=None):
    doctype = filters.get("doctype", "Contact")  # Default to Contact if doctype is not provided
    columns, data = [], []

    # Dynamically retrieve all fields for the specified doctype
    meta = frappe.get_meta(doctype)
    fields = [field.fieldname for field in meta.fields]

    # Define columns dynamically based on the doctype fields
    columns.append({"label": "Document", "fieldname": "docname", "fieldtype": "Data", "width": 150})
    columns.append({"label": "Change Instance", "fieldname": "change_instance", "fieldtype": "Data", "width": 150})
    for field in fields:
        columns.append({"label": field, "fieldname": field, "fieldtype": "Data", "width": 150})
    columns.append({"label": "Changed By", "fieldname": "changed_by", "fieldtype": "Data", "width": 150})
    columns.append({"label": "Changed On", "fieldname": "timestamp", "fieldtype": "Datetime", "width": 150})

    # Fetch all documents for the specified doctype
    documents = frappe.get_all(doctype, fields=["name"])

    for doc in documents:
        docname = doc.name

        # Fetch all version logs for this document, ordered by modification date (ascending)
        version_logs = frappe.get_all(
            "Version",
            filters={"ref_doctype": doctype, "docname": docname},
            fields=["data", "modified_by", "modified"],
            order_by="modified ASC"
        )

        # Initialize initial values as None
        initial_values = {field: None for field in fields}
        current_values = {field: None for field in fields}  # To track current values for each field

        # Check if the first version log exists, and extract initial values from it
        if version_logs:
            first_version_log = json.loads(version_logs[0]["data"])
            for change in first_version_log.get("changed", []):
                field_name, old_value, new_value = change
                if field_name in initial_values and initial_values[field_name] is None:
                    initial_values[field_name] = old_value  # Set the initial value from the first change log

        # Initialize the initial row to be added first
        initial_row = {
            "docname": docname,
            "change_instance": "Initial Value",
            **initial_values,  # Include the initial values here
            "changed_by": "-",
            "timestamp": "-"
        }

        # Add the initial row as the first row
        data.append(initial_row)

        # Process version logs and capture changes
        for idx, log in enumerate(version_logs):
            version_data = json.loads(log["data"])

            # Prepare a row for each version change
            row = {
                "docname": docname,
                "change_instance": f"Change {idx + 1}",
                "changed_by": log["modified_by"],
                "timestamp": get_datetime(log["modified"])
            }

            # Mark all fields as blank initially
            for field in fields:
                row[field] = ""  # Set to blank for all fields initially

            # Update the row with changes, but only for fields that have changed
            for change in version_data.get("changed", []):
                field_name, old_value, new_value = change
                if field_name in row:
                    row[field_name] = new_value  # Update the row with new values
                    current_values[field_name] = new_value  # Track the updated value

            # Add the row for this change to the data
            data.append(row)

    return columns, data