// Copyright (c) 2024, Rehan and contributors
// For license information, please see license.txt

frappe.query_reports["Version Audit 2"] = {
	"filters": [
		{
			fieldname: "doctype",
			label: __("DocType"),
			fieldtype: "Link",
			options: "DocType",
			reqd: 1
		},
		{
			fieldname: "docname",
			label: __("Docname"),
			fieldtype: "Dynamic Link",
			options: "doctype"
		},
	]
};
