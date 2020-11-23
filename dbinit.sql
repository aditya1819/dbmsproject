drop database project;
create database project;
use project;

create table customer (
	cust_id int auto_increment primary key,
    c_name varchar(50),
    c_contact varchar(15)
);

create table products (
	p_id int primary key auto_increment, 
	p_name varchar(30) not null unique, 
    cost int unsigned not null, 
    cost_p int unsigned not null,
    avl_qn int unsigned not null
);

create table users ( 
	u_id int primary key auto_increment , 
    u_name varchar(30) not null, 
    u_pass varchar(200) not null, 
    admin_status boolean not null
);


create table t_hist( 
	id int auto_increment primary key,
    c_id int,
    emp_id int,
    total varchar(20),
	total_p varchar(20),
    ddtt timestamp default current_timestamp,
    foreign key(c_id) references customer(cust_id),
    foreign key(emp_id) references users(u_id)
);

create table record (
	id int,
    p_id int,
    cost int,
    cost_p int,
    qunt int,
    ddmm timestamp default current_timestamp,
    foreign key(p_id) references products(p_id),
    foreign key(id) references t_hist(id)
);
