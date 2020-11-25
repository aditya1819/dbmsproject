from flask import Flask, render_template, redirect,request, url_for, flash, session
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators,SelectField, IntegerField, BooleanField
from wtforms.fields.html5 import DateField
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import date
import pygal
from forms import *
from dbconnet import dbconnect
import numpy as np

app = Flask(__name__)
app.secret_key='thisisnotasecretkeycozitsnotsecret'

# mysql config

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = dbconnect.user
app.config['MYSQL_PASSWORD'] = dbconnect.passwd
app.config['MYSQL_DB'] = 'project'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


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

# urls
@is_logged_in
@app.route('/', methods=["POST",'GET'])
def index():
	return render_template('index.html')

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
			# return redirect('inv_det')
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
		cost_p= form.cost_p.data
		cur = mysql.connection.cursor()
		try:
			cur.execute("INSERT INTO products(p_name, cost,cost_p, avl_qn) VALUES(%s, %s, %s,%s);", (p_name, cost,cost_p, added))
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
	cur.execute("UPDATE products SET avl_qn = 0,cost=0,cost_p=0 WHERE p_name=%s", [p_name])
	mysql.connection.commit()
	cur.close()
	return redirect(url_for('inv_det'))

@app.route('/edit_cost/<string:p_name>', methods=['GET', 'POST'])
@is_logged_in
@is_admin
def edit_cost(p_name):
	cur = mysql.connection.cursor()
	temp = cur.execute("SELECT * FROM products WHERE p_name = %s", [p_name])
	prods = cur.fetchone()
	form = EditCost(request.form)
	form.cost.data = prods['cost']
	form.cost_p.data = prods['cost_p']
	cur.close()
	if request.method == 'POST' and form.validate():
		cost = request.form['cost']
		cost_p = request.form['cost_p']
		cur = mysql.connection.cursor()
		cur.execute("USE project")
		cur.execute("UPDATE products SET cost = %s,cost_p=%s WHERE p_name=%s", (cost,cost_p, p_name))
		mysql.connection.commit()
		return redirect(url_for('inv_det'))

	return render_template('edit_cost.html', form=form, prods=prods)




@app.route('/edit_quantity/<string:p_name>', methods=['GET', 'POST'])
@is_logged_in
def edit_quantity(p_name):
	cur = mysql.connection.cursor()
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
		try:
			cur.execute('INSERT INTO users(u_name, u_pass, admin_status) VALUES (%s, %s, %s);', (u_name, u_pass, admin_status))
			mysql.connection.commit()
			cur.close()
			flash('user added', 'success')
		except mysql.connection.IntegrityError:
			flash('Username already exists !', 'danger')
			redirect(url_for('add_emp'))
		return redirect(url_for('index'))
	return render_template('add_emp.html', form=form)

@app.route('/pass_change', methods=['GET', 'POST'])
def pass_change():
	cur = mysql.connection.cursor()
	form = PassChange(request.form)
	if request.method == 'POST' and form.validate():
		prev = form.prev.data
		new = sha256_crypt.hash(str(form.new.data))
		result = cur.execute("SELECT * FROM users WHERE u_name = %s",[session['username']])
		if result > 0:
			# get stored hash
			data = cur.fetchone()
			password = data['u_pass']
			# compare pass
			if sha256_crypt.verify(str(prev), password):
				cur.execute("UPDATE users SET u_pass=%s WHERE u_name=%s",(new, session['username']))
				mysql.connection.commit()
				cur.close()
				flash('Password Changed', 'success')
				return redirect(url_for('index'))
			else:
				flash('Incorrect Previous Password', 'danger')
				return redirect(url_for('index'))
	return render_template('pass_change.html', form=form)

# billing system code
#  |
#  V

@app.route('/makebill', methods=['GET', 'POST'])
@is_logged_in
def makebill():
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
		cost_p = int(temp['cost_p'])
		if int(added) > int(avl_qn) :
			flash('REQ QUANTITY NOT AVAILABLE', 'danger')
			return redirect(url_for('makebill'))
		cur.execute("UPDATE products SET avl_qn=%s WHERE p_id=%s", ((avl_qn-added),p_id))
		mysql.connection.commit()
		t_cost = added * cost
		t_cost_p = added * cost_p
		if p_name not in session['cart']:
			result = cur.execute("select * from products where p_name=%s",[p_name])
			data = cur.fetchone()
			cur.close()
			p_id = data['p_id']
			session['cart'][p_name] = {'a': 0, 'c': cost,'c_p':cost_p,'t': 0,'p_id':p_id}
		session['cart'][p_name]['a'] += added
		session['cart'][p_name]['t'] += t_cost
		# if ('total' not in session):
		session['total']["sell"] += t_cost
		session['total']["p"] += t_cost_p
		flash('Item added t o cart', 'success')
		return redirect('makebill')
	return render_template('makebill.html', prods=prods, form=form, sess=session['cart'], total=session['total'])

