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
                // Clear the docname filter when doctype changes
                frappe.query_report.set_filter_value("docname", null);
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
                // Fetch document names dynamically based on the selected doctype
                return frappe.db.get_link_options(selected_doctype, txt);
            },
        },
    ];
}

frappe.query_reports["Version Audit 2"] = {
    filters: get_filters(),
};
