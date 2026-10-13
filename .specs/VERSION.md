# Versão do Ergon

## Estado atual

Primeira versão implementada em código em 12/10/2026. API Flask, esquema PostgreSQL e interface React estão presentes. Sintaxe Python, importação Flask e build Vite foram verificados. Execução integrada com PostgreSQL, SMTP e Cloudflare permanece pendente das credenciais e do ambiente de implantação.

## Funcionalidades

- Cadastro inicial da assistência com primeiro gerente; consulta, edição e desativação pela equipe autorizada.
- Cadastro, consulta, edição e desativação de funcionários e clientes; aparelhos vinculados aos clientes.
- Solicitação online em formulário único, com cadastro de cliente, aparelho e orçamento na mesma transação.
- Orçamentos presenciais de decisão imediata e posterior, resposta da equipe, link individual por email para decisão do cliente, vencimento de dois dias corridos.
- OS criada somente após aprovação, listada por cliente, com etapas de recebimento, reparo, previsão, conclusão, entrega e pagamento.

## Adições necessárias ao documento de requisitos

- `Funcionario.SenhaHash` e `SessaoAcesso` para login dos funcionários.
- `Orcamento.AcessoTokenHash` para o link único do cliente, sem conta.
- `Cliente.Documento` e `Aparelho.TipoAparelho` opcionais para viabilizar o formulário online de seis campos.
- Desativação lógica dos cadastros com histórico.
- Processamento do vencimento no acesso ao orçamento, sem agendador.

## Limites atuais

- O envio depende de SMTP configurado e pode ser repetido pela equipe se falhar.
- O vencimento é processado na próxima consulta ou tentativa de decisão, sem tarefa em segundo plano.
- Testes de banco, email e implantação dependem de serviços configurados.
