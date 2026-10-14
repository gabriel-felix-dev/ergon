# Alterações necessárias para a demonstração local do Ergon

Atualizado em 14/10/2026. Este é o registro canônico das mudanças **pendentes** identificadas na revisão da documentação e do código. Nenhum item abaixo significa que a mudança já foi implementada. O histórico de entregas permanece em `VERSION.md`; ao concluir um item, registrar lá o resultado e a verificação realizada.

## Decisões confirmadas pelo responsável

- O objetivo atual é uma **demonstração acadêmica local**. Publicação em Cloudflare não é requisito para essa demonstração.
- O frontend usa React, o backend usa Flask e o banco é PostgreSQL. Os slides definem os conceitos didáticos e o nível de simplicidade do código; não são uma lista fechada de bibliotecas. A troca do MySQL ensinado por PostgreSQL está autorizada.
- O PostgreSQL foi mantido em 14/10/2026 após considerar SQL Server/Azure SQL. A familiaridade prévia com a sintaxe SQL será usada no estudo; não há migração de banco planejada para esta demonstração.
- React e Flask trocam solicitações e respostas JSON por HTTP; o backend acessa o PostgreSQL com SQL. Para leitura, o método HTTP é `GET`; para atualização, o código usa `PUT`. `READ` é a operação do CRUD, não um método HTTP.
- A demonstração deve incluir **sessões com JWT** e **recuperação de senha por email**, além do email com o link de orçamento. O responsável quer que senhas e outros dados sensíveis sejam protegidos por hash no banco. Senhas e tokens usados apenas para verificação podem ser armazenados como hash; ainda é necessário identificar quais outros campos sensíveis precisam ser lidos pelo sistema, pois hash não permite recuperar o valor original.
- O código deve continuar simples de estudar e explicar na apresentação.

## Mudanças de implementação confirmadas

### ALT-01 — Adequar a autenticação a JWT

- **Evidência:** `back-end/auth.py` gera um token aleatório, armazena seu SHA-256 em `SessaoAcesso` e consulta essa tabela a cada requisição. Isso é uma sessão com token opaco, não JWT. `front-end/src/App.jsx` guarda e envia esse token.
- **Mudança:** definir um contrato JWT simples para login, autenticação e expiração, então adequar API, frontend e testes. Preservar as proteções já existentes contra acesso de funcionário ou assistência desativados e explicitar o comportamento do logout.
- **Aceite:** o login emite um JWT verificável; acesso sem token, token alterado ou expirado é recusado; permissões e isolamento entre assistências continuam funcionando; o comportamento de logout está definido e testado.
- **Estado:** pendente. O formato do token e a estratégia de invalidação ainda serão decididos antes da implementação.

### ALT-02 — Implementar recuperação de senha por email

- **Evidência:** `back-end/app.py` e `front-end/src/App.jsx` só oferecem cadastro e login. O Flask-Mail em `back-end/app.py` envia atualmente o link de orçamento, não um link de redefinição de senha.
- **Mudança:** adicionar solicitação de recuperação, envio de email e redefinição da senha do funcionário. Definir antes o prazo e o uso único do link, o tratamento de contas inexistentes e o que acontece com sessões anteriores à troca da senha.
- **Aceite:** em uma demonstração local com SMTP de teste, o funcionário solicita a recuperação, recebe o link, define nova senha, entra com ela e não consegue reutilizar o link.
- **Estado:** pendente; funcionalidade exigida explicitamente pelo responsável.

### ALT-03 — Tratar falha no envio do orçamento

- **Evidência:** `back-end/services.py::respond_budget` grava `AguardandoAprovacao` e o hash do link; só depois `back-end/app.py::respond_budget_route` tenta enviar o email. Se o envio falha, a API retorna erro após a mudança de estado. `RESUMO_DO_PROJETO.md` registra o problema.
- **Mudança:** definir e implementar um resultado coerente para falha de SMTP, com mensagem clara à equipe e recuperação simples do envio. Não presumir rollback de uma transação já confirmada.
- **Aceite:** uma falha simulada de SMTP deixa o orçamento em estado conhecido e a interface informa qual ação permite que o cliente receba um link válido; reenvio não cria OS nem duplica decisão.
- **Estado:** pendente; a regra de negócio exata para a falha ainda precisa ser fechada.

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
- **Estado:** concluído na documentação em 14/10/2026, com recorte da demonstração, `US12` e `US13` no levantamento e atualização de `.specs/IDEIA.md`. JWT e recuperação de senha ainda não foram implementados.

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
- **Estado:** pendente; não executar o smoke em dados de produção.

### ALT-08 — Conferir a separação MVC sem refatoração desnecessária

- **Evidência:** `.specs/regra-tecnologias/regras-de-tecnoligias.md` pede que acesso a dados e lógica de domínio não se concentrem nas rotas; `back-end/app.py` contém SQL diretamente em várias rotas de cadastro, enquanto `back-end/services.py` concentra o fluxo de orçamento e OS.
- **Mudança:** avaliar se a apresentação consegue explicar essa divisão como está. Extrair somente trechos que atrapalhem o entendimento ou violem uma regra importante, preservando a simplicidade.
- **Aceite:** responsabilidades de React, rotas Flask, serviços e acesso SQL são explicáveis com exemplos concretos.
- **Estado:** análise pendente; não há autorização para uma refatoração ampla implícita.

### ALT-09 — Resolver a regra de fuso horário da assistência

- **Evidência:** o requisito `RNF11` em `.specs/regra-requisitos-classes/regra-requisitos-e-diagrama-de-classes-ergon.md` fala em fuso configurado por assistência, mas `data-base/script/script-ergon.sql` não possui configuração de fuso na tabela `AssistenciaTecnica`. Os dois dias do orçamento são calculados em `back-end/services.py` com timestamp do banco.
- **Mudança:** decidir se a demonstração usa um fuso único explicitamente documentado ou se o fuso por assistência realmente integra a primeira versão; só então alinhar requisito, interface e dados.
- **Aceite:** o prazo de aprovação e a apresentação de datas seguem uma regra única e testável.
- **Estado:** decisão pendente.

### ALT-10 — Ajustar instruções de execução à demonstração

- **Evidência:** `README.md` mistura a execução local com detalhes de publicação em Cloudflare. `.specs/regra-tecnologias/regras-de-tecnoligias.md` apresenta Cloudflare como plataforma indicada, embora a meta atual seja uma demonstração local.
- **Mudança:** destacar o caminho mínimo reproduzível para React, Flask, PostgreSQL e SMTP de teste; manter a implantação como possibilidade futura, identificada como fora do critério de conclusão atual.
- **Aceite:** outra pessoa consegue preparar e apresentar a jornada crítica localmente seguindo o README sem precisar publicar serviços.
- **Estado:** parcialmente concluído na documentação em 14/10/2026: as regras tecnológicas identificam Cloudflare como futuro; o README local ainda precisa ser revisado.

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
- **Estado:** classificação pendente com o responsável; nenhuma alteração de esquema foi feita.

## Como manter esta lista

Adicionar novas descobertas com evidência, mudança proposta, critério de aceite e estado. Distinguir requisito confirmado, defeito observado e decisão em aberto. Não marcar um item como concluído somente porque o código foi escrito: registrar a verificação que demonstrou o comportamento.
