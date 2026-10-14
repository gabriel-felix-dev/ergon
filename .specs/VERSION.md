# Versão do Ergon

## Estado atual

Em 14/10/2026, a branch `prototipo-local` contém a implementação do recorte de demonstração local: solicitação iniciada pelo cliente, resposta da equipe, decisão por link, OS automática e registro manual do pagamento. A sintaxe Python, importação Flask, rota de saúde, quatro testes de autenticação, validação sintática do esquema SQL, build Vite e envio para capturador SMTP local passaram nesta sessão. **Ainda não foi executada a jornada integrada com PostgreSQL**, pois este computador não tem banco configurado. Entrega por conta SMTP real também não foi testada. Publicação em Cloudflare está fora do critério desta versão.

## Funcionalidades

- Cadastro inicial da assistência com primeiro gerente; consulta, edição e desativação pela equipe autorizada.
- Convite de funcionário por email; ele completa cadastro e cria a senha. CRUD lógico de funcionário, cliente e aparelho.
- Login JWT de equipe e cliente; recuperação de senha por código enviado por email.
- Solicitação online em formulário único, com cadastro de cliente, aparelho e orçamento na mesma transação.
- Resposta da equipe, correção antes da decisão, link individual por email e vencimento após 48 horas.
- OS criada somente após aprovação, listada pelo cliente, com etapas de recebimento, reparo, previsão, conclusão, entrega, cancelamento/desistência e pagamento manual.

## Modelo de dados do recorte local

- `Funcionario.SenhaHash`, `Cliente.SenhaHash` e `VersaoSessao` para contas com JWT.
- `ConviteFuncionario` e `RecuperacaoSenha` para links e códigos de uso único.
- `Orcamento.AcessoTokenHash` para o link único do cliente.
- `Cliente.Documento` e `Aparelho.TipoAparelho` opcionais para viabilizar o formulário online de seis campos.
- Desativação lógica dos cadastros com histórico.
- Processamento do vencimento no acesso ao orçamento, sem agendador.

## Limites atuais

- O envio depende de SMTP configurado. A confirmação da solicitação, a resposta do orçamento e a criação da OS são enviadas na mesma transação do respectivo registro.
- O vencimento é processado na próxima consulta ou tentativa de decisão, sem tarefa em segundo plano.
- O smoke antigo em `back-end/tests/system_smoke.py` precisa ser adaptado ao contrato de convite e login do cliente antes de ser executado com banco de teste.
- `RESUMO_DO_PROJETO.md` descreve uma execução anterior e serve como histórico, não como estado atual de validação.
