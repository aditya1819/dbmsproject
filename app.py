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
        cur.execute("USE project")
        result = cur.execute("SELECT * FROM users WHERE u_name = %s", [username])

        if result > 0:
            # get stored hash
            data = cur.fetchone()
            password = data['u_pass']

            # compare pass
            if sha256_crypt.verify(pass_cand, password):
                # app.logger.info("PASS MATCHE")
                session['logged_in'] = True
                session['username'] = username
                if data['admin_status'] == 1:
                    session['admin_status'] = True
                flash("You are now logged in !",'success')
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
        if 'admnin_status' in session:
            return f(*args, **kwargs)
        else:
            flash('You need Admin Access for this Operation','danger')
            return redirect(url_for('login'))
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
		# else :
		#     msg = "No Products found"
		#     return render_template('inv_det.html', msg = msg)
		cur.close()
	except Exception as e:
		print(e)
	return render_template('inv_det.html', prods=prods)

@app.route('/up_inv', methods=['GET', 'POST'])
@is_logged_in
def up_inv():

	cur = mysql.connection.cursor()
	cur.execute("USE project")
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
		# if form.cost.data:
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
def remove_prod(p_name):
	cur = mysql.connection.cursor()
	cur.execute("USE project")
	cur.execute("DELETE FROM products WHERE p_name=%s", [p_name])
	mysql.connection.commit()
	cur.close()
	return redirect(url_for('inv_det'))

@app.route('/edit_cost/<string:p_name>', methods=['GET', 'POST'])
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

@app.route('/add_emp', methods=['GET', 'POST'])
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
		print('admin_status : ', admin_status )
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


if __name__ == "__main__":
	app.run(debug=True)

