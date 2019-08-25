from contextlib import contextmanager
import datetime
import dateutil.parser
import logging
import pytz
import io
import sqlalchemy, sqlalchemy.exc
from sqlalchemy import Table, MetaData, text
import threading
import traceback
import types
from warnings import filterwarnings

from .structures import dictobj

logger = logging.getLogger(__name__)
filterwarnings('ignore', message='Invalid utf8mb4 character string')
filterwarnings('ignore', message='Duplicate entry')

try:
    import flask
except Exception as e:
    logger.warn("Failed to import flask")

_thread_locals = None


def chunked(iterator, chunksize):
    """
    Yields items from 'iterator' in chunks of size 'chunksize'.

    >>> list(chunked([1, 2, 3, 4, 5], chunksize=2))
    [(1, 2), (3, 4), (5,)]
    """
    chunk = []
    for idx, item in enumerate(iterator, 1):
        chunk.append(item)
        if idx % chunksize == 0:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def thread_id():
    t = threading.current_thread()
    return '{}/{}'.format(t.name, t.ident % 100000)


class SQLBase(object):
    def __init__(
            self, connection_string, echo=False, echo_pool=False, isolation_level=None,
            pool_size=5, max_overflow=10, poolclass=None, pool_recycle=30*60, flask_storage=False,
    ):
        global _thread_locals
        kwargs = {
            'logging_name': __name__,
            'echo': echo,
            'echo_pool': echo_pool,
        }

        for (arg, val) in (
            ('pool_recycle', pool_recycle),
            ('pool_size', pool_size),
            ('max_overflow', max_overflow),
            ('isolation_level', isolation_level),
            ('poolclass', poolclass),
        ):
            if val is not None:
                kwargs[arg] = val

        self.engine = sqlalchemy.create_engine(connection_string, **kwargs)
        self.metadata = MetaData()
        self.mysql = 'mysql' in connection_string
        self.postgres = 'postgres' in connection_string
        self.sqlite = 'sqlite' in connection_string

        if flask_storage:
            _thread_locals = flask.g
        else:
            _thread_locals = threading.local()

    def conn(self):
        if not hasattr(_thread_locals, 'conn'):
            _thread_locals.conn = SQLConn(self)

        return _thread_locals.conn

    @classmethod
    def cleanup_conn(cls, dump_log=False):
        logs = None
        if hasattr(_thread_locals, 'conn'):
            _thread_locals.conn.cleanup()
            if dump_log:
                io = io.StringIO.StringIO()
                _thread_locals.conn.dump_log(io)
                logs = io.getvalue()

            del _thread_locals.conn
        else:
            logs = ['No thread locals?']

        return logs

    # transaction decorator
    def is_transaction(self, orig_fn):
        def new_fn(*args, **kwargs):
            with self.transaction():
                return orig_fn(*args, **kwargs)

        return new_fn

    def table(self, table_name):
        if not hasattr(_thread_locals, 'tables'):
            _thread_locals.tables = {}

        if table_name not in _thread_locals.tables:
            try:
                _thread_locals.tables[table_name] = Table(
                    table_name, self.metadata, autoload=True, autoload_with=self.engine
                )
            except sqlalchemy.exc.NoSuchTableError:
                return None

        return _thread_locals.tables[table_name]

    def table_exists(self, table_name):
        return self.engine.dialect.has_table(self.engine, table_name)

    def ensure_table(self, table_name, query, drop_first=False, dry_run=False):
        do_create = False
        if self.table_exists(table_name):
            table = self.table(table_name)
            if drop_first:
                do_create = True
                table.drop()
        else:
            do_create = True

        if do_create:
            logger.warn(u'Creating table %r', table_name)
            self.execute(u'create table {} ({})'.format(table_name, query), dry_run=dry_run)
        else:
            logger.warn(u'Not creating table %r', table_name)

    @classmethod
    def in_clause(cls, in_list):
        return u','.join([u'%s'] * len(in_list))

    # @classmethod
    def auto_where(self, asdict=False, **kwargs):
        asdict = asdict or not self.mysql
        where = []
        bindvars = {} if asdict or not self.mysql else []
        count = 0
        for k, v in kwargs.items():
            if v is not None:
                count += 1
                if asdict:
                    if self.mysql:
                        where.append(u'{}=%({})s'.format(k, k))
                    else:
                        where.append(u'{}=:{}'.format(k, k))
                        bindvars[k] = v
                else:
                    where.append(u'{}=%s'.format(k))
                    bindvars.append(v)

        return where, bindvars

    @classmethod
    def where_clause(cls, where_list, join_with=u'and', prefix=u'where'):
        if where_list is None:
            where_list = []
        elif isinstance(where_list, str):
            where_list = [where_list]

        join_with = u' {} '.format(join_with.strip())
        return u'{where_prefix}{where_clause}'.format(
            where_prefix=u'{} '.format(prefix) if prefix and len(where_list) else '',
            where_clause=join_with.join(where_list) if where_list else '',
        )

    @classmethod
    def construct_where(cls, where_data, prefix=u'where'):
        def _sub(dd):
            out = []
            for k, v in dd.items():
                bindvars.append(v)
                out.append(u'{}=%s'.format(k))

            return u'({})'.format(cls.where_clause(out, join_with=u'and', prefix=''))

        bindvars = []

        if not isinstance(where_data, (list, tuple)):
            where_data = [where_data]

        return bindvars, cls.where_clause([_sub(x) for x in where_data], join_with='or', prefix=prefix)

    def limit(self, start=None, limit=None, page=None):
        if page is not None and limit is not None:
            start = (page-1)*limit

        if start or limit:
            if start:
                if self.mysql:
                    return u'limit {},{}'.format(max(0, start), max(1, limit or 1))  # Is 1 a good default?
                else:
                    return u' offset {} limit {}'.format(max(0, start), max(1, limit or 1))  # Is 1 a good default?
            else:
                return u'limit {}'.format(max(1, limit))
        else:
            return ''

    @classmethod
    def orderby(cls, sort_key, default=None):
        sort_key = sort_key or default
        if sort_key is None:
            return ''
        elif isinstance(sort_key, (list, tuple)):
            return u'order by {} {}'.format(*sort_key) if sort_key else u''
        elif isinstance(sort_key, str):
            keys = []
            for key in sort_key.split(','):
                order = u'asc'
                if key[0] == '-':
                    order = u'desc'
                    key = key[1:]
                keys.append(u'{} {}'.format(key, order))

            return u'order by {}'.format(u','.join(keys))
        else:
            logger.error(u'Invalid sort key specified: %r', sort_key)
            return u''

    @classmethod
    def process_date(cls, dtstr, default=None, strip_timezone=True):
        if not dtstr:
            dtstr = default

        if not dtstr:
            return dtstr

        if isinstance(dtstr, datetime.datetime):
            dt = dtstr
        else:
            dt = dateutil.parser.parse(dtstr) if dtstr else None

        if dt.tzinfo is None and not strip_timezone:
            dt = pytz.utc.localize(dt)
        elif dt.tzinfo is not None and strip_timezone:
            dt = dt.astimezone(pytz.utc).replace(tzinfo=None)

        return dt

    def result_count(self, with_count, results, count_query, bindvars=None):
        if with_count:
            bindvars = bindvars or {}
            return {
                'results': results,
                'count': self.select_one(count_query, bindvars).count
            }
        else:
            return results

    # This is intended to proxy any unknown function automatically to the connection
    def __getattr__(self, item):
        conn = self.conn()

        def proxy(*args, **kwargs):
            return getattr(conn, item)(*args, **kwargs)

        return proxy


