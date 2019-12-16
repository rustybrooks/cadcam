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
    'machines', 'tools', 'project_files', 'projects', 'users',
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
initial.add_statement("create unique index machines_unique on machines(user_id, machine_key)")

initial.add_statement("""
    create table tools(
        tool_id serial primary key,
        user_id bigint not null references users(user_id),
        tool_key varchar(100) not null,
        description varchar(300),
        type varchar(100),
        material varchar(100),
        flutes integer,
        xoffset real,
        yoffset real,
        zoffset real,
        diameter real
    )
""")
initial.add_statement("create index tools_tool_id on tools(tool_id)")
initial.add_statement("create unique index tools_unique on tools(user_id, tool_key)")

initial.add_statement("""
    create table projects(
        project_id serial primary key,
        user_id bigint not null references users(user_id),
        project_key varchar(100) not null,
        name varchar(100),
        project_type varchar(100),
        date_created timestamp,
        date_modified timestamp
    )
""")
initial.add_statement("create unique index projects_unique on projects(user_id, project_key)")

#############################

new = Migration(2, "adding project_files table")
for table in [
    'project_files'
]:
    new.add_statement("drop table if exists {}".format(table))

new.add_statement("""
    create table project_files(
        project_file_id serial primary key,
        project_id bigint not null references projects(project_id),
        file_name varchar(200) not null,
        s3_key varchar(200) not null,
        source_project_file_id bigint references project_files(project_file_id),
        date_uploaded timestamp not null,
        is_deleted bool default false,
        date_deleted timestamp
    )
""")
new.add_statement("create index project_files_id on project_files(project_file_id)")
new.add_statement("create index project_files_project_id on project_files(project_id)")

###############################

new = Migration(3, "Adding columns to project")
new.add_statement("alter table projects add column is_public bool not null default true")

new = Migration(6, "Adding columns to project")
new.add_statement("alter table project_files add column date_deleted timestamp")
new.add_statement("alter table project_files add column is_deleted bool not null default false")


