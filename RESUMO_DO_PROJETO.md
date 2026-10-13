# Ergon — resumo das decisões, implementação e testes

Atualizado em **13/10/2026**. Este arquivo registra o que foi discutido e realizado até agora. As regras originais estão em `.specs/`; este texto é um resumo de continuidade.

## 1. Objetivo e escopo confirmado

O Ergon é um sistema de gestão para assistências técnicas independentes, como projeto de faculdade. Os slides de Flask são a referência e o limite didático para o backend, mesmo quando mostram MySQL. A implementação escolhida usa **React com Vite**, **Flask** e **PostgreSQL**. O banco usado nos testes é o PostgreSQL gerenciado pelo **Supabase**.

A primeira versão foi fechada com:

- CRUD de assistência técnica, funcionário e cliente;
- solicitação e orçamento por cliente, com cadastro do aparelho;
- consulta das ordens de serviço (OS) de cada cliente;
- processo completo de orçamento, aprovação ou recusa, OS, reparo, entrega e registro do pagamento.

Estoque, fornecedores, receitas, despesas e relatórios ficaram fora desta versão. O primeiro gerente cria a própria assistência e administra somente ela; não existe administrador global. Funcionários entram com senha. Clientes não precisam criar conta.

### Jornada do cliente e regras de negócio

O formulário público pede **nome, telefone, email, marca, modelo e defeito**, todos obrigatórios. Uma solicitação cria cliente, aparelho e orçamento de uma vez. Depois da resposta da equipe, o cliente recebe por email um link individual para ver o orçamento e aprovar ou recusar. O mesmo link permite acompanhar a OS após a aprovação.

Há três origens de orçamento: **online**, **loja com decisão imediata** e **loja com análise posterior por email**. A decisão deve ocorrer em até dois dias corridos. Recusa ou vencimento não criam OS. A OS só nasce da aprovação de um orçamento; não há cadastro direto de OS. O ciclo registra responsável, recebimento do aparelho quando necessário, início e conclusão do reparo, previsão, entrega e um único pagamento. Os cadastros são desativados logicamente para preservar o histórico.

## 2. O que foi implementado

| Parte | Estado |
| --- | --- |
| Interface React/Vite | Formulário público, login, painel, cadastros, orçamento, OS e área do cliente por link implementados em `front-end/`. |
| API Flask | Rotas REST, validações, autenticação e regras de negócio implementadas em `back-end/`. |
| PostgreSQL | Script de criação em `data-base/script/script-ergon.sql`; consultas chegaram a funcionar no Supabase. |
| Autenticação | Senhas de funcionários derivadas por PBKDF2; tokens de sessão e de orçamento armazenados como hash. |
| Separação entre assistências | Consultas e alterações usam o identificador da assistência. |
| Email | Envio via Flask-Mail implementado; o teste com SMTP local está preparado, mas o fluxo completo de links ainda precisa ser executado. |

O frontend foi montado como projeto React/Vite. Também discutimos o comando `npm create vite@latest`: o resultado é um projeto Vite funcional, embora sua estrutura inicial tenha sido criada diretamente em vez de passar pelo assistente desse comando.

## 3. Supabase e execução local discutidos

O Supabase hospeda o **banco PostgreSQL**; ele não hospeda automaticamente o React nem o Flask. No painel **Connect**, as opções de framework mostradas para Next.js não correspondem a este projeto. A API Flask deve usar a **string de conexão PostgreSQL** e manter a senha somente no ambiente do servidor. O frontend conversa com o Flask e não precisa receber a URI do banco nem uma chave de acesso direto às tabelas. Também discutimos a instalação local do PostgreSQL: para este projeto, a versão efetiva do banco hospedado é gerenciada pelo Supabase; a instalação local é opcional para desenvolver fora dele.

Conversamos sobre as opções de segurança do projeto Supabase, Data API, exposição automática de novas tabelas e RLS. Para esta arquitetura, o acesso às tabelas ocorre pelo Flask, de modo que a Data API/PostgREST não é necessária para o frontend. O SQL Editor apareceu cinza enquanto o projeto estava `Coming up`/`Unhealthy`; depois o painel mostrou `Healthy` para o banco e os demais serviços, com PostgREST desativado.

Na string de conexão, `[YOUR-PASSWORD]` representa a senha do banco do Supabase. A URI completa **não deve ser enviada no chat nem gravada no repositório**. No PowerShell, `Read-Host -AsSecureString` permite colá-la sem exibir os caracteres. Variáveis definidas com `$env:` valem somente para aquele processo e seus filhos: iniciar o Flask em outro PowerShell sem repetir a configuração provoca `DATABASE_URL não foi configurada`. O comando `Invoke-WebRequest` deve ser executado em outra janela enquanto o Flask permanece rodando.

Houve problemas de certificado SSL ao conectar o Python ao Supabase: primeiro uma cadeia com certificado autoassinado e depois `CA cert does not include key usage extension`. O backend passou a aceitar `DATABASE_SSL_CA_FILE` para carregar o certificado baixado do Supabase. Para o pooler, desliga apenas a verificação X.509 estrita incompatível com o certificado intermediário observado; a verificação da autoridade certificadora e do nome do servidor continua ativa. O arquivo local de certificado e arquivos de ambiente são ignorados pelo Git.

Como plano de publicação, discutimos **frontend em Cloudflare Pages**, **API Flask em Cloudflare Python Workers** e **PostgreSQL no Supabase**. O repositório tem `back-end/worker.py` e `back-end/wrangler.jsonc` para essa direção. **Não há publicação em produção confirmada**, e a integração com SMTP e o ambiente de hospedagem ainda precisa ser validada.