def reset_cart():
	session['cart'] = {}
	session['total'] = {'sell':0,'p':0}



@is_logged_in
@app.route('/delete_cart')
def delete_cart():
	cur = mysql.connection.cursor()
	for key in session['cart']:
		cur.execute("SELECT avl_qn FROM products WHERE p_name=%s", [key])
		temp = cur.fetchone()
		avl_qn = int(temp['avl_qn'])
		cur.execute("UPDATE products SET avl_qn=%s WHERE p_name=%s", ((avl_qn+session['cart'][key]['a']),key))
		mysql.connection.commit()
	reset_cart()
	flash('Transaction cancelled', 'danger')
	return redirect('/')

@is_logged_in
@app.route('/payment', methods=['GET', 'POST'])
def payment():
	if(bool(session['cart'])):
		cur = mysql.connection.cursor()
		form = CusName(request.form)
		if request.method == 'POST' and form.validate():
			cusname = form.cusname.data
			cusphone = form.cusphone.data
			b_date = form.b_date.data
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
			cur.execute("insert into t_hist(c_id,emp_id,total,total_p,ddtt) values(%s,%s,%s,%s,%s)",(c_id,emp_id,[session['total']["sell"]],[session['total']["p"]],b_date))
			mysql.connection.commit()

			result = cur.execute("select * from t_hist order by id DESC limit 1")
			data = cur.fetchone()
			id = data['id']
			for key in session['cart']:
				cur.execute("insert into record(id,p_id,cost,cost_p,qunt,ddmm) values(%s,%s,%s,%s,%s,%s)",(id,[session['cart'][key]['p_id']],[session['cart'][key]['c']],[session['cart'][key]['c_p']],[session['cart'][key]['a']],b_date))
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
@is_admin
def rec_genrate():
	form = RecordGenration(request.form)
	if request.method == 'POST': 
		rec_type= form.rec_type.data
		rec_type1 = form.rec_type1.data 	
		if rec_type1 == "All":
			if rec_type == "Date_Interval":
				return redirect("dates")
			elif rec_type == "Date_to_Days":
				return redirect("days")
			else:
				return redirect("month") 
		else:
			cur = mysql.connection.cursor()
			cur.execute("USE project")
			result = cur.execute("SELECT * FROM products")
			prods = cur.fetchall()
			if rec_type == "Date_Interval":
				return redirect("datep")
			elif rec_type == "Date_to_Days":
				return redirect("daysp")
			else:
				return redirect("monthp")

	return render_template('rec_genrate.html',form=form )
@app.route('/dates', methods=['GET','POST'])
@is_logged_in
@is_admin
def dates():
	form = DateInterval(request.form)
	if request.method == 'POST':
		date1 = form.date1.data
		date2 = form.date2.data
		if (date1 < date2):
			cur = mysql.connection.cursor()
			result = cur.execute("select sum(total) as total,sum(total_p) as total_p , date(ddtt) dd from t_hist where date(ddtt) between %s and %s group by date(ddtt)",(date1,date2))
			data = cur.fetchall() 
			cur.close()		
			dates= [x['dd'] for x in data]
			total = [x['total'] for x in data]
			total_p = [x['total_p'] for x in data]
			line_chart = pygal.Bar()
			line_chart.title = 'Form '+str(date1)+' to '+str(date2)+" sell"
			line_chart.x_labels = map(str, dates)
			line_chart.add("Total",total)
			prof=np.array(total)-np.array(total_p)
			line_chart.add("Profit",prof)
			line_chart.render()
			chart = line_chart.render_data_uri()
			return render_template( 'charts2.html', chart = chart,data=data,typ="Date TO Date",type1="Date" )
		else:
			flash("1st date should be less than 2nd one",'danger')
			return render_template('dates.html',form=form)
	return render_template('dates.html',form=form)



