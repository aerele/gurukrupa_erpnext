import frappe
from frappe.model.naming import make_autoname


def autoname(self, method=None):
	if frappe.flags.autoname_done:
		return self.name

	inventory_type_field_map = {"Stock Entry": "stock_entry_type", "Purchase Receipt": "inventory_type"}

	customer_name_field_map = {"Stock Entry": "_customer", "Purchase Receipt": "customer"}

	def _get_field_values(reference_type, reference_name, fieldname, customer_field):
		key = "name"
		if reference_type == "Purchase Receipt":
			reference_type = f"{reference_type} Item"
			key = "parent"

		return frappe.db.get_value(reference_type, {key: reference_name}, [fieldname, customer_field])

	inventory_type, customer = _get_field_values(
		self.reference_doctype,
		self.reference_name,
		inventory_type_field_map.get(self.reference_doctype),
		customer_name_field_map.get(self.reference_doctype),
	)

	item_code = self.item

	if inventory_type in ["Customer Goods Received", "Customer Goods"] and "24KT" in item_code:
		if customer:
			naming_series = f"{customer}-.YY.-.MM.-{item_code}-.##"
			self.name = make_autoname(naming_series)
			frappe.flags.autoname_done = True
			return self.name

	return None
