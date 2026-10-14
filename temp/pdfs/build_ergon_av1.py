from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output' / 'pdf' / 'Ergon_Projeto_Integrador_AV1_Gabriel_Felix.pdf'
SCREENS = Path(__file__).parent / 'screens'
OUT.parent.mkdir(parents=True, exist_ok=True)

pdfmetrics.registerFont(TTFont('Segoe', r'C:\Windows\Fonts\segoeui.ttf'))
pdfmetrics.registerFont(TTFont('SegoeBold', r'C:\Windows\Fonts\segoeuib.ttf'))
pdfmetrics.registerFontFamily('Segoe', normal='Segoe', bold='SegoeBold')

W, H = 960, 540
BG = HexColor('#F5F7F3')
DARK = HexColor('#163B31')
GREEN = HexColor('#1E6A56')
MID = HexColor('#416A59')
PALE = HexColor('#E5F0E8')
PALE2 = HexColor('#EEF3EE')
TEXT = HexColor('#23372F')
MUTED = HexColor('#687C70')
WARM = HexColor('#E9A35F')
WHITE = HexColor('#FFFFFF')

c = canvas.Canvas(str(OUT), pagesize=(W, H), pageCompression=1)
c.setTitle('Ergon — Projeto Integrador AV1')
c.setAuthor('Gabriel Felix')
c.setSubject('Apresentação acadêmica do protótipo local Ergon')

def rect(x, y, w, h, fill, radius=0, stroke=None, sw=1):
    c.setLineWidth(sw)
    c.setFillColor(fill)
    c.setStrokeColor(stroke or fill)
    if radius:
        c.roundRect(x, y, w, h, radius, fill=1, stroke=int(stroke is not None))
    else:
        c.rect(x, y, w, h, fill=1, stroke=int(stroke is not None))

def line(x1, y1, x2, y2, color=PALE, width=1):
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.line(x1, y1, x2, y2)

def txt(s, x, y, size=18, color=TEXT, bold=False):
    c.setFillColor(color)
    c.setFont('SegoeBold' if bold else 'Segoe', size)
    c.drawString(x, y, s)

def para(s, x, top, width, size=17, leading=None, color=TEXT, bold=False):
    st = ParagraphStyle('p', fontName='SegoeBold' if bold else 'Segoe', fontSize=size,
                        leading=leading or size*1.32, textColor=color, spaceAfter=0)
    p = Paragraph(s, st)
    _, h = p.wrap(width, H)
    p.drawOn(c, x, top-h)
    return top-h

def bullet(s, x, top, width, size=17, gap=15):
    rect(x, top-10, 5, 5, GREEN, 2)
    bottom = para(s, x+18, top, width-18, size)
    return bottom-gap

def img(name, x, y, maxw, maxh, border=False):
    p = SCREENS / name
    im = ImageReader(str(p))
    iw, ih = im.getSize()
    scale = min(maxw/iw, maxh/ih)
    w, h = iw*scale, ih*scale
    if border:
        rect(x-2, y-2, w+4, h+4, WHITE, 8, PALE, 0.8)
    c.drawImage(im, x, y, width=w, height=h, mask='auto')
    return w, h

def base(num, title, subtitle=None):
    rect(0, 0, W, H, BG)
    txt('ERGON  /  PROJETO INTEGRADOR AV1', 48, 504, 11, GREEN, True)
    txt(title, 48, 448, 31, DARK, True)
    if subtitle:
        para(subtitle, 49, 429, 860, 14, color=MUTED)
    line(48, 45, 912, 45, HexColor('#D7E4DA'))
    txt('Gabriel Felix  ·  ADS  ·  Demonstração local', 48, 23, 10, MUTED)
    c.setFillColor(MUTED)
    c.setFont('Segoe', 10)
    c.drawRightString(912, 23, f'{num:02d} / 13')

def label(text, x, y, color=GREEN):
    txt(text.upper(), x, y, 11, color, True)

def photo_note(x=47):
    txt('Tela do frontend com dados ilustrativos; captura feita para esta apresentação.', x, 56, 10, MUTED)

