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
                frappe.query_report.set_filter_value("view_type", "Document Level");
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
            options: ["Document Level", "Child Table Diff"],
            default: "Document Level",
            onchange: function () {
                const viewType = frappe.query_report.get_filter_value("view_type");
                const doctype = frappe.query_report.get_filter_value("doctype");

                if (viewType === "Child Table Diff" && doctype) {
                    frappe.call({
                        method: "frappe.desk.query_report.get_script", // dummy to trigger doctype meta load
                        args: { report_name: "Version Audit 2" },
                        callback: function () {
                            const meta = frappe.get_meta(doctype);
                            const child_tables = meta.fields
                                .filter(df => df.fieldtype === "Table")
                                .map(df => ({ label: df.label, value: df.fieldname }));
                            frappe.query_report.get_filter("child_table").df.options = child_tables;
                            frappe.query_report.set_filter_value("child_table", null);
                            frappe.query_report.refresh_filter("child_table");
                        }
                    });
                }
            }
        },
        {
            fieldname: "child_table",
            label: __("Child Table"),
            fieldtype: "Select",
            hidden: 1,
        }
    ];
}

frappe.query_reports["Version Audit 2"] = {
    filters: get_filters(),
    onload: function (report) {
        frappe.query_report.get_filter("view_type").onchange();
    },
    get_datatable_options(options) {
        return Object.assign({}, options, {
            dynamicRowHeight: true,
        });
    }
};
