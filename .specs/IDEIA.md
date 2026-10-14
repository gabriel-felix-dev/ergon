# Ideia e decisões do Ergon

## Escopo da demonstração local confirmado em 14/10/2026

Sistema de gestão para assistências técnicas independentes. Cada assistência tem seus próprios funcionários, clientes, aparelhos, orçamentos, ordens de serviço e pagamentos. O primeiro gerente cria a assistência e administra somente ela. Não há administrador global.

A versão local inclui CRUD de assistência técnica, funcionário, cliente e aparelho; cadastro de assistência com primeiro gerente; convite por email para o funcionário criar o próprio acesso; solicitação online de orçamento pelo cliente; resposta da equipe; decisão do cliente; criação automática da OS após aprovação; reparo, entrega, cancelamento ou desistência e registro manual do pagamento. Funcionários e clientes entram com JWT e podem recuperar a senha por email. O cliente acompanha seus orçamentos e OS pelo sistema e pelo link recebido.

O funcionário **não inicia** um orçamento em nome do cliente nem abre uma OS manualmente nesta versão. Atendimento presencial com aprovação imediata ou análise posterior, estoque, fornecedores, receitas, despesas, relatórios e implantação em Cloudflare pertencem à visão futura. A equipe continua responsável por analisar e responder às solicitações feitas online.

## Tecnologias e aulas

O sistema usa React na interface, Flask na API e PostgreSQL no Supabase, conforme as regras de tecnologias. Os exemplos MySQL/PyMySQL dos slides servem como base para Flask, SQL e CRUD, sem mudar a decisão por PostgreSQL. As rotas, métodos HTTP, JSON, SQL e login seguem os conceitos das aulas. O email usa Flask-Mail, apresentado na aula de autenticação.

## Jornada do cliente

- Solicitação online em um formulário público com nome, telefone, email, marca, modelo e defeito, todos obrigatórios.
- O primeiro envio cria cliente, aparelho e orçamento na mesma transação. O email do cliente é único dentro de cada assistência. Se o email já estiver cadastrado, a interface orienta o cliente a usar a recuperação de senha para entrar; após entrar, ele pode solicitar outro orçamento ligado ao cadastro existente.
- O cliente recebe um email confirmando a solicitação e indicando a recuperação de senha para criar seu primeiro acesso. A tela de recuperação não recebe o email preenchido automaticamente pelo link.
- A equipe responde com diagnóstico, valores e previsão. O cliente recebe link único por email para abrir e aprovar ou recusar a proposta.
- A decisão deve ocorrer em até dois dias corridos. Recusa ou vencimento não cria OS.
- Depois da aprovação, o mesmo link e o acesso do cliente ao sistema permitem acompanhar a OS vinculada ao orçamento. A criação da OS também é confirmada por email.

## Atendimento na loja (visão futura)

- Na aprovação imediata, o funcionário cadastra cliente e aparelho, abre e responde o orçamento, e registra a decisão do cliente no atendimento.
- Na análise posterior, o aparelho já está na loja. A equipe responde e envia o link para decisão posterior do cliente por email.
- Uma OS é criada apenas após aprovação. Seu vínculo com o cliente passa pelo orçamento. Não há registro direto de OS.

## Ciclo da OS

A OS registra responsável, recebimento do aparelho quando necessário, início e conclusão do reparo, previsão, entrega e pagamento. Ela termina com pagamento ou cancelamento/desistência, sem remoção física do banco. O pagamento é registrado manualmente no máximo uma vez, com data inicial do momento do pagamento, que o funcionário pode corrigir; o momento do lançamento também fica registrado. O pagamento muda a OS para `Paga`. Orçamentos vencidos são processados quando acessados, sem agendador, conforme as técnicas disponíveis.

## Decisões técnicas desta versão

- Funcionários e clientes têm acesso com senha e JWT. O primeiro gerente define sua senha no cadastro da assistência. O gerente informa o email de um funcionário e este recebe um convite para completar o cadastro e criar a própria senha. O cliente cria a senha pelo fluxo de recuperação após a primeira solicitação.
- Separação de dados por `IdAssistenciaTecnica` em consultas e operações.
- Senhas, códigos de recuperação, convites e tokens usados apenas para verificação devem ser armazenados como hash. Emails e demais campos que precisam ser exibidos ou enviados não podem ser recuperados de um hash; seu acesso deve respeitar a assistência e o usuário autenticado. A migração para JWT deve preservar a verificação de contas e assistências ativas.
- Desativação lógica de cadastros para preservar histórico referenciado. Orçamentos recusados ou vencidos e OS canceladas ou desistidas permanecem no banco em estados terminais.
- Documento do cliente e tipo de aparelho opcionais para manter os seis campos do formulário público.
- Credenciais de banco e SMTP e URL pública do frontend vêm do ambiente.

## Verificação pendente

Este documento registra o escopo desejado, não declara que todas as funções já estão prontas. JWT, conta de cliente, convites, recuperação de senha, novos emails e cancelamento de OS ainda exigem implementação e verificação. A implantação em Cloudflare não é requisito para a demonstração local. O vencimento sem agendador só altera o estado na próxima consulta ou tentativa de decisão.
