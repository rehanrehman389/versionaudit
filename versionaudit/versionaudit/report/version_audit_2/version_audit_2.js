// Copyright (c) 2024, Rehan and contributors
// For license information, please see license.txt

function get_filters() {
    return [
        {
            fieldname: "doctype",
            label: __("DocType"),
            fieldtype: "Link",
            options: "DocType",
            reqd: 1,
            onchange: function () {
                frappe.query_report.set_filter_value("docname", null);
                frappe.query_report.set_filter_value("child_table", null);

                const doctype = frappe.query_report.get_filter_value("doctype");

                // Fetch child table options via your API
                frappe.call({
                    method: "versionaudit.versionaudit.report.version_audit_2.version_audit_2.get_child_tables",
                    args: { doctype },
                    callback: function (r) {
                        if (r.message) {
                            frappe.query_report.set_filter_options("child_table", r.message);
                        }
                    },
                });
            },
        },
        {
            fieldname: "docname",
            label: __("Docname"),
            fieldtype: "MultiSelectList",
            get_data: function (txt) {
                const selected_doctype = frappe.query_report.get_filter_value("doctype");
                if (!selected_doctype) return [];
                return frappe.db.get_link_options(selected_doctype, txt);
            },
        },
        {
            fieldname: "view_type",
            label: __("View Type"),
            fieldtype: "Select",
            options: ["Document Level Diff", "Child Table Diff"],
            default: "Document Level Diff"
        },
        {
            fieldname: "child_table",
            label: __("Child Table"),
            fieldtype: "Select",
            depends_on: "eval:doc.view_type === 'Child Table Diff'",
            options: []  // Will be set dynamically on doctype change
        },
        {
            fieldname: "include_empty_fields",
            label: __("Include Empty Fields"),
            fieldtype: "Check",
            default: 0,
            depends_on: "eval:doc.view_type === 'Document Level Diff'"
        }
    ];
}

frappe.query_reports["Version Audit 2"] = {
    filters: get_filters(),
};
