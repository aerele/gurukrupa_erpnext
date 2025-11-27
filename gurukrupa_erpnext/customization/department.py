import frappe


@frappe.whitelist()
def delete_dpartment(deparmrnt_id):
	delete_background(deparmrnt_id)


def delete_background(deparmrnt_id):
	frappe.delete_doc("Department", deparmrnt_id, force=1)
