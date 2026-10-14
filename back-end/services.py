"""Regras de orçamento, ordem de serviço e pagamento."""

from datetime import date
import hashlib
import secrets

from db import all_rows, execute, one, transaction


class RuleError(Exception):
    def __init__(self, message, status=409):
        super().__init__(message)
        self.status = status


def cancel_expired(connection, assistance_id):
    """Processa vencimentos ao acessar o fluxo, sem depender de agendador."""
    return execute(
        connection,
        '''UPDATE public."Orcamento"
              SET "Status" = 'Cancelado', "Ativo" = FALSE
            WHERE "IdAssistenciaTecnica" = %s
              AND "Status" = 'AguardandoAprovacao'
              AND "PrazoParaAprovacaoCliente" <= CURRENT_TIMESTAMP''',
        (assistance_id,),
    )


def budget(connection, assistance_id, budget_id, lock=False):
    sql = '''SELECT * FROM public."Orcamento"
              WHERE "Id" = %s AND "IdAssistenciaTecnica" = %s'''
    if lock:
        sql += " FOR UPDATE"
    item = one(connection, sql, (budget_id, assistance_id))
    if item is None:
        raise RuleError("Orçamento não encontrado", 404)
    return item


def list_budgets(assistance_id, client_id=None):
    with transaction() as connection:
        cancel_expired(connection, assistance_id)
        sql = '''SELECT o."Id", o."IdAssistenciaTecnica", o."IdCliente", o."IdAparelho",
                        o."IdFuncionario", o."Origem", o."Status", o."DescricaoProblemaCliente",
                        o."DiagnosticoFuncionario", o."ValorMaoDeObra", o."ValorPecas",
                        o."PrazoConclusao", o."CriadoEm", o."RespondidoEm",
                        o."PrazoParaAprovacaoCliente", o."Ativo",
                        a."Marca" AS "MarcaAparelho", a."Modelo" AS "ModeloAparelho",
                        c."Nome" AS "NomeCliente", c."Email" AS "EmailCliente"
                   FROM public."Orcamento" o
                   JOIN public."Aparelho" a ON a."Id" = o."IdAparelho"
                   JOIN public."Cliente" c ON c."Id" = o."IdCliente"
                  WHERE o."IdAssistenciaTecnica" = %s'''
        params = [assistance_id]
        if client_id is not None:
            sql += ' AND o."IdCliente" = %s'
            params.append(client_id)
        sql += ' ORDER BY o."CriadoEm" DESC'
        return all_rows(connection, sql, tuple(params))


def create_budget(assistance_id, client_id, device_id, origin, problem):
    if origin not in ("Online", "LojaImediata", "LojaPosterior"):
        raise RuleError("Origem do orçamento inválida", 400)
    if not problem or not problem.strip():
        raise RuleError("Descrição do problema é obrigatória", 400)
    with transaction() as connection:
        item = one(
            connection,
            '''INSERT INTO public."Orcamento"
                   ("IdAssistenciaTecnica", "IdCliente", "IdAparelho", "Origem",
                    "DescricaoProblemaCliente")
               VALUES (%s, %s, %s, %s, %s)
            RETURNING *''',
            (assistance_id, client_id, device_id, origin, problem.strip()),
        )
        return _safe_budget(item)


def _safe_budget(item):
    return {key: value for key, value in item.items() if key != "AcessoTokenHash"}


def create_online_request(assistance_id, name, phone, email, brand, model, problem, send):
    """Grava os três registros da solicitação pública em uma transação."""
    with transaction() as connection:
        active = one(connection, '''SELECT "Id" FROM public."AssistenciaTecnica"
                              WHERE "Id" = %s AND "Ativo" = TRUE''', (assistance_id,))
        if not active:
            raise RuleError("Assistência não encontrada", 404)
        existing = one(connection, '''SELECT "Id" FROM public."Cliente"
            WHERE "IdAssistenciaTecnica" = %s AND LOWER("Email") = LOWER(%s)''',
            (assistance_id, email))
        if existing:
            raise RuleError(
                "Este email já está cadastrado nesta assistência. "
                "Acesse Clique aqui para recuperar a senha e entrar.", 409)
        client = one(connection, '''INSERT INTO public."Cliente"
                              ("IdAssistenciaTecnica", "Nome", "Telefone", "Email")
                              VALUES (%s, %s, %s, %s) RETURNING "Id"''',
                     (assistance_id, name, phone, email))
        device = one(connection, '''INSERT INTO public."Aparelho"
                              ("IdAssistenciaTecnica", "IdCliente", "Marca", "Modelo")
                              VALUES (%s, %s, %s, %s) RETURNING "Id"''',
                     (assistance_id, client["Id"], brand, model))
        item = one(connection, '''INSERT INTO public."Orcamento"
                            ("IdAssistenciaTecnica", "IdCliente", "IdAparelho", "Origem", "DescricaoProblemaCliente")
                            VALUES (%s, %s, %s, 'Online', %s) RETURNING "Id", "Status"''',
                   (assistance_id, client["Id"], device["Id"], problem))
        send(email, item["Id"])
    return item