class SQLConn(object):
    def __init__(self, sql):
        self.sql = sql
        self._transaction = []
        self._connection = self.sql.engine.connect()
        self._log = []

    def __str__(self):
        return 'SQLConn({})'.format(hex(id(self._connection)))

    def log(self, msg, *args, **kwargs):
        logmsg = u'[%s %s] %s' % (
                thread_id(),
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                msg.format(*args, **kwargs)
            )
        self._log.append(logmsg)

    def dump_log(self, fh):
        for l in self._log:
            fh.write(l)
            fh.write('\n')

    def panic(self, error):
        logger.error(u'An error occurred during a SQL operation.  Error: %r -- Dumping logs: %r', error, self._log)

    def cleanup(self):
        if self._transaction:
            self.log(u'Rolling back transaction')
            self.rollback_transaction()
            self.panic(u'SQL object has leftover transaction.  ROLLING BACK.')

        if self._connection:
            self.log(u'Closing connection')
            self._connection.close()
            self._connection = None

    @contextmanager
    def transaction(self):
        self.begin_transaction()
        try:
            yield 1

            self.commit_transaction()
        except Exception as e:
            self.rollback_transaction()
            raise e

    @contextmanager
    def cursor(self, options=None):
        if options:
            yield self._connection.execution_options(**options)
        else:
            yield self._connection

    def begin_transaction(self):
        if not self._connection:
            self.panic(u'Connection is none.  WHY??')
            raise Exception('Bailing')

        self._transaction.append(self._connection.begin())

    def commit_transaction(self):
        trans = self._transaction.pop()
        trans.commit()

    def rollback_transaction(self):
        if not self._transaction:
            return

        trans = self._transaction.pop()
        trans.rollback()
        self._transaction = []

    def select_column(self, statement, data=None):
        with self.cursor() as c:
            rs = c.execute(text(statement), data or {})

            for row in rs:
                yield row[0]

    def select_columns(self, statement, data=None):
        cols = {}
        with self.cursor() as c:
            rs = c.execute(text(statement), data or {})

            cols = {k: [] for k in rs.keys()}

            for row in rs:
                map(lambda x: cols[x[0]].append(x[1]), row.items())

        return cols

    def select_foreach(self, statement, data=None, stream=False):
        options = {}
        if stream:
            options['stream_results'] = True
        with self.cursor() as c:
            rs = c.execute(text(statement), data or {})

            for row in rs:
                yield dictobj(row.items())

    def select(self, statement, index=None, data=None):
        results = {'list': []}
        with self.cursor() as c:
            rs = c.execute(text(statement), data or {})

            results['columns'] = None
            this_index = -1
            for row in rs:
                if results['columns'] is None:
                    results['columns'] = row.keys()

                if index is None:
                    this_index += 1
                else:
                    this_index = row[index[0]] if len(index) == 1 else tuple(row[x] for x in index)
                results['list'].append(this_index)
                results[this_index] = dictobj(row.items())

        return results

    def select_one(self, statement, data=None):
        with self.cursor() as c:
            rs = c.execute(text(statement), data or {})
            row = rs.fetchone()
            rs.close()
            return dictobj(row.items())

    def select_0or1(self, statement, data=None):
        with self.cursor() as c:
            rs = c.execute(text(statement), data or {})
            count = 0
            result = None
            for row in rs:
                count += 1
                if count == 1:
                    result = row
                elif count == 2:
                    raise Exception(u'Query was expected to return 0 or 1 rows, returned more')

            return dictobj(result.items()) if result is not None else None

    def insert(self, table_name, data, ignore_duplicates=False, batch_size=200, returning=True):
        def _ignore_pre():
            if self.sql.mysql:
                return ' ignore'
            elif self.sql.sqlite:
                return "or ignore"

            return ''

        def _ignore_post():
            if self.sql.postgres:
                return "on conflict do nothing"

            return ''

        if not data:
            return 0

        sample = data if isinstance(data, dict) else data[0]
        columns = sorted(sample.keys())
        if self.sql.mysql:
            values = [u'%({})s'.format(c) for c in columns]
        else:
            values = [u':{}'.format(c) for c in columns]

        query = u'insert{ignore_pre} into {table}({columns}) values ({values}) {ignore_post} {returning}'.format(
            ignore_pre=_ignore_pre() if ignore_duplicates else '',
            ignore_post=_ignore_post() if ignore_duplicates else '',
            table=table_name,
            columns=u', '.join(columns),
            values=u', '.join(values),
            returning=u'returning *' if self.sql.postgres and returning else ''
        )

        with self.cursor() as c:
            if isinstance(data, dict):
                rs = c.execute(text(query), data)
                if self.sql.postgres:
                    return dictobj(rs.fetchone().items())
                else:
                    return rs.lastrowid  # mysql only??
            else:
                count = 0
                for chunk in chunked(data, batch_size):
                    count += c.execute(text(query), chunk).rowcount

                return count

    def update(self, table_name, where, data=None, where_data=None):

        if self.sql.mysql:
            bindvars = [data[k] for k in sorted(data.keys())] + (where_data or [])
            # set_vals = u', '.join([u'{}=%({})s'.format(k, k) for k in sorted(data.keys())])
            set_vals = u', '.join([u'{}=%s'.format(k) for k in sorted(data.keys())])
        else:
            bindvars = {}
            bindvars.update(data)
            bindvars.update(where_data or {})
            set_vals = u', '.join([u'{}=:{}'.format(k, k) for k in sorted(data.keys())])

        query = u'update {table} set {sets} {where}'.format(
            table=table_name,
            sets=set_vals,
            where=u'where {}'.format(where) if len(where) else '',
        )

        with self.cursor() as c:
            rs = c.execute(text(query), bindvars)
            return rs.rowcount

    def update_multiple(self, table_name, where, data=None, where_columns=None, batch_size=200):
        sample = data if isinstance(data, dict) else data[0]
        columns = sorted([k for k in sample.keys() if k not in (where_columns or [])])

        query = u'update {table} set {sets} {where}'.format(
                table=table_name,
                sets=u', '.join([u'{}=%({})s'.format(k, k) for k in columns]),
                where=u'where {}'.format(where) if len(where) else '',
        )

        with self.cursor() as c:
            count = 0
            for chunk in chunked(data, batch_size):
                count += c.execute(text(query), chunk).rowcount

            return count

    def delete(self, table_name, where_clause=None, data=None):
        query = u'delete from {table} {where}'.format(table=table_name, where=self.sql.where_clause(where_clause))

        with self.cursor() as c:
            rs = c.execute(text(query), data or [])
            return rs.rowcount

    def execute(self, query, data=None, dry_run=False, log=False):
        if dry_run or log:
            logger.warn(u'SQL Run: {}'.format(query))

        if dry_run:
            return

        with self.cursor() as c:
            rs = c.execute(text(query), data or [])

        return rs.rowcount


