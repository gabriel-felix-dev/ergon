"""End-to-end exercise of the local API against an explicitly configured test DB.

Creates uniquely named records and deactivates the test assistances at the end.
Outgoing mail must be routed to tests/smtp_capture.py.
"""

import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import date, timedelta
from email import policy
from email.parser import Parser
from pathlib import Path
from uuid import uuid4


BASE = os.environ.get("ERGON_TEST_BASE", "http://127.0.0.1:5000/api")
MAIL = Path(__file__).resolve().parents[1] / ".test-mail" / "messages.jsonl"
SUFFIX = uuid4().hex[:10]
PASSWORD = "TesteErgon123!"
TOMORROW = (date.today() + timedelta(days=5)).isoformat()
results = []


def call(method, path, data=None, token=None, expected=200):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = None
    if data is not None:
        payload = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            status = response.status
            raw = response.read()
    except urllib.error.HTTPError as error:
        status = error.code
        raw = error.read()
    try:
        result = json.loads(raw) if raw else None
    except ValueError:
        result = raw.decode("utf-8", "replace")[:300]
    if status != expected:
        raise AssertionError(f"{method} {path}: expected {expected}, got {status}: {str(result)[:300]}")
    return result


def check(name, actual, expected):
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")
    results.append(name)
    print("OK", name, flush=True)


def mail_token(recipient, after=0):
    for _ in range(30):
        if MAIL.exists():
            lines = MAIL.read_text(encoding="utf-8").splitlines()
            for line in reversed(lines[after:]):
                message = json.loads(line)
                if any(recipient in address for address in message["recipients"]):
                    parsed = Parser(policy=policy.default).parsestr(message["data"])
                    body = parsed.get_body(preferencelist=("plain",)).get_content() if parsed.is_multipart() else parsed.get_content()
                    match = re.search(r"\?orcamento=([A-Za-z0-9_-]+)", body)
                    if match:
                        return match.group(1)
        time.sleep(0.1)
    raise AssertionError(f"Email de teste não capturado para {recipient}")


def mail_count():
    return len(MAIL.read_text(encoding="utf-8").splitlines()) if MAIL.exists() else 0


