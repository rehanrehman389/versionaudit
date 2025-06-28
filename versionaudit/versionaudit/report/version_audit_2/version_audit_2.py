# Copyright (c) 2024, Rehan and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.utils import get_datetime

def execute(filters=None):
    doctype = filters.get("doctype")
    docname_filter = filters.get("docname")
    view_type = filters.get("view_type")
    selected_child_table = filters.get("child_table")
    include_empty_fields = filters.get("include_empty_fields")
    columns, data = [], []

    meta = frappe.get_meta(doctype)

    # ----------- CHILD TABLE VIEW -----------
    if view_type == "Child Table Diff" and selected_child_table:
        columns = [
            {"label": "Document", "fieldname": "docname", "fieldtype": "Data", "width": 150},
            {"label": "Change Instance", "fieldname": "change_instance", "fieldtype": "Link", "options": "Version", "width": 150},
            {"label": "Row #", "fieldname": "idx", "fieldtype": "Int", "width": 80},
            {"label": "Field", "fieldname": "field", "fieldtype": "Data", "width": 120},
            {"label": "Old Value", "fieldname": "old_value", "fieldtype": "Data", "width": 150},
            {"label": "New Value", "fieldname": "new_value", "fieldtype": "Data", "width": 150},
            {"label": "Changed By", "fieldname": "changed_by", "fieldtype": "Data", "width": 120},
            {"label": "Changed On", "fieldname": "timestamp", "fieldtype": "Datetime", "width": 150}
        ]

        docname_filters = {"name": ["in", docname_filter]} if docname_filter else {}
        documents = frappe.get_all(doctype, fields=["name"], filters=docname_filters)

        for doc in documents:
            docname = doc.name
            version_logs = frappe.get_all(
                "Version",
                filters={"ref_doctype": doctype, "docname": docname},
                fields=["name", "data", "modified_by", "modified"],
                order_by="modified ASC"
            )

            for log in version_logs:
                version_data = json.loads(log["data"])
                for row_change in version_data.get("row_changed", []):
                    if row_change["parentfield"] != selected_child_table:
                        continue
                    idx = row_change.get("idx")
                    for change in row_change.get("changed", []):
                        fieldname, old_val, new_val = change
                        data.append({
                            "docname": docname,
                            "change_instance": log["name"],
                            "idx": idx,
                            "field": fieldname,
                            "old_value": old_val,
                            "new_value": new_val,
                            "changed_by": log["modified_by"],
                            "timestamp": get_datetime(log["modified"])
                        })
        return columns, data

    # ----------- DOCUMENT LEVEL VIEW -----------
    fields = [
        field.fieldname for field in meta.fields
        if field.fieldtype not in ["Tab Break", "Section Break", "Column Break"]
    ]

    docname_filters = {"name": ["in", docname_filter]} if docname_filter else {}
    documents = frappe.get_all(doctype, fields=["name"], filters=docname_filters)

    field_value_tracker = {field: [] for field in fields}
    temp_data = []

    for doc in documents:
        docname = doc.name
        current_doc = frappe.get_doc(doctype, docname)
        current_values = {field: current_doc.get(field) for field in fields}
        initial_values = {field: current_values[field] for field in fields}

        version_logs = frappe.get_all(
            "Version",
            filters={"ref_doctype": doctype, "docname": docname},
            fields=["name", "data", "modified_by", "modified"],
            order_by="modified ASC"
        )

        for log in version_logs:
            version_data = json.loads(log["data"])
            for change in version_data.get("changed", []):
                field_name, old_value, _ = change
                if field_name in initial_values and initial_values[field_name] == current_values[field_name]:
                    initial_values[field_name] = old_value

        initial_row = {
            "docname": docname,
            "change_instance": "Initial Value",
            **initial_values,
            "changed_by": current_doc.owner,
            "timestamp": get_datetime(current_doc.creation)
        }
        temp_data.append(initial_row)

        for field in fields:
            field_value_tracker[field].append(initial_row.get(field))

        for log in version_logs:
            version_data = json.loads(log["data"])
            if not any(key in version_data for key in ["added", "changed", "data_import", "removed", "row_changed"]):
                continue

            row = {
                "docname": docname,
                "change_instance": log["name"],
                "changed_by": log["modified_by"],
                "timestamp": get_datetime(log["modified"])
            }

            for field in fields:
                row[field] = "No Change"

            for change in version_data.get("changed", []):
                field_name, _, new_value = change
                if field_name in row:
                    row[field_name] = new_value

            for field in fields:
                field_value_tracker[field].append(row.get(field))

            temp_data.append(row)

        current_row = {
            "docname": docname,
            "change_instance": "Current Value",
            **current_values,
            "changed_by": "-",
            "timestamp": "-"
        }
        temp_data.append(current_row)

        for field in fields:
            field_value_tracker[field].append(current_row.get(field))

    # ✅ Filter empty fields properly
    if not include_empty_fields:
        fields = [
            field for field in fields
            if any(val not in [None, "", "No Change"] for val in field_value_tracker[field])
        ]

    columns = [
        {"label": "Document", "fieldname": "docname", "fieldtype": "Data", "width": 150},
        {"label": "Change Instance", "fieldname": "change_instance", "fieldtype": "Link", "options": "Version", "width": 150}
    ]
    for field in fields:
        columns.append({"label": field, "fieldname": field, "fieldtype": "Data", "width": 150})
    columns.extend([
        {"label": "Changed By", "fieldname": "changed_by", "fieldtype": "Data", "width": 150},
        {"label": "Changed On", "fieldname": "timestamp", "fieldtype": "Datetime", "width": 150}
    ])

    final_data = []
    for row in temp_data:
        filtered_row = {k: v for k, v in row.items() if k in fields or k in ["docname", "change_instance", "changed_by", "timestamp"]}
        final_data.append(filtered_row)

    return columns, final_data


# ✅ New API method to fetch child tables for a doctype
@frappe.whitelist()
def get_child_tables(doctype):
    meta = frappe.get_meta(doctype)
    return [
        {"label": df.label, "value": df.fieldname}
        for df in meta.fields if df.fieldtype == "Table"
    ]