# 1 — Identificação
rect(0, 0, W, H, DARK)
rect(50, 484, 54, 4, WARM, 2)
txt('TÓPICOS INTEGRADORES  ·  PROJETO INTEGRADOR AV1', 50, 458, 13, HexColor('#BDE3C8'), True)
txt('Ergon', 48, 300, 90, WHITE, True)
para('Da solicitação de orçamento ao acompanhamento da ordem de serviço.', 53, 264, 790, 28, 36, WHITE)
line(51, 143, 906, 143, HexColor('#45705E'))
txt('Sistema web para assistências técnicas independentes', 52, 110, 17, WHITE)
txt('Gabriel Felix  ·  Projeto individual', 52, 81, 15, HexColor('#BDE3C8'))
txt('Análise e Desenvolvimento de Sistemas  ·  Prof. Joseph Donald  ·  14/10/2026', 52, 52, 12, HexColor('#BDE3C8'))
c.showPage()

# 2 — Problema e objetivo
base(2, 'Problema e objetivo', 'Cenário de uso que motivou o protótipo')
label('Problema', 49, 386)
top = 360
for s in [
    'Pedido, diagnóstico, proposta e andamento podem ficar dispersos entre conversas e registros separados.',
    'Cliente e assistência precisam saber o que foi solicitado, decidido e executado, com datas e histórico.',
    'O público-alvo são assistências técnicas independentes e seus clientes.'
]: top = bullet(s, 50, top, 402, 16, 15)
rect(501, 166, 411, 220, PALE, 14)
label('Objetivo principal', 527, 354)
para('Reunir a jornada do atendimento em um fluxo único, do orçamento à OS e ao registro do pagamento.', 527, 325, 352, 22, 30, DARK, True)
para('Resultado esperado: mais rastreabilidade para a equipe e consulta clara para o cliente.', 527, 215, 340, 16, color=MID)
txt('Relação direta: cada decisão registrada alimenta a próxima etapa do atendimento.', 50, 105, 16, GREEN, True)
c.showPage()

# 3 — Escopo
base(3, 'Recorte da versão local', 'Funções previstas no protótipo acadêmico e visão posterior')
label('Nesta versão', 50, 387)
top = 361
for s in [
    '<b>Acesso e cadastros:</b> assistência e gerente, convite de funcionário, cliente e aparelho; edição e desativação lógica.',
    '<b>Orçamento:</b> solicitação iniciada pelo cliente, resposta da equipe, email e decisão por link em até 48 horas.',
    '<b>OS:</b> nasce da aprovação; acompanha reparo, entrega, cancelamento ou desistência e pagamento registrado manualmente.'
]: top = bullet(s, 50, top, 522, 15.2, 13)
rect(613, 193, 299, 186, PALE2, 13)
label('Depois', 635, 350)
top = 324
for s in ['Atendimento iniciado pela equipe na loja', 'Estoque, financeiro e relatórios', 'Publicação e metas de operação']:
    top = bullet(s, 635, top, 253, 14.5, 10)
line(50, 146, 912, 146, HexColor('#D7E4DA'))
label('Perfis', 50, 117)
para('<b>Gerente:</b> administra a assistência e a equipe', 50, 105, 270, 14.5, color=TEXT)
para('<b>Funcionário:</b> responde orçamento e conduz a OS', 351, 105, 286, 14.5, color=TEXT)
para('<b>Cliente:</b> solicita, decide e acompanha', 680, 105, 229, 14.5, color=TEXT)
c.showPage()

# 4 — Acesso e cadastro
base(4, 'Telas de acesso e cadastro', 'A assistência cria o primeiro gerente; equipe e cliente acessam seus próprios perfis')
label('Cadastrar assistência', 50, 392)
label('Entrar', 360, 392)
label('Recuperar senha', 658, 392)
img('06-cadastro-assistencia.png', 51, 78, 280, 300, True)
img('07-login.png', 361, 133, 256, 245, True)
img('08-recuperacao.png', 660, 78, 252, 300, True)
para('Dados da assistência e senha do primeiro gerente.', 50, 70, 281, 12, color=MUTED)
para('Perfil, assistência, email e senha.', 360, 124, 255, 12, color=MUTED)
para('Código por email e nova senha.', 658, 70, 252, 12, color=MUTED)
c.showPage()

# 4 — Fluxo
base(5, 'A jornada principal', 'O cliente inicia o orçamento; a equipe responde; a OS depende da aprovação')
steps = [
    ('01', 'Solicitação', 'Cliente informa contato, aparelho e defeito.'),
    ('02', 'Análise', 'Equipe registra diagnóstico, valores e previsão.'),
    ('03', 'Proposta', 'Email entrega um link individual para o Ergon.'),
]
x_positions = [50, 353, 656]
for x, (n, title, desc) in zip(x_positions, steps):
    rect(x, 267, 254, 112, WHITE, 12, HexColor('#D8E6DC'))
    txt(n, x+18, 349, 15, GREEN, True)
    txt(title, x+60, 347, 20, DARK, True)
    para(desc, x+18, 328, 219, 14.5, color=MID)
