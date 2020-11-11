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

3. Chnage local MySQL DB username and password in dbconnect.py
```python
class dbconnect():
    user = 'root'     # mysql db username
    passwd = 'pass'   # mysql db password
```

### Some Images of Project :

![Screenshot from 2020-11-12 00-29-59](https://user-images.githubusercontent.com/57535120/98853387-106da600-247f-11eb-96f0-9678130261d0.png)


![Screenshot from 2020-11-12 00-30-10](https://user-images.githubusercontent.com/57535120/98853469-36934600-247f-11eb-98c0-f324f8968a61.png)


![Screenshot from 2020-11-12 00-30-26](https://user-images.githubusercontent.com/57535120/98853524-4448cb80-247f-11eb-86c2-80f7567c3107.png)
