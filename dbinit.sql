create table products ( p_id int primary key auto_increment, p_name varchar(30)
not null unique, cost int unsigned not null, avl_qn int unsigned not null);

create table t_hist ( tid int primary key auto_increment, cusname varchar(30) not null, cusphone int not null, total_cost int not null, sold_by varchar(30) not null ); 

create table users ( u_id int primary key auto_increment , u_name varchar(30) not null, u_pass varchar(200) not null, admin_status boolean not null);

