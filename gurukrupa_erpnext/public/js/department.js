frappe.ui.form.on("Department", {
	refresh: function (frm) {
		if (frm.doc.disabled && !cur_frm.doc.__unsaved) {
			frm.add_custom_button(__("Delete"), function () {
				frappe.warn(
					"Are you sure you want to Delete?",
					"This action will forcefully delete the document.",
					() => {
						frappe.call({
							method: "gurukrupa_erpnext.customization.department.delete_dpartment",
							args: {
								department_id: frm.doc.name,
							},
							callback: function () {
								frappe.set_route("List", "Department");
							},
						});
					},
					"Proceed",
					true
				);
			});
		}
	},
});
