# This is to manage the database structure

import logging
from warnings import filterwarnings

from lib.database.sql import Migration

logger = logging.getLogger(__name__)
filterwarnings('ignore', message='Invalid utf8mb4 character string')
filterwarnings('ignore', message='Duplicate entry')

##########################################################################################

initial = Migration(1, "initial version")
for table in [
    'users'
]:
    initial.add_statement("drop table if exists {}".format(table))


initial.add_statement("""
    create table users(
        user_id serial primary key,
        password varchar(200),
        email varchar(200),
        username varchar(50),
        is_admin bool default false
    )
""")
initial.add_statement("create index users_user_id on users(user_id)")
initial.add_statement("create index users_user_id on users(username)")
initial.add_statement("create index users_user_id on users(email)")

initial.add_statement("""
    create table machines(
        machine_id serial primary key,
        user_id bigint not null references users(user_id),
        name varchar(100),
        min_rpm double,
        max_rpm double,
        max_feedrate_x double,
        max_feedrate_y double,
        max_feedrate_z double,
    )
""")
initial.add_statement("create index machines_machine_id on machines(machine_id)")
initial.add_statement("create index machines_user_id on machines(user_id)")
