"""Credenciais e sessões dos funcionários."""

import hashlib
import hmac
import secrets

from db import execute, one, transaction
from services import RuleError


ITERATIONS = 600_000


def password_hash(password):
    if not isinstance(password, str) or not 10 <= len(password) <= 256:
        raise RuleError("A senha deve ter entre 10 e 256 caracteres", 400)
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


def login(assistance_id, email, password):
    with transaction() as connection:
        user = one(
            connection,
            '''SELECT f."Id", f."Nome", f."Email", f."SenhaHash", f."Ativo",
                      f."Gerente", a."Ativo" AS "AssistenciaAtiva"
                 FROM public."Funcionario" f
                 JOIN public."AssistenciaTecnica" a ON a."Id" = f."IdAssistenciaTecnica"
                WHERE f."IdAssistenciaTecnica" = %s AND LOWER(f."Email") = LOWER(%s)''',
            (assistance_id, email),
        )
        if not user or not user["Ativo"] or not user["AssistenciaAtiva"] or not verify_password(password, user["SenhaHash"]):
            raise RuleError("Credenciais inválidas", 401)
        token = secrets.token_urlsafe(32)
        digest = hashlib.sha256(token.encode()).hexdigest()
        execute(
            connection,
            '''INSERT INTO public."SessaoAcesso"
                   ("TokenHash", "IdAssistenciaTecnica", "IdFuncionario", "ExpiraEm")
               VALUES (%s, %s, %s, CURRENT_TIMESTAMP + INTERVAL '12 hours')''',
            (digest, assistance_id, user["Id"]),
        )
    return {"token": token, "usuario": {
        "id": user["Id"], "nome": user["Nome"], "email": user["Email"],
        "gerente": user["Gerente"], "assistenciaId": assistance_id,
    }}


def principal(token):
    if not token:
        raise RuleError("Acesso não autenticado", 401)
    digest = hashlib.sha256(token.encode()).hexdigest()
    with transaction() as connection:
        record = one(
            connection,
            '''SELECT s."IdAssistenciaTecnica", f."Id", f."Nome", f."Gerente",
                      f."Ativo" AS "FuncionarioAtivo", a."Ativo" AS "AssistenciaAtiva"
                 FROM public."SessaoAcesso" s
                 JOIN public."Funcionario" f ON f."Id" = s."IdFuncionario"
                 JOIN public."AssistenciaTecnica" a ON a."Id" = s."IdAssistenciaTecnica"
                WHERE s."TokenHash" = %s AND s."ExpiraEm" > CURRENT_TIMESTAMP''',
            (digest,),
        )
    if not record or not record["AssistenciaAtiva"] or not record["FuncionarioAtivo"]:
        raise RuleError("Sessão inválida ou expirada", 401)
    return {"id": record["Id"], "nome": record["Nome"],
            "gerente": record["Gerente"], "assistenciaId": record["IdAssistenciaTecnica"]}


def logout(token):
    digest = hashlib.sha256(token.encode()).hexdigest()
    with transaction() as connection:
        execute(connection, '''DELETE FROM public."SessaoAcesso" WHERE "TokenHash" = %s''', (digest,))
