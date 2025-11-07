import frappe


def create_customer_main_slip(doc, method):
	# Only trigger for Material Transfer
	if doc.stock_entry_type == "Material Transfer":
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

			frappe.msgprint(
				f"Customer Metal Main Slip {cms.name} created successfully for Batch {row.batch_no}"
			)

	# Handle Repack-Metal Conversion stock entry type
	if doc.stock_entry_type == "Repack-Metal Conversion":
		data = frappe.db.sql(
			""" SELECT
			se1.batch_no,
			se2.item_code,
			se2.qty,
			se2.batch_no AS new_batch
			from `tabStock Entry Detail` se1
			JOIN `tabStock Entry Detail` se2 ON se1.parent = se2.parent
			WHERE se1.parent = %s
			AND se1.s_warehouse != ''
			AND se1.item_code LIKE '%%KT%%'
			And se2.t_warehouse != ''
			LIMIT 1""",
			(doc.name,),
			as_dict=True,
		)
		if not data:
			return
		parent_batch = data[0].batch_no
		item_code = data[0].item_code
		new_batch = data[0].new_batch
		qty = data[0].qty

		cms_name = frappe.db.get_value("Customer Metal Main Slip", {"batch_no": parent_batch}, "name")

		if not cms_name:
			child = frappe.db.get_value(
				"Customer Batch Detail", {"batch_no": parent_batch}, ["parent"], as_dict=True
			)
			if not child:
				frappe.throw("No CMS is available for this batch")
			cms_name = child.parent

		cms = frappe.get_doc("Customer Metal Main Slip", cms_name)

		cms.append(
			"batch_details",
			{
				"batch_no": new_batch,
				"item_code": item_code,
				"msl_qty": 0,
				"msl_consume_qty": qty,
				"consumed_qty": 0,
				"balance_qty": qty,
				"inventory_type": "Customer Goods",
			},
		)

		for row in cms.batch_details:
			if row.batch_no == parent_batch:
				row.consumed_qty = (row.consumed_qty or 0) + qty
				base_qty = row.msl_qty if row.msl_qty else row.msl_consume_qty
				row.balance_qty = base_qty - row.consumed_qty
				break

		cms.flags.ignore_permissions = True
		cms.flags.ignore_version = True
		cms.save()
		frappe.msgprint("CMS updated successfully")
