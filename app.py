from flask import Flask, render_template, redirect,request, url_for
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators,SelectField, IntegerField

app = Flask(__name__)
app.secret_key='thisisnotasecretkeycozitsnotsecret'

# mysql config

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'pass'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

class UpdateFrom(Form):
	p_name = SelectField('Product', choices=[])
	added = IntegerField('Quantity Added', [validators.NumberRange(min=1, max=100)])
	cost = IntegerField('Cost per unit')

class AddNewProd(Form):
	p_name = StringField('Product Name', [validators.Length(min=4, max=30)])
	added = IntegerField('Intital Quantity', [validators.NumberRange(min=1, max=100)])
	cost = IntegerField('Cost per unit')

@app.route('/')
def index():
	return render_template('index.html')


@app.route('/inv_det')
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
		cur.execute("SELECT avl_qn FROM products WHERE p_name= %s", [p_name])
		avl = cur.fetchone()
		ans = int(avl['avl_qn']) + int(added)
		cur.execute('UPDATE products SET avl_qn=%s WHERE p_name=%s', (ans, p_name))
		mysql.connection.commit()
		
		if cost != -1:
			cur.execute('UPDATE products SET cost=%s WHERE p_name=%s', (cost, p_name))
			mysql.connection.commit()
		cur.close()
		return redirect(url_for('inv_det'))
		# if form.cost.data:
	return render_template('up_inv.html', form=form)

@app.route('/addprod', methods=['GET', 'POST'])
def addprod():
	form = AddNewProd(request.form)
	if request.method =='POST' and form.validate():
		p_name = form.p_name.data
		added = form.added.data
		cost = form.cost.data
		cur = mysql.connection.cursor()
		cur.execute("USE project")
		cur.execute("INSERT INTO products(p_name, cost, avl_qn) VALUES(%s, %s, %s);", (p_name, cost, added))
		mysql.connection.commit()
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

if __name__ == "__main__":
	app.run(debug=True)