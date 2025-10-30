import datetime
import random
import string

import frappe
from frappe.model.naming import make_autoname


def autoname(self, method=None):
	# Flag to prevent multiple autoname calls
	if getattr(self, "autoname_done", False):
		return
	self.autoname_done = True

	# Stock entry batch Renaming
	stock_entry_type = frappe.db.get_value("Stock Entry", self.reference_name, "stock_entry_type")
	if stock_entry_type == "Customer Goods Received":
		item_code = self.item
		if "24KT" in item_code:
			customer = frappe.db.get_value("Stock Entry", self.reference_name, "_customer")
			naming_series = f"{customer}-.YY.-.MM.-{item_code}-.##"
			self.name = make_autoname(naming_series)
			return

	# Purchase Receipt Batch Renaming
	pr_inventory_type = frappe.db.get_value(
		"Purchase Receipt Item", {"parent": self.reference_name}, "inventory_type"
	)
	if pr_inventory_type == "Customer Goods":
		frappe.msgprint("Autonaming Purchase Receipt Batch")
		item_code = self.item
		if "24KT" in item_code:
			customer = frappe.db.get_value(
				"Purchase Receipt Item", {"parent": self.reference_name, "item_code": item_code}, "customer"
			)
			naming_series = f"{customer}-.YY.-.MM.-{item_code}-.##"
			self.name = make_autoname(naming_series)
			return
	item_group = frappe.db.get_value("Item", {self.item}, "item_group")

	if item_group in ["Metal - V", "Diamond - V", "Gemstone - V", "Finding - V", "Other - V"]:
		year_code = get_year_code()
		month_code = get_month_code()
		week_code = get_week_code()
		# start_of_week, end_of_week = get_current_week_date_range()
		company = {
			"Gurukrupa Export Private Limited": "GE",
			"KG GK Jewellers Private Limited": "KG",
			"Sadguru Diamond": "SD",
			"Sadguru Hallmarking Centre": "SHC",
		}
		company_abbr = company.get(self.custom_company)

		if item_group == "Diamond - V":
			batch_number = f"{company_abbr}{year_code}{month_code}{week_code}-D".format(
				year_code=year_code, month_code=month_code, week_code=week_code
			)
		elif item_group == "Metal - V":
			batch_number = f"{company_abbr}{month_code}{week_code}-M".format(
				year_code=year_code, month_code=month_code, week_code=week_code
			)
		elif item_group == "Gemstone - V":
			batch_number = f"{company_abbr}{month_code}{week_code}-G".format(
				year_code=year_code, month_code=month_code, week_code=week_code
			)
		elif item_group == "Finding - V":
			batch_number = f"{company_abbr}{month_code}{week_code}-F".format(
				year_code=year_code, month_code=month_code, week_code=week_code
			)
		elif item_group == "Other - V":
			batch_number = f"{company_abbr}{month_code}{week_code}-O".format(
				year_code=year_code, month_code=month_code, week_code=week_code
			)
		batch_abbr_code_list = []

		for i in frappe.get_doc("Item", self.item).attributes:
			if i.attribute == "Finding Category":
				continue
			batch_abbreviation = frappe.db.get_value(
				"Attribute Value", i.attribute_value, "custom_batch_abbreviation"
			)
			if i.attribute_value:
				if batch_abbreviation:
					batch_abbr_code_list.append(batch_abbreviation)
				else:
					frappe.throw(f"Abbrivation is missing for {i.attribute_value}")
		batch_code = batch_number + "".join(batch_abbr_code_list)
		sequence = generate_unique_alphanumeric()
		self.name = batch_code + "-" + sequence


def get_year_code():
	year_dict = {
		"1": "A",
		"2": "B",
		"3": "C",
		"4": "D",
		"5": "E",
		"6": "F",
		"7": "G",
		"8": "H",
		"9": "I",
		"0": "J",
	}
	current_year = datetime.datetime.now().year
	last_two_digits = current_year % 100
	return str(last_two_digits)[0] + year_dict[str(last_two_digits)[1]]


def get_week_code():
	current_date = datetime.date.today()
	week_number = (current_date.day - 1) // 7 + 1
	return str(week_number)


def get_month_code():
	current_date = datetime.datetime.now()
	month_two_digit = current_date.strftime("%m")
	return str(month_two_digit)


def generate_unique_alphanumeric():
	while True:
		# Ensure at least one letter and one number
		letters = random.choices(string.ascii_uppercase, k=2)  # At least 2 letters
		digits = random.choices(string.digits, k=3)  # At least 3 numbers
		random_code = "".join(random.sample(letters + digits, 5))  # Shuffle & combine

		# Check if it already exists
		existing_doc = frappe.get_value("Manufacturing Operation", {"name": f"MOP-{random_code}"}, "name")

		if not existing_doc:  # If unique, return it
			return random_code
