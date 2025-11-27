import frappe


@frappe.whitelist()
def delete_dpartment(department_id):
	delete_background(department_id)


def delete_background(department_id):
	frappe.delete_doc("Department", department_id, force=1)
