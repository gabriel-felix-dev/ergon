# Prompt — Projeto Ergon (protótipo)

## Contexto

Projeto de conclusão de curso da faculdade em **React + Flask + Postgress**. Os arquivos estão na pasta do projeto:

- **Ideia do projeto**: existe a pasta `regra-requisitos-classes/` com o arquivo `regra-requisitos-e-diagrama-de-classes-ergon.md` descrevendo a ideia, os requisitos, as classes do sistema, stakeholders, usuários, histórias de usuário, requisitos não-funcionais e as regras de negócio.
- **Tecnologias para serem usadas**: existe as pastas `regra-requisitos-back-end-flask/`, `regra-tecnologias/` e `regra-banco-de-dados/` descrevendo as tecnologias que devem ser implementadas no sistema e como devem ser implementadas.
- **Conteúdo base do back-end**: em **PDF**, separado na pasta `regra-requisitos-back-end-flask/` são os slides do que é para ser **usado para o back-end**.

## Sobre os formatos (importante)

- O conteúdo que está em **PDF** → a extração é mais trabalhosa e pode vir incompleta, mas dá pra fazer. Tome as decisões com base no que conseguir extrair e, se algo ficar ilegível, me avise em vez de adivinhar.

## As duas travas inegociáveis

1. **Não construa nada enquanto a ideia não estiver definida e confirmada por mim.** Seu papel agora é entender o material e me ajudar a fechar o escopo — não sair implementando.

2. **O projeto só pode usar o que está definido nos arquivos.** Os slides dos PDFs em `Flask/` é o **limite** do que pode ser usado (libs, padrões, técnicas). Antes de propor qualquer abordagem, valide contra os slides. Se algo necessário **não** foi ensinado, sinalize e proponha uma alternativa dentro do que foi ensinado.

## Passo 0 — Ler e devolver entendimento (sem alterar nada)

Leia, nesta ordem:

1. Acessar `regra-tecnologias/` com as regras de quais tecnologias serão usadas.
2. Acessar `regra-requisitos-back-end-flask/` com os **PDFs**.
3. Acessar `regra-banco-de-dados/` com as regras de de estrutura do banco de dados.
4. Acessar  `regra-requisitos-classes/` para entender o que o sistema deve fazer.

Depois, me devolva um resumo e **espere minha resposta**:

- (a) Regras/critérios da atividade como você entendeu.
- (b) O que os slides permitem (resumo do que foi lecionado e que dá pra usar).
- (c) O que você entendeu da ideia do projeto.
- (d) Qual o primeiro passo.

## Conforme eu for definindo a ideia

- Vá refinando o escopo a cada coisa que eu mandar.
- Mantenha um arquivo (ex.: `IDEIA.md`) de decisões atualizado dentro da pasta `.specs/` com: ideia atual, escopo fechado, o que ainda falta definir, e quais técnicas dos slides cada parte vai usar. Isso evita perder o fio.
- Mantenha um arquivo (ex.: `VERSION.md`) com a versão atual do projeto e o que foi implementado de novo que não estava no arquivo `regra-requisitos-e-diagrama-de-classes-ergon.md`.
- A cada proposta de funcionalidade, diga explicitamente: **isso cabe no que foi lecionado? Sim/Não — e onde nos slides.**

## Escopo

- Manter no **mínimo viável que atende as regras**. Não inflar com features, telas ou arquitetura além do pedido — nem além do que foi ensinado nos slides. Sempre mantenha o código simples e estável para futuras implementações e atualizações.
- Conforme cada parte do sistema for criada siga a seguinte organização:

  - `back-end/`: **(toda a estrutura do back-end do projeto)**
  - `data-base/`: **(toda estrutura a estrutura do banco de dados)**
  - `script/`: **(estrutura de criação do banco)**
  - `trg/`: **(pasta para guardar as triggers)**
  - `fnc/`: **(pasta para guardar as triggers)**
  - `sp/`: **(pasta para guardar as store procedures)**
  - `vw/`: **(pasta para guardar as views)**
  - `front-end/`: **(toda a estrutura do front-end do projeto)**

## Estrutura de pastas do projeto

```text
    ergon/
    ├── README.md
    ├── .specs/
    │   ├── prompt.md
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

## Só depois de eu confirmar

- Escopo fechado + tudo dentro do que foi lecionado → aí sim começa a implementar, em blocos pequenos, validando que compila e funciona a cada etapa.

## Sempre

- Comunicação em PT-BR.
- Mudanças estruturais ou destrutivas: perguntar antes.
- Ao fim de cada etapa: resumo do que foi decidido/feito e do que ainda falta definir.
