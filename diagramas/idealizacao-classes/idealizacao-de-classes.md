**Sistema de Assistência Técnica Ergon**

O intuito do sistema é ser usado por assistências técnicas para gerenciar Clientes, Funcionários, Ordens de Serviço, Fornecedores, Entradas e Saídas de dinheiro, Peças em estoque e emissão de relatórios.


Entidades:

- **Assistência Técnica**:	

  - Atributos:

    - Id

    - Nome

    - Documento

    - Email

    - Telefone

    - endereco

  - Cardinalidades

    - a Assistência Técnica tem um ou mais Funcionários;

    - a Assistência Técnica tem zero ou mais Receitas;

    - a Assistência Técnica tem zero ou mais Despesas;

    - a Assistência Técnica tem zero ou mais Peças;

    - a Assistência Técnica tem zero ou mais Fornecedor;

    - a Assistência Técnica tem zero ou mais Ordens de Serviço;

- **Cliente**:

  - Atributos:

    - Id

    - IdAssistenciaTecnica

    - Nome

    - Documento

    - Email

    - Telefone

    - endereco

    - Ativo (bool) 

  - Ações:

    - solicitar uma Ordem de Serviço (OS) informando os dados do Aparelho e os detalhes para o serviço; 

    - aprovar ou recusar uma OS que pode ser gerada por um Funcionário; 

    - realizar Pagamentos; 

  - Cardinalidades:

    - o Cliente tem um ou mais Aparelhos;

    - o Cliente tem zero ou mais OS;

    - o Cliente tem zero ou mais Pagamentos;

    - o Cliente pertence a uma Assistência Técnica;

- **Funcionário (Gerente = False)**: 

  - Atributos:

    - Id

    - IdAssistenciaTecnica

    - Nome

    - Documento

    - Emial

    - Telefone

    - Gerente (bool) = False

    - Ativo (bool)

  - Ações:

    - receber uma solicitação OS;

    - criar uma OS para enviar ao Cliente;

    - receber um Pagamento;

    - emitir relatórios simples;

    - verificar Estoque – Consulta de Peças por de relatórios;

    - enviar a solicitação de uma Peça que está em Falta ao Gerente;

    - movimentar Peças do estoque para serem usadas em uma OS;

  - Cardinalidades:

    - o Funcionário tem zero ou mais OS;

    - o Funcionário é de uma Assistência Técnica;

    - o Funcionário pode ter zero ou mais solicitação de Peça;

- **Funcionário (Gerente = True)**: 

  - Atributos:

    - Id

    - IdAssistenciaTecnica

    - Nome

    - Documento

    - Emial

    - Telefone

    - Gerente (bool) = True

    - Ativo (bool)

  - Ações:

    - emitir relatórios simples e avançados;

    - verificar Estoque – Consulta de Peças por de relatórios;

    - receber solicitações de Peças de Funcionários;

    - cadastrar Fornecedor (CRUD);

    - cadastrar Peça (CRUD);

    - cadastra Receitas e Despesas (CRUD);

  - Cardinalidades:

    - o Gerente é de uma Assistência Técnica;

    - o Gerente pode ter zero ou mais solicitação de Peça;

- **Aparelho**: 

  - Atributos:

    - Id

    - Marca

    - Modelo

    - TipoAparelho

  - Cardinalidade:

    - um Aparelho é de uma ou mais OS;

    - um Aparelho é de um Cliente;

- Ordem de Serviço (OS): 

  - **Atributos**: 

    - Id

    - IdAssistenciaTecnica

    - IdCliente

    - IdFuncionario

    - IdAparelho

    - Status

    - Diagnostico

    - ValorMaoDeObra

    - ValorPecas

    - PrazoConclusao

    - PrazoRealConclusao

  - Cardinalidade:

    - a OS é de uma Cliente;

    - a OS é de um Funcionário;

    - a OS é de uma Assistência Técnica;

    - a OS tem um Aparelho;

    - a OS tem zero ou mais Peças utilizadas;

    - a OS tem um Pagamento

    - a OS tem zerou ou várias Movimentações de Peça

- **Pagamento**:

  - Atributos:

    - Id

    - IdOrdemServico

    - Valor

    - Data

    - FormaPagamento

    - Status

  - Cardinalidades:

    - o Pagamento tem uma OS

- **Receita**:

  - Atributos:

    - Id

    - Tipo

    - Valor

    - Data

    - Descricao

  - Cardinalidade:

    - a Receita é de uma Assistência Técnica;