def respond_budget(assistance_id, budget_id, employee_id, diagnosis,
                   labor_value, parts_value, completion_date, send, problem=None):
    if not diagnosis or not diagnosis.strip():
        raise RuleError("Diagnóstico é obrigatório", 400)
    if labor_value < 0 or parts_value < 0:
        raise RuleError("Os valores não podem ser negativos", 400)
    with transaction() as connection:
        cancel_expired(connection, assistance_id)
        item = budget(connection, assistance_id, budget_id, lock=True)
        if item["Status"] not in ("EmAnalise", "AguardandoAprovacao"):
            raise RuleError("Somente orçamentos ainda não decididos podem ser corrigidos")
        problem = problem or item["DescricaoProblemaCliente"]
        raw_token = secrets.token_urlsafe(32)
        item = one(
            connection,
            '''UPDATE public."Orcamento"
                  SET "IdFuncionario" = %s,
                      "DiagnosticoFuncionario" = %s,
                      "DescricaoProblemaCliente" = %s,
                      "ValorMaoDeObra" = %s,
                      "ValorPecas" = %s,
                      "PrazoConclusao" = %s,
                      "RespondidoEm" = CURRENT_TIMESTAMP,
                      "PrazoParaAprovacaoCliente" = CURRENT_TIMESTAMP + INTERVAL '2 days',
                      "AcessoTokenHash" = %s,
                      "Status" = 'AguardandoAprovacao'
                WHERE "Id" = %s AND "IdAssistenciaTecnica" = %s
            RETURNING *''',
            (employee_id, diagnosis.strip(), problem, labor_value, parts_value,
             completion_date, hashlib.sha256(raw_token.encode()).hexdigest(), budget_id, assistance_id),
        )
        recipient = one(connection, '''SELECT "Email" FROM public."Cliente" WHERE "Id" = %s''', (item["IdCliente"],))
        send(raw_token, recipient["Email"])
        return _safe_budget(item), raw_token, recipient["Email"]


def public_budget(raw_token):
    digest = hashlib.sha256(raw_token.encode()).hexdigest()
    with transaction() as connection:
        row = one(connection, '''SELECT o."Id", o."IdAssistenciaTecnica" FROM public."Orcamento" o
                                JOIN public."AssistenciaTecnica" a ON a."Id" = o."IdAssistenciaTecnica"
                               WHERE o."AcessoTokenHash" = %s AND a."Ativo" = TRUE''', (digest,))
        if not row:
            raise RuleError("Link inválido", 404)
        cancel_expired(connection, row["IdAssistenciaTecnica"])
        detail = one(connection, '''SELECT o."Id", o."IdAssistenciaTecnica", o."Status", o."Origem", o."DescricaoProblemaCliente",
                                  o."DiagnosticoFuncionario", o."ValorMaoDeObra", o."ValorPecas",
                                  o."PrazoConclusao", o."PrazoParaAprovacaoCliente",
                                  c."Nome" AS "NomeCliente", a."Marca", a."Modelo",
                                  s."Id" AS "IdOrdemServico", s."Status" AS "StatusOS",
                                  s."DataAparelhoRecebido", s."DataPrevisaoConclusao",
                                  s."DataRealConclusao", s."DataEntregaAparelho"
                             FROM public."Orcamento" o
                             JOIN public."Cliente" c ON c."Id" = o."IdCliente"
                             JOIN public."Aparelho" a ON a."Id" = o."IdAparelho"
                        LEFT JOIN public."OrdemServico" s ON s."IdOrcamento" = o."Id"
                            WHERE o."Id" = %s''', (row["Id"],))
        return detail


