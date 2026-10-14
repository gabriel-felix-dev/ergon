"""Acesso PostgreSQL da aplicação, concentrado na camada Model."""

from contextlib import contextmanager
import os
import ssl
from urllib.parse import unquote, urlparse

import pg8000.dbapi
from flask import has_request_context, request


class DatabaseConfigurationError(Exception):
    pass


class DatabaseUnavailableError(Exception):
    pass


def _database_url():
    if has_request_context():
        worker_env = request.environ.get("workers.env")
        if worker_env is not None:
            value = getattr(worker_env, "DATABASE_URL", None)
            if value:
                return str(value)
    value = os.environ.get("DATABASE_URL")
    if not value:
        raise DatabaseConfigurationError("Configure DATABASE_URL com a URI real do PostgreSQL")
    return value


def _ssl_context(host):
    context = ssl.create_default_context()
    ca_file = os.environ.get("DATABASE_SSL_CA_FILE")
    if ca_file:
        context.load_verify_locations(cafile=ca_file)
        # O intermediário do pooler Supabase não tem Key Usage. Python 3.13+
        # o rejeita em modo X.509 estrito; CA e hostname continuam verificados.
        if host.endswith(".pooler.supabase.com"):
            context.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return context


def _connect():
    parts = urlparse(_database_url())
    if parts.scheme not in ("postgres", "postgresql") or not parts.hostname:
        raise DatabaseConfigurationError("DATABASE_URL deve ser uma URL PostgreSQL válida")
    if parts.hostname == "host":
        raise DatabaseConfigurationError("DATABASE_URL ainda usa o servidor de exemplo 'host'; informe o endereço real do PostgreSQL")
    try:
        port = parts.port or 5432
    except ValueError as error:
        raise DatabaseConfigurationError("DATABASE_URL tem uma porta inválida") from error
    local = parts.hostname in ("localhost", "127.0.0.1", "::1")
    try:
        return pg8000.dbapi.connect(
            user=unquote(parts.username or ""),
            password=unquote(parts.password or ""),
            host=parts.hostname,
            port=port,
            database=unquote(parts.path.lstrip("/") or "postgres"),
            ssl_context=False if local else _ssl_context(parts.hostname),
            timeout=10,
        )
    except (pg8000.dbapi.InterfaceError, pg8000.dbapi.DatabaseError) as error:
        raise DatabaseUnavailableError("Não foi possível conectar ao PostgreSQL; confira DATABASE_URL, acesso à rede e se o banco está ativo") from error


@contextmanager
def transaction():
    connection = _connect()
    try:
        yield connection
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def one(connection, sql, parameters=()):
    cursor = connection.cursor()
    try:
        cursor.execute(sql, parameters)
        row = cursor.fetchone()
        return dict(zip((col[0] for col in cursor.description), row)) if row else None
    finally:
        cursor.close()


def all_rows(connection, sql, parameters=()):
    cursor = connection.cursor()
    try:
        cursor.execute(sql, parameters)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        cursor.close()


def execute(connection, sql, parameters=()):
    cursor = connection.cursor()
    try:
        cursor.execute(sql, parameters)
        return cursor.rowcount
    finally:
        cursor.close()
