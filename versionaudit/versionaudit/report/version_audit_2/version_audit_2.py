# Copyright (c) 2024, Rehan and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.utils import get_datetime

def execute(filters=None):
    doctype = filters.get("doctype")
    docname_filter = filters.get("docname")  # Get the optional document name filter
    columns, data = [], []

    # Dynamically retrieve all fields for the specified doctype, excluding layout fields
    meta = frappe.get_meta(doctype)
    fields = [
        field.fieldname for field in meta.fields
        if field.fieldtype not in ["Tab Break", "Section Break", "Column Break"]
    ]

    # Define columns dynamically based on the doctype fields
    columns.append({"label": "Document", "fieldname": "docname", "fieldtype": "Data", "width": 150})
    columns.append({"label": "Change Instance", "fieldname": "change_instance", "fieldtype": "Data", "width": 150})
    for field in fields:
        columns.append({"label": field, "fieldname": field, "fieldtype": "Data", "width": 150})
    columns.append({"label": "Changed By", "fieldname": "changed_by", "fieldtype": "Data", "width": 150})
    columns.append({"label": "Changed On", "fieldname": "timestamp", "fieldtype": "Datetime", "width": 150})

    # Fetch documents based on filters
    if docname_filter:
        documents = frappe.get_all(doctype, fields=["name"], filters={"name": docname_filter})
    else:
        documents = frappe.get_all(doctype, fields=["name"])

    for doc in documents:
        docname = doc.name

        # Fetch the document's current values
        current_doc = frappe.get_doc(doctype, docname)
        current_values = {field: current_doc.get(field) for field in fields}

        # Initialize initial values from the current document
        initial_values = {field: current_values[field] for field in fields}

        # Fetch all version logs for this document, ordered by modification date (ascending)
        version_logs = frappe.get_all(
            "Version",
            filters={"ref_doctype": doctype, "docname": docname},
            fields=["data", "modified_by", "modified"],
            order_by="modified ASC"
        )

        # Update initial values dynamically based on the version logs
        for log in version_logs:
            version_data = json.loads(log["data"])
            for change in version_data.get("changed", []):
                field_name, old_value, _ = change

                # Set the initial value from the log only if it's not already captured
                if field_name in initial_values and initial_values[field_name] == current_values[field_name]:
                    initial_values[field_name] = old_value

        # Add the initial row with captured initial values
        initial_row = {
            "docname": docname,
            "change_instance": "Initial Value",
            **initial_values,  # Include the initial values here
            "changed_by": "-",
            "timestamp": "-"
        }
        data.append(initial_row)

        # Process version logs and capture changes for each change instance
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
                field_name, _, new_value = change
                if field_name in row:
                    row[field_name] = new_value  # Update the row with new values

            # Add the row for this change to the data
            data.append(row)

        # Add the last row with current values
        current_row = {
            "docname": docname,
            "change_instance": "Current Value",
            **current_values,  # Include the current values here
            "changed_by": "-",  # No specific user for current values
            "timestamp": "-"    # No specific timestamp for current values
        }
        data.append(current_row)

    return columns, data