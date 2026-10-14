# Ergon

Demonstração acadêmica local de assistência técnica. O cliente inicia o orçamento online; a equipe responde; o cliente aprova ou recusa por email; a aprovação cria a OS, que segue até pagamento manual ou cancelamento.

## Estrutura

- `front-end/`: interface React/Vite.
- `back-end/`: API Flask e regras do fluxo.
- `data-base/script/script-ergon.sql`: esquema PostgreSQL para banco vazio.
- `data-base/script/migrations/001-prototipo-local.sql`: atualização de um banco criado pela versão anterior.
- `.specs/`: requisitos, decisões e histórico da versão.

## Executar localmente

1. Crie um banco PostgreSQL vazio e execute `data-base/script/script-ergon.sql`. Se já tiver o esquema anterior, faça cópia do banco e execute `data-base/script/migrations/001-prototipo-local.sql` nessa cópia. Antes da migração, confira emails duplicados de clientes na mesma assistência, pois a nova unicidade impedirá duplicatas.
2. No terminal da API:

   ```powershell
   cd back-end
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -e .
   $env:DATABASE_URL = "postgresql://usuario:senha@host:5432/postgres"
   $env:JWT_SECRET = "coloque-aqui-um-segredo-aleatorio-com-mais-de-32-caracteres"
   $env:FRONTEND_ORIGIN = "http://localhost:5173"
   $env:PUBLIC_FRONTEND_URL = "http://localhost:5173"
   $env:MAIL_SERVER = "smtp.exemplo.com"
   $env:MAIL_PORT = "587"
   $env:MAIL_USE_TLS = "true"
   $env:MAIL_USERNAME = "usuario"
   $env:MAIL_PASSWORD = "senha"
   $env:MAIL_DEFAULT_SENDER = "ergon@exemplo.com"
   .\.venv\Scripts\python.exe app.py
   ```

3. Em outro terminal:

   ```powershell
   cd front-end
   npm.cmd install
   $env:VITE_API_URL = "http://localhost:5000"
   npm.cmd run dev
   ```

O banco pode ser PostgreSQL local (`localhost`, sem TLS) ou Supabase (conexão TLS). Use uma conta SMTP capaz de enviar para os emails da demonstração. Guarde `DATABASE_URL`, `JWT_SECRET` e credenciais SMTP fora do Git. Sem essas configurações, a jornada com banco e email não funciona.

Para ensaiar o fluxo sem enviar mensagens externas, abra outro terminal em `back-end` e execute `.\.venv\Scripts\python.exe tests\smtp_capture.py`. Na API, use `MAIL_SERVER=127.0.0.1`, `MAIL_PORT=1025`, `MAIL_USE_TLS=false`, `MAIL_DEFAULT_SENDER=teste@ergon.local`, sem usuário e senha. As mensagens aparecem em `back-end/.test-mail/messages.jsonl`. Para a apresentação com recebimento no email do participante, configure a conta SMTP real antes de iniciar a API.

Se a conexão local apresentar `CERTIFICATE_VERIFY_FAILED`, baixe o certificado raiz em **Supabase → Database → Settings → SSL Configuration → Download Certificate** e configure `DATABASE_SSL_CA_FILE` com o caminho completo do arquivo antes de iniciar a API. A API acrescenta esse certificado às autoridades confiáveis. Para o pooler do Supabase, desativa apenas a checagem X.509 estrita incompatível com o certificado intermediário atual; a cadeia de confiança e o nome do servidor continuam verificados.

## Fluxo

O primeiro gerente cria a assistência e define a própria senha. Ele convida funcionários pelo email; cada funcionário completa o cadastro e define sua senha pelo link recebido. Funcionários gerenciam clientes, aparelhos, orçamentos, OS e pagamentos.

O cliente solicita orçamento em um único formulário público com nome, telefone, email, marca, modelo e defeito. O sistema cria cliente, aparelho e orçamento e envia confirmação por email. O email orienta a pedir o código de recuperação para criar a senha e entrar na área do cliente. Um email já cadastrado na assistência exige login ou recuperação de senha; o cliente autenticado pode pedir outro orçamento. A equipe responde por email com link único; o cliente aprova ou recusa por esse link. O link e a área do cliente mostram o andamento da OS.

A proposta vence após 48 horas. O vencimento é processado ao consultar orçamentos ou abrir o link. A OS é criada uma vez, somente na aprovação. A equipe registra recebimento do aparelho, reparo, entrega e pagamento. O pagamento não é processado pelo sistema: o funcionário registra valor, forma e data efetiva, com o dia atual sugerido.

Exclusões de assistência, funcionário, cliente e aparelho são desativações lógicas. Orçamentos recusados ou vencidos e OS canceladas/desistidas mantêm os registros e recebem status terminal. A desativação da assistência encerra os acessos. Senhas, códigos e tokens de convite são armazenados como hash; os emails continuam legíveis para envio.

## Depois da demonstração

Atendimento presencial com orçamento iniciado pela equipe, abertura manual de OS, estoque, financeiro, relatórios e publicação em Cloudflare ficam para versões posteriores. O recorte completo está em `.specs/IDEIA.md` e no levantamento de requisitos.
