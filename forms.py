from wtforms import Form, StringField, TextAreaField, PasswordField, validators,SelectField, IntegerField, BooleanField
from wtforms.fields.html5 import DateField
from passlib.hash import sha256_crypt


# forms used

class AddNewProd(Form):
	p_name = StringField('Product Name', [validators.Length(min=4, max=30)])
	added = IntegerField('Intital Quantity', [validators.NumberRange(min=1, max=100)])
	cost = IntegerField('selling Cost per unit')
	cost_p = IntegerField('purchase Cost per unit')

class EditCost(Form):
	cost = IntegerField('Selling Cost per unit')
	cost_p = IntegerField('Purchase Cost per unit')

class EditQuantity(Form):
	quantity = IntegerField('Original quantity')
	no_products = IntegerField("Add new quantity")

class AddEmp(Form):
	u_name = StringField('Username', [validators.Length(min=4, max=30)])
	u_pass = PasswordField('Password', [validators.DataRequired()])
	u_type = SelectField('Access Type', choices=['Admin', 'Non-Admin'])

	# u_type is admin_status in database 
	# admin_status as 1 is user is admin
	# admin_status as 0 is user is non admin/employee
	
class AddToCart(Form):
	# cus_name = StringField('Customer Name')
	p_name = SelectField('Product', choices=[])
	added = IntegerField('Quantity', [validators.NumberRange(min=1, max=100)])
	
class CusName(Form):
	cusname = StringField('Customer Name', [validators.Length(min=1, max=30)])
	cusphone = IntegerField("Customer Phone")
	b_date = DateField("Date",format="%Y-%m-%d")

class RecordGenration(Form):
	rec_type = SelectField("Type",choices = ['Date_Interval','Date_to_Days','All_Month'])
	rec_type1 = SelectField("Product", choices = ['All','Product'])


class DateInterval(Form):
	date1 = DateField("Start Date",format="%Y-%m-%d")
	date2 = DateField("End Date",format="%Y-%m-%d")

class DayInterval(Form):
	date = DateField("Start Date",format="%Y-%m-%d")
	days = IntegerField("Days",[validators.NumberRange(min=1, max=30)])

class DateIntervalP(Form):
	date1 = DateField("Start Date",format="%Y-%m-%d")
	date2 = DateField("End Date",format="%Y-%m-%d")
	prod  = SelectField("Product", choices=[])

class DayIntervalP(Form):
	date = DateField("Start Date",format="%Y-%m-%d")
	days = IntegerField("Days",[validators.NumberRange(min=1, max=30)])
	prod  = SelectField("Product", choices=[])

class Month(Form):
	year = IntegerField("Year",[validators.NumberRange(min=2010, max=2020)])

class MonthP(Form):
	year = IntegerField("Year",[validators.NumberRange(min=2010, max=2020)])
	prod  = SelectField("Product", choices=[])

class PassChange(Form):
	prev = PasswordField('Previous Password', [validators.DataRequired()])
	new = PasswordField('New Password', [validators.DataRequired()])


class SearchBill(Form):
	c_name=SelectField("Name",choices=[])
	c_contact=SelectField("Contact no",choices=[])