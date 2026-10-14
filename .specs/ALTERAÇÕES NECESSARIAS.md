# Alterações necessárias para a demonstração local do Ergon

Atualizado em 14/10/2026. Este é o registro canônico das mudanças identificadas na revisão da documentação e do código. Cada item distingue implementação de validação. O histórico de entregas permanece em `VERSION.md`.

## Decisões confirmadas pelo responsável

- O objetivo atual é uma **demonstração acadêmica local**. Publicação em Cloudflare não é requisito para essa demonstração.
- O frontend usa React, o backend usa Flask e o banco é PostgreSQL. Os slides definem os conceitos didáticos e o nível de simplicidade do código; não são uma lista fechada de bibliotecas. A troca do MySQL ensinado por PostgreSQL está autorizada.
- O PostgreSQL foi mantido em 14/10/2026 após considerar SQL Server/Azure SQL. A familiaridade prévia com a sintaxe SQL será usada no estudo; não há migração de banco planejada para esta demonstração.
- React e Flask trocam solicitações e respostas JSON por HTTP; o backend acessa o PostgreSQL com SQL. Para leitura, o método HTTP é `GET`; para atualização, o código usa `PUT`. `READ` é a operação do CRUD, não um método HTTP.
- A demonstração deve incluir **sessões com JWT** e **recuperação de senha por email**, além do email com o link de orçamento. O responsável quer que senhas e outros dados sensíveis sejam protegidos por hash no banco. Senhas e tokens usados apenas para verificação podem ser armazenados como hash; ainda é necessário identificar quais outros campos sensíveis precisam ser lidos pelo sistema, pois hash não permite recuperar o valor original.
- O código deve continuar simples de estudar e explicar na apresentação.
- Somente o cliente inicia o orçamento na demonstração local. A equipe responde; aprovação do cliente cria a OS automaticamente. Abertura de orçamento ou OS pela equipe permanece para outra versão.

## Mudanças de implementação confirmadas

### ALT-01 — Adequar a autenticação a JWT

- **Evidência:** `back-end/auth.py` gera um token aleatório, armazena seu SHA-256 em `SessaoAcesso` e consulta essa tabela a cada requisição. Isso é uma sessão com token opaco, não JWT. `front-end/src/App.jsx` guarda e envia esse token.
- **Mudança:** definir um contrato JWT simples para login, autenticação e expiração, então adequar API, frontend e testes. Preservar as proteções já existentes contra acesso de funcionário ou assistência desativados e explicitar o comportamento do logout.
- **Aceite:** o login emite um JWT verificável; acesso sem token, token alterado ou expirado é recusado; permissões e isolamento entre assistências continuam funcionando; o comportamento de logout está definido e testado.
- **Estado:** implementado em código com JWT HS256 de 12 horas, verificação da conta a cada requisição e `VersaoSessao` para invalidar tokens ao sair ou trocar senha. Compilação Python passou; testes de integração com PostgreSQL ainda pendentes.

### ALT-02 — Implementar recuperação de senha por email

- **Evidência:** `back-end/app.py` e `front-end/src/App.jsx` só oferecem cadastro e login. O Flask-Mail em `back-end/app.py` envia atualmente o link de orçamento, não um link de redefinição de senha.
- **Mudança:** adicionar solicitação de recuperação, envio de código por email e redefinição da senha de funcionário ou cliente; código de 15 minutos e uso único.
- **Aceite:** em uma demonstração local com SMTP de teste, o titular solicita a recuperação, recebe o código, define nova senha, entra com ela e não consegue reutilizar o código.
- **Estado:** implementado em código para funcionário e cliente com código de seis dígitos por SMTP, validade de 15 minutos, cinco tentativas e uso único. Interface criada. Entrega SMTP real e teste integrado ainda pendentes.

### ALT-03 — Tratar falha no envio do orçamento

