from flask import Flask, render_template, redirect,request, url_for, flash, session
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators,SelectField, IntegerField, BooleanField
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

class UpdateFrom(Form):
	p_name = SelectField('Product', choices=[])
	added = IntegerField('Quantity Added', [validators.NumberRange(min=1, max=100)])
	cost = IntegerField('Cost per unit')

class AddNewProd(Form):
	p_name = StringField('Product Name', [validators.Length(min=4, max=30)])
	added = IntegerField('Intital Quantity', [validators.NumberRange(min=1, max=100)])
	cost = IntegerField('Cost per unit')

class EditCost(Form):
	cost = IntegerField('Cost per unit')

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
	added = IntegerField('Quantity', [validators.NumberRange(min=1, max=30)])
	
class CusName(Form):
	cusname = StringField('Customer Name', [validators.Length(min=1, max=30)])
	cusphone = IntegerField("Customer Phone")

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
			session['admin_status'] = True
			# if data['admin_status'] == 1:
			#     session['admin_status'] = True
			flash("You are now logged in !",'success')
			return redirect(url_for('index'))
		else:
			error = 'Invalid Login'
			render_template('login.html', error=error)

		cur = mysql.connection.cursor()
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
				# print("type(session) : ",type(session))
				# print("type(session['username'] : ", type(session['username']))
				# print("session : ", session)
				session['total'] = 0
				session['cart'] = {}
				# print('session cart created')
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
		result = cur.execute("SELECT * FROM products")
		prods = cur.fetchall()
		if result > 0:
			return render_template('inv_det.html', prods=prods)
		cur.close()
	except Exception as e:
		print(e)
	return render_template('inv_det.html', prods=prods)

@app.route('/up_inv', methods=['GET', 'POST'])
@is_logged_in
def up_inv():

	cur = mysql.connection.cursor()
	result = cur.execute("SELECT * FROM products")
	prods = cur.fetchall()

	form = UpdateFrom(request.form)
	form.p_name.choices = [x['p_name'] for x in prods]

	if request.method =='POST' and form.validate():
		p_name = form.p_name.data
		added = form.added.data
		cost = form.cost.data

		cur.execute("SELECT p_id FROM products where p_name=%s", [p_name])
		result = cur.fetchone()
		p_id = result['p_id']
		cur.execute("SELECT avl_qn FROM products WHERE p_id=%s", [p_id])
		avl = cur.fetchone()
		ans = int(avl['avl_qn']) + int(added)
		cur.execute('UPDATE products SET avl_qn=%s WHERE p_id=%s', (ans, p_id))
		mysql.connection.commit()
		
		if cost != -1:
			cur.execute('UPDATE products SET cost=%s WHERE p_id=%s', (cost, p_id))
			mysql.connection.commit()
		cur.close()
		flash('Product Details Updated', 'success')
		return redirect(url_for('inv_det'))
	return render_template('up_inv.html', form=form)

@app.route('/addprod', methods=['GET', 'POST'])
@is_logged_in
def addprod():
	form = AddNewProd(request.form)
	if request.method =='POST' and form.validate():
		p_name = form.p_name.data
		added = form.added.data
		cost = form.cost.data
		cur = mysql.connection.cursor()
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
	cur.execute("DELETE FROM products WHERE p_name=%s", [p_name])
	mysql.connection.commit()
	cur.close()
	return redirect(url_for('inv_det'))

@app.route('/edit_cost/<string:p_name>', methods=['GET', 'POST'])
@is_logged_in
def edit_cost(p_name):
	cur = mysql.connection.cursor()

	temp = cur.execute("SELECT * FROM products WHERE p_name = %s", [p_name])
	prods = cur.fetchone()

	form = EditCost(request.form)
	form.cost.data = prods['cost']
	cur.close()
	if request.method == 'POST' and form.validate():
		cost = request.form['cost']
		cur = mysql.connection.cursor()
		cur.execute("UPDATE products SET cost = %s WHERE p_name=%s", (cost, p_name))
		mysql.connection.commit()
		return redirect(url_for('inv_det'))

	return render_template('edit_cost.html', form=form, prods=prods)

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
	# try:
	cur = mysql.connection.cursor()
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
		mysql.connection.commit()
		cur.close()
		t_cost = added * cost
		if p_name not in session['cart']:
			session['cart'][p_name] = {'a': 0, 'c': cost,'t': 0}
		print(session)

		session['cart'][p_name]['a'] += added
		session['cart'][p_name]['t'] += t_cost
		session['total'] += t_cost
		print(session)

		flash('Item added to cart', 'success')

		return redirect('makebill')

	return render_template('makebill.html', prods=prods, form=form, sess=session['cart'], total=session['total'])

def reset_cart():
	session['cart'] = {}
	session['total'] = 0

@app.route('/delete_cart')
def delete_cart():
	cur = mysql.connection.cursor()
	for a in session['cart']:
		cur.execute("SELECT avl_qn FROM products WHERE p_name=%s", [a])
		temp = cur.fetchone()
		avl_qn = int(temp['avl_qn'])
		cur.execute("UPDATE products SET avl_qn=%s WHERE p_name=%s", ((avl_qn+session['cart'][a]['a']),a))
		mysql.connection.commit()
	cur.close()
	reset_cart()
	flash('Transaction cancelled', 'danger')
	return redirect('/')

@app.route('/payment', methods=['GET', 'POST'])
def payment():
	cur = mysql.connection.cursor()

	form = CusName(request.form)
	if request.method == 'POST' and form.validate():
		cusname = form.cusname.data
		cusphone = form.cusphone.data
		cur.execute("INSERT into t_hist(cusname, cusphone, total_cost, sold_by) VALUES (%s, %s, %s, %s)", (cusname, cusphone, session['total'], session['username']))
		mysql.connection.commit()
		cur.close()
		reset_cart()
		# print(session)
		flash('transaction complete', 'success')
		return redirect('/')
	return render_template('payment.html', form=form)



if __name__ == "__main__":
	app.run(debug=True)

