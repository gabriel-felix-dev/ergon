# Tecnologias

## Interface e front-end

- **React** — biblioteca usada para construir a interface.
- **HTML** — estrutura das páginas.
- **CSS** — apresentação visual.
- **JavaScript** — linguagem do front-end.

## Back-end e execução

- **Python** — linguagem do serviço de back-end.
- **Flask** — framework usado para implementar as rotas da API.
- **WSGI** — interface/adaptador indicada para executar a aplicação Flask no Python Worker.
- **Cloudflare Workers** — plataforma indicada para executar o Python Worker.

## Hospedagem

- **Cloudflare Pages** — hospedagem indicada para os arquivos do front-end React.

## Comunicação e dados

- **HTTPS** — protocolo seguro usado nas conexões.
- **REST** — estilo de comunicação da API.
- **JSON** — formato indicado para solicitações e respostas.

## Banco de dados

- **Supabase** — serviço onde os dados ficam armazenados.
- **PostgreSQL** — sistema de gerenciamento de banco de dados usado pelo Supabase no diagrama.

## Arquitetura do sistema

- O sistema deverá seguir o padrão **MVC (Model-View-Controller)**.
- **Model**: representa os dados e as regras do domínio e concentra o acesso ao banco PostgreSQL hospedado no Supabase.
- **View**: corresponde à interface desenvolvida em React, HTML, CSS e JavaScript. A View consome a API e apresenta os dados ao usuário.
- **Controller**: corresponde às rotas e controladores desenvolvidos em Flask. Recebe as requisições HTTP, coordena a operação necessária e retorna respostas, incluindo JSON para a API REST.
- O fluxo entre as camadas deve ser: View → Controller → Model; a resposta retorna do Controller para a View.
- Manter as responsabilidades separadas: a View não acessa o banco diretamente, e a lógica de domínio e o acesso a dados não devem ficar concentrados nas rotas dos Controllers.
