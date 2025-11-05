import frappe
from frappe.model.naming import make_autoname


def create_customer_main_slip(doc, method):
	# Only trigger for Material Transfer
	if doc.stock_entry_type != "Material Transfer":
		return

	# Loop through all child items in Stock Entry
	for row in doc.items:
		# Basic validations
		if not row.t_warehouse or not row.batch_no or not row.item_code:
			continue

		# Only process 24KT metals
		if "24KT" not in row.item_code:
			continue

		# Check if target warehouse is CMS warehouse
		is_cms_warehouse = frappe.db.get_value("Warehouse", row.t_warehouse, "custom_checkbox_field")
		if not is_cms_warehouse:
			continue

		# Fetch batch reference details
		ref_data = frappe.db.get_value(
			"Batch",
			row.batch_no,
			["reference_doctype", "reference_name", "custom_customer"],
			as_dict=True,
		)
		if not ref_data:
			frappe.msgprint(f"No Batch data found for {row.batch_no}")
			continue

		ref_doctype = ref_data.reference_doctype
		ref_name = ref_data.reference_name
		batch_customer = ref_data.custom_customer

		# Prevent duplicate CMS
		if frappe.db.exists("Customer Metal Main Slip", {"batch_no": row.batch_no}):
			frappe.throw(f"CMS already exists for Batch {row.batch_no}")

		customer = None

		if ref_doctype == "Stock Entry":
			stock_data = frappe.db.get_value(
				"Stock Entry",
				ref_name,
				["stock_entry_type", "customer_voucher_type", "_customer"],
				as_dict=True,
			)
			if (
				stock_data
				and stock_data.stock_entry_type == "Customer Goods Received"
				and stock_data.customer_voucher_type == "Customer Subcontracting"
			):
				customer = stock_data._customer

		elif ref_doctype == "Purchase Receipt":
			customer = batch_customer

		if not customer:
			frappe.throw(f"Customer not found for Batch {row.batch_no}")
			continue

		# Create CMS document
		cms = frappe.new_doc("Customer Metal Main Slip")
		cms.company = doc.company
		cms.warehouse = row.t_warehouse
		cms.customer = customer
		cms.batch_no = row.batch_no
		cms.voucher_type = ref_doctype
		cms.voucher_no = ref_name
		cms.append(
			"batch_details",
			{
				"batch_no": row.batch_no,
				"item_code": row.item_code,
				"msl_qty": row.qty,
				"msl_consume_qty": 0.0,
				"consumed_qty": 0.0,
				"auto_created": "No",
				"inventory_type": "Customer Goods",
				"balance_qty": row.qty,
			},
		)
		cms.insert(ignore_permissions=True)

		frappe.msgprint(f"Customer Metal Main Slip {cms.name} created successfully for Batch {row.batch_no}")
