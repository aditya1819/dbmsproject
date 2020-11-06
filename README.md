# DBMS project
###  Inventory Management, Billing System and Record generation
Using HTML ,CSS ,Bootstrap on Frontend and Python Web-framework Flask along with MySQL database

1. Install python modules ( use pip3 for linux )
```
pip install -r requirements.txt
```
2. Change the username and password in dbinit.py to your local system MySQL username and password in app.py
```python
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'Your Database Username here'
app.config['MYSQL_PASSWORD'] = 'Your Database Password here'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
```

3. Run dbinit.py to Inital database and create required Schema for the project
