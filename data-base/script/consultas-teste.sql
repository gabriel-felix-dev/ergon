-- Consultas de leitura para o Query Tool do pgAdmin.
-- Execute um bloco por vez. Em um banco recém-criado, as contagens serão zero
-- até cadastrar uma assistência e registrar dados pelo aplicativo.

-- 1. Confirma banco, usuário e existência da tabela principal.
SELECT current_database() AS banco,
       current_user AS usuario,
       to_regclass('public."AssistenciaTecnica"') AS tabela_assistencia;

-- 2. Quantidade de registros nas tabelas principais.
SELECT 'Assistencias' AS tabela, COUNT(*) AS total FROM public."AssistenciaTecnica"
UNION ALL SELECT 'Funcionarios', COUNT(*) FROM public."Funcionario"
UNION ALL SELECT 'Clientes', COUNT(*) FROM public."Cliente"
UNION ALL SELECT 'Aparelhos', COUNT(*) FROM public."Aparelho"
UNION ALL SELECT 'Orcamentos', COUNT(*) FROM public."Orcamento"
UNION ALL SELECT 'Ordens de servico', COUNT(*) FROM public."OrdemServico"
UNION ALL SELECT 'Pagamentos', COUNT(*) FROM public."Pagamento"
ORDER BY tabela;

-- 3. Assistências cadastradas e seus funcionários, sem exibir hashes de senha.
SELECT a."Id" AS assistencia_id,
       a."Nome" AS assistencia,
       a."Ativo" AS assistencia_ativa,
       f."Id" AS funcionario_id,
       f."Nome" AS funcionario,
       f."Email" AS email_funcionario,
       f."Gerente",
       f."Ativo" AS funcionario_ativo
FROM public."AssistenciaTecnica" AS a
LEFT JOIN public."Funcionario" AS f
       ON f."IdAssistenciaTecnica" = a."Id"
ORDER BY a."Nome", f."Nome";

-- 4. Clientes e aparelhos vinculados a cada assistência.
SELECT a."Nome" AS assistencia,
       c."Id" AS cliente_id,
       c."Nome" AS cliente,
       c."Email" AS email_cliente,
       c."Ativo" AS cliente_ativo,
       ap."Id" AS aparelho_id,
       ap."Marca",
       ap."Modelo",
       ap."Ativo" AS aparelho_ativo
FROM public."Cliente" AS c
JOIN public."AssistenciaTecnica" AS a
  ON a."Id" = c."IdAssistenciaTecnica"
LEFT JOIN public."Aparelho" AS ap
  ON ap."IdCliente" = c."Id"
 AND ap."IdAssistenciaTecnica" = c."IdAssistenciaTecnica"
ORDER BY a."Nome", c."Nome", ap."Id";

-- 5. Orçamentos recentes com cliente, aparelho, status e valor proposto.
SELECT o."Id" AS orcamento_id,
       a."Nome" AS assistencia,
       c."Nome" AS cliente,
       ap."Marca",
       ap."Modelo",
       o."Origem",
       o."Status",
       o."CriadoEm",
       o."PrazoParaAprovacaoCliente",
       COALESCE(o."ValorMaoDeObra", 0) + COALESCE(o."ValorPecas", 0) AS valor_total
FROM public."Orcamento" AS o
JOIN public."AssistenciaTecnica" AS a
  ON a."Id" = o."IdAssistenciaTecnica"
JOIN public."Cliente" AS c
  ON c."Id" = o."IdCliente"
 AND c."IdAssistenciaTecnica" = o."IdAssistenciaTecnica"
JOIN public."Aparelho" AS ap
  ON ap."Id" = o."IdAparelho"
 AND ap."IdCliente" = o."IdCliente"
 AND ap."IdAssistenciaTecnica" = o."IdAssistenciaTecnica"
ORDER BY o."CriadoEm" DESC
LIMIT 50;

-- 6. Ordens de serviço e pagamentos; pagamento fica vazio até ser registrado.
SELECT os."Id" AS ordem_id,
       os."IdOrcamento" AS orcamento_id,
       c."Nome" AS cliente,
       os."Status" AS status_ordem,
       os."DataAparelhoRecebido",
       os."DataRealConclusao",
       os."DataEntregaAparelho",
       p."Valor" AS valor_pago,
       p."FormaPagamento",
       p."Data" AS data_pagamento
FROM public."OrdemServico" AS os
JOIN public."Orcamento" AS o
  ON o."Id" = os."IdOrcamento"
 AND o."IdAssistenciaTecnica" = os."IdAssistenciaTecnica"
JOIN public."Cliente" AS c
  ON c."Id" = o."IdCliente"
 AND c."IdAssistenciaTecnica" = o."IdAssistenciaTecnica"
LEFT JOIN public."Pagamento" AS p
  ON p."IdOrdemServico" = os."Id"
ORDER BY os."Id" DESC;