line(304, 322, 345, 322, GREEN, 2)
line(607, 322, 648, 322, GREEN, 2)
rect(50, 128, 545, 104, PALE, 12)
txt('Aprova em até 48 h', 69, 199, 20, DARK, True)
para('O sistema cria uma única OS; a equipe conduz reparo e entrega e informa o pagamento realizado fora do sistema.', 69, 179, 505, 15.5, color=MID)
rect(625, 128, 285, 104, HexColor('#F6EDE4'), 12)
txt('Recusa ou vence', 644, 199, 20, DARK, True)
para('O orçamento termina sem criar OS.', 644, 179, 244, 15.5, color=MID)
txt('Emails do fluxo: confirmação da solicitação, proposta e confirmação da OS; senha por código.', 50, 81, 14, GREEN, True)
c.showPage()

# 5 — Tela de entrada
base(6, 'Tela 1  ·  solicitação online')
label('Ação do cliente', 50, 386)
top = 356
for s in [
    'Seleciona a assistência e informa nome, telefone, email, marca, modelo e defeito.',
    'O envio cria cliente, aparelho e orçamento vinculados à mesma assistência.',
    'Campos obrigatórios e email repetido geram orientação de correção.'
]: top = bullet(s, 50, top, 375, 17, 17)
rect(50, 91, 370, 94, PALE, 10)
para('<b>Confirmação:</b> solicitação registrada; confira o email.<br/><b>Erro:</b> email já cadastrado; recuperar senha.', 68, 166, 335, 14.5, color=DARK)
img('01b-formulario.png', 545, 71, 340, 376, True)
photo_note()
c.showPage()

# 6 — Tela de resposta
base(7, 'Tela 2  ·  resposta da equipe')
label('Ação do funcionário', 50, 386)
top = 357
for s in [
    'O painel mostra solicitações em análise e ordens em andamento.',
    'A equipe registra diagnóstico, mão de obra, peças e previsão de conclusão.',
    'Ao responder, o sistema envia a proposta por email; a correção é possível antes da decisão.'
]: top = bullet(s, 50, top, 375, 17, 17)
rect(50, 104, 365, 76, PALE, 10)
para('Regra: só o cliente inicia o orçamento nesta versão.', 68, 160, 335, 16, color=DARK, bold=True)
img('03b-resposta.png', 481, 74, 431, 372, True)
photo_note()
c.showPage()

# 7 — Tela de decisão
base(8, 'Tela 3  ·  decisão do cliente')
label('Ação pelo link recebido', 50, 386)
top = 356
for s in [
    'O link abre a proposta dentro do Ergon, sem exigir login.',
    'O cliente vê diagnóstico, valores, total, previsão e prazo para decidir.',
    'Aprovar cria a OS; recusar encerra o orçamento; vencimento bloqueia a decisão.'
]: top = bullet(s, 50, top, 374, 17, 17)
rect(50, 100, 366, 75, PALE, 10)
para('Depois da aprovação, o mesmo link mostra o andamento da OS.', 68, 155, 333, 15.5, color=DARK, bold=True)
img('04b-proposta.png', 477, 64, 432, 385, True)
photo_note()
c.showPage()

# 9 — Área do cliente
base(9, 'Área do cliente  ·  acompanhamento', 'Consulta de orçamentos e ordens de serviço após a definição da senha')
label('Visão do cliente', 50, 386)
top = 357
for s in [
    'O cliente consulta seus orçamentos, aparelhos e OS em um único painel.',
    'Pode iniciar outra solicitação usando um aparelho já cadastrado.',
    'O status da OS também permanece acessível pelo link do orçamento.'
]: top = bullet(s, 50, top, 355, 16.5, 12)
label('Histórico no painel', 50, 163)
img('09b-acompanhamento.png', 50, 72, 356, 78, True)
img('09-area-cliente.png', 432, 86, 478, 335, True)
photo_note()
c.showPage()

# 8 — Tela OS
base(10, 'Tela 4  ·  ordem de serviço e pagamento')
label('Ação da equipe', 50, 386)
top = 356
for s in [
    'A OS mantém vínculo com cliente, aparelho e orçamento aprovado.',
    'A equipe registra recebimento, responsável, reparo, previsão e entrega.',
    'O pagamento é lançado manualmente com valor, forma e data; o Ergon não cobra o cliente.'
]: top = bullet(s, 50, top, 383, 16, 12)
label('Registro manual do pagamento', 50, 160)
img('05c-pagamento.png', 50, 70, 372, 80, True)
img('05b-os-card.png', 545, 65, 335, 340, True)
photo_note()
c.showPage()

