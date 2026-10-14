"""API REST do Ergon."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import hmac
import os
import secrets
from urllib.parse import quote

import pg8000.dbapi
from flask import Flask, jsonify, request
from flask.json.provider import DefaultJSONProvider
from flask_mail import Mail, Message

import auth
from db import (
    DatabaseConfigurationError, DatabaseUnavailableError, all_rows, execute,
    one, transaction,
)
from services import (
    RuleError, create_online_request, decide_budget, list_budgets,
    list_orders, public_budget, register_payment, resend_link, respond_budget,
    update_order,
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024


class ISODateJSONProvider(DefaultJSONProvider):
    def default(self, value):
        if isinstance(value, date) and not isinstance(value, datetime):
            return value.isoformat()
        return super().default(value)


app.json = ISODateJSONProvider(app)


def setting(name):
    worker_env = request.environ.get("workers.env")
    value = getattr(worker_env, name, None) if worker_env is not None else None
    return str(value) if value else os.environ.get(name)


@app.after_request
def headers(response):
    allowed = setting("FRONTEND_ORIGIN") or "http://localhost:5173"
    if request.headers.get("Origin") == allowed:
        response.headers["Access-Control-Allow-Origin"] = allowed
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.before_request
def preflight():
    if request.method == "OPTIONS":
        return ("", 204)


@app.errorhandler(RuleError)
def rule_error(error):
    return jsonify({"erro": str(error)}), error.status


@app.errorhandler(pg8000.dbapi.IntegrityError)
def integrity_error(_error):
    return jsonify({"erro": "Dados duplicados ou relacionamento inválido"}), 409


@app.errorhandler(DatabaseConfigurationError)
@app.errorhandler(DatabaseUnavailableError)
def database_error(error):
    app.logger.error("Falha no banco: %s", error)
    return jsonify({"erro": str(error)}), 503


def body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise RuleError("Envie um objeto JSON", 400)
    return data


def text(data, key, limit=255, required=True):
    value = data.get(key)
    if value is None and not required:
        return None
    if not isinstance(value, str):
        raise RuleError(f"{key} deve ser texto", 400)
    value = value.strip()
    if (required and not value) or len(value) > limit:
        raise RuleError(f"{key} inválido", 400)
    return value or None


def email(data):
    value = text(data, "email").lower()
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        raise RuleError("Email inválido", 400)
    return value


def integer(data, key):
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise RuleError(f"{key} deve ser inteiro positivo", 400)
    return value


def money(data, key):
    try:
        value = data.get(key)
        if isinstance(value, bool):
            raise InvalidOperation()
        result = Decimal(str(value))
        if not result.is_finite() or result.as_tuple().exponent < -2:
            raise InvalidOperation()
        return result
    except (InvalidOperation, TypeError, ValueError):
        raise RuleError(f"{key} deve ser valor monetário válido", 400)


def day(data, key):
    try:
        return date.fromisoformat(text(data, key, 10))
    except ValueError:
        raise RuleError(f"{key} deve estar no formato AAAA-MM-DD", 400)


def token():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise RuleError("Acesso não autenticado", 401)
    return header[7:].strip()


def actor(manager=False):
    user = auth.principal(token())
    if user["tipo"] != "funcionario":
        raise RuleError("Ação restrita à equipe", 403)
    if manager and not user["gerente"]:
        raise RuleError("Ação restrita a gerente", 403)
    return user


def client_actor():
    user = auth.principal(token())
    if user["tipo"] != "cliente":
        raise RuleError("Ação restrita ao cliente", 403)
    return user


def same_assistance(user, assistance_id):
    if user["assistenciaId"] != assistance_id:
        raise RuleError("Registro de outra assistência", 403)


def active_employee(connection, assistance_id, employee_id):
    item = one(connection, '''SELECT "Id" FROM public."Funcionario"
        WHERE "Id" = %s AND "IdAssistenciaTecnica" = %s AND "Ativo" = TRUE''',
        (employee_id, assistance_id))
    if not item:
        raise RuleError("Funcionário responsável inválido", 400)


def send_budget_email(raw_token, recipient):
    link = frontend_link("orcamento", raw_token)
    send_email("Seu orçamento Ergon", recipient,
               "Abra seu orçamento e aprove ou recuse em até dois dias:\n" + link)


def frontend_link(parameter, value=None):
    base = setting("PUBLIC_FRONTEND_URL")
    if not base:
        raise RuleError("Configure PUBLIC_FRONTEND_URL para enviar emails", 503)
    return base.rstrip("/") + ("/?" + parameter + "=" + quote(str(value)) if value else "/?" + parameter)


def send_email(subject, recipient, content):
    required = ("MAIL_SERVER", "MAIL_DEFAULT_SENDER", "PUBLIC_FRONTEND_URL")
    if any(not setting(name) for name in required):
        raise RuleError("Configure SMTP e PUBLIC_FRONTEND_URL para enviar emails", 503)
    app.config.update(
        MAIL_SERVER=setting("MAIL_SERVER"),
        MAIL_PORT=int(setting("MAIL_PORT") or 587),
        MAIL_USE_TLS=(setting("MAIL_USE_TLS") or "true").lower() == "true",
        MAIL_USERNAME=setting("MAIL_USERNAME"),
        MAIL_PASSWORD=setting("MAIL_PASSWORD"),
        MAIL_DEFAULT_SENDER=setting("MAIL_DEFAULT_SENDER"),
    )
    mailer = Mail(app)
    message = Message(subject, recipients=[recipient])
    message.body = content
    try:
        mailer.send(message)
    except Exception as error:
        app.logger.error("Falha ao enviar email: %s", type(error).__name__)
        raise RuleError("Email não enviado. Verifique o SMTP e tente novamente.", 502) from error


@app.get("/api/saude")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/assistencias")
def assistance_public_list():
    with transaction() as connection:
        rows = all_rows(connection, '''SELECT "Id", "Nome" FROM public."AssistenciaTecnica"
            WHERE "Ativo" = TRUE ORDER BY "Nome"''')
    return jsonify(rows)


@app.post("/api/assistencias")
def create_assistance():
    data = body()
    manager = data.get("primeiroGerente")
    if not isinstance(manager, dict):
        raise RuleError("Dados do primeiro gerente são obrigatórios", 400)
    hashed = auth.password_hash(text(manager, "senha", 256))
    with transaction() as connection:
        assistance = one(connection, '''INSERT INTO public."AssistenciaTecnica"
            ("Nome", "Documento", "Email", "Telefone", "Endereco")
            VALUES (%s, %s, %s, %s, %s) RETURNING *''',
            (text(data, "nome"), text(data, "documento", 30), email(data),
             text(data, "telefone", 30, False), text(data, "endereco", 500, False)))
        employee = one(connection, '''INSERT INTO public."Funcionario"
            ("IdAssistenciaTecnica", "Nome", "Documento", "Email", "Telefone", "Gerente", "SenhaHash")
            VALUES (%s, %s, %s, %s, %s, TRUE, %s)
            RETURNING "Id", "Nome", "Email", "Gerente", "Ativo"''',
            (assistance["Id"], text(manager, "nome"), text(manager, "documento", 30),
             email(manager), text(manager, "telefone", 30, False), hashed))
    return jsonify({"assistencia": assistance, "primeiroGerente": employee}), 201


@app.get("/api/assistencias/<int:assistance_id>")
def get_assistance(assistance_id):
    same_assistance(actor(), assistance_id)
    with transaction() as connection:
        item = one(connection, '''SELECT * FROM public."AssistenciaTecnica" WHERE "Id" = %s''', (assistance_id,))
    return jsonify(item)


@app.put("/api/assistencias/<int:assistance_id>")
def edit_assistance(assistance_id):
    same_assistance(actor(manager=True), assistance_id)
    data = body()
    with transaction() as connection:
        item = one(connection, '''UPDATE public."AssistenciaTecnica"
            SET "Nome" = %s, "Documento" = %s, "Email" = %s, "Telefone" = %s, "Endereco" = %s
            WHERE "Id" = %s RETURNING *''',
            (text(data, "nome"), text(data, "documento", 30), email(data),
             text(data, "telefone", 30, False), text(data, "endereco", 500, False), assistance_id))
    return jsonify(item)


@app.delete("/api/assistencias/<int:assistance_id>")
def deactivate_assistance(assistance_id):
    same_assistance(actor(manager=True), assistance_id)
    with transaction() as connection:
        item = one(connection, '''UPDATE public."AssistenciaTecnica" SET "Ativo" = FALSE
            WHERE "Id" = %s RETURNING "Id", "Ativo"''', (assistance_id,))
    return jsonify(item)


@app.post("/api/login")
def login():
    data = body()
    return jsonify(auth.login(integer(data, "assistenciaId"), email(data), text(data, "senha", 256)))


@app.post("/api/logout")
def logout():
    auth.logout(token())
    return ("", 204)


@app.get("/api/me")
def me():
    return jsonify(auth.principal(token()))


@app.post("/api/clientes/login")
def client_login():
    data = body()
    return jsonify(auth.login(integer(data, "assistenciaId"), email(data),
                             text(data, "senha", 256), "cliente"))


def account_table(kind):
    if kind == "cliente":
        return 'public."Cliente"', '"IdCliente"'
    if kind == "funcionario":
        return 'public."Funcionario"', '"IdFuncionario"'
    raise RuleError("tipo deve ser cliente ou funcionario", 400)


@app.post("/api/senhas/recuperacao")
def request_password_reset():
    data = body()
    assistance_id = integer(data, "assistenciaId")
    address = email(data)
    kind = text(data, "tipo", 20)
    table, id_column = account_table(kind)
    code = f"{secrets.randbelow(1_000_000):06d}"
    with transaction() as connection:
        account = one(connection, f'''SELECT u."Id" FROM {table} u
            JOIN public."AssistenciaTecnica" a ON a."Id" = u."IdAssistenciaTecnica"
            WHERE u."IdAssistenciaTecnica" = %s AND LOWER(u."Email") = LOWER(%s)
              AND u."Ativo" = TRUE AND a."Ativo" = TRUE''', (assistance_id, address))
        if account:
            recent = one(connection, f'''SELECT r."Id" FROM public."RecuperacaoSenha" r
                WHERE r.{id_column} = %s AND r."IdAssistenciaTecnica" = %s
                  AND r."CriadoEm" > CURRENT_TIMESTAMP - INTERVAL '1 minute'
                LIMIT 1''', (account["Id"], assistance_id))
            if recent:
                raise RuleError("Aguarde um minuto antes de pedir outro código", 429)
            execute(connection, f'''UPDATE public."RecuperacaoSenha" SET "UsadoEm" = CURRENT_TIMESTAMP
                WHERE {id_column} = %s AND "IdAssistenciaTecnica" = %s AND "UsadoEm" IS NULL''',
                (account["Id"], assistance_id))
            send_email("Código para recuperar acesso Ergon", address,
                       "Seu código para definir uma nova senha é: " + code +
                       "\nEle vence em 15 minutos. Se você não solicitou, ignore este email.")
            execute(connection, f'''INSERT INTO public."RecuperacaoSenha"
                ("IdAssistenciaTecnica", {id_column}, "CodigoHash", "ExpiraEm")
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP + INTERVAL '15 minutes')''',
                (assistance_id, account["Id"], auth.secret_hash(code)))
    return jsonify({"mensagem": "Se o email estiver cadastrado, o código será enviado."})


@app.post("/api/senhas/redefinicao")
def reset_password():
    data = body()
    assistance_id = integer(data, "assistenciaId")
    address = email(data)
    kind = text(data, "tipo", 20)
    table, id_column = account_table(kind)
    code = text(data, "codigo", 6)
    if len(code) != 6 or not code.isdigit():
        raise RuleError("Código inválido", 400)
    hashed = auth.password_hash(text(data, "senha", 256))
    with transaction() as connection:
        account = one(connection, f'''SELECT u."Id" FROM {table} u
            WHERE u."IdAssistenciaTecnica" = %s AND LOWER(u."Email") = LOWER(%s)
              AND u."Ativo" = TRUE FOR UPDATE''', (assistance_id, address))
        if not account:
            raise RuleError("Código inválido ou vencido", 400)
        attempt = one(connection, f'''SELECT * FROM public."RecuperacaoSenha"
            WHERE {id_column} = %s AND "IdAssistenciaTecnica" = %s
              AND "UsadoEm" IS NULL AND "ExpiraEm" > CURRENT_TIMESTAMP
            ORDER BY "Id" DESC LIMIT 1 FOR UPDATE''', (account["Id"], assistance_id))
        if not attempt or attempt["Tentativas"] >= 5:
            raise RuleError("Código inválido ou vencido", 400)
        if not hmac.compare_digest(attempt["CodigoHash"], auth.secret_hash(code)):
            execute(connection, '''UPDATE public."RecuperacaoSenha"
                SET "Tentativas" = "Tentativas" + 1 WHERE "Id" = %s''', (attempt["Id"],))
            # Retornar após o commit para preservar a contagem de tentativas.
            invalid = True
        else:
            invalid = False
            execute(connection, f'''UPDATE {table}
                SET "SenhaHash" = %s, "VersaoSessao" = "VersaoSessao" + 1
                WHERE "Id" = %s AND "IdAssistenciaTecnica" = %s''',
                (hashed, account["Id"], assistance_id))
            execute(connection, '''UPDATE public."RecuperacaoSenha"
                SET "UsadoEm" = CURRENT_TIMESTAMP WHERE "Id" = %s''', (attempt["Id"],))
    if invalid:
        raise RuleError("Código inválido ou vencido", 400)
    return jsonify({"mensagem": "Senha definida. Entre com seu email e nova senha."})


@app.get("/api/funcionarios")
def employees():
    user = actor()
    with transaction() as connection:
        rows = all_rows(connection, '''SELECT "Id", "IdAssistenciaTecnica", "Nome", "Documento",
            "Email", "Telefone", "Gerente", "Ativo" FROM public."Funcionario"
            WHERE "IdAssistenciaTecnica" = %s ORDER BY "Nome"''', (user["assistenciaId"],))
    return jsonify(rows)


@app.post("/api/funcionarios")
def create_employee():
    user = actor(manager=True)
    data = body()
    address = email(data)
    raw_token = secrets.token_urlsafe(32)
    with transaction() as connection:
        item = one(connection, '''INSERT INTO public."Funcionario"
            ("IdAssistenciaTecnica", "Email", "Gerente", "Ativo")
            VALUES (%s, %s, FALSE, FALSE)
            RETURNING "Id", "IdAssistenciaTecnica", "Nome", "Documento", "Email", "Telefone", "Gerente", "Ativo"''',
            (user["assistenciaId"], address))
        execute(connection, '''INSERT INTO public."ConviteFuncionario"
            ("IdAssistenciaTecnica", "IdFuncionario", "TokenHash", "ExpiraEm")
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP + INTERVAL '24 hours')''',
            (user["assistenciaId"], item["Id"], auth.secret_hash(raw_token)))
        send_email("Convite para trabalhar no Ergon", address,
                   "O gerente convidou você para acessar a assistência. "
                   "Complete seu cadastro e defina sua senha em até 24 horas:\n" +
                   frontend_link("convite", raw_token))
    return jsonify(item), 201


@app.get("/api/funcionarios/convites/<raw_token>")
def invitation(raw_token):
    with transaction() as connection:
        item = one(connection, '''SELECT f."Email", a."Nome" AS "Assistencia"
            FROM public."ConviteFuncionario" i
            JOIN public."Funcionario" f ON f."Id" = i."IdFuncionario"
            JOIN public."AssistenciaTecnica" a ON a."Id" = i."IdAssistenciaTecnica"
            WHERE i."TokenHash" = %s AND i."UsadoEm" IS NULL
              AND i."ExpiraEm" > CURRENT_TIMESTAMP AND a."Ativo" = TRUE''',
            (auth.secret_hash(raw_token),))
    if not item:
        raise RuleError("Convite inválido ou vencido", 404)
    return jsonify(item)


@app.post("/api/funcionarios/convites/<raw_token>")
def accept_invitation(raw_token):
    data = body()
    hashed = auth.password_hash(text(data, "senha", 256))
    with transaction() as connection:
        invite = one(connection, '''SELECT i."Id", i."IdFuncionario", i."IdAssistenciaTecnica"
            FROM public."ConviteFuncionario" i
            JOIN public."AssistenciaTecnica" a ON a."Id" = i."IdAssistenciaTecnica"
            WHERE i."TokenHash" = %s AND i."UsadoEm" IS NULL
              AND i."ExpiraEm" > CURRENT_TIMESTAMP AND a."Ativo" = TRUE
            FOR UPDATE OF i''', (auth.secret_hash(raw_token),))
        if not invite:
            raise RuleError("Convite inválido ou vencido", 404)
        item = one(connection, '''UPDATE public."Funcionario"
            SET "Nome" = %s, "Documento" = %s, "Telefone" = %s,
                "SenhaHash" = %s, "Ativo" = TRUE
            WHERE "Id" = %s AND "IdAssistenciaTecnica" = %s AND "SenhaHash" IS NULL
            RETURNING "Id", "IdAssistenciaTecnica", "Nome", "Email", "Ativo"''',
            (text(data, "nome"), text(data, "documento", 30),
             text(data, "telefone", 30, False), hashed,
             invite["IdFuncionario"], invite["IdAssistenciaTecnica"]))
        if not item:
            raise RuleError("Este convite já foi usado", 409)
        execute(connection, '''UPDATE public."ConviteFuncionario"
            SET "UsadoEm" = CURRENT_TIMESTAMP WHERE "Id" = %s''', (invite["Id"],))
    return jsonify(item)


def keep_manager(connection, assistance_id, employee_id, new_manager, new_active):
    current = one(connection, '''SELECT "Gerente", "Ativo" FROM public."Funcionario"
        WHERE "Id" = %s AND "IdAssistenciaTecnica" = %s''', (employee_id, assistance_id))
    if not current:
        raise RuleError("Funcionário não encontrado", 404)
    if current["Gerente"] and current["Ativo"] and not (new_manager and new_active):
        count = one(connection, '''SELECT COUNT(*) AS quantidade FROM public."Funcionario"
            WHERE "IdAssistenciaTecnica" = %s AND "Gerente" = TRUE AND "Ativo" = TRUE''',
            (assistance_id,))["quantidade"]
        if count <= 1:
            raise RuleError("A assistência precisa manter um gerente ativo")


@app.put("/api/funcionarios/<int:employee_id>")
def edit_employee(employee_id):
    user = actor(manager=True)
    data = body()
    manager = data.get("gerente") is True
    active = data.get("ativo") is not False
    with transaction() as connection:
        one(connection, '''SELECT "Id" FROM public."AssistenciaTecnica" WHERE "Id" = %s FOR UPDATE''', (user["assistenciaId"],))
        keep_manager(connection, user["assistenciaId"], employee_id, manager, active)
        account = one(connection, '''SELECT "SenhaHash" FROM public."Funcionario"
            WHERE "Id" = %s AND "IdAssistenciaTecnica" = %s''',
            (employee_id, user["assistenciaId"]))
        if active and not account["SenhaHash"]:
            raise RuleError("O funcionário deve concluir o convite antes de ser ativado")
        item = one(connection, '''UPDATE public."Funcionario"
            SET "Nome" = %s, "Documento" = %s, "Email" = %s, "Telefone" = %s, "Gerente" = %s, "Ativo" = %s
            WHERE "Id" = %s AND "IdAssistenciaTecnica" = %s
            RETURNING "Id", "IdAssistenciaTecnica", "Nome", "Documento", "Email", "Telefone", "Gerente", "Ativo"''',
            (text(data, "nome"), text(data, "documento", 30), email(data),
             text(data, "telefone", 30, False), manager, active, employee_id, user["assistenciaId"]))
    return jsonify(item)


@app.delete("/api/funcionarios/<int:employee_id>")
def deactivate_employee(employee_id):
    user = actor(manager=True)
    with transaction() as connection:
        one(connection, '''SELECT "Id" FROM public."AssistenciaTecnica" WHERE "Id" = %s FOR UPDATE''', (user["assistenciaId"],))
        keep_manager(connection, user["assistenciaId"], employee_id, False, False)
        item = one(connection, '''UPDATE public."Funcionario" SET "Ativo" = FALSE
            WHERE "Id" = %s AND "IdAssistenciaTecnica" = %s
            RETURNING "Id", "Ativo"''', (employee_id, user["assistenciaId"]))
    return jsonify(item)


def insert_client(connection, assistance_id, data):
    return one(connection, '''INSERT INTO public."Cliente"
        ("IdAssistenciaTecnica", "Nome", "Documento", "Email", "Telefone", "Endereco")
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING "Id", "IdAssistenciaTecnica", "Nome", "Documento", "Email", "Telefone", "Endereco", "Ativo"''',
        (assistance_id, text(data, "nome"), text(data, "documento", 30, False), email(data),
         text(data, "telefone", 30), text(data, "endereco", 500, False)))


@app.get("/api/clientes")
def clients():
    user = actor()
    with transaction() as connection:
        rows = all_rows(connection, '''SELECT "Id", "IdAssistenciaTecnica", "Nome", "Documento",
            "Email", "Telefone", "Endereco", "Ativo" FROM public."Cliente"
            WHERE "IdAssistenciaTecnica" = %s ORDER BY "Nome"''', (user["assistenciaId"],))
    return jsonify(rows)


@app.post("/api/clientes")
def create_client():
    user = actor()
    with transaction() as connection:
        item = insert_client(connection, user["assistenciaId"], body())
    return jsonify(item), 201


@app.get("/api/clientes/<int:client_id>")
def get_client(client_id):
    user = actor()
    with transaction() as connection:
        item = one(connection, '''SELECT "Id", "IdAssistenciaTecnica", "Nome", "Documento",
            "Email", "Telefone", "Endereco", "Ativo" FROM public."Cliente"
            WHERE "Id" = %s AND "IdAssistenciaTecnica" = %s''', (client_id, user["assistenciaId"]))
    if not item:
        raise RuleError("Cliente não encontrado", 404)
    return jsonify(item)


@app.put("/api/clientes/<int:client_id>")
def edit_client(client_id):
    user = actor()
    data = body()
    with transaction() as connection:
        item = one(connection, '''UPDATE public."Cliente"
            SET "Nome" = %s, "Documento" = %s, "Email" = %s, "Telefone" = %s, "Endereco" = %s
            WHERE "Id" = %s AND "IdAssistenciaTecnica" = %s
            RETURNING "Id", "IdAssistenciaTecnica", "Nome", "Documento",
                "Email", "Telefone", "Endereco", "Ativo"''',
            (text(data, "nome"), text(data, "documento", 30, False), email(data),
             text(data, "telefone", 30), text(data, "endereco", 500, False),
             client_id, user["assistenciaId"]))
    if not item:
        raise RuleError("Cliente não encontrado", 404)
    return jsonify(item)


@app.delete("/api/clientes/<int:client_id>")
def deactivate_client(client_id):
    user = actor()
    with transaction() as connection:
        item = one(connection, '''UPDATE public."Cliente" SET "Ativo" = FALSE
            WHERE "Id" = %s AND "IdAssistenciaTecnica" = %s RETURNING "Id", "Ativo"''',
            (client_id, user["assistenciaId"]))
    if not item:
        raise RuleError("Cliente não encontrado", 404)
    return jsonify(item)


@app.get("/api/clientes/<int:client_id>/aparelhos")
def devices(client_id):
    user = actor()
    with transaction() as connection:
        rows = all_rows(connection, '''SELECT "Id", "IdCliente", "Marca", "Modelo", "TipoAparelho", "Ativo"
            FROM public."Aparelho" WHERE "IdCliente" = %s AND "IdAssistenciaTecnica" = %s
            ORDER BY "Id" DESC''', (client_id, user["assistenciaId"]))
    return jsonify(rows)


@app.post("/api/clientes/<int:client_id>/aparelhos")
def create_device(client_id):
    user = actor()
    data = body()
    with transaction() as connection:
        client = one(connection, '''SELECT "Id" FROM public."Cliente"
            WHERE "Id" = %s AND "IdAssistenciaTecnica" = %s AND "Ativo" = TRUE''',
            (client_id, user["assistenciaId"]))
        if not client:
            raise RuleError("Cliente não encontrado ou inativo", 404)
        item = one(connection, '''INSERT INTO public."Aparelho"
            ("IdAssistenciaTecnica", "IdCliente", "Marca", "Modelo", "TipoAparelho")
            VALUES (%s, %s, %s, %s, %s)
            RETURNING "Id", "IdCliente", "Marca", "Modelo", "TipoAparelho", "Ativo"''',
            (user["assistenciaId"], client_id, text(data, "marca", 100),
             text(data, "modelo", 100), text(data, "tipoAparelho", 100, False)))
    return jsonify(item), 201


@app.put("/api/clientes/<int:client_id>/aparelhos/<int:device_id>")
def edit_device(client_id, device_id):
    user = actor()
    data = body()
    with transaction() as connection:
        item = one(connection, '''UPDATE public."Aparelho"
            SET "Marca" = %s, "Modelo" = %s, "TipoAparelho" = %s
            WHERE "Id" = %s AND "IdCliente" = %s AND "IdAssistenciaTecnica" = %s
            RETURNING "Id", "IdCliente", "Marca", "Modelo", "TipoAparelho", "Ativo"''',
            (text(data, "marca", 100), text(data, "modelo", 100),
             text(data, "tipoAparelho", 100, False), device_id, client_id,
             user["assistenciaId"]))
    if not item:
        raise RuleError("Aparelho não encontrado", 404)
    return jsonify(item)


@app.delete("/api/clientes/<int:client_id>/aparelhos/<int:device_id>")
def deactivate_device(client_id, device_id):
    user = actor()
    with transaction() as connection:
        item = one(connection, '''UPDATE public."Aparelho" SET "Ativo" = FALSE
            WHERE "Id" = %s AND "IdCliente" = %s AND "IdAssistenciaTecnica" = %s
            RETURNING "Id", "Ativo"''', (device_id, client_id, user["assistenciaId"]))
    if not item:
        raise RuleError("Aparelho não encontrado", 404)
    return jsonify(item)


@app.post("/api/assistencias/<int:assistance_id>/solicitacoes")
def online_request(assistance_id):
    data = body()
    def confirmation(address, budget_id):
        send_email("Solicitação de orçamento registrada no Ergon", address,
                   f"Sua solicitação de orçamento #{budget_id} foi registrada.\n"
                   f"Cliente: {text(data, 'nome')}\n"
                   f"Telefone: {text(data, 'telefone', 30)}\n"
                   f"Email: {address}\n"
                   f"Aparelho: {text(data, 'marca', 100)} {text(data, 'modelo', 100)}\n"
                   f"Defeito informado: {text(data, 'defeito', 5000)}\n\n"
                   "Para acessar o sistema, abra Clique aqui, peça um código de "
                   "recuperação de senha e defina sua senha:\n" +
                   frontend_link("recuperar"))
    item = create_online_request(assistance_id, text(data, "nome"), text(data, "telefone", 30),
                                 email(data), text(data, "marca", 100),
                                 text(data, "modelo", 100), text(data, "defeito", 5000),
                                 confirmation)
    return jsonify(item), 201


@app.get("/api/orcamentos")
def budgets():
    user = actor()
    return jsonify(list_budgets(user["assistenciaId"], request.args.get("clienteId", type=int)))


@app.put("/api/orcamentos/<int:budget_id>/resposta")
def respond_budget_route(budget_id):
    user = actor()
    data = body()
    item, raw_token, recipient = respond_budget(
        user["assistenciaId"], budget_id, user["id"],
        text(data, "diagnosticoFuncionario", 5000), money(data, "valorMaoDeObra"),
        money(data, "valorPecas"), day(data, "prazoConclusao"), send_budget_email,
        text(data, "descricaoProblemaCliente", 5000) if data.get("descricaoProblemaCliente") else None)
    return jsonify(item)


@app.post("/api/orcamentos/<int:budget_id>/reenviar")
def resend_budget_route(budget_id):
    user = actor()
    resend_link(user["assistenciaId"], budget_id, send_budget_email)
    return jsonify({"enviado": True})


@app.get("/api/orcamentos/acesso/<raw_token>")
def public_budget_route(raw_token):
    return jsonify(public_budget(raw_token))


@app.post("/api/orcamentos/acesso/<raw_token>/decisao")
def public_decision_route(raw_token):
    data = body()
    approve = data.get("aprovar")
    if not isinstance(approve, bool):
        raise RuleError("aprovar deve ser verdadeiro ou falso", 400)
    item = public_budget(raw_token)
    if item["Origem"] == "LojaImediata":
        raise RuleError("Este orçamento é decidido no atendimento", 403)
    result = decide_budget(item["IdAssistenciaTecnica"], item["Id"], approve,
                           device_received=item["Origem"] == "LojaPosterior",
                           expected_token=raw_token,
                           send=(lambda address, order_id: send_email(
                               "Ordem de serviço criada no Ergon", address,
                               f"O orçamento #{item['Id']} foi aprovado e a OS #{order_id} foi criada. "
                               "Acompanhe o serviço pelo seu link:\n" +
                               frontend_link("orcamento", raw_token))) if approve else None)
    if result.get("expired"):
        return jsonify({"erro": "Prazo encerrado; orçamento cancelado"}), 409
    return jsonify(result)


@app.get("/api/ordens-servico")
def orders():
    user = actor()
    return jsonify(list_orders(user["assistenciaId"], request.args.get("clienteId", type=int)))


@app.get("/api/clientes/<int:client_id>/ordens-servico")
def client_orders(client_id):
    user = actor()
    return jsonify(list_orders(user["assistenciaId"], client_id))


@app.get("/api/clientes/me/orcamentos")
def my_budgets():
    user = client_actor()
    return jsonify(list_budgets(user["assistenciaId"], user["id"]))


@app.get("/api/clientes/me/ordens-servico")
def my_orders():
    user = client_actor()
    return jsonify(list_orders(user["assistenciaId"], user["id"]))


@app.get("/api/clientes/me/aparelhos")
def my_devices():
    user = client_actor()
    with transaction() as connection:
        items = all_rows(connection, '''SELECT "Id", "Marca", "Modelo", "TipoAparelho", "Ativo"
            FROM public."Aparelho" WHERE "IdAssistenciaTecnica" = %s AND "IdCliente" = %s
            ORDER BY "Id" DESC''', (user["assistenciaId"], user["id"]))
    return jsonify(items)


@app.post("/api/clientes/me/solicitacoes")
def my_request():
    user = client_actor()
    data = body()
    problem = text(data, "defeito", 5000)
    with transaction() as connection:
        if data.get("aparelhoId") is not None:
            device_id = integer(data, "aparelhoId")
            device = one(connection, '''SELECT "Id", "Marca", "Modelo" FROM public."Aparelho"
                WHERE "Id" = %s AND "IdCliente" = %s
                  AND "IdAssistenciaTecnica" = %s AND "Ativo" = TRUE''',
                (device_id, user["id"], user["assistenciaId"]))
            if not device:
                raise RuleError("Aparelho não encontrado ou inativo", 404)
        else:
            device = one(connection, '''INSERT INTO public."Aparelho"
                ("IdAssistenciaTecnica", "IdCliente", "Marca", "Modelo")
                VALUES (%s, %s, %s, %s) RETURNING "Id", "Marca", "Modelo"''',
                (user["assistenciaId"], user["id"],
                 text(data, "marca", 100), text(data, "modelo", 100)))
        item = one(connection, '''INSERT INTO public."Orcamento"
            ("IdAssistenciaTecnica", "IdCliente", "IdAparelho", "Origem",
             "DescricaoProblemaCliente")
            VALUES (%s, %s, %s, 'Online', %s) RETURNING "Id", "Status"''',
            (user["assistenciaId"], user["id"], device["Id"], problem))
        send_email("Solicitação de orçamento registrada no Ergon", user["email"],
                   f"Sua solicitação de orçamento #{item['Id']} foi registrada.\n"
                   f"Cliente: {user['nome']}\nEmail: {user['email']}\n"
                   f"Aparelho: {device['Marca']} {device['Modelo']}\n"
                   f"Defeito informado: {problem}\n\n"
                   "Acompanhe seus pedidos no sistema:\n" + frontend_link("entrar"))
    return jsonify(item), 201


@app.put("/api/ordens-servico/<int:order_id>")
def change_order(order_id):
    user = actor()
    data = body()
    action = text(data, "acao", 30)
    responsible = integer(data, "funcionarioResponsavelId") if action == "atribuir" else None
    completion_date = day(data, "dataPrevisaoConclusao") if action == "previsao" else None
    if responsible is not None:
        with transaction() as connection:
            active_employee(connection, user["assistenciaId"], responsible)
    def notify_client(address, status):
        send_email("Atualização da ordem de serviço Ergon", address,
                   f"A OS #{order_id} foi encerrada com status {status}. "
                   "Consulte seus dados no sistema:\n" + frontend_link("entrar"))
    return jsonify(update_order(user["assistenciaId"], order_id, action, responsible,
                                completion_date, notify_client))


@app.post("/api/ordens-servico/<int:order_id>/pagamentos")
def pay_order(order_id):
    user = actor()
    data = body()
    item = register_payment(user["assistenciaId"], order_id, money(data, "valor"),
                            text(data, "formaPagamento", 100),
                            day(data, "dataPagamento") if data.get("dataPagamento") else None)
    return jsonify(item), 201


if __name__ == "__main__":
    app.run(debug=True)
