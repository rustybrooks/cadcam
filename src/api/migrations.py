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
    'users', 'machines',
]:
    initial.add_statement("drop table if exists {}".format(table))


initial.add_statement("""
    create table users(
        user_id serial primary key,
        password varchar(200) not null,
        email varchar(200) not null unique,
        username varchar(50) not null unique,
        is_admin bool default false not null,
        api_key char(64) not null
    )
""")
initial.add_statement("create index users_user_id on users(user_id)")
initial.add_statement("create index users_username on users(username)")
initial.add_statement("create index users_email on users(email)")
initial.add_statement("create index users_api_key on users(api_key)")

initial.add_statement("""
    create table machines(
        machine_id serial primary key,
        user_id bigint not null references users(user_id),
        machine_key varchar(100) not null,
        name varchar(100),
        min_rpm real not null default 0,
        max_rpm real not null,
        max_feedrate_x real not null,
        max_feedrate_y real not null,
        max_feedrate_z real not null
    )
""")
initial.add_statement("create index machines_machine_id on machines(machine_id)")
initial.add_statement("create unique index machines_unique in machines(user_id, machine_key")

initial.add_statement("""
    create table projects(
        project_id serial primary key,
        user_id bigint not null references users(user_id),
        project_key varchar(100) not null,
        name varchar(100),
        s3_key varchar(200),
        date_created timestamp,
        date_modified timestamp,
    )
""")
initial.add_statement("create unique index projects_unique in machines(user_id, project_key")