@app.route('/days', methods=['GET','POST'])
@is_logged_in
@is_admin
def days():
	form = DayInterval(request.form)
	if request.method == 'POST' and form.validate():
		date = form.date.data
		days = form.days.data
		cur = mysql.connection.cursor()
		resurl = cur.execute("select sum(total) as total , sum(total_p) as total_p,date(ddtt) as dd from t_hist where date(ddtt) between %s and date_add(%s, interval %s day) group by date(ddtt)",(date,date,days))
		data = cur.fetchall()
		cur.close()
		dates = [x['dd'] for x in data]
		total = [x['total'] for x in data]
		total_p = [x['total_p'] for x in data]
		line_chart = pygal.Bar()
		line_chart.title = "From "+str(date)+" to "+str(days)+' days sell'
		line_chart.x_labels = map(str, dates)
		line_chart.add("Total",total)
		prof=np.array(total)-np.array(total_p)
		line_chart.add("Profit",prof)
		line_chart.render()
		chart = line_chart.render_data_uri()
		return render_template( 'charts2.html', chart = chart,data=data,typ="Days" ,type1="Date")
	return render_template('days.html',form=form)

@app.route('/month',methods=["POST","GET"] )
@is_logged_in
@is_admin
def month():
	form = Month(request.form)
	if request.method == 'POST' and form.validate():
		year = form.year.data
		cur = mysql.connection.cursor()
		resurl = cur.execute("select sum(total) as total , sum(total_p) as total_p,monthname(ddtt) as dd from t_hist where year(ddtt) = %s group by month(ddtt) order by month(ddtt)",[year])
		data = cur.fetchall()
		cur.close()
		dates = [x['dd'] for x in data]
		total = [x['total'] for x in data]
		total_p = [x['total_p'] for x in data]
		line_chart = pygal.Bar()
		line_chart.title = 'Month wise sell of all Product' 
		line_chart.x_labels = map(str, dates)
		line_chart.add("Total",total)
		prof=np.array(total)-np.array(total_p)
		line_chart.add("Profit",prof)
		line_chart.render()
		chart = line_chart.render_data_uri()
		return render_template( 'charts2.html', chart = chart,data=data,typ = "MONTH " ,type1="Month")
	return render_template('month.html',form=form)



@app.route('/datep', methods=['GET','POST'])
@is_logged_in
@is_admin
def datep():
	form = DateIntervalP(request.form)
	cur = mysql.connection.cursor()
	cur.execute("USE project")
	result = cur.execute("SELECT * FROM products")
	prods = cur.fetchall()
	form.prod.choices = [x['p_name'] for x in prods]
	if request.method == 'POST' and form.validate():
		date1 = form.date1.data
		date2 = form.date2.data
		prod = form.prod.data
		if (date1 < date2):
			result = cur.execute("select * from products where p_name = %s",[prod])
			data = cur.fetchone()
			p_id = data['p_id']
			result = cur.execute("select sum(qunt*cost) as total, sum(qunt*cost_p) as cost_p,sum(qunt) as qunt , date(ddmm) as dd from record where date(ddmm) between %s and %s  and p_id= %s group by date(ddmm)",(date1,date2,[p_id]))
			data = cur.fetchall()
			cur.close()
			total = [x['total'] for x in data]
			qunt = [x['qunt'] for x in data]
			cost_p = [x['cost_p'] for x in data]
			dates= [x['dd'] for x in data]
			line_chart = pygal.Bar()
			line_chart.title = 'Form '+str(date1)+' to '+str(date2)+" sell of "+str(prod)
			line_chart.x_labels = map(str, dates)
			# line_chart.add("quantity",qunt)
			prof=np.array(total)-np.array(cost_p)
			line_chart.add("Profir",prof)
			line_chart.render()
			chart = line_chart.render_data_uri()
			return render_template( 'charts1.html', chart = chart,data=data ,prod=prod.capitalize(), typ="Date To Date",type1="Date")
		else:
			flash("1st date should be less than 2nd one",'danger')
			return render_template('datep.html',form=form)

	return render_template('datep.html',form=form)



@app.route('/daysp', methods=['GET','POST'])
@is_logged_in
@is_admin
def daysp():
	form = DayIntervalP(request.form)
	cur = mysql.connection.cursor()
	cur.execute("USE project")
	result = cur.execute("SELECT * FROM products")
	prods = cur.fetchall()
	form.prod.choices = [x['p_name'] for x in prods]
	if request.method == 'POST' and form.validate():
		date = form.date.data
		days = form.days.data
		prod = form.prod.data
		result = cur.execute("select * from products where p_name = %s",[prod])
		data = cur.fetchone()
		p_id = data['p_id']
		result = cur.execute("select sum(qunt*cost) as total,sum(qunt*cost_p) as cost_p,sum(qunt) as qunt , date(ddmm) as dd from record where date(ddmm) between %s and date_add(%s, interval %s day)  and p_id=%s  group by date(ddmm)",(date,date,days,[p_id]))
		data = cur.fetchall()
		cur.close()
		total = [x['total'] for x in data]
		qunt = [x['qunt'] for x in data]
		cost_p = [x['cost_p'] for x in data]
		dates = [x['dd'] for x in data]
		line_chart = pygal.Bar()
		line_chart.title = "From "+str(date)+" to "+str(days)+' days sell of '+str(prod)
		line_chart.x_labels = map(str, dates)
		# line_chart.add("quantity",qunt)
		prof=np.array(total)-np.array(cost_p)
		line_chart.add("Profir",prof)
		line_chart.render()
		chart = line_chart.render_data_uri()
		return render_template( 'charts1.html', chart = chart,data=data ,prod=prod.capitalize(),typ="days",type1="Date")
	return render_template('daysp.html',form=form)

