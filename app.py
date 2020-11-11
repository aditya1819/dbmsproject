from flask import Flask, render_template, redirect,request, url_for, flash, session
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators,SelectField, IntegerField, BooleanField
from wtforms.fields.html5 import DateField
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)
app.secret_key='thisisnotasecretkeycozitsnotsecret'

# mysql config

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'pass'
app.config['MYSQL_DB'] = 'project'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# forms used

class AddNewProd(Form):
	p_name = StringField('Product Name', [validators.Length(min=4, max=30)])
	added = IntegerField('Intital Quantity', [validators.NumberRange(min=1, max=100)])
	cost = IntegerField('Cost per unit')

class EditCost(Form):
	cost = IntegerField('Cost per unit')

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

class RecordGenration(Form):
	rec_type = SelectField("Type",choices = ['Date_Inteval','Date_to_days','all_month'])
	rec_type1 = SelectField("type1", choices = ['All','product'])


class DateInterval(Form):
	date1 = DateField("start Date",format="%Y-%m-%d")
	date2 = DateField("end Date",format="%Y-%m-%d")

class DayIntervak(Form):
	date = DateField("start Date",formate="%Y-%m-%d")
	days = IntegerField("Days",[validators.NumberRange(min=1, max=30)])

# urls

@app.route('/')
def index():
	return render_template('index.html')