- **Evidência:** `back-end/services.py::respond_budget` grava `AguardandoAprovacao` e o hash do link; só depois `back-end/app.py::respond_budget_route` tenta enviar o email. Se o envio falha, a API retorna erro após a mudança de estado. `RESUMO_DO_PROJETO.md` registra o problema.
- **Mudança:** definir e implementar um resultado coerente para falha de SMTP, com mensagem clara à equipe e recuperação simples do envio. Não presumir rollback de uma transação já confirmada.
- **Aceite:** uma falha simulada de SMTP deixa o orçamento em estado conhecido e a interface informa qual ação permite que o cliente receba um link válido; reenvio não cria OS nem duplica decisão.
- **Estado:** envio agora ocorre dentro da transação de resposta, antes do commit; falha SMTP devolve erro e desfaz a resposta. Teste de falha com PostgreSQL e SMTP ainda pendente.

## Documentação a ajustar

### ALT-04 — Corrigir o contrato didático em `prompt.md` e nas regras tecnológicas

- **Evidência inicial:** `.specs/prompt.md` afirmava que somente bibliotecas e técnicas presentes nos PDFs podiam ser usadas, contrariando a decisão atual sobre PostgreSQL e bibliotecas equivalentes. O arquivo também citava nomes de pastas inexistentes e escrevia `Postgress`. `.specs/regra-tecnologias/regras-de-tecnoligias.md` não explicava a distinção JSON/SQL nem quais métodos HTTP a aplicação usa.
- **Mudança:** substituir a proibição literal por critérios verificáveis: conceitos dos slides, stack aprovada, código simples e justificativa para qualquer técnica nova; corrigir caminhos e terminologia; explicitar JSON entre interface e API, SQL entre API e banco, e `GET`, `POST`, `PUT` e `DELETE` como métodos usados pelo projeto.
- **Aceite:** um leitor consegue avaliar se uma proposta cabe na atividade sem concluir erroneamente que PostgreSQL ou o driver correspondente estão proibidos.
- **Estado:** concluído na documentação em 14/10/2026, com revisão de `.specs/prompt.md` e `.specs/regra-tecnologias/regras-de-tecnoligias.md`. Não representa validação do código.

### ALT-05 — Separar o escopo da versão demonstrável da visão completa

- **Evidência inicial:** `.specs/IDEIA.md` excluía estoque, fornecedores, receitas, despesas e relatórios da primeira versão, mas `.specs/regra-requisitos-classes/regra-requisitos-e-diagrama-de-classes-ergon.md` ainda descrevia esses módulos sem um recorte explícito. A recuperação de senha havia sido confirmada, mas não constava do escopo da versão.
- **Mudança:** manter o documento amplo como visão do produto e identificar, nele ou por ponteiro claro, quais histórias e regras são da demonstração local e quais ficam para depois; atualizar o escopo da versão com recuperação de senha e JWT.
- **Aceite:** não há dúvida sobre o que precisa funcionar na apresentação, sem apagar o levantamento completo já feito.
- **Estado:** documentação atualizada em 14/10/2026 com recorte online e `US12` a `US18`. Código JWT e recuperação escrito, aguardando teste integrado.

### ALT-06 — Consolidar o estado de validação em uma fonte

- **Evidência:** `.specs/VERSION.md` ainda descreve o estado de 12/10/2026 e diz que a integração com PostgreSQL está pendente; `RESUMO_DO_PROJETO.md` relata testes parciais posteriores com o Supabase e lista exatamente onde a execução parou. `.specs/IDEIA.md` agora aponta para esse resumo, mas a fonte canônica dos resultados de validação ainda não foi escolhida.
- **Mudança:** escolher um único local para o estado atual e resultados dos testes; deixar os demais documentos como histórico ou ponteiros. Registrar separadamente o que foi implementado, o que passou e o que ainda não foi executado.
- **Aceite:** não existem duas afirmações incompatíveis sobre o que já foi validado.
- **Estado:** pendente; a fonte canônica de estado precisa ser escolhida antes de reescrever os documentos.

## Verificações e decisões técnicas pendentes

### ALT-07 — Concluir a jornada crítica em ambiente local