def main():
    check("saúde da API", call("GET", "/saude")["status"], "ok")
    check("lista pública inicial", isinstance(call("GET", "/assistencias"), list), True)
    check("cadastro exige gerente", call("POST", "/assistencias", {}, expected=400)["erro"] != "", True)
    assisted = {}
    try:
        def make_assistance(label):
            email = f"manager-{label}-{SUFFIX}@example.invalid"
            record = call("POST", "/assistencias", {
                "nome": f"Ergon Teste {label} {SUFFIX}", "documento": f"test-{label}-{SUFFIX}",
                "email": f"shop-{label}-{SUFFIX}@example.invalid", "telefone": "11999990000",
                "endereco": "Rua de teste, 1",
                "primeiroGerente": {"nome": f"Gerente {label}", "documento": f"mgr-{label}-{SUFFIX}",
                                    "email": email, "telefone": "11988880000", "senha": PASSWORD},
            }, expected=201)
            assisted[record["assistencia"]["Id"]] = email
            return record["assistencia"]["Id"], email

        shop, manager_email = make_assistance("A")
        other_shop, other_email = make_assistance("B")
        check("assistência e primeiro gerente", len(assisted), 2)
        check("senha incorreta bloqueada", call("POST", "/login", {
            "assistenciaId": shop, "email": manager_email, "senha": "errada"
        }, expected=401)["erro"] != "", True)
        session = call("POST", "/login", {
            "assistenciaId": shop, "email": manager_email, "senha": PASSWORD
        })
        manager = session["token"]
        other = call("POST", "/login", {
            "assistenciaId": other_shop, "email": other_email, "senha": PASSWORD
        })["token"]
        check("login e perfil", call("GET", "/me", token=manager)["gerente"], True)
        check("isolamento entre assistências", call("GET", f"/assistencias/{other_shop}",
            token=manager, expected=403)["erro"] != "", True)
        updated = call("PUT", f"/assistencias/{shop}", {
            "nome": f"Ergon Teste A Editada {SUFFIX}", "documento": f"test-A-{SUFFIX}",
            "email": f"shop-A-{SUFFIX}@example.invalid", "telefone": "11911110000", "endereco": "Rua B",
        }, manager)
        check("editar assistência", updated["Endereco"], "Rua B")

        employee_email = f"employee-{SUFFIX}@example.invalid"
        employee = call("POST", "/funcionarios", {
            "nome": "Funcionário Teste", "documento": f"emp-{SUFFIX}",
            "email": employee_email, "telefone": "11999990001", "senha": PASSWORD, "gerente": False,
        }, manager, 201)
        employee_id = employee["Id"]
        check("cadastrar funcionário", employee["Gerente"], False)
        check("listar funcionários", any(f["Id"] == employee_id for f in call("GET", "/funcionarios", token=manager)), True)
        employee_token = call("POST", "/login", {
            "assistenciaId": shop, "email": employee_email, "senha": PASSWORD,
        })["token"]
        check("funcionário sem permissão gerencial", call("POST", "/funcionarios", {
            "nome": "Proibido"
        }, employee_token, 403)["erro"] != "", True)
        check("proteção do último gerente", call("DELETE", f"/funcionarios/{session['usuario']['id']}",
            token=manager, expected=409)["erro"] != "", True)
        changed = call("PUT", f"/funcionarios/{employee_id}", {
            "nome": "Funcionário Editado", "documento": f"emp-{SUFFIX}",
            "email": employee_email, "telefone": "11999990002", "gerente": False, "ativo": True,
        }, manager)
        check("editar funcionário", changed["Nome"], "Funcionário Editado")

        client_email = f"client-{SUFFIX}@example.invalid"
        client = call("POST", "/clientes", {
            "nome": "Cliente Teste", "documento": f"client-{SUFFIX}",
            "email": client_email, "telefone": "11999990003", "endereco": "Rua C",
        }, employee_token, 201)
        client_id = client["Id"]
        check("cadastrar e ler cliente", call("GET", f"/clientes/{client_id}", token=manager)["Nome"], "Cliente Teste")
        check("cliente de outra assistência oculto", call("GET", f"/clientes/{client_id}",
            token=other, expected=404)["erro"] != "", True)
        edited = call("PUT", f"/clientes/{client_id}", {
            "nome": "Cliente Editado", "documento": f"client-{SUFFIX}",
            "email": client_email, "telefone": "11999990004", "endereco": "Rua D",
        }, manager)
        check("editar cliente", edited["Nome"], "Cliente Editado")
        device = call("POST", f"/clientes/{client_id}/aparelhos", {
            "marca": "Teste", "modelo": "Modelo 1", "tipoAparelho": "Notebook",
        }, manager, 201)
        device_id = device["Id"]
        check("cadastrar e listar aparelho", call("GET", f"/clientes/{client_id}/aparelhos",
            token=manager)[0]["Id"], device_id)

        online_email = f"online-{SUFFIX}@example.invalid"
        online = call("POST", f"/assistencias/{shop}/solicitacoes", {
            "nome": "Cliente Online", "telefone": "11999990005", "email": online_email,
            "marca": "Marca Online", "modelo": "Modelo Online", "defeito": "Não liga",
        }, expected=201)
        online_id = online["Id"]
        budgets = call("GET", "/orcamentos", token=manager)
        check("solicitação cria cliente, aparelho e orçamento", next(b for b in budgets if b["Id"] == online_id)["Origem"], "Online")
        check("cliente online aparece no cadastro", any(c["Email"] == online_email for c in call("GET", "/clientes", token=manager)), True)
        before = mail_count()
        call("PUT", f"/orcamentos/{online_id}/resposta", {
            "diagnosticoFuncionario": "Trocar placa", "valorMaoDeObra": "120.50",
            "valorPecas": "30.00", "prazoConclusao": TOMORROW,
        }, employee_token)
        link = mail_token(online_email, before)
        proposal = call("GET", f"/orcamentos/acesso/{link}")
        check("email e link do orçamento online", proposal["Id"], online_id)
        check("token inválido bloqueado", call("GET", "/orcamentos/acesso/invalido",
            expected=404)["erro"] != "", True)
        check("equipe não decide orçamento online", call("POST", f"/orcamentos/{online_id}/decisao",
            {"aprovar": True}, manager, 403)["erro"] != "", True)
        online_order = call("POST", f"/orcamentos/acesso/{link}/decisao", {"aprovar": True})
        check("aprovação online cria OS aguardando aparelho", online_order["Status"], "AguardandoAparelho")
        check("decisão duplicada bloqueada", call("POST", f"/orcamentos/acesso/{link}/decisao",
            {"aprovar": True}, expected=409)["erro"] != "", True)

        def shop_budget(origin, problem):
            return call("POST", "/orcamentos", {
                "clienteId": client_id, "aparelhoId": device_id, "origem": origin,
                "descricaoProblemaCliente": problem,
            }, manager, 201)["Id"]

        def answer(budget_id):
            return call("PUT", f"/orcamentos/{budget_id}/resposta", {
                "diagnosticoFuncionario": "Diagnóstico de teste", "valorMaoDeObra": "100.00",
                "valorPecas": "25.00", "prazoConclusao": TOMORROW,
            }, employee_token)

        immediate_rejected = shop_budget("LojaImediata", "Problema 1")
        answer(immediate_rejected)
        rejected = call("POST", f"/orcamentos/{immediate_rejected}/decisao", {"aprovar": False}, manager)
        check("orçamento imediato recusado", rejected["Status"], "Recusado")
        immediate_approved = shop_budget("LojaImediata", "Problema 2")
        answer(immediate_approved)
        immediate_order = call("POST", f"/orcamentos/{immediate_approved}/decisao", {"aprovar": True}, manager)
        check("orçamento imediato aprovado", immediate_order["Status"], "AguardandoReparo")

        posterior_rejected = shop_budget("LojaPosterior", "Problema 3")
        before = mail_count()
        answer(posterior_rejected)
        old_link = mail_token(client_email, before)
        before = mail_count()
        call("POST", f"/orcamentos/{posterior_rejected}/reenviar", {}, manager)
        new_link = mail_token(client_email, before)
        check("reenvio troca o link", new_link != old_link, True)
        check("link antigo invalidado", call("GET", f"/orcamentos/acesso/{old_link}",
            expected=404)["erro"] != "", True)
        rejected = call("POST", f"/orcamentos/acesso/{new_link}/decisao", {"aprovar": False})
        check("orçamento posterior recusado", rejected["Status"], "Recusado")
        posterior_approved = shop_budget("LojaPosterior", "Problema 4")
        before = mail_count()
        answer(posterior_approved)
        posterior_link = mail_token(client_email, before)
        posterior_order = call("POST", f"/orcamentos/acesso/{posterior_link}/decisao", {"aprovar": True})
        check("orçamento posterior aprovado", posterior_order["Status"], "AguardandoReparo")

        order_id = online_order["Id"]
        check("transição de OS inválida bloqueada", call("PUT", f"/ordens-servico/{order_id}",
            {"acao": "concluir"}, manager, 409)["erro"] != "", True)
        check("receber aparelho", call("PUT", f"/ordens-servico/{order_id}",
            {"acao": "receber"}, manager)["Status"], "AguardandoReparo")
        check("atribuir responsável", call("PUT", f"/ordens-servico/{order_id}", {
            "acao": "atribuir", "funcionarioResponsavelId": employee_id,
        }, manager)["IdFuncionario"], employee_id)
        check("alterar previsão", str(call("PUT", f"/ordens-servico/{order_id}", {
            "acao": "previsao", "dataPrevisaoConclusao": TOMORROW,
        }, manager)["DataPrevisaoConclusao"]), TOMORROW)
        check("iniciar reparo", call("PUT", f"/ordens-servico/{order_id}",
            {"acao": "iniciar"}, employee_token)["Status"], "EmReparo")
        check("pagamento prematuro bloqueado", call("POST", f"/ordens-servico/{order_id}/pagamentos", {
            "valor": "150.50", "formaPagamento": "Pix",
        }, manager, 409)["erro"] != "", True)
        check("concluir reparo", call("PUT", f"/ordens-servico/{order_id}",
            {"acao": "concluir"}, employee_token)["Status"], "ReparoConcluido")
        check("pagamento inválido bloqueado", call("POST", f"/ordens-servico/{order_id}/pagamentos", {
            "valor": "0", "formaPagamento": "Pix",
        }, manager, 400)["erro"] != "", True)
        paid = call("POST", f"/ordens-servico/{order_id}/pagamentos", {
            "valor": "150.50", "formaPagamento": "Pix",
        }, manager, 201)
        check("pagamento registrado", paid["FormaPagamento"], "Pix")
        check("pagamento duplicado bloqueado", call("POST", f"/ordens-servico/{order_id}/pagamentos", {
            "valor": "150.50", "formaPagamento": "Pix",
        }, manager, 409)["erro"] != "", True)
        delivered = call("PUT", f"/ordens-servico/{order_id}", {"acao": "entregar"}, manager)
        check("entrega registrada", delivered["DataEntregaAparelho"] is not None, True)
        check("OS por cliente", any(o["Id"] == immediate_order["Id"] for o in call("GET",
            f"/clientes/{client_id}/ordens-servico", token=manager)), True)
        check("OS em listagem geral", any(o["Id"] == order_id for o in call("GET",
            "/ordens-servico", token=manager)), True)

        check("desativar cliente", call("DELETE", f"/clientes/{client_id}", token=manager)["Ativo"], False)
        check("cliente inativo não recebe aparelho", call("POST", f"/clientes/{client_id}/aparelhos", {
            "marca": "X", "modelo": "Y"
        }, manager, 404)["erro"] != "", True)
        check("desativar funcionário", call("DELETE", f"/funcionarios/{employee_id}", token=manager)["Ativo"], False)
        check("sessão do funcionário desativado", call("GET", "/me", token=employee_token,
            expected=401)["erro"] != "", True)
        call("POST", "/logout", token=other, expected=204)
        check("logout invalida sessão", call("GET", "/me", token=other,
            expected=401)["erro"] != "", True)
    finally:
        for assistance_id, credentials in assisted.items():
            try:
                token = call("POST", "/login", {
                    "assistenciaId": assistance_id, "email": credentials, "senha": PASSWORD,
                })["token"]
                call("DELETE", f"/assistencias/{assistance_id}", token=token)
                print("Desativada assistência de teste", assistance_id, flush=True)
            except Exception as error:
                print("Falha ao desativar assistência de teste:", assistance_id, error, flush=True)
    check("assistências de teste ocultas", all(a["Id"] not in assisted for a in call("GET", "/assistencias")), True)
    print(json.dumps({"result": "passed", "count": len(results), "checks": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
