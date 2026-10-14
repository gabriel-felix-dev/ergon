# Ideia e decisões do Ergon

## Escopo confirmado em 12/10/2026

Sistema de gestão para assistências técnicas independentes. Cada assistência tem seus próprios funcionários, clientes, aparelhos, orçamentos, ordens de serviço e pagamentos. O primeiro gerente cria a assistência e administra somente ela. Não há administrador global.

A primeira versão, destinada a uma **demonstração acadêmica local**, inclui CRUD de assistência técnica, funcionário e cliente, consulta de OS por cliente e todo o processo de orçamento e OS. Também deve incluir autenticação de funcionários com JWT e recuperação de senha por email, confirmadas em 14/10/2026 e ainda pendentes de implementação. Estoque, fornecedores, receitas, despesas, relatórios e implantação em Cloudflare ficam fora desta versão.

## Tecnologias e aulas

O sistema usa React na interface, Flask na API e PostgreSQL no Supabase, conforme as regras de tecnologias. Os exemplos MySQL/PyMySQL dos slides servem como base para Flask, SQL e CRUD, sem mudar a decisão por PostgreSQL. As rotas, métodos HTTP, JSON, SQL e login seguem os conceitos das aulas. O email usa Flask-Mail, apresentado na aula de autenticação.

## Jornada do cliente

- Solicitação online em um formulário público com nome, telefone, email, marca, modelo e defeito, todos obrigatórios.
- O envio cria cliente, aparelho e orçamento na mesma transação. O cliente não precisa criar conta ou cadastrar aparelho em outra etapa.
- A equipe responde com diagnóstico, valores e previsão. O cliente recebe link único por email para abrir e aprovar ou recusar a proposta.
- A decisão deve ocorrer em até dois dias corridos. Recusa ou vencimento não cria OS.
- Depois da aprovação, o mesmo link permite acompanhar o estado da OS vinculada ao orçamento.

## Atendimento na loja

- Na aprovação imediata, o funcionário cadastra cliente e aparelho, abre e responde o orçamento, e registra a decisão do cliente no atendimento.
- Na análise posterior, o aparelho já está na loja. A equipe responde e envia o link para decisão posterior do cliente por email.
- Uma OS é criada apenas após aprovação. Seu vínculo com o cliente passa pelo orçamento. Não há registro direto de OS.

## Ciclo da OS

A OS registra responsável, recebimento do aparelho quando necessário, início e conclusão do reparo, previsão, entrega e pagamento. O pagamento é registrado no máximo uma vez e muda o status para `Paga`. Orçamentos vencidos são processados quando acessados, sem agendador, conforme as técnicas disponíveis.

## Decisões técnicas desta versão

- Login com senha somente para funcionários; clientes usam o link individual. A demonstração deve usar JWT para a sessão dos funcionários; a implementação atual com token opaco precisa ser adequada.
- Separação de dados por `IdAssistenciaTecnica` em consultas e operações.
- A implementação atual guarda apenas hashes dos tokens de sessão e de orçamento; as senhas de funcionário são derivadas por PBKDF2. A migração para JWT deve preservar a verificação de funcionários e assistências ativos. Links de recuperação de senha também precisarão de proteção por hash e uso único.
- Desativação lógica de cadastros para preservar histórico referenciado.
- Documento do cliente e tipo de aparelho opcionais para manter os seis campos do formulário público.
- Credenciais de banco e SMTP e URL pública do frontend vêm do ambiente.

## Verificação pendente

O código compila e houve testes parciais com PostgreSQL e SMTP local, descritos em `RESUMO_DO_PROJETO.md`. O fluxo completo de email e a recuperação de senha ainda não foram validados; JWT ainda não foi implementado. A implantação em Cloudflare não é requisito para a demonstração local. O vencimento sem agendador só altera o estado na próxima consulta ou tentativa de decisão.
