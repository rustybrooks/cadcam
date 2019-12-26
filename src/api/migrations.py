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
    'machines', 'tools', 'project_files', 'project_jobs', 'projects', 'users',
]:
    initial.add_statement("drop table if exists {}".format(table))

for sql_type in ['project_job_status', 'tool_type']:
    initial.add_statement('drop type if exists {}'.format(sql_type))

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
    create type tool_type as enum(
        'straight', 'ball', 'dovetail', 'vee'
    )
""")

initial.add_statement("""
    create table tools(
        tool_id serial primary key,
        user_id bigint references users(user_id),
        date_created timestamp,
        date_modified timestamp,
        tool_key varchar(100) not null,
        description varchar(300),
        type varchar(100),
        material varchar(100),
        flutes integer,
        cutting_length float,
        xoffset real,
        yoffset real,
        zoffset real,
        diameter real,
        minor_diameter real,
        edge_radius real,
        included_angle real
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
        date_modified timestamp,
        is_public bool not null default true
    )
""")
initial.add_statement("create unique index projects_unique on projects(user_id, project_key)")

initial.add_statement("create type project_job_status as enum('running', 'failed', 'succeeded')")
initial.add_statement("""
    create table project_jobs(
        project_job_id serial primary key, 
        project_id bigint not null references projects(project_id),
        status project_job_status,
        job_hash char(32),
        date_created timestamp not null,
        date_completed timestamp
    )
""")
initial.add_statement("create index project_jobs_id on project_jobs(project_job_id)")
initial.add_statement("create unique index project_jobs_project_id_hash on project_jobs(project_id, job_hash)")

initial.add_statement("""
    create table project_files(
        project_file_id serial primary key,
        project_id bigint not null references projects(project_id),
        project_job_id bigint references project_jobs(project_job_id),
        file_name varchar(200) not null,
        s3_key varchar(200) not null,
        source_project_file_id bigint references project_files(project_file_id),
        date_uploaded timestamp not null,
        date_deleted timestamp,
        is_deleted bool default false
    )
""")
initial.add_statement("create index project_files_id on project_files(project_file_id)")
initial.add_statement("create index project_files_project_id on project_files(project_id)")
initial.add_statement("create index project_files_job_id on project_files(project_job_id)")




