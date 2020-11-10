

create table customer (
	cust_id int auto_increment primary key,
    c_name varchar(50),
    c_contact varchar(15)
);
drop table cutomer;
desc customer;
select * from customer;


create table t_hist( 
	id int auto_increment primary key,
    c_id int,
    emp_id int,
    total varchar(20),
    ddtt timestamp default current_timestamp,
    foreign key(c_id) references customer(cust_id),
    foreign key(emp_id) references users(u_id)
);

create table record (
	id int,
    p_id int,
    cost int,
    qunt int,
    ddmm timestamp default current_timestamp,
    foreign key(p_id) references products(p_id),
    foreign key(id) references t_hist(id)
);

