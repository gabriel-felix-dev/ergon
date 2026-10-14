# Tecnologias

## Objetivo atual

- A primeira entrega é uma demonstração acadêmica local. Cloudflare Pages e Workers permanecem como possibilidades futuras; não são necessários para validar esta entrega.
- Os slides fornecem os conceitos didáticos. Bibliotecas equivalentes necessárias para React, Flask e PostgreSQL podem ser utilizadas quando a escolha for simples de explicar.

## Interface e front-end

- **React** — biblioteca usada para construir a interface.
- **HTML** — estrutura das páginas.
- **CSS** — apresentação visual.
- **JavaScript** — linguagem do front-end.

## Back-end e execução

- **Python** — linguagem do serviço de back-end.
- **Flask** — framework usado para implementar as rotas da API.
- **WSGI** — interface/adaptador indicada para executar a aplicação Flask no Python Worker.
- **Cloudflare Workers** — possibilidade futura para executar o Python Worker.

## Hospedagem

- **Cloudflare Pages** — possibilidade futura para hospedar os arquivos do front-end React.

## Comunicação e dados

- **HTTPS** — protocolo seguro usado nas conexões.
- **REST** — estilo de comunicação da API.
- **JSON** — formato das solicitações e respostas entre React e a API Flask; não é o formato usado pela API para consultar o banco.
- **Métodos HTTP** — `GET` para leitura, `POST` para criação ou ações, `PUT` para atualização e `DELETE` para desativação. `READ` é uma operação do CRUD, não um método HTTP.

## Banco de dados

- **Supabase** — serviço onde os dados ficam armazenados.
- **PostgreSQL** — banco escolhido para o Ergon, mantido no lugar do MySQL exemplificado nos slides.
- **SQL** — linguagem usada pelo backend para consultar e modificar o PostgreSQL.

## Autenticação e email da demonstração

- Funcionários entram com senha e sessão representada por JWT. A implementação atual ainda usa token opaco e precisa ser adequada.
- Senhas e tokens usados apenas para verificação são armazenados como hash. Outros dados sensíveis devem ser classificados antes de escolher sua proteção, pois alguns precisam ser recuperados para consulta ou envio de email.
- O backend usa Flask-Mail para enviar tanto o link de orçamento quanto o link de recuperação de senha. A recuperação ainda precisa ser implementada.

## Arquitetura do sistema

- O sistema deverá seguir o padrão **MVC (Model-View-Controller)**.
- **Model**: representa os dados e as regras do domínio e concentra o acesso ao banco PostgreSQL hospedado no Supabase.
- **View**: corresponde à interface desenvolvida em React, HTML, CSS e JavaScript. A View consome a API e apresenta os dados ao usuário.
- **Controller**: corresponde às rotas e controladores desenvolvidos em Flask. Recebe as requisições HTTP, coordena a operação necessária e retorna respostas, incluindo JSON para a API REST.
- O fluxo entre as camadas deve ser: View → Controller → Model; a resposta retorna do Controller para a View.
- Manter as responsabilidades separadas: a View não acessa o banco diretamente, e a lógica de domínio e o acesso a dados não devem ficar concentrados nas rotas dos Controllers.