def resend_link(assistance_id, budget_id, send):
    with transaction() as connection:
        cancel_expired(connection, assistance_id)
        item = budget(connection, assistance_id, budget_id, lock=True)
        if item["Status"] != "AguardandoAprovacao" or item["Origem"] == "LojaImediata":
            raise RuleError("Este orçamento não aguarda decisão por email")
        raw_token = secrets.token_urlsafe(32)
        recipient = one(connection, '''SELECT "Email" FROM public."Cliente" WHERE "Id" = %s''',
                        (item["IdCliente"],))
        send(raw_token, recipient["Email"])
        execute(connection, '''UPDATE public."Orcamento" SET "AcessoTokenHash" = %s WHERE "Id" = %s''',
                (hashlib.sha256(raw_token.encode()).hexdigest(), budget_id))


def decide_budget(assistance_id, budget_id, approve, repair_employee_id=None,
                  device_received=False, expected_token=None, send=None):
    with transaction() as connection:
        item = budget(connection, assistance_id, budget_id, lock=True)
        if expected_token is not None and item["AcessoTokenHash"] != hashlib.sha256(expected_token.encode()).hexdigest():
            raise RuleError("Link inválido", 404)
        if item["Status"] == "AguardandoAprovacao":
            expired = one(
                connection,
                '''SELECT "PrazoParaAprovacaoCliente" <= CURRENT_TIMESTAMP AS expired
                     FROM public."Orcamento" WHERE "Id" = %s''',
                (budget_id,),
            )["expired"]
            if expired:
                execute(
                    connection,
                    '''UPDATE public."Orcamento"
                          SET "Status" = 'Cancelado', "Ativo" = FALSE
                        WHERE "Id" = %s''',
                    (budget_id,),
                )
                return {"expired": True}
        if item["Status"] != "AguardandoAprovacao":
            raise RuleError("Este orçamento já foi decidido ou não foi respondido")
        if not approve:
            return _safe_budget(one(
                connection,
                '''UPDATE public."Orcamento"
                      SET "Status" = 'Recusado', "Ativo" = FALSE
                    WHERE "Id" = %s RETURNING *''',
                (budget_id,),
            ))
        responsible = repair_employee_id or item["IdFuncionario"]
        if responsible is None:
            raise RuleError("Funcionário responsável pelo reparo é obrigatório", 400)
        execute(
            connection,
            '''UPDATE public."Orcamento" SET "Status" = 'Aprovado', "Ativo" = FALSE
                WHERE "Id" = %s''',
            (budget_id,),
        )
        status = "AguardandoReparo" if device_received else "AguardandoAparelho"
        created = one(
            connection,
            '''INSERT INTO public."OrdemServico"
                   ("IdAssistenciaTecnica", "IdOrcamento", "IdFuncionario", "Status",
                    "DataAparelhoRecebido", "DataPrevisaoConclusao")
               VALUES (%s, %s, %s, %s,
                       CASE WHEN %s THEN CURRENT_TIMESTAMP ELSE NULL END, %s)
            RETURNING *''',
            (assistance_id, budget_id, responsible, status,
             device_received, item["PrazoConclusao"]),
        )
        if send:
            recipient = one(connection, '''SELECT "Email" FROM public."Cliente"
                WHERE "Id" = %s AND "IdAssistenciaTecnica" = %s''',
                (item["IdCliente"], assistance_id))
            send(recipient["Email"], created["Id"])
        return created


def list_orders(assistance_id, client_id=None):
    with transaction() as connection:
        sql = '''SELECT os.*, o."IdCliente", o."IdAparelho", o."DescricaoProblemaCliente",
                        o."DiagnosticoFuncionario", o."ValorMaoDeObra", o."ValorPecas",
                        c."Nome" AS "NomeCliente", a."Marca" AS "MarcaAparelho",
                        a."Modelo" AS "ModeloAparelho", p."Id" AS "IdPagamento"
                   FROM public."OrdemServico" os
                   JOIN public."Orcamento" o ON o."Id" = os."IdOrcamento"
                   JOIN public."Cliente" c ON c."Id" = o."IdCliente"
                   JOIN public."Aparelho" a ON a."Id" = o."IdAparelho"
              LEFT JOIN public."Pagamento" p ON p."IdOrdemServico" = os."Id"
                  WHERE os."IdAssistenciaTecnica" = %s'''
        params = [assistance_id]
        if client_id is not None:
            sql += ' AND o."IdCliente" = %s'
            params.append(client_id)
        sql += ' ORDER BY os."Id" DESC'
        return all_rows(connection, sql, tuple(params))


def order(connection, assistance_id, order_id, lock=False):
    sql = '''SELECT * FROM public."OrdemServico"
              WHERE "Id" = %s AND "IdAssistenciaTecnica" = %s'''
    if lock:
        sql += " FOR UPDATE"
    item = one(connection, sql, (order_id, assistance_id))
    if item is None:
        raise RuleError("Ordem de serviço não encontrada", 404)
    return item


