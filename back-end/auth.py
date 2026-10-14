"""Senhas e sessões JWT de funcionários e clientes."""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
import secrets

import jwt

from db import execute, one, transaction
from services import RuleError


ITERATIONS = 600_000
SESSION_HOURS = 12


def password_hash(password):
    if not isinstance(password, str) or not 8 <= len(password) <= 256:
        raise RuleError("A senha deve ter entre 8 e 256 caracteres", 400)
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password, stored):
    try:
        algorithm, rounds, salt_hex, digest_hex = stored.split("$")
        if algorithm != "pbkdf2_sha256" or int(rounds) < 100_000:
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds)
        )
        return hmac.compare_digest(actual, bytes.fromhex(digest_hex))
    except (AttributeError, TypeError, ValueError):
        return False


def _secret():
    value = os.environ.get("JWT_SECRET", "")
    if len(value) < 32:
        raise RuntimeError("Configure JWT_SECRET com pelo menos 32 caracteres")
    return value


def _table(kind):
    if kind == "funcionario":
        return 'public."Funcionario"'
    if kind == "cliente":
        return 'public."Cliente"'
    raise RuleError("Tipo de acesso inválido", 400)


def login(assistance_id, email, password, kind="funcionario"):
    table = _table(kind)
    with transaction() as connection:
        user = one(
            connection,
            f'''SELECT u."Id", u."Nome", u."Email", u."SenhaHash", u."Ativo",
                       u."VersaoSessao", a."Ativo" AS "AssistenciaAtiva"
                       {', u."Gerente"' if kind == 'funcionario' else ''}
                  FROM {table} u
                  JOIN public."AssistenciaTecnica" a ON a."Id" = u."IdAssistenciaTecnica"
                 WHERE u."IdAssistenciaTecnica" = %s AND LOWER(u."Email") = LOWER(%s)''',
            (assistance_id, email),
        )
    if not user or not user["Ativo"] or not user["AssistenciaAtiva"] or not verify_password(password, user["SenhaHash"]):
        raise RuleError("Credenciais inválidas", 401)
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user["Id"]), "kind": kind, "assistanceId": assistance_id,
        "version": user["VersaoSessao"], "iat": now,
        "exp": now + timedelta(hours=SESSION_HOURS),
    }
    token = jwt.encode(payload, _secret(), algorithm="HS256")
    return {"token": token, "usuario": {
        "id": user["Id"], "nome": user["Nome"], "email": user["Email"],
        "gerente": user.get("Gerente", False), "assistenciaId": assistance_id,
        "tipo": kind,
    }}


def principal(token):
    if not token:
        raise RuleError("Acesso não autenticado", 401)
    try:
        payload = jwt.decode(
            token, _secret(), algorithms=["HS256"],
            options={"require": ["exp", "iat", "sub", "kind", "assistanceId", "version"]},
        )
        kind = payload["kind"]
        table = _table(kind)
        account_id = int(payload["sub"])
        assistance_id = int(payload["assistanceId"])
        version = int(payload["version"])
    except (jwt.InvalidTokenError, KeyError, ValueError, TypeError, RuleError) as error:
        raise RuleError("Sessão inválida ou expirada", 401) from error
    with transaction() as connection:
        user = one(
            connection,
            f'''SELECT u."Id", u."Nome", u."Email", u."Ativo", u."VersaoSessao",
                       a."Ativo" AS "AssistenciaAtiva"
                       {', u."Gerente"' if kind == 'funcionario' else ''}
                  FROM {table} u
                  JOIN public."AssistenciaTecnica" a ON a."Id" = u."IdAssistenciaTecnica"
                 WHERE u."Id" = %s AND u."IdAssistenciaTecnica" = %s''',
            (account_id, assistance_id),
        )
    if not user or not user["Ativo"] or not user["AssistenciaAtiva"] or user["VersaoSessao"] != version:
        raise RuleError("Sessão inválida ou expirada", 401)
    return {"id": user["Id"], "nome": user["Nome"], "email": user["Email"],
            "gerente": user.get("Gerente", False), "assistenciaId": assistance_id,
            "tipo": kind}


def logout(token):
    user = principal(token)
    table = _table(user["tipo"])
    with transaction() as connection:
        execute(connection, f'''UPDATE {table} SET "VersaoSessao" = "VersaoSessao" + 1
            WHERE "Id" = %s AND "IdAssistenciaTecnica" = %s''',
            (user["id"], user["assistenciaId"]))


def secret_hash(value):
    """Hash para códigos de recuperação e links de convite."""
    return hmac.new(_secret().encode(), value.encode(), hashlib.sha256).hexdigest()
