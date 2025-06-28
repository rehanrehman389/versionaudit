# Copyright (c) 2024, Rehan and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.utils import get_datetime

def execute(filters=None):
    doctype = filters.get("doctype")
    docname_filter = filters.get("docname")
    view_type = filters.get("view_type") or "Document Level"
    child_table_field = filters.get("child_table")
    columns, data = [], []

    if view_type == "Child Table Diff" and child_table_field:
        return get_child_table_diff(doctype, docname_filter, child_table_field)
    else:
        return get_document_level_diff(doctype, docname_filter)

def get_document_level_diff(doctype, docname_filter):
    columns, data = [], []

    meta = frappe.get_meta(doctype)
    fields = [
        field.fieldname for field in meta.fields
        if field.fieldtype not in ["Tab Break", "Section Break", "Column Break"]
    ]

    columns.append({"label": "Document", "fieldname": "docname", "fieldtype": "Data", "width": 150})
    columns.append({"label": "Change Instance", "fieldname": "change_instance", "fieldtype": "Link", "options": "Version", "width": 150})
    for field in fields:
        columns.append({"label": field, "fieldname": field, "fieldtype": "Data", "width": 150})
    columns.append({"label": "Changed By", "fieldname": "changed_by", "fieldtype": "Data", "width": 150})
    columns.append({"label": "Changed On", "fieldname": "timestamp", "fieldtype": "Datetime", "width": 150})

    docname_filters = {"name": ["in", docname_filter]} if docname_filter else {}
    documents = frappe.get_all(doctype, fields=["name"], filters=docname_filters)

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

        data.append({
            "docname": docname,
            "change_instance": "Initial Value",
            **initial_values,
            "changed_by": current_doc.owner,
            "timestamp": get_datetime(current_doc.creation)
        })

        for log in version_logs:
            version_data = json.loads(log["data"])
            if not version_data.get("changed"):
                continue

            row = {
                "docname": docname,
                "change_instance": log["name"],
                "changed_by": log["modified_by"],
                "timestamp": get_datetime(log["modified"])
            }
            for field in fields:
                row[field] = ""
            for change in version_data.get("changed", []):
                field_name, _, new_value = change
                if field_name in row:
                    row[field_name] = new_value
            data.append(row)

        data.append({
            "docname": docname,
            "change_instance": "Current Value",
            **current_values,
            "changed_by": "-",
            "timestamp": "-"
        })

    return columns, data

def get_child_table_diff(doctype, docname_filter, child_table_field):
    columns = [
        {"label": "Document", "fieldname": "docname", "fieldtype": "Data", "width": 150},
        {"label": "Change Instance", "fieldname": "change_instance", "fieldtype": "Link", "options": "Version", "width": 150},
        {"label": "Row ID", "fieldname": "row_id", "fieldtype": "Data", "width": 100},
        {"label": "Field", "fieldname": "field", "fieldtype": "Data", "width": 150},
        {"label": "Old Value", "fieldname": "old_value", "fieldtype": "Data", "width": 200},
        {"label": "New Value", "fieldname": "new_value", "fieldtype": "Data", "width": 200},
        {"label": "Changed By", "fieldname": "changed_by", "fieldtype": "Data", "width": 120},
        {"label": "Changed On", "fieldname": "timestamp", "fieldtype": "Datetime", "width": 150}
    ]

    data = []
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
                if row_change.get("parentfield") != child_table_field:
                    continue

                row_id = row_change.get("row")
                for change in row_change.get("changed", []):
                    fieldname, old_value, new_value = change
                    data.append({
                        "docname": docname,
                        "change_instance": log["name"],
                        "row_id": row_id,
                        "field": fieldname,
                        "old_value": old_value,
                        "new_value": new_value,
                        "changed_by": log["modified_by"],
                        "timestamp": get_datetime(log["modified"])
                    })

    return columns, data