def update_order(assistance_id, order_id, action, responsible=None,
                 completion_date=None, send=None):
    with transaction() as connection:
        item = order(connection, assistance_id, order_id, lock=True)
        if action == "receber" and item["Status"] == "AguardandoAparelho":
            sql = '''UPDATE public."OrdemServico"
                        SET "Status" = 'AguardandoReparo',
                            "DataAparelhoRecebido" = CURRENT_TIMESTAMP
                      WHERE "Id" = %s RETURNING *'''
            params = (order_id,)
        elif action == "iniciar" and item["Status"] == "AguardandoReparo":
            sql = '''UPDATE public."OrdemServico" SET "Status" = 'EmReparo'
                      WHERE "Id" = %s RETURNING *'''
            params = (order_id,)
        elif action == "concluir" and item["Status"] == "EmReparo":
            sql = '''UPDATE public."OrdemServico"
                        SET "Status" = 'ReparoConcluido',
                            "DataRealConclusao" = CURRENT_TIMESTAMP
                      WHERE "Id" = %s RETURNING *'''
            params = (order_id,)
        elif action == "entregar" and item["Status"] == "ReparoConcluido" and not item["DataEntregaAparelho"]:
            sql = '''UPDATE public."OrdemServico"
                        SET "DataEntregaAparelho" = CURRENT_TIMESTAMP
                      WHERE "Id" = %s RETURNING *'''
            params = (order_id,)
        elif action == "atribuir" and responsible is not None and item["Status"] not in ("Paga", "Cancelada", "Desistencia"):
            sql = '''UPDATE public."OrdemServico" SET "IdFuncionario" = %s
                      WHERE "Id" = %s RETURNING *'''
            params = (responsible, order_id)
        elif action == "previsao" and completion_date is not None and item["Status"] not in ("Paga", "Cancelada", "Desistencia"):
            sql = '''UPDATE public."OrdemServico" SET "DataPrevisaoConclusao" = %s
                      WHERE "Id" = %s RETURNING *'''
            params = (completion_date, order_id)
        elif action in ("cancelar", "desistencia") and item["Status"] not in ("Paga", "Cancelada", "Desistencia"):
            sql = '''UPDATE public."OrdemServico" SET "Status" = %s
                      WHERE "Id" = %s RETURNING *'''
            params = ("Cancelada" if action == "cancelar" else "Desistencia", order_id)
        else:
            raise RuleError("Transição de ordem de serviço inválida")
        updated = one(connection, sql, params)
        if action in ("cancelar", "desistencia") and send:
            recipient = one(connection, '''SELECT c."Email" FROM public."OrdemServico" os
                JOIN public."Orcamento" o ON o."Id" = os."IdOrcamento"
                JOIN public."Cliente" c ON c."Id" = o."IdCliente"
                WHERE os."Id" = %s AND os."IdAssistenciaTecnica" = %s''',
                (order_id, assistance_id))
            send(recipient["Email"], updated["Status"])
        return updated


def register_payment(assistance_id, order_id, value, payment_method, payment_date=None):
    if value <= 0 or not payment_method or not payment_method.strip():
        raise RuleError("Valor e forma de pagamento válidos são obrigatórios", 400)
    with transaction() as connection:
        item = order(connection, assistance_id, order_id, lock=True)
        if item["Status"] == "Paga":
            raise RuleError("A ordem de serviço já foi paga")
        if item["Status"] != "ReparoConcluido":
            raise RuleError("Conclua o reparo antes de registrar o pagamento")
        existing = one(
            connection,
            '''SELECT "Id" FROM public."Pagamento" WHERE "IdOrdemServico" = %s''',
            (order_id,),
        )
        if existing:
            raise RuleError("A ordem de serviço já tem pagamento")
        if payment_date is not None and payment_date > date.today():
            raise RuleError("A data do pagamento não pode ser futura", 400)
        payment = one(
            connection,
            '''INSERT INTO public."Pagamento"
                   ("IdOrdemServico", "Valor", "FormaPagamento", "Data")
               VALUES (%s, %s, %s, COALESCE(%s, CURRENT_TIMESTAMP)) RETURNING *''',
            (order_id, value, payment_method.strip(), payment_date),
        )
        execute(
            connection,
            '''UPDATE public."OrdemServico" SET "Status" = 'Paga' WHERE "Id" = %s''',
            (order_id,),
        )
        return payment
