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

	if inventory_type == "Repack-Metal Conversion":
		parent_data = frappe.db.sql(
			"""SELECT
			se1.batch_no,
			se2.item_code
			FROM `tabStock Entry Detail` se1
			JOIN `tabStock Entry Detail` se2 ON se1.parent = se2.parent
			WHERE se1.parent = %s
			AND se1.s_warehouse != ''
			AND se1.item_code LIKE '%%KT%%'
			AND se2.t_warehouse != ''
			LIMIT 1""",
			self.reference_name,
			as_dict=True,
		)

		parent_batch = parent_data[0].batch_no
		item_code = parent_data[0].item_code

		cms_data = frappe.db.get_value(
			"Customer Metal Main Slip", {"batch_no": parent_batch}, ["name", "customer"], as_dict=True
		)
		if not cms_data:
			data = frappe.db.sql(
				"""
						SELECT
						cms.name, cms.customer
						FROM `tabCustomer Batch Detail` cbd
						JOIN `tabCustomer Metal Main Slip` cms
						ON cms.name = cbd.parent
						WHERE cbd.batch_no = %s
						LIMIT 1""",
				(parent_batch,),
				as_dict=True,
			)
			cms_customer = data[0].customer if data else None
			parent_no = parent_batch[-4:]
			naming_series = f"{cms_customer}-.YY.-.MM.-{item_code}-{parent_no.strip()}-.##"
			self.name = make_autoname(naming_series)
			frappe.flags.autoname_done = True
			return self.name

		count = frappe.db.sql(
			"""
						SELECT COUNT(*)
						FROM `tabCustomer Batch Detail`
						WHERE parent = %s
						AND SUBSTRING(batch_no, -1) >= 'A'
						AND SUBSTRING(batch_no, -1) <= 'Z'
						""",
			(cms_data.name,),
		)[0][0]
		suffix = chr(65 + count)
		new_batch = f"{cms_data.customer}-.YY.-.MM.-{item_code}-.##.-{suffix}"
		self.name = make_autoname(new_batch)
		frappe.flags.autoname_done = True
		return self.name

	return None