# UserLogin
@app.route('/login', methods=['GET','POST'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		pass_cand = request.form['password']

# temporary login for admin as 1st user needs to be admin to add other users/employees
		if username == 'admin' and pass_cand == 'admin':
			session['logged_in'] = True
			session['username'] = username
			session['admin_status'] =  True
			reset_cart()
			flash("You are now logged in !",'success')
			return redirect(url_for('index'))
		else:
			error = 'Invalid Login'
			render_template('login.html', error=error)

		cur = mysql.connection.cursor()
		cur.execute("USE project")
		result = cur.execute("SELECT * FROM users WHERE u_name = %s", [username])

		if result > 0:
			# get stored hash
			data = cur.fetchone()
			password = data['u_pass']

			# compare pass
			if sha256_crypt.verify(pass_cand, password):
				# app.logger.info("PASS MATCHEd")
				session['logged_in'] = True
				session['username'] = username
				if data['admin_status'] == 1:
					session['admin_status'] = True
				elif data['admin_status'] == 0:
					session['admin_status'] = False				
				flash("You are now logged in !",'success')
				reset_cart()
				return redirect(url_for('index'))
			else:
				# app.logger.info("PASS NOT MATCHED")
				error = 'Invalid Login Credentials'
				return render_template('login.html',error=error)
			cur.close()
		else:
			# app.logger.info("NO USER FOUND")
			error = 'Username not found'
			return render_template('login.html',error=error)

	return render_template('login.html')
	

#check if user logged in
def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unathorised Access Please Log in','danger')
			return redirect(url_for('login'))
	return wrap

# check if user has admin access
def is_admin(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if session['admin_status'] == True:
			return f(*args, **kwargs)
		elif session['admin_status'] == False:
			flash('You need Admin Access for this Operation','danger')
			# return redirect(url_for('login'))
			return redirect(url_for('index'))
	return wrap

#logout
@app.route('/logout')
@is_logged_in
def logout():
	session.clear()
	flash('You are Logged Out', 'primary')
	return redirect(url_for('login'))

@app.route('/inv_det')
@is_logged_in
def inv_det():
	try:
		cur = mysql.connection.cursor()
		cur.execute("USE project")
		result = cur.execute("SELECT * FROM products")
		prods = cur.fetchall()
		if result > 0:
			return render_template('inv_det.html', prods=prods)
		cur.close()
	except Exception as e:
		print(e)
	return render_template('inv_det.html', prods=prods)


@app.route('/addprod', methods=['GET', 'POST'])
@is_logged_in
def addprod():
	form = AddNewProd(request.form)
	if request.method =='POST' and form.validate():
		p_name = form.p_name.data
		added = form.added.data
		cost = form.cost.data
		cur = mysql.connection.cursor()
		cur.execute("USE project")
		try:
			cur.execute("INSERT INTO products(p_name, cost, avl_qn) VALUES(%s, %s, %s);", (p_name, cost, added))
			mysql.connection.commit()
			cur.close()
		except mysql.connection.IntegrityError:
			flash('Product already exists with this name', 'danger')
			return redirect(url_for('addprod'))
		return redirect(url_for('inv_det'))
	return render_template('addprod.html', form=form)

@app.route('/remove_prod/<string:p_name>', methods=['POST'])
@is_logged_in
def remove_prod(p_name):
	cur = mysql.connection.cursor()
	cur.execute("USE project")
	cur.execute("DELETE FROM products WHERE p_name=%s", [p_name])
	mysql.connection.commit()
	cur.close()
	return redirect(url_for('inv_det'))

@app.route('/edit_cost/<string:p_name>', methods=['GET', 'POST'])
@is_logged_in
def edit_cost(p_name):
	cur = mysql.connection.cursor()
	cur.execute("USE project")
	temp = cur.execute("SELECT * FROM products WHERE p_name = %s", [p_name])
	prods = cur.fetchone()
	form = EditCost(request.form)
	form.cost.data = prods['cost']
	cur.close()
	if request.method == 'POST' and form.validate():
		cost = request.form['cost']
		cur = mysql.connection.cursor()
		cur.execute("USE project")
		cur.execute("UPDATE products SET cost = %s WHERE p_name=%s", (cost, p_name))
		mysql.connection.commit()
		return redirect(url_for('inv_det'))

	return render_template('edit_cost.html', form=form, prods=prods)




@app.route('/edit_quantity/<string:p_name>', methods=['GET', 'POST'])
@is_logged_in
def edit_quantity(p_name):
	cur = mysql.connection.cursor()
	cur.execute("USE project")
	temp = cur.execute("SELECT * FROM products WHERE p_name = %s", [p_name])
	prods = cur.fetchone()
	form = EditQuantity(request.form)
	form.quantity.data = prods['avl_qn']
	cur.close()
	if request.method == 'POST' and form.validate():
		quantity = int(request.form['quantity']) + int(request.form['no_products'])
		cur = mysql.connection.cursor()
		cur.execute("USE project")
		cur.execute("UPDATE products SET avl_qn = %s WHERE p_name=%s", (quantity, p_name))
		mysql.connection.commit()
		return redirect(url_for('inv_det'))

	return render_template('edit_quantity.html', form=form, prods=prods)




@app.route('/add_emp', methods=['GET', 'POST'])
@is_logged_in
@is_admin
def add_emp():
	form = AddEmp(request.form)

	if request.method == 'POST' and form.validate():
		u_name = form.u_name.data
		u_pass = sha256_crypt.hash(str(form.u_pass.data))
		u_type = form.u_type.data
		if u_type == 'Admin':
			admin_status = 1
		else:
			admin_status = 0
		cur = mysql.connection.cursor()
		cur.execute("USE project")
		try:
			cur.execute('INSERT INTO users(u_name, u_pass, admin_status) VALUES (%s, %s, %s);', (u_name, u_pass, admin_status))
			mysql.connection.commit()
			cur.close()
		except mysql.connection.IntegrityError:
			flash = ('Username already exists !', 'danger')
			redirect(url_for('add_emp'))
		return redirect(url_for('index'))
	return render_template('add_emp.html', form=form)

# billing system code
#  |
#  V

@app.route('/makebill', methods=['GET', 'POST'])
@is_logged_in
def makebill():
	cur = mysql.connection.cursor()
	cur.execute("USE project")
	result = cur.execute("SELECT * FROM products")
	prods = cur.fetchall()
	form = AddToCart(request.form)
	form.p_name.choices = [x['p_name'] for x in prods]
	if request.method == 'POST' and form.validate():
		p_name = form.p_name.data
		added = form.added.data
		cur.execute("SELECT * FROM products WHERE p_name=%s", [p_name])
		temp = cur.fetchone()
		p_id = int(temp['p_id'])
		avl_qn = int(temp['avl_qn'])
		cost = int(temp['cost'])
		if int(added) > int(avl_qn) :
			flash('REQ QUANTITY NOT AVAILABLE', 'danger')
			return redirect(url_for('makebill'))
		cur.execute("UPDATE products SET avl_qn=%s WHERE p_id=%s", ((avl_qn-added),p_id))
		print('ranjeet')
		mysql.connection.commit()
		t_cost = added * cost
		if p_name not in session['cart']:
			result = cur.execute("select * from products where p_name=%s",[p_name])
			data = cur.fetchone()
			cur.close()
			p_id = data['p_id']
			session['cart'][p_name] = {'a': 0, 'c': cost,'t': 0,'p_id':p_id}
		session['cart'][p_name]['a'] += added
		session['cart'][p_name]['t'] += t_cost
		session['total'] += t_cost
		flash('Item added to cart', 'success')
		return redirect('makebill')
	return render_template('makebill.html', prods=prods, form=form, sess=session['cart'], total=session['total'])

def reset_cart():
	session['cart'] = {}
	session['total'] = 0

@app.route('/delete_cart')
def delete_cart():
	cur = mysql.connection.cursor()
	cur.execute("USE project")
	for key in session['cart']:
		cur.execute("SELECT avl_qn FROM products WHERE p_name=%s", [key])
		temp = cur.fetchone()
		avl_qn = int(temp['avl_qn'])
		cur.execute("UPDATE products SET avl_qn=%s WHERE p_name=%s", ((avl_qn+session['cart'][key]['a']),key))
		mysql.connection.commit()
	reset_cart()
	flash('Transaction cancelled', 'danger')
	return redirect('/')

@app.route('/payment', methods=['GET', 'POST'])
def payment():
	if(bool(session['cart'])):
		cur = mysql.connection.cursor()
		form = CusName(request.form)
		if request.method == 'POST' and form.validate():
			cusname = form.cusname.data
			cusphone = form.cusphone.data
			cur.execute('USE project')
			result = cur.execute("select * from customer where c_name = %s and c_contact = %s",(cusname,cusphone))
			if result > 0:
				data = cur.fetchone()
				c_id = data['cust_id']
			else:	
				cur.execute("INSERT into customer(c_name, c_contact) VALUES (%s, %s)", (cusname, cusphone))
				mysql.connection.commit()
				result = cur.execute("select * from customer where c_name = %s and c_contact = %s",(cusname,cusphone))
				data = cur.fetchone()
				c_id = data['cust_id']

			result = cur.execute("select * from users where u_name = %s",[session['username']])
			data = cur.fetchone()
			emp_id=data['u_id']
			cur.execute("insert into t_hist(c_id,emp_id,total) values(%s,%s,%s)",(c_id,emp_id,[session['total']]))
			mysql.connection.commit()

			result = cur.execute("select * from t_hist order by id DESC limit 1")
			data = cur.fetchone()
			id = data['id']
			for key in session['cart']:
				cur.execute("insert into record(id,p_id,cost,qunt) values(%s,%s,%s,%s)",(id,[session['cart'][key]['p_id']],[session['cart'][key]['c']],[session['cart'][key]['a']]))
				mysql.connection.commit() 
			cur.close()
			reset_cart()

			flash('transaction complete', 'success')
			return redirect('/')
		return render_template('payment.html', form=form)
	else:
		flash("No product is selected","danger")
		return redirect("makebill")
	# return render_template("/index.html")



@app.route('/rec_genrate', methods=['GET', 'POST'])
@is_logged_in
def rec_genrate():
	form = RecordGenration(request.form)
	if request.method == 'POST': 
		rec_type= form.rec_type.data
		rec_type1 = form.rec_type1.data 	
		if rec_type== 'Date_Inteval':
			if rec_type1 == "All":
				return redirect("date")
	return render_template('rec_genrate.html',form=form )


@app.route('/date', methods=['GET','POST'])
@is_logged_in
def date():
	form = DateInterval(request.form)
	# print(request.method == "POST")
	if request.method == 'POST':
		date1 = form.date1.data
		date2 = form.date2.data
		# return render_template('date.html',form=form)
		print('ok')
	# else:

	# 	print("fdff")
	# 	return redirect("/")
	return render_template('date.html',form=form)

if __name__ == "__main__":
	app.run(debug=True)