- **Evidência:** `back-end/tests/system_smoke.py` cobre grande parte do fluxo, mas `RESUMO_DO_PROJETO.md` informa que a execução integral parou na resposta do primeiro orçamento por falta de configuração SMTP. Não há teste automatizado de navegador no repositório.
- **Mudança:** executar o fluxo com banco de teste e capturador SMTP local: solicitação, resposta, email, aprovação ou recusa por link, criação única da OS, reparo, entrega e pagamento; incluir recuperação de senha e casos de falha relevantes. Para a interface web, adicionar ao menos uma jornada de navegador executável quando a implementação estiver pronta.
- **Aceite:** resultados reproduzíveis registrados para API e navegador, com limpeza dos dados de teste.
- **Estado:** pendente; compilação Python e build React passaram. O `system_smoke.py` existente usa contratos da versão anterior e precisa ser atualizado antes de executar em banco de teste. Não executar em dados de produção.

### ALT-08 — Conferir a separação MVC sem refatoração desnecessária

- **Evidência:** `.specs/regra-tecnologias/regras-de-tecnoligias.md` pede que acesso a dados e lógica de domínio não se concentrem nas rotas; `back-end/app.py` contém SQL diretamente em várias rotas de cadastro, enquanto `back-end/services.py` concentra o fluxo de orçamento e OS.
- **Mudança:** avaliar se a apresentação consegue explicar essa divisão como está. Extrair somente trechos que atrapalhem o entendimento ou violem uma regra importante, preservando a simplicidade.
- **Aceite:** responsabilidades de React, rotas Flask, serviços e acesso SQL são explicáveis com exemplos concretos.
- **Estado:** análise pendente; não há autorização para uma refatoração ampla implícita.

### ALT-09 — Resolver a regra de fuso horário da assistência

- **Evidência:** o requisito `RNF11` em `.specs/regra-requisitos-classes/regra-requisitos-e-diagrama-de-classes-ergon.md` fala em fuso configurado por assistência, mas `data-base/script/script-ergon.sql` não possui configuração de fuso na tabela `AssistenciaTecnica`. Os dois dias do orçamento são calculados em `back-end/services.py` com timestamp do banco.
- **Mudança:** decidir se a demonstração usa um fuso único explicitamente documentado ou se o fuso por assistência realmente integra a primeira versão; só então alinhar requisito, interface e dados.
- **Aceite:** o prazo de aprovação e a apresentação de datas seguem uma regra única e testável.
- **Estado:** recorte local definido em 14/10/2026: prazo de 48 horas calculado pelo PostgreSQL com `TIMESTAMPTZ`, interface no fuso do navegador; fuso por assistência futuro. Falta testar mudança de fuso na integração.

### ALT-10 — Ajustar instruções de execução à demonstração

- **Evidência:** `README.md` mistura a execução local com detalhes de publicação em Cloudflare. `.specs/regra-tecnologias/regras-de-tecnoligias.md` apresenta Cloudflare como plataforma indicada, embora a meta atual seja uma demonstração local.
- **Mudança:** destacar o caminho mínimo reproduzível para React, Flask, PostgreSQL e SMTP de teste; manter a implantação como possibilidade futura, identificada como fora do critério de conclusão atual.
- **Aceite:** outra pessoa consegue preparar e apresentar a jornada crítica localmente seguindo o README sem precisar publicar serviços.
- **Estado:** README revisado em 14/10/2026 para execução local e migração. Reprodução por outra pessoa ainda pendente.

### ALT-11 — Tornar condicionais os padrões de objetos SQL

- **Evidência:** `.specs/regras-banco-de-dados/regras-estruturas-banco-de-dados.md` detalha padrões para procedures, functions, triggers e views, mas a primeira versão usa tabelas e SQL chamado pelo Flask. A existência das pastas não obriga a criar objetos de cada tipo.
- **Mudança:** explicitar que os modelos de arquivo, nome e documentação valem **quando** um objeto SQL desse tipo for necessário e aprovado para uma regra concreta; não transformar o modelo em meta de implementação da demonstração.
- **Aceite:** uma tarefa de banco pode seguir o padrão pertinente sem acrescentar procedure, trigger ou view apenas para preencher a estrutura de pastas.
- **Estado:** concluído na documentação em 14/10/2026, com a ressalva incluída em `.specs/regras-banco-de-dados/regras-estruturas-banco-de-dados.md`.

