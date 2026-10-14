const { chromium } = require('C:/Users/Gabriel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('fs');
const path = require('path');

const out = path.resolve(__dirname, 'screens');
fs.mkdirSync(out, { recursive: true });
const assistance = { Id: 1, Nome: 'Oficina Aurora', Documento: '00.000.000/0001-00', Email: 'contato@exemplo.test', Telefone: '(85) 99999-0000', Endereco: 'Fortaleza' };
const budget = { Id: 42, NomeCliente: 'Ana Lima', MarcaAparelho: 'Samsung', ModeloAparelho: 'Galaxy A54', Origem: 'Online', Status: 'EmAnalise', DescricaoProblemaCliente: 'O aparelho não carrega.' };
const order = { Id: 18, NomeCliente: 'Ana Lima', MarcaAparelho: 'Samsung', ModeloAparelho: 'Galaxy A54', IdOrcamento: 42, Status: 'ReparoConcluido', DescricaoProblemaCliente: 'O aparelho não carrega.', DataPrevisaoConclusao: '2026-10-20' };
const proposal = { Id: 42, NomeCliente: 'Ana Lima', Marca: 'Samsung', Modelo: 'Galaxy A54', DescricaoProblemaCliente: 'O aparelho não carrega.', DiagnosticoFuncionario: 'Conector de carga danificado.', ValorMaoDeObra: 80, ValorPecas: 45, PrazoConclusao: '2026-10-20', Status: 'AguardandoAprovacao', PrazoParaAprovacaoCliente: '2026-10-16T15:00:00' };
const base = 'http://localhost:5174/';

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', args: ['--no-sandbox'] });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1.4, locale: 'pt-BR' });
  await context.route('**/api/**', async route => {
    const u = new URL(route.request().url());
    const p = u.pathname;
    let body;
    let status = 200;
    if (p === '/api/assistencias') body = [{ Id: 1, Nome: assistance.Nome }];
    else if (p === '/api/assistencias/1') body = assistance;
    else if (p === '/api/clientes') body = [{ Id: 7, Nome: 'Ana Lima', Email: 'ana@exemplo.test', Telefone: '(85) 99999-1111', Ativo: true }];
    else if (p === '/api/orcamentos') body = [budget];
    else if (p === '/api/ordens-servico') body = [order];
    else if (p === '/api/funcionarios') body = [{ Id: 3, Nome: 'Gabriel', Email: 'gabriel@exemplo.test', Gerente: true, Ativo: true }];
    else if (p === '/api/clientes/me/orcamentos') body = [{ Id: 42, MarcaAparelho: 'Samsung', ModeloAparelho: 'Galaxy A54', DescricaoProblemaCliente: 'O aparelho não carrega.', Status: 'Aprovado' }];
    else if (p === '/api/clientes/me/ordens-servico') body = [{ Id: 18, MarcaAparelho: 'Samsung', ModeloAparelho: 'Galaxy A54', IdOrcamento: 42, Status: 'EmReparo' }];
    else if (p === '/api/clientes/me/aparelhos') body = [{ Id: 9, Marca: 'Samsung', Modelo: 'Galaxy A54', Ativo: true }];
    else if (p.startsWith('/api/orcamentos/acesso/')) body = proposal;
    else if (p === '/api/assistencias/1/solicitacoes' && route.request().method() === 'POST') { status = 409; body = { erro: 'Este email já está cadastrado nesta assistência.' }; }
    else body = {};
    await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
  });
  const page = await context.newPage();
  await page.goto(base, { waitUntil: 'networkidle' });
  await page.locator('select').first().selectOption('1');
  await page.screenshot({ path: path.join(out, '01-solicitacao.png') });
  await page.locator('.card.request').screenshot({ path: path.join(out, '01b-formulario.png') });

  await page.getByRole('button', { name: 'Criar assistência' }).click();
  await page.locator('.auth.wide').screenshot({ path: path.join(out, '06-cadastro-assistencia.png') });
  await page.getByRole('button', { name: 'Entrar' }).first().click();
  await page.locator('.auth').screenshot({ path: path.join(out, '07-login.png') });
  await page.getByRole('button', { name: 'Recuperar senha' }).click();
  await page.locator('.auth').screenshot({ path: path.join(out, '08-recuperacao.png') });
  await page.getByRole('button', { name: 'Solicitar orçamento' }).first().click();

  await page.locator('input[type=email]').first().fill('ana@exemplo.test');
  await page.locator('input').nth(0).fill('Ana Lima');
  await page.locator('input').nth(1).fill('(85) 99999-1111');
  await page.locator('input').nth(3).fill('Samsung');
  await page.locator('input').nth(4).fill('Galaxy A54');
  await page.locator('textarea').first().fill('O aparelho não carrega.');
  await page.getByRole('button', { name: 'Enviar solicitação' }).click();
  await page.locator('.alert.error').waitFor();
  await page.screenshot({ path: path.join(out, '02-validacao.png') });
  await page.locator('.alert.error').screenshot({ path: path.join(out, '02b-erro.png') });

  await page.evaluate(() => sessionStorage.setItem('ergon-session', JSON.stringify({ token: 'exemplo', usuario: { tipo: 'funcionario', assistenciaId: 1, gerente: true, nome: 'Gabriel' } })));
  await page.reload({ waitUntil: 'networkidle' });
  await page.getByRole('button', { name: 'Painel' }).click();
  await page.getByText('Responder orçamento').waitFor();
  await page.screenshot({ path: path.join(out, '03-equipe-orcamento.png') });
  await page.locator('.budget-list').evaluate(el => { el.style.maxWidth = '760px'; });
  await page.locator('.budget-list').screenshot({ path: path.join(out, '03b-resposta.png') });
  await page.getByRole('button', { name: 'Ordens de serviço' }).click();
  await page.getByText('Registrar pagamento').waitFor();
  await page.screenshot({ path: path.join(out, '05-os-pagamento.png') });
  await page.locator('.order-grid .card').first().screenshot({ path: path.join(out, '05b-os-card.png') });
  await page.getByRole('button', { name: 'Registrar pagamento' }).locator('..').screenshot({ path: path.join(out, '05c-pagamento.png') });

  await page.evaluate(() => sessionStorage.setItem('ergon-session', JSON.stringify({ token: 'exemplo-cliente', usuario: { tipo: 'cliente', assistenciaId: 1, nome: 'Ana' } })));
  await page.reload({ waitUntil: 'networkidle' });
  await page.getByRole('button', { name: 'Painel' }).click();
  await page.getByText('Meus orçamentos').waitFor();
  await page.screenshot({ path: path.join(out, '09-area-cliente.png') });
  await page.locator('.grid.two').last().screenshot({ path: path.join(out, '09b-acompanhamento.png') });

  const decision = await context.newPage();
  await decision.goto(base + '?orcamento=exemplo-ilustrativo', { waitUntil: 'networkidle' });
  await decision.getByText('Aprovar orçamento').waitFor();
  await decision.screenshot({ path: path.join(out, '04-decisao-cliente.png') });
  await decision.locator('.card').screenshot({ path: path.join(out, '04b-proposta.png') });
  await browser.close();
  console.log(out);
})().catch(error => { console.error(error); process.exit(1); });
