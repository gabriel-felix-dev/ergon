# Instruções do projeto Ergon — demonstração acadêmica local

## Contexto

Projeto de conclusão de curso da faculdade em **React + Flask + PostgreSQL**. O objetivo atual é uma demonstração acadêmica local. A implantação em Cloudflare é uma possibilidade futura, não um critério para concluir esta etapa. Os arquivos estão na pasta do projeto:

- **Visão completa do projeto**: `.specs/regra-requisitos-classes/regra-requisitos-e-diagrama-de-classes-ergon.md` descreve requisitos, classes, stakeholders, histórias de usuário e regras de negócio.
- **Tecnologias para serem usadas**: as pastas `.specs/regra-tecnologias/` e `.specs/regras-banco-de-dados/` descrevem as tecnologias e convenções aprovadas.
- **Conteúdo didático do back-end**: os PDFs em `.specs/regras-back-end-flask/` mostram os conceitos desenvolvidos nas aulas.
- **Escopo da demonstração**: `.specs/IDEIA.md` delimita a versão atual; o documento em `.specs/regra-requisitos-classes/` também preserva a visão futura do produto.
- **Mudanças pendentes**: `.specs/ALTERAÇÕES NECESSARIAS.md` registra o que ainda precisa ser implementado ou decidido. `.specs/VERSION.md` registra o que foi entregue.

## Sobre os formatos (importante)

- O conteúdo que está em **PDF** → a extração é mais trabalhosa e pode vir incompleta, mas dá pra fazer. Tome as decisões com base no que conseguir extrair e, se algo ficar ilegível, me avise em vez de adivinhar.

## Regras para continuar o projeto

1. **Não amplie o escopo nem resolva uma regra de negócio ambígua por conta própria.** A primeira versão já foi definida em `.specs/IDEIA.md`; mudanças de produto, domínio ou arquitetura ainda pendentes devem ser apresentadas para decisão antes da implementação.

2. **Use os conceitos desenvolvidos nos slides e preserve um código simples de estudar e explicar.** Os exemplos de bibliotecas e o uso de MySQL nos PDFs não formam uma lista fechada. A stack aprovada é React, Flask e PostgreSQL; uma biblioteca equivalente necessária para essa stack pode ser usada quando sua função e sua relação com os conceitos das aulas forem explicadas claramente. Se uma técnica acrescentar complexidade sem necessidade para a demonstração, proponha uma alternativa mais simples.

3. **Use os termos de comunicação corretamente.** React e Flask trocam requisições e respostas em JSON por HTTP; Flask consulta o PostgreSQL com SQL. Os métodos HTTP usados são `GET`, `POST`, `PUT` e `DELETE`. `READ` nomeia a leitura no CRUD, não um método HTTP.

4. **A demonstração inclui autenticação de funcionários com JWT e dois fluxos de email:** envio do link de orçamento e recuperação de senha. Senhas e tokens usados apenas para verificação devem ser armazenados como hash no banco. Antes de definir a proteção de outros dados sensíveis, identifique se o sistema precisa recuperar seu valor, como ocorre com o email do destinatário.

## Leitura de contexto antes de uma tarefa

Leia os contratos relevantes à tarefa, nesta ordem quando precisar de uma visão geral:

1. `.specs/IDEIA.md` e `.specs/ALTERAÇÕES NECESSARIAS.md` para o escopo atual e as pendências.
2. `.specs/regra-tecnologias/` e, se a tarefa envolver banco, `.specs/regras-banco-de-dados/`.
3. PDFs em `.specs/regras-back-end-flask/` relacionados à técnica em questão.
4. `.specs/regra-requisitos-classes/` para regras detalhadas, distinguindo demonstração atual de visão futura.

Ao encontrar uma decisão ainda pendente, devolva um resumo e **espere minha resposta** antes da parte que depende dela:

- (a) Qual decisão falta e por que ela muda a implementação.
- (b) Quais conceitos dos slides e contratos existentes se aplicam.
- (c) Quais opções simples atendem ao escopo confirmado.

## Evolução do escopo

- Vá refinando o escopo a cada coisa que eu mandar.
- Mantenha `.specs/IDEIA.md` como escopo e decisões atuais, `.specs/ALTERAÇÕES NECESSARIAS.md` como lista de mudanças pendentes e `.specs/VERSION.md` como histórico de implementação e validação, sem repetir manualmente o mesmo estado nos três arquivos.
- A cada proposta de funcionalidade, diga qual conceito dos slides ela aplica e como sua implementação permanece simples de explicar.

## Escopo

- Manter no **mínimo viável para a demonstração local**. Não acrescentar estoque, fornecedores, receitas, despesas, relatórios ou implantação em produção como condição para concluir esta versão. Manter o código simples e estável para futuras implementações e atualizações.
- Conforme cada parte do sistema for criada siga a seguinte organização:

  - `back-end/`: **(toda a estrutura do back-end do projeto)**
  - `data-base/`: **(toda estrutura a estrutura do banco de dados)**
  - `script/`: **(estrutura de criação do banco)**
  - `trg/`: **(pasta para guardar as triggers)**
  - `fnc/`: **(pasta para guardar as functions)**
  - `sp/`: **(pasta para guardar as store procedures)**
  - `vw/`: **(pasta para guardar as views)**
  - `front-end/`: **(toda a estrutura do front-end do projeto)**

## Estrutura de pastas do projeto

```text
    ergon/
    ├── README.md
    ├── .specs/
    │   ├── prompt.md
    │   ├── IDEIA.md
    │   ├── VERSION.md
    │   ├── ALTERAÇÕES NECESSARIAS.md
    │   ├── regra-requisitos-classes/
    │   │   └── regra-requisitos-e-diagrama-de-classes-ergon.md
    │   ├── regra-tecnologias/
    │   │   └── regras-de-tecnoligias.md
    │   ├── regras-back-end-flask/
    │   │   ├── aula-1-introducao-a-backend.pdf
    │   │   ├── aula-2-introducao-ao-python.pdf
    │   │   ├── aula-2-2-estruturas-de-repeticao-e-listas.pdf
    │   │   ├── aula-3-padroes-de-arquitetura.pdf
    │   │   ├── aula-4-ambiente-virtual-e-roteiro-inicial-do-flask.pdf
    │   │   ├── aula-5-rendertemplate-redirect-jinja-com-flask.pdf
    │   │   ├── aula-6-metodos-de-requisicao.pdf
    │   │   ├── aula-7-conectando-ao-banco-de-dados.pdf
    │   │   ├── aula-8-a-importancia-das-apis-no-desenvolvimento-backend.pdf
    │   │   └── aula-9-cadastro-login-recuperacao-senha-usuario.pdf
    │   └── regras-banco-de-dados/
    │       └── regras-estruturas-banco-de-dados.md
    ├── back-end/
    ├── data-base/
    │   ├── fnc/
    │   ├── script/
    │   ├── sp/
    │   ├── trg/
    │   └── vw/
    └── front-end/
```

## Implementação e validação

- Para escopo confirmado, implementar em blocos pequenos e validar o comportamento observado a cada etapa. A demonstração só estará pronta quando o fluxo de orçamento até OS e a recuperação de senha por email funcionarem localmente; compilar, por si só, não comprova o fluxo.

## Sempre

- Comunicação em PT-BR.
- Mudanças estruturais ou destrutivas: perguntar antes.
- Ao fim de cada etapa: resumo do que foi decidido/feito e do que ainda falta definir.
