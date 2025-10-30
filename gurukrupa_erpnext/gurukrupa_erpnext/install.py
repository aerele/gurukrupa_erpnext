import frappe


def after_install():
	checkbox_creation()


def checkbox_creation():
	if not frappe.db.get_value("Custom Field", {"fieldname": "custom_is_customer_main_slip"}):
		frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "Warehouse",
				"label": "Is Customer Main Slip",
				"fieldname": "custom_is_customer_main_slip",
				"fieldtype": "Check",
				"insert_after": "is_group",
				"description": "Check if this warehouse is used for Customer Metal Main Slip (CMS)",
			}
		).insert(ignore_permissions=True)
		frappe.db.commit()
		frappe.msgprint("Custom field 'Is Customer Main Slip Warehouse' added to Warehouse doctype.")
	else:
		frappe.msgprint("Custom field 'Is Customer Main Slip Warehouse' already exists in Warehouse doctype.")
