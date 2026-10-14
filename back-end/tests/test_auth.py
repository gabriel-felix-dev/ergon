"""Testes da autenticação que não exigem PostgreSQL nem SMTP."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from unittest import TestCase
from unittest.mock import patch
import os

import jwt

import auth
from app import actor, app
from services import RuleError


@contextmanager
def fake_transaction():
    yield object()


class AuthenticationTests(TestCase):
    def setUp(self):
        self.secret = "segredo-de-teste-com-mais-de-trinta-e-dois-caracteres"
        self.environment = patch.dict(os.environ, {"JWT_SECRET": self.secret})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_password_is_salted_and_verified(self):
        first = auth.password_hash("SenhaErgon123!")
        second = auth.password_hash("SenhaErgon123!")
        self.assertNotEqual(first, second)
        self.assertNotIn("SenhaErgon123!", first)
        self.assertTrue(auth.verify_password("SenhaErgon123!", first))
        self.assertFalse(auth.verify_password("SenhaErrada123!", first))

    def test_staff_token_requires_active_matching_session_version(self):
        account = {
            "Id": 7, "Nome": "Gerente", "Email": "gerente@teste.com",
            "SenhaHash": auth.password_hash("SenhaErgon123!"), "Ativo": True,
            "VersaoSessao": 2, "AssistenciaAtiva": True, "Gerente": True,
        }
        with patch.object(auth, "transaction", fake_transaction), patch.object(auth, "one", return_value=account):
            result = auth.login(3, account["Email"], "SenhaErgon123!")
            claims = jwt.decode(result["token"], self.secret, algorithms=["HS256"])
            self.assertEqual((claims["kind"], claims["assistanceId"], claims["version"]), ("funcionario", 3, 2))
            self.assertTrue(auth.principal(result["token"])["gerente"])
            account["VersaoSessao"] = 3
            with self.assertRaises(RuleError):
                auth.principal(result["token"])

    def test_client_cannot_use_staff_route(self):
        account = {
            "Id": 9, "Nome": "Cliente", "Email": "cliente@teste.com",
            "Ativo": True, "VersaoSessao": 0, "AssistenciaAtiva": True,
        }
        now = datetime.now(timezone.utc)
        token = jwt.encode({
            "sub": "9", "kind": "cliente", "assistanceId": 3,
            "version": 0, "iat": now, "exp": now + timedelta(hours=1),
        }, self.secret, algorithm="HS256")
        with patch.object(auth, "transaction", fake_transaction), patch.object(auth, "one", return_value=account):
            with app.test_request_context(headers={"Authorization": "Bearer " + token}):
                with self.assertRaises(RuleError) as blocked:
                    actor()
        self.assertEqual(blocked.exception.status, 403)

    def test_expired_token_is_rejected_before_database_access(self):
        old = datetime.now(timezone.utc) - timedelta(hours=2)
        token = jwt.encode({
            "sub": "7", "kind": "funcionario", "assistanceId": 3,
            "version": 0, "iat": old, "exp": old + timedelta(hours=1),
        }, self.secret, algorithm="HS256")
        with patch.object(auth, "transaction") as database:
            with self.assertRaises(RuleError) as blocked:
                auth.principal(token)
            database.assert_not_called()
        self.assertEqual(blocked.exception.status, 401)
