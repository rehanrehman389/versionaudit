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
            },
        },
        {
            fieldname: "docname",
            label: __("Docname"),
            fieldtype: "MultiSelectList",
            get_data: function (txt) {
                const selected_doctype = frappe.query_report.get_filter_value("doctype");
                if (!selected_doctype) {
                    return [];
                }
                return frappe.db.get_link_options(selected_doctype, txt);
            },
        },
        {
            fieldname: "view_type",
            label: __("View Type"),
            fieldtype: "Select",
            options: ["Document Level Diff", "Child Table Diff"],
            default: "Document Level Diff",
            onchange: function () {
                frappe.query_report.refresh();  // To toggle child_table filter visibility
            },
        },
        {
            fieldname: "child_table",
            label: __("Child Table"),
            fieldtype: "Select",
            depends_on: "eval:doc.view_type === 'Child Table Diff'",
            get_data: function () {
                const doctype = frappe.query_report.get_filter_value("doctype");
                if (!doctype) return [];

                return frappe.meta.get_docfield(doctype, null).then(meta_fields => {
                    return meta_fields
                        .filter(df => df.fieldtype === "Table")
                        .map(df => ({ label: df.label, value: df.fieldname }));
                });
            },
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
    filters: get_filters()
};
