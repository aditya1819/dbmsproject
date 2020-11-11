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

3. Change the username and password in dbinit.py to your local system MySQL username and password in dbconnect.py
```python
class dbconnect():
    user = 'root'     # mysql db username
    passwd = 'pass'   # mysql db password
```

![Screenshot from 2020-11-12 00-29-59](https://user-images.githubusercontent.com/57535120/98852888-5d04b180-247e-11eb-931b-feb7b1e1703e.png)