@app.route('/monthp', methods=["POST","GET"])
@is_logged_in
@is_admin
def monthp():
	form = MonthP(request.form)
	cur = mysql.connection.cursor()
	cur.execute("USE project")
	result = cur.execute("SELECT * FROM products")
	prods = cur.fetchall()
	form.prod.choices = [x['p_name'] for x in prods]
	if request.method == 'POST' and form.validate():
		prod = form.prod.data
		year = form.year.data
		result = cur.execute("select * from products where p_name = %s",[prod])
		data = cur.fetchone()
		p_id = data['p_id']
		result = cur.execute("select sum(qunt*cost) as total,sum(qunt*cost_p) as cost_p,sum(qunt) as qunt , monthname(ddmm) as dd from record where year(ddmm)=%s  and p_id= %s group by month(ddmm)",(year,[p_id]))
		data = cur.fetchall()
		cur.close()
		total = [x['total'] for x in data]
		qunt = [x['qunt'] for x in data]
		cost_p = [x['cost_p'] for x in data]
		dates = [x['dd'] for x in data]
		line_chart = pygal.Bar()
		line_chart.title = 'Month wise sell of '+ str(prod)
		line_chart.x_labels = map(str, dates)
		# line_chart.add("quantity",qunt)
		prof=np.array(total)-np.array(cost_p)
		line_chart.add("Profit",prof)
		line_chart.render()
		chart = line_chart.render_data_uri()
		return render_template( 'charts1.html', chart = chart,data=data ,prod=prod.capitalize(),typ = "MONTH",type1="Month")
	return render_template('monthp.html',form=form)


@app.route('/all_prev')
@is_logged_in
def all_prev():
	cur = mysql.connection.cursor()
	cur.execute("select t.id, c.c_name as CusName,c.c_contact as ContNo, t.total as Total, u.u_name as EmpName, t.ddtt as DateTime from t_hist t, customer c, users u where t.c_id=c.cust_id and t.emp_id=u.u_id order by t.ddtt desc")
	res = cur.fetchall()
	return render_template('all_prev.html', res=res)



@app.route('/get_bills/<string:c_id>', methods=['GET' , 'POST'])
@is_logged_in
def get_bills(c_id):
	return render_template('get_bills.html')

@app.route('/search_by_cus', methods=["POST","GET"])
@is_logged_in
@is_admin
def search_by_cus():
	form=SearchBill(request.form)
	cur = mysql.connection.cursor()
	cur.execute("USE project")
	result = cur.execute("SELECT distinct c_name FROM customer")
	cust = cur.fetchall()
	print(cust)
	form.c_name.choices = [x['c_name'] for x in cust]
	if request.method == 'POST':
		temp = form.c_name.data
		print(temp)
		result = cur.execute("SELECT c_contact FROM customer where c_name=%s",[temp])
		cust = cur.fetchall()
		print(cust)
		form.c_contact.choices=[x['c_contact'] for x in cust]
		if form.validate():			
			result = cur.execute("SELECT cust_id FROM customer where c_name=%s and c_contact=%s",(temp,form.c_contact.data))
			cust_id=cur.fetchone()
			print(cust_id)
			id_c = cust_id["cust_id"]
			cur.execute("select t_hist.id, customer.c_name as CusName, t_hist.total as Total, users.u_name as EmpName, t_hist.ddtt as DateTime from t_hist inner join  customer on customer.cust_id=t_hist.c_id inner join  users on  users.u_id=t_hist.emp_id where t_hist.c_id=%s",[id_c])
			data=cur.fetchall()
			# print(data)
			return render_template('get_bills.html',data=data)
	return render_template('search_by_cus.html',form=form)

@app.route('/about_us')
def about_us():
	return render_template('about_us.html')

if __name__ == "__main__":
	app.run(debug=True)

