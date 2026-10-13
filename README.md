# Ergon

Primeira versão do sistema para assistências técnicas: cadastros de assistência, funcionários e clientes; solicitação e decisão de orçamentos; ordens de serviço; entrega e pagamento.

## Estrutura

- `front-end/`: interface React/Vite.
- `back-end/`: API Flask e regras do fluxo.
- `data-base/script/script-ergon.sql`: esquema PostgreSQL.
- `.specs/`: requisitos, decisões e histórico da versão.

## Executar localmente

1. Crie um banco PostgreSQL vazio e execute `data-base/script/script-ergon.sql`.
2. No terminal da API:

   ```powershell
   cd back-end
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -e .
   $env:DATABASE_URL = "postgresql://usuario:senha@host:5432/postgres"
   $env:FRONTEND_ORIGIN = "http://localhost:5173"
   $env:PUBLIC_FRONTEND_URL = "http://localhost:5173"
   $env:MAIL_SERVER = "smtp.exemplo.com"
   $env:MAIL_PORT = "587"
   $env:MAIL_USE_TLS = "true"
   $env:MAIL_USERNAME = "usuario"
   $env:MAIL_PASSWORD = "senha"
   $env:MAIL_DEFAULT_SENDER = "orcamentos@exemplo.com"
   .\.venv\Scripts\python.exe app.py
   ```

3. Em outro terminal:

   ```powershell
   cd front-end
   npm.cmd install
   $env:VITE_API_URL = "http://localhost:5000"
   npm.cmd run dev
   ```

No Supabase, use uma URL de conexão PostgreSQL apropriada para funções sem servidor, com SSL. Guarde URL e credenciais SMTP como segredos no ambiente; não as grave no repositório.

Se a conexão local apresentar `CERTIFICATE_VERIFY_FAILED`, baixe o certificado raiz em **Supabase → Database → Settings → SSL Configuration → Download Certificate** e configure `DATABASE_SSL_CA_FILE` com o caminho completo do arquivo antes de iniciar a API. A API acrescenta esse certificado às autoridades confiáveis. Para o pooler do Supabase, desativa apenas a checagem X.509 estrita incompatível com o certificado intermediário atual; a cadeia de confiança e o nome do servidor continuam verificados.

## Fluxo

O primeiro gerente cria a assistência na interface. Ele administra os funcionários e os dados da própria assistência. Funcionários gerenciam clientes, aparelhos, orçamentos, OS e pagamentos.

O cliente solicita orçamento em um único formulário público com nome, telefone, email, marca, modelo e defeito. A resposta da equipe envia um link único por email, pelo qual o cliente vê a proposta e aprova ou recusa. O link também mostra a OS após a aprovação. No atendimento presencial imediato, a equipe registra a decisão no painel. Na análise posterior presencial, a decisão ocorre pelo link.

A proposta vence após dois dias corridos. O vencimento é processado ao consultar orçamentos ou abrir o link. A OS é criada uma vez, somente na aprovação. A equipe registra recebimento do aparelho quando necessário, início e conclusão do reparo, entrega e pagamento.

Exclusões de assistência, funcionário e cliente são desativações lógicas para preservar o histórico. A desativação da assistência encerra o acesso da equipe. Solicitações públicas repetidas criam novos cadastros de cliente, evitando associar dados de uma solicitação a outro cliente somente por email.

## Implantação

O frontend pode ser compilado com `npm run build` e publicado a partir de `front-end/dist` no Cloudflare Pages. A API tem ponto de entrada WSGI para Cloudflare Python Workers em `back-end/worker.py`. Configure `DATABASE_URL`, `FRONTEND_ORIGIN`, `PUBLIC_FRONTEND_URL` e as variáveis SMTP no ambiente de implantação. Banco e SMTP reais ainda precisam de teste de integração nesse ambiente.
