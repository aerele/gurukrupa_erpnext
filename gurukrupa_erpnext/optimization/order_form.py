import frappe
from frappe import _

# key (field name in the Order Details of the Order Form)
# Value record name in Item Attribute ,which are predefined, for mapping.
ITEM_ATTRIBUTE_KEYS = {
	"design_type": "Design Type",
	"diamond_quality": "Diamond Quality",
	"setting_type": "Setting Type",
	"sub_setting_type1": "Sub Setting Type1",
	"sub_setting_type2": "Sub Setting Type2",
	"metal_type": "Metal Type",
	"metal_colour": "Metal Colour",
	"metal_touch": "Metal Touch",
	"diamond_type": "Diamond Type",
	"sizer_type": "Sizer Type",
	"stone_changeable": "Stone Changeable",
	"feature": "Feature",
	"rhodium": "Rhodium",
	"enamal": "Enamal",
	"gemstone_type": "Gemstone Type",
	"gemstone_quality": "Gemstone Quality",
	"mod_reason": "Mod Reason",
	"finding_category": "Finding Category",
	"finding_subcategory": "Finding Sub-Category",
	"finding_size": "Finding Size",
	"metal_target_from_range": "Metal Target Range",
	"diamond_target_from_range": "Diamond Target Range",
	"detachable": "Detachable",
	"lock_type": "Lock Type",
	"capganthan": "Cap/Ganthan",
	"charm": "Charm",
	"back_chain": "Back Chain",
	"back_belt": "Black Bead",
	"two_in_one": "2 in 1",
	"chain_type": "Chain Type",
	"nakshi_from": "Nakshi From",
}


def validate(self):
	self.attribute_value = {}
	if self.get("order_details"):
		self.attribute_value = frappe.db.sql(
			f"""
			SELECT
			JSON_OBJECTAGG(attribute, main_values) AS final_dict
				FROM (
					SELECT
						parent AS attribute,
						JSON_ARRAYAGG(attribute_value) AS main_values
					FROM `tabItem Attribute Value`
					WHERE parenttype = 'Item Attribute'
					and parent in
					{tuple(ITEM_ATTRIBUTE_KEYS.values())}
					GROUP BY parent
				) as t """,
			as_dict=True,
		)
		# storing the item_attribute_values as per the Item Attribute based on ITEM_ATTRIBUTE_KEYS
		self.attribute_value = (
			frappe.parse_json(self.attribute_value[0].get("final_dict"))
			if self.attribute_value
			else frappe.throw(_("No Item Attribute Founed Under Defined"))
		)

		for row in self.order_details:
			validate_category_subcaegory(row)
			validate_filed_value(self, row)


def validate_category_subcaegory(row):
	if (
		row.subcategory
		and row.get("category")
		and row.get("subcategory_parent_attribute_value") == row.get("category")
	):
		frappe.throw(_(f"Category & Sub Category mismatched in row #{row.idx}"))


def validate_filed_value(self, row):
	def check(key):
		row_key = ITEM_ATTRIBUTE_KEYS[key]
		row_vaue = row.get(key)
		if row_vaue and row_vaue not in (self.attribute_value.get(row_key) or []):
			frappe.throw(_(f"{row_key} is not correct at #{row.idx}"))

	map(check, ITEM_ATTRIBUTE_KEYS)
