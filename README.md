# DBMS project
###  Inventory Management, Billing System and Record generation
Using HTML ,CSS ,Bootstrap on Frontend and Python Web-framework Flask along with MySQL database

1. Install python modules ( use pip3 for linux )
```bash
pip install mysqlclient-1.4.6-cp38-cp38-win32.whl
```
```linux
pip install -r requirements.txt
```

2. Run dbinit.sql to Inital database and create required Schema for the project
```
mysql -u yourUserName -p project < dbinit.sql
```

3. Change the username and password in dbinit.py to your local system MySQL username and password in app.py
```python
class dbconnect():
    host = 'localhost'
    user = 'root'     # mysql db username
    passwd = 'pass'   # mysql db password
    cursorclass = 'DictCursor'
```
