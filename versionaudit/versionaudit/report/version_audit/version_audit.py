# Copyright (c) 2024, Rehan and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.utils import get_datetime


def execute(filters=None):
    # columns, data = [], []
    columns = [
        {"label": "Document", "fieldname": "docname", "fieldtype": "Data", "width": 150},
        {"label": "Field", "fieldname": "field_name", "fieldtype": "Data", "width": 150},
        {"label": "Previous Value", "fieldname": "prev_value", "fieldtype": "Data", "width": 150},
        {"label": "New Value", "fieldname": "new_value", "fieldtype": "Data", "width": 150},
        {"label": "Changed On", "fieldname": "timestamp", "fieldtype": "Datetime", "width": 150},
        {"label": "Changed By", "fieldname": "changed_by", "fieldtype": "Data", "width": 150},
    ]

    data = []
    version_logs = frappe.get_all(
        "Version",
        filters={"ref_doctype": "Contact"},
        fields=["data", "docname", "modified_by", "modified"],
        order_by="modified ASC"
    )

    for log in version_logs:
        version_data = json.loads(log["data"])
        docname = log["docname"]
        changed_by = log["modified_by"]
        timestamp = get_datetime(log["modified"])

        for change in version_data.get("changed", []):
            field_name, prev_value, new_value = change
            data.append({
                "docname": docname,
                "field_name": field_name,
                "prev_value": prev_value,
                "new_value": new_value,
                "timestamp": timestamp,
                "changed_by": changed_by,
            })
    return columns, data