- **Despesa**:

  - Atributos:

    - Id

    - Tipo

    - Valor

    - Data

    - Descricao

  - Cardinalidade:

    - a Despesa é de uma Assistência Técnica;

- **Peça**:

  - Atributos:

    - Id

    - IdFornecedor

    - Nome

    - Marca

    - Modelo

    - Quantidade

  - Cardinalidade:

    - a Peça é de uma Assistência Técnica;

    - a Peça é de uma ou mais OS;

    - a Peça é de um Fornecedor;

    - a Peça pode está em zero ou mais Solicitações de Peça

- **Fornecedor**:

  - Atributos:	

    - Id

    - Nome

    - Documento

    - Email

    - Telefone

  - Cardinalidade:

    - o Fornecedor tem zero ou mais Peças;

- **Solicitação de Peça**:

  - Atributos:

    - Id

    - IdFuncionario

    - IdGerente

    - IdPeça

    - Status

    - DataSolicitacao

    - DataResposta

    - Descricao

    - Quantidade

  - Cardinalidade

    - a Solicitação de Peça tem um ou mais Funcionário;

    - a Solicitação de Peça tem um ou mais Gerente;

- **Movimentação de Estoque**:

  - Atributo:

    - Id

    - IdPeça

    - IdFuncionario

    - IdOrdemServico

    - TipoMovimentacao

    - Data

    - Quantidade

  - Cardinalidade:

    - a Movimentação é feita por um Funcionário;

    - a Movimentação tem uma OS;

    - a Movimentação tem uma Peça;

  - Regras adicionais:

- **Cadastro do Cliente e do Aparelho**: os cadastros podem ocorrer de duas maneiras: 

  - Solicitação de OS: Quando o Cliente solicitar uma OS ele deverá informar obrigatoriamente: nome, e-mail, telefone, marca do aparelho, tipo, modelo e qual serviço deverá ser prestado;

  - Registro direto de OS: O Funcionário poderá registrar diretamente as informações que o um Cliente deve informar no momento de solicitação de uma OS;

- **Gerente**:

  - tem todas as funções do Funcionário (com exceção a opção de solicitação de Peça a um Gerente);

  - Haverá apenas uma entidade **Funcionário**, mas ela tem um **atributo **chamado **Gerente de tipo booliano. O Funcionário só será um Gerente se o atributo Gerente for True. Caso contrário, ele será um Funcionário simples. Os acessos são diferentes para cada Funcionário.**

- **Status de uma OS**: 

  - Solicitada: Quando o Cliente envia uma solicitação de OS;

  - Em Análise: Quando o Funcionário recebe a solicitação e estiver montando a devolutiva para o Cliente;

  - Aguardando Aprovação: Quando for devolvida para o Cliente e o Cliente precisar aprovar ou recusar;

  - Aprovada: Quando o Cliente tiver aprovado a devolutiva do Funcionário;

  - Recusada: Quando o Cliente tiver recusado a devolutiva do Funcionário;

  - Aguardando Reparo: Após o Cliente ter aprovado ou quando o Funcionário realizar o cadastro direto da OS com as informações do Cliente e do Aparelho;

  - Em Reparo: Após o Cliente ter aprovado, o Funcionário inicia o processo de reparo no Aparelho;

  - Finalizada: Quando o Funcionário tiver concluído o serviço no Aparelho;

  - Paga: Quando o Cliente tiver pago o pelo serviço;

- **Peça**:

  - a Peça é usada em um reparo de uma OS;

  - a Peça tem que ser rastreada no sistema para saber qual Funcionário usou ela e em qual OS é ela foi utilizada;

  - também deve ser possível rastrear a solicitação de uma Peça feita por um Funcionário ao Gerente;

- Fornecedor:

  - o Fornecedor é quem vende uma Peça para a Assistência Técnica;

  - a existência de um Fornecedor no sistema da Assistência é para que o Gerente tenha controle dos contatos e saiba a quem pedir determinada Peça;

- Solicitação de Peça:

  - Solicitada por um Funcionário para um Gerente.

  - Deve ser possível rastrear quem solicitou, a quem solicitou, quando solicitou, quando foi respondido, qual a quantidade, o que foi solicitado 

- Movimentação de estoque:

  - Ação realizada por um Funcionário quando retira uma Peça do estoque.

  - Deve ser possível rastrear quem retirou, quando retirou, o qual peça foi retirada, em qual serviço foi usado, a quantidade, a data e qual o tipo da movimentação