class MigrationStatement(object):
    def __init__(self, statement=None, message=None, ignore_error=False):
        self.statement = statement
        self.message = message
        self.ignore_error = ignore_error

    @classmethod
    def log(self, logs, msg, *args):
        formatted = msg % args
        if logs:
            logs.append(formatted)
        logger.warn(formatted)

    def execute(self, SQL, dry_run=False, logs=None):
        if self.message:
            self.log(logs, u'%r', self.message)

        try:
            self.log(logs, "SQL Execute: %r", self.statement)
            SQL.execute(self.statement, dry_run=dry_run, log=False)
        except Exception as e:
            self.log(logs, u'Error while running statment: %r', traceback.format_exc())
            if not self.ignore_error:
                raise e


class Migration(object):
    registry = {}

    def __init__(self, version, message):
        self.registry[version] = self
        self.statements = []
        self.message = message
        self.logs = []

    @classmethod
    def log(self, logs, msg, *args):
        formatted = msg % args
        logs.append(formatted)
        logger.warn(formatted)

    @classmethod
    def migrate(cls, SQL, dry_run=False, initial=False, apply_versions=None):
        logs = []
        apply_versions = apply_versions or []
        if SQL.sqlite:
            SQL.ensure_table('migrations', u'''
            migration_id integer not null primary key,
            migration_datetime datetime,
            version_pre int,
            version_post int
        ''')
        elif SQL.postgres:
            SQL.ensure_table('migrations', u'''
            migration_id serial primary key,
            migration_datetime timestamp,
            version_pre int,
            version_post int
        ''')
        else:
            SQL.ensure_table('migrations', u'''
                migration_id serial integer not null primary key auto_increment,
                migration_datetime datetime,
                version_pre int,
                version_post int
            ''')

        res = SQL.select_one('select max(version_post) as version from migrations')
        version = res.version if (res.version is not None and not initial) else -1
        todo = sorted([x for x in cls.registry.keys() if x > version] + apply_versions)
        cls.log(logs, u'Version = %d, todo = %r, initial=%r', version, todo, initial)

        version_pre = version_post = version
        for v in todo:
            cls.log(logs, u'Running migration %d: %s', v, cls.registry[v].message)

            for statement in cls.registry[v].statements:
                statement.execute(SQL=SQL, dry_run=dry_run, logs=logs)

            if v > version_pre:
                version_post = v

        if len(todo) and not dry_run:
            SQL.insert(u'migrations', {
                u'migration_datetime': datetime.datetime.utcnow(),
                u'version_pre': version, u'version_post': version_post,
            })

        return logs

    def add_statement(self, statement, ignore_error=False, message=None):
        self.statements.append(
            MigrationStatement(statement, ignore_error=ignore_error, message=message)
        )
