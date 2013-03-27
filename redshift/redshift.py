# redshift.py

"""
.. dialect:: postgresql+redshift
	:name: redshift
	:dbapi: redshift
	:connectstring: postgresql+redshift://user:password@host:port/dbname[?key=value&key=value...]

"""
from sqlalchemy.dialects.postgresql.base import PGDialect, PGCompiler, \
								PGIdentifierPreparer, PGExecutionContext, \
								ENUM, ARRAY, _DECIMAL_TYPES, _FLOAT_TYPES,\
								_INT_TYPES
from sqlalchemy.dialects import util
from sqlalchemy.dialects.postgresql.psycopg2 import _PGHStore, _PGArray, _PGEnum, _PGNumeric, PGExecutionContext_psycopg2, PGCompiler_psycopg2, PGIdentifierPreparer_psycopg2
from sqlalchemy import types as sqltypes
from sqlalchemy.dialects.postgresql.hstore import HSTORE
import re

class PGDialect_RedShift(PGDialect):
	driver = 'psycopg2'
	# Py2K
	supports_unicode_statements = False
	# end Py2K
	default_paramstyle = 'pyformat'
	supports_sane_multi_rowcount = False
	execution_ctx_cls = PGExecutionContext_psycopg2
	statement_compiler = PGCompiler_psycopg2
	preparer = PGIdentifierPreparer_psycopg2
	psycopg2_version = (0, 0)

	_has_native_hstore = False

	colspecs = util.update_copy(
		PGDialect.colspecs,
		{
			sqltypes.Numeric: _PGNumeric,
			ENUM: _PGEnum,  # needs force_unicode
			sqltypes.Enum: _PGEnum,  # needs force_unicode
			ARRAY: _PGArray,  # needs force_unicode
			HSTORE: _PGHStore,
		}
	)

	def __init__(self, server_side_cursors=False, use_native_unicode=True,
						client_encoding=None,
						use_native_hstore=True,
						**kwargs):
		PGDialect.__init__(self, **kwargs)
		self.server_side_cursors = server_side_cursors
		self.use_native_unicode = use_native_unicode
		self.use_native_hstore = use_native_hstore
		self.supports_unicode_binds = use_native_unicode
		self.client_encoding = client_encoding
		if self.dbapi and hasattr(self.dbapi, '__version__'):
			m = re.match(r'(\d+)\.(\d+)(?:\.(\d+))?',
								self.dbapi.__version__)
			if m:
				self.psycopg2_version = tuple(
											int(x)
											for x in m.group(1, 2, 3)
											if x is not None)

	def initialize(self, connection):
		super(PGDialect_RedShift, self).initialize(connection)
		self._has_native_hstore = self.use_native_hstore and \
						self._hstore_oids(connection.connection) \
							is not None

	@classmethod
	def dbapi(cls):
		import psycopg2
		return psycopg2

	def get_isolation_level(self, connection):
		return None

	@util.memoized_property
	def _isolation_lookup(self):
		extensions = __import__('psycopg2.extensions').extensions
		return {
			'READ COMMITTED': extensions.ISOLATION_LEVEL_READ_COMMITTED,
			'READ UNCOMMITTED': extensions.ISOLATION_LEVEL_READ_UNCOMMITTED,
			'REPEATABLE READ': extensions.ISOLATION_LEVEL_REPEATABLE_READ,
			'SERIALIZABLE': extensions.ISOLATION_LEVEL_SERIALIZABLE
		}

	def set_isolation_level(self, connection, level):
		try:
			level = self._isolation_lookup[level.replace('_', ' ')]
		except KeyError:
			raise exc.ArgumentError(
				"Invalid value '%s' for isolation_level. "
				"Valid isolation levels for %s are %s" %
				(level, self.name, ", ".join(self._isolation_lookup))
				)

		connection.set_isolation_level(level)

	def on_connect(self):
		from psycopg2 import extras, extensions

		fns = []
		if self.client_encoding is not None:
			def on_connect(conn):
				conn.set_client_encoding(self.client_encoding)
			fns.append(on_connect)

		if self.isolation_level is not None:
			def on_connect(conn):
				self.set_isolation_level(conn, self.isolation_level)
			fns.append(on_connect)

		if self.dbapi and self.use_native_unicode:
			def on_connect(conn):
				extensions.register_type(extensions.UNICODE, conn)
			fns.append(on_connect)

		if self.dbapi and self.use_native_hstore:
			def on_connect(conn):
				hstore_oids = self._hstore_oids(conn)
				if hstore_oids is not None:
					oid, array_oid = hstore_oids
					extras.register_hstore(conn, oid=oid, array_oid=array_oid)
			fns.append(on_connect)

		if fns:
			def on_connect(conn):
				for fn in fns:
					fn(conn)
			return on_connect
		else:
			return None

	@util.memoized_instancemethod
	def _hstore_oids(self, conn):
		if self.psycopg2_version >= (2, 4):
			from psycopg2 import extras
			oids = extras.HstoreAdapter.get_oids(conn)
			if oids is not None and oids[0]:
				return oids[0:2]
		return None

	def create_connect_args(self, url):
		opts = url.translate_connect_args(username='user')
		if 'port' in opts:
			opts['port'] = int(opts['port'])
		opts.update(url.query)
		return ([], opts)

	def is_disconnect(self, e, connection, cursor):
		if isinstance(e, self.dbapi.OperationalError):
			# these error messages from libpq: interfaces/libpq/fe-misc.c.
			# TODO: these are sent through gettext in libpq and we can't
			# check within other locales - consider using connection.closed
			return 'terminating connection' in str(e) or \
					'closed the connection' in str(e) or \
					'connection not open' in str(e) or \
					'could not receive data from server' in str(e)
		elif isinstance(e, self.dbapi.InterfaceError):
			# psycopg2 client errors, psycopg2/conenction.h, psycopg2/cursor.h
			return 'connection already closed' in str(e) or \
					'cursor already closed' in str(e)
		elif isinstance(e, self.dbapi.ProgrammingError):
			# not sure where this path is originally from, it may
			# be obsolete.   It really says "losed", not "closed".
			return "losed the connection unexpectedly" in str(e)
		else:
			return False

dialect = PGDialect_RedShift
