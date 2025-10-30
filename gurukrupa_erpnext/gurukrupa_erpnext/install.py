import json
import os

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
	make_custom_fields()


def make_custom_fields():
	print("Creating/Updating Custom Fields....")
	CUSTOM_FIELDS = {}
	path = os.path.join(os.path.dirname(__file__), "custom_fields")

	for file in os.listdir(path):
		if file.endswith(".json"):
			with open(os.path.join(path, file)) as f:
				CUSTOM_FIELDS.update(json.load(f))

	create_custom_fields(CUSTOM_FIELDS)

	print("Custom Fields Created Successfully")