### ALT-12 — Distinguir metas acadêmicas de metas futuras de operação

- **Evidência:** o levantamento de requisitos marca desempenho, disponibilidade e backup (`RNF07` a `RNF09`) como metas propostas a confirmar antes da implantação. A demonstração local não prevê ambiente de produção para comprová-las.
- **Mudança:** manter essas metas como propostas para uma etapa futura e definir para a apresentação apenas critérios observáveis da jornada local, sem declarar atendimento a metas ainda não medidas.
- **Aceite:** a documentação não apresenta disponibilidade, carga ou backup como funcionalidades comprovadas pela demonstração.
- **Estado:** concluído na documentação em 14/10/2026: o levantamento separa `RNF07` a `RNF09` dos critérios da demonstração local. As metas continuam propostas para uma etapa futura.

### ALT-13 — Classificar os demais dados sensíveis antes de definir o armazenamento

- **Evidência:** o responsável confirmou a exigência de proteger senhas e outros dados sensíveis no banco por hash. O sistema precisa recuperar alguns dados, como o email do cliente para enviar o orçamento e o email do funcionário para recuperar a senha; um hash isolado não permite esse uso.
- **Mudança:** listar os campos considerados sensíveis além de senhas e tokens. Para cada campo, decidir se o sistema só precisa verificar igualdade ou se precisa ler o valor. Usar hash para os valores de verificação; definir outra proteção apropriada para valores recuperáveis, sem prometer que um hash possa ser revertido.
- **Aceite:** cada campo sensível da demonstração tem finalidade e forma de proteção explícitas, compatíveis com os fluxos de email e consulta.
- **Estado:** senhas, tokens de convite e códigos de recuperação implementados como hash; emails legíveis para login e SMTP. Demais campos sensíveis ainda precisam ser classificados com o responsável.

### ALT-14 — Completar e validar o fluxo exclusivo do cliente

- **Evidência:** a decisão final do escopo em 14/10/2026 retirou a abertura de orçamento e OS pela equipe da demonstração. O frontend anterior ainda exibia orçamento na loja.
- **Mudança:** manter a solicitação pública e a solicitação do cliente autenticado; esconder o atendimento na loja no painel; criar OS somente após aprovação pelo link; permitir cancelamento/desistência e pagamento manual.
- **Aceite:** jornada completa no navegador e na API com banco de teste e email capturado, sem criação manual de OS.
- **Estado:** código e interface alterados; build React passou. Jornada integrada ainda pendente.

### ALT-15 — Preparar banco de teste e SMTP para a apresentação

- **Evidência:** este computador não possui `DATABASE_URL`, `MAIL_SERVER`, serviço PostgreSQL local, Docker ou WSL configurados.
- **Mudança:** disponibilizar um banco descartável, executar o esquema ou a migração em cópia, configurar SMTP e testar entrega aos emails que serão usados na apresentação.
- **Aceite:** smoke completo e roteiro visual executam sem edição de código nem uso do banco de produção.
- **Estado:** capturador SMTP local recebeu uma mensagem de teste em 14/10/2026. PostgreSQL e conta SMTP real ainda não estão configurados; entrega externa não foi comprovada.

### ALT-16 — Inicializar Flask-Mail antes de construir a mensagem

- **Evidência:** o teste SMTP isolado falhou com `KeyError: 'mail'` porque `Message` foi construído antes de `Mail(app)`.
- **Mudança:** inicializar a extensão após configurar o SMTP e só então construir e enviar `Message`.
- **Aceite:** mensagem recebida pelo capturador SMTP local.
- **Estado:** corrigido e verificado em 14/10/2026 com mensagem capturada em `back-end/.test-mail/messages.jsonl`.

## Como manter esta lista

Adicionar novas descobertas com evidência, mudança proposta, critério de aceite e estado. Distinguir requisito confirmado, defeito observado e decisão em aberto. Não marcar um item como concluído somente porque o código foi escrito: registrar a verificação que demonstrou o comportamento.