## 4. Testes realizados e correções

O projeto já compilou com `npm run build`, e os arquivos Python foram compilados com `compileall`. Em um teste anterior, `GET /api/assistencias` retornou **HTTP 200** e `[]`, confirmando comunicação entre Flask e Supabase naquele processo.

Nos testes de API com banco real, passaram as primeiras verificações de saúde, lista pública, exigência do primeiro gerente, criação de assistência, senha incorreta, login, perfil, isolamento entre assistências, edição de assistência, criação/listagem/edição de funcionário, restrição de ação gerencial, proteção contra desativar o último gerente, criação/leitura/edição de cliente, isolamento do cliente entre assistências, cadastro/listagem de aparelho e solicitação online criando cliente, aparelho e orçamento. A execução parou ao responder o primeiro orçamento online: a API em uso retornou **503** porque não tinha as variáveis de SMTP e URL pública configuradas. As duas assistências criadas por essa execução automática foram desativadas pelo próprio roteiro.

Pela interface no navegador, foram confirmados: cadastro de uma assistência com primeiro gerente; login do gerente; cadastro de cliente e aparelho; criação, resposta e aprovação de orçamento de loja imediato; criação da OS; início e conclusão do reparo; registro de um pagamento fictício; entrega do aparelho; cadastro e edição de funcionário; e solicitação pública de orçamento. O servidor SMTP local recebeu uma mensagem de prova sem enviar email externo.

Erros e ajustes identificados durante esses testes:

1. **Página branca no frontend:** faltava importar `React` em `App.jsx`. Foi corrigido e a tela passou a renderizar.
2. **Falha de conexão da interface na porta de teste 5174:** a origem não correspondia à configuração antiga de CORS. Foi criado um proxy de desenvolvimento no Vite e as chamadas passaram a usar `/api` na mesma origem; `VITE_API_URL` continua disponível para implantação.
3. **Login não permitia selecionar a assistência:** o campo gravava `assistanceId`, mas a tela e o envio liam `assistenciaId`. O nome da propriedade foi corrigido, e o login do gerente funcionou no navegador.
4. **Após criar a assistência, ela não vinha pré-selecionada no login:** o mesmo nome de propriedade estava incorreto no estado inicial do formulário. Foi corrigido. A mensagem de sucesso do cadastro também deixou de ser apagada pela atualização da lista de assistências.
5. **Previsão da OS aparecia um dia antes:** uma data do PostgreSQL era serializada como data HTTP à meia-noite UTC. O Flask agora envia campos `date` em ISO (`AAAA-MM-DD`); o navegador mostrou a data informada corretamente.
6. **Resposta de orçamento online sem SMTP configurado:** a tentativa retornou 503. É uma limitação de configuração ainda aberta para o teste completo. Como a resposta do orçamento é gravada antes da tentativa de envio, uma falha de email pode deixar o orçamento aguardando aprovação sem que o cliente receba o link; o reenvio existe, mas esse comportamento merece correção e novo teste.
7. **Outra instância do Flask na porta 5000:** em uma verificação posterior, ela devolveu erro SSL por não ter a configuração de certificado. Foi preparado um script separado para testes na porta 5001, com certificado e SMTP local.

No Windows desta sessão, a porta 5173 recusou a inicialização (`EACCES`), então o Vite foi executado na **5174** durante os testes. Isso não altera a porta padrão do projeto.

## 5. Estado atual e pendências

Em **13/10/2026**, uma verificação local não encontrou processos escutando nas portas **5000, 5001, 5174 ou 1025**. Os servidores precisam ser iniciados novamente para continuar. O roteiro de testes completos está em `back-end/tests/system_smoke.py`; o capturador de email está em `back-end/tests/smtp_capture.py`; e `back-end/start-local-tests.ps1` prepara a API na porta 5001, solicitando a URI do banco de forma oculta. O proxy do Vite pode apontar para essa porta com `ERGON_DEV_API_TARGET`.

Ainda faltam testes reais de ponta a ponta para: entrega do email com link, aprovação e recusa pelo link, reenvio e invalidação do link anterior, atendimento de loja com análise posterior, vencimento após dois dias, OS por cliente em todos os cenários e repetição integral do roteiro automático. Também faltam testes no ambiente publicado. **Não é correto afirmar ainda que todas as funcionalidades foram validadas.**

Uma assistência de teste criada pela interface, **`Ergon Teste Interface 1210`**, permaneceu ativa no banco quando o backend parou. Ela contém clientes, funcionário, orçamento e OS fictícios dos testes. Deve ser desativada depois de concluir a validação para não aparecer na lista pública. Nenhuma credencial de banco é registrada neste documento.

## 6. Arquivos de referência

- `.specs/prompt.md`: instruções iniciais e limites didáticos.
- `.specs/IDEIA.md`: escopo e decisões de negócio.
- `.specs/VERSION.md`: histórico da versão.
- `README.md`: estrutura, execução local e plano de implantação.
- `data-base/script/script-ergon.sql`: estrutura do banco.
- `back-end/app.py`, `auth.py`, `db.py`, `services.py`: API, autenticação, conexão e regras.
- `front-end/src/App.jsx`, `api.js`, `vite.config.js`: interface e comunicação com a API.

O estado atual do Git inclui vários arquivos ainda **não versionados** e uma alteração em `README.md`; não houve commit confirmado neste resumo.