# 9 — Arquitetura
base(11, 'Como o sistema foi construído', 'Execução local com interface, API, banco e serviço de email')
blocks = [
    (50, 'React + Vite', 'Telas do cliente e da equipe;<br/>envia e recebe JSON por HTTP.'),
    (354, 'Flask', 'Rotas, autenticação e regras;<br/>GET, POST, PUT e DELETE.'),
    (658, 'PostgreSQL', 'Tabelas, chaves e histórico;<br/>Flask consulta o banco com SQL.'),
]
for x, title, desc in blocks:
    rect(x, 260, 252, 129, WHITE, 12, HexColor('#D8E6DC'))
    txt(title, x+21, 349, 23, DARK, True)
    para(desc, x+21, 328, 208, 15, color=MID)
line(302, 324, 346, 324, GREEN, 2)
line(606, 324, 650, 324, GREEN, 2)
rect(330, 136, 300, 86, PALE, 12)
txt('Email / SMTP', 351, 189, 19, DARK, True)
para('Confirmações, proposta, convite e recuperação de senha.', 351, 172, 258, 13.5, color=MID)
line(480, 260, 480, 223, GREEN, 2)
para('<b>Proteção:</b> JWT para sessões; hash para senhas, códigos e tokens; permissões e dados separados por assistência.', 50, 117, 850, 16, color=TEXT)
txt('Versionamento: Git, branch prototipo-local. Credenciais ficam em variáveis de ambiente.', 50, 70, 13.5, MUTED)
c.showPage()

# 10 — Estado real
base(12, 'Estado real do protótipo', 'Separação entre código escrito, checagens executadas e validação pendente')
cols = [
    (50, 'Implementado em código', ['Jornada cliente → proposta → decisão → OS', 'Cadastros e perfis; JWT e recuperação', 'Emails e registro manual do pagamento']),
    (356, 'Já verificado', ['Build do React e importação do Flask', 'Rota de saúde e testes de autenticação', 'Envio de prova ao capturador SMTP local']),
    (662, 'Próxima verificação', ['Jornada completa com PostgreSQL de teste', 'Entrega por SMTP real', 'Fluxo visual no navegador e falhas de envio']),
]
for x, title, items in cols:
    rect(x, 163, 254, 215, WHITE, 12, HexColor('#D8E6DC'))
    para(title, x+18, 350, 218, 18, color=DARK, bold=True)
    top = 304
    for item in items:
        top = bullet(item, x+18, top, 217, 14.3, 11)
rect(50, 77, 866, 59, PALE, 10)
para('As telas exibidas são capturas do frontend com dados ilustrativos. A integração ponta a ponta com PostgreSQL e email externo ainda não foi comprovada nesta versão.', 68, 121, 830, 14.5, color=DARK)
c.showPage()

# 11 — Planejamento
base(13, 'Planejamento, entregáveis e riscos')
label('Etapas', 50, 386)
stages = [
    ('1', 'Requisitos e recorte', 'Concluído'),
    ('2', 'Interface, API e SQL', 'Código implementado'),
    ('3', 'Integração e roteiro de teste', 'Próximo passo'),
]
for i, (n, title, state) in enumerate(stages):
    y = 336 - i*69
    rect(50, y-18, 34, 34, GREEN, 17)
    txt(n, 61, y-7, 16, WHITE, True)
    txt(title, 101, y+3, 18, DARK, True)
    txt(state, 101, y-17, 13, MUTED)
rect(509, 205, 401, 176, PALE, 12)
label('Responsável e entregáveis', 530, 352)
para('<b>Gabriel Felix:</b> requisitos, interface, API, banco, testes, documentação e apresentação.', 530, 329, 348, 15.3, color=TEXT)
para('<b>Entregáveis:</b> repositório, esquema SQL, protótipo local e esta apresentação em PDF.', 530, 262, 348, 15.3, color=TEXT)
line(50, 175, 912, 175, HexColor('#D7E4DA'))
label('Riscos e resposta', 50, 145)
para('<b>Banco e email:</b> preparar PostgreSQL de teste e SMTP de captura antes da demonstração. <b>Prazo de 48 h e permissões:</b> testar aprovação, recusa, expiração e separação entre assistências.', 50, 122, 854, 15, color=TEXT)
c.showPage()

c.save()
print(OUT)
