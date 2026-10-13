import React, { useEffect, useState } from 'react'
import { api } from './api'

const readSession = () => {
  try { return JSON.parse(sessionStorage.getItem('ergon-session') || 'null') } catch { return null }
}

const fields = {
  assistencia: [
    ['nome', 'Nome da assistência', 'text', true], ['documento', 'Documento', 'text', true],
    ['email', 'Email', 'email', true], ['telefone', 'Telefone', 'tel'], ['endereco', 'Endereço'],
  ],
  gerente: [
    ['nome', 'Nome do gerente', 'text', true], ['documento', 'Documento do gerente', 'text', true],
    ['email', 'Email do gerente', 'email', true], ['telefone', 'Telefone', 'tel'],
    ['senha', 'Senha (mínimo 10 caracteres)', 'password', true],
  ],
  cliente: [
    ['nome', 'Nome', 'text', true], ['telefone', 'Telefone', 'tel', true],
    ['email', 'Email', 'email', true], ['documento', 'Documento'], ['endereco', 'Endereço'],
  ],
  funcionario: [
    ['nome', 'Nome', 'text', true], ['documento', 'Documento', 'text', true],
    ['email', 'Email', 'email', true], ['telefone', 'Telefone', 'tel'],
  ],
  solicitacao: [
    ['nome', 'Nome', 'text', true], ['telefone', 'Telefone', 'tel', true],
    ['email', 'Email', 'email', true], ['marca', 'Marca', 'text', true],
    ['modelo', 'Modelo', 'text', true], ['defeito', 'Defeito', 'textarea', true],
  ],
}

function Inputs({ schema, values, setValues }) {
  return <div className="fields">{schema.map(([key, label, type = 'text', required]) =>
    <label key={key}>{label}
      {type === 'textarea'
        ? <textarea required={required} value={values[key] ?? ''} onChange={e => setValues({ ...values, [key]: e.target.value })} />
        : <input type={type} required={required} value={values[key] ?? ''} onChange={e => setValues({ ...values, [key]: e.target.value })} />}
    </label>,
  )}</div>
}

function Card({ title, children, className = '' }) {
  return <section className={`card ${className}`}><h2>{title}</h2>{children}</section>
}

function App() {
  const accessToken = new URLSearchParams(window.location.search).get('orcamento')
  const [session, setSession] = useState(readSession)
  const [assistances, setAssistances] = useState([])
  const [view, setView] = useState('inicio')
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [publicForm, setPublicForm] = useState({})
  const [assistanceId, setAssistanceId] = useState('')
  const [loginForm, setLoginForm] = useState({})
  const [newAssistance, setNewAssistance] = useState({})
  const [newManager, setNewManager] = useState({})
  const [proposal, setProposal] = useState(null)
  const [dashboard, setDashboard] = useState(null)
  const [tab, setTab] = useState('orcamentos')

  const run = async (fn, success) => {
    setError('')
    setNotice('')
    try {
      const result = await fn()
      if (success) setNotice(success)
      return result
    } catch (cause) {
      setError(cause.message)
      return null
    }
  }

  const loadAssistances = async () => {
    try { setAssistances(await api('/assistencias')) }
    catch (cause) { setError(cause.message) }
  }
  const loadProposal = async () => {
    try { setProposal(await api(`/orcamentos/acesso/${encodeURIComponent(accessToken)}`)) }
    catch (cause) { setError(cause.message) }
  }
  const loadDashboard = async (activeSession = session) => {
    if (!activeSession) return
    const bearer = { token: activeSession.token }
    const id = activeSession.usuario.assistenciaId
    try {
      const [assistance, clients, budgets, orders, employees] = await Promise.all([
        api(`/assistencias/${id}`, bearer),
        api('/clientes', bearer),
        api('/orcamentos', bearer),
        api('/ordens-servico', bearer),
        api('/funcionarios', bearer),
      ])
      setDashboard({ assistance, clients, budgets, orders, employees })
    } catch (cause) { setError(cause.message) }
  }

  useEffect(() => {
    if (accessToken) loadProposal()
    else { loadAssistances(); if (session) loadDashboard(session) }
  }, [])

  const login = async e => {
    e.preventDefault()
    const result = await run(() => api('/login', { method: 'POST', data: {
      assistenciaId: Number(loginForm.assistenciaId), email: loginForm.email, senha: loginForm.senha,
    } }))
    if (result) {
      sessionStorage.setItem('ergon-session', JSON.stringify(result))
      setSession(result); setView('painel'); await loadDashboard(result)
    }
  }

  const register = async e => {
    e.preventDefault()
    const result = await run(() => api('/assistencias', {
      method: 'POST', data: { ...newAssistance, primeiroGerente: newManager },
    }), 'Assistência criada. Entre com o email do gerente.')
    if (result) {
      await loadAssistances()
      setLoginForm({ assistenciaId: result.assistencia.Id, email: newManager.email })
      setView('login')
    }
  }

  const submitRequest = async e => {
    e.preventDefault()
    const result = await run(() => api(`/assistencias/${assistanceId}/solicitacoes`, {
      method: 'POST', data: publicForm,
    }), 'Solicitação enviada. A assistência enviará a proposta por email.')
    if (result) setPublicForm({})
  }

  const decidePublic = async approve => {
    const result = await run(() => api(`/orcamentos/acesso/${encodeURIComponent(accessToken)}/decisao`, {
      method: 'POST', data: { aprovar: approve },
    }), approve ? 'Orçamento aprovado. A ordem de serviço foi criada.' : 'Orçamento recusado.')
    await loadProposal()
  }

  const logout = async () => {
    await run(() => api('/logout', { method: 'POST', token: session.token }))
    sessionStorage.removeItem('ergon-session')
    setSession(null); setDashboard(null); setView('inicio')
  }

  const act = async (path, method, data, success) => {
    const result = await run(() => api(path, { method, data, token: session.token }), success)
    await loadDashboard()
    return result
  }

  if (accessToken) return <main className="shell narrow">
    <header className="brand"><span className="mark">E</span><span>ergon</span></header>
    <div className="eyebrow">ÁREA DO CLIENTE</div>
    <h1>Seu orçamento</h1>
    {error && <p className="alert error">{error}</p>}{notice && <p className="alert">{notice}</p>}
    {!proposal ? <p>Carregando proposta…</p> : <Card title={`Orçamento #${proposal.Id}`}>
      <div className="detail">
        <p><strong>Cliente</strong><span>{proposal.NomeCliente}</span></p>
        <p><strong>Aparelho</strong><span>{proposal.Marca} {proposal.Modelo}</span></p>
        <p><strong>Defeito informado</strong><span>{proposal.DescricaoProblemaCliente}</span></p>
        <p><strong>Diagnóstico</strong><span>{proposal.DiagnosticoFuncionario}</span></p>
        <p><strong>Mão de obra</strong><span>{currency(proposal.ValorMaoDeObra)}</span></p>
        <p><strong>Peças</strong><span>{currency(proposal.ValorPecas)}</span></p>
        <p><strong>Total</strong><span>{currency(Number(proposal.ValorMaoDeObra) + Number(proposal.ValorPecas))}</span></p>
        <p><strong>Previsão</strong><span>{formatDate(proposal.PrazoConclusao)}</span></p>
        <p><strong>Status</strong><span className="pill">{statusLabel(proposal.Status)}</span></p>
        {proposal.Status === 'AguardandoAprovacao' && <p><strong>Decidir até</strong><span>{formatDate(proposal.PrazoParaAprovacaoCliente)}</span></p>}
        {proposal.IdOrdemServico && <p><strong>OS #{proposal.IdOrdemServico}</strong><span>{statusLabel(proposal.StatusOS)}{proposal.DataEntregaAparelho ? ' · aparelho entregue' : ''}</span></p>}
      </div>
      {proposal.Status === 'AguardandoAprovacao' && <div className="actions">
        <button onClick={() => decidePublic(true)}>Aprovar orçamento</button>
        <button className="secondary" onClick={() => decidePublic(false)}>Recusar</button>
      </div>}
    </Card>}
  </main>

  return <main className="shell">
    <header className="topbar">
      <div className="brand"><span className="mark">E</span><span>ergon</span></div>
      <nav>
        <button className="nav" onClick={() => { setView('inicio'); setError('') }}>Solicitar orçamento</button>
        {session ? <><button className="nav" onClick={() => setView('painel')}>Painel</button><button className="nav" onClick={logout}>Sair</button></>
          : <><button className="nav" onClick={() => setView('login')}>Entrar</button><button className="nav" onClick={() => setView('cadastro')}>Criar assistência</button></>}
      </nav>
    </header>
    {error && <p className="alert error">{error}</p>}{notice && <p className="alert">{notice}</p>}
    {view === 'inicio' && <div className="landing">
      <div className="hero"><div className="eyebrow">ASSISTÊNCIA TÉCNICA SEM COMPLICAÇÃO</div>
        <h1>Seu aparelho em boas mãos.</h1>
        <p>Conte o que aconteceu. A assistência analisa e envia o orçamento para seu email. Você decide pelo link recebido.</p>
        <div className="steps"><span>01 Solicite</span><span>02 Avalie</span><span>03 Acompanhe</span></div>
      </div>
      <Card title="Solicitar orçamento" className="request">
        <form onSubmit={submitRequest}>
          <label>Assistência técnica<select required value={assistanceId} onChange={e => setAssistanceId(e.target.value)}>
            <option value="">Selecione</option>{assistances.map(a => <option key={a.Id} value={a.Id}>{a.Nome}</option>)}
          </select></label>
          <Inputs schema={fields.solicitacao} values={publicForm} setValues={setPublicForm} />
          <button type="submit">Enviar solicitação</button>
        </form>
      </Card>
    </div>}
    {view === 'login' && <Card title="Acesso da equipe" className="auth">
      <p className="muted">Use os dados cadastrados pelo gerente da assistência.</p>
      <form onSubmit={login}>
        <label>Assistência<select required value={loginForm.assistenciaId ?? ''} onChange={e => setLoginForm({ ...loginForm, assistenciaId: e.target.value })}>
          <option value="">Selecione</option>{assistances.map(a => <option key={a.Id} value={a.Id}>{a.Nome}</option>)}
        </select></label>
        <Inputs schema={[[ 'email', 'Email', 'email', true ], [ 'senha', 'Senha', 'password', true ]]} values={loginForm} setValues={setLoginForm} />
        <button>Entrar</button>
      </form>
    </Card>}
    {view === 'cadastro' && <Card title="Cadastrar assistência" className="auth wide">
      <form onSubmit={register}>
        <h3>Dados da assistência</h3><Inputs schema={fields.assistencia} values={newAssistance} setValues={setNewAssistance} />
        <h3>Primeiro gerente</h3><Inputs schema={fields.gerente} values={newManager} setValues={setNewManager} />
        <button>Criar assistência</button>
      </form>
    </Card>}
    {view === 'painel' && session && dashboard && <div className="workspace">
      <div className="workspace-head"><div><div className="eyebrow">PAINEL DA EQUIPE</div><h1>{dashboard.assistance.Nome}</h1>
        <p>Olá, {session.usuario.nome}. Gerencie atendimentos, clientes e ordens de serviço.</p></div>
        <button className="secondary" onClick={() => loadDashboard()}>Atualizar</button></div>
      <div className="stats"><div><strong>{dashboard.budgets.filter(b => b.Status === 'EmAnalise').length}</strong><span>Em análise</span></div>
        <div><strong>{dashboard.budgets.filter(b => b.Status === 'AguardandoAprovacao').length}</strong><span>Aguardando cliente</span></div>
        <div><strong>{dashboard.orders.filter(o => o.Status !== 'Paga').length}</strong><span>OS em andamento</span></div></div>
      <div className="tabs">{[
        ['orcamentos', 'Orçamentos'], ['ordens', 'Ordens de serviço'], ['clientes', 'Clientes'],
        ...(session.usuario.gerente ? [['funcionarios', 'Funcionários'], ['assistencia', 'Assistência']] : []),
      ].map(([id, label]) => <button key={id} className={tab === id ? 'active' : ''} onClick={() => setTab(id)}>{label}</button>)}</div>
      {tab === 'orcamentos' && <Budgets data={dashboard} act={act} />}
      {tab === 'ordens' && <Orders data={dashboard} act={act} />}
      {tab === 'clientes' && <Clients data={dashboard} act={act} />}
      {tab === 'funcionarios' && <Employees data={dashboard} act={act} />}
      {tab === 'assistencia' && <Assistance data={dashboard} act={act} logout={logout} />}
    </div>}
  </main>
}

function Clients({ data, act }) {
  const [form, setForm] = useState({})
  const [editing, setEditing] = useState(null)
  const [deviceClient, setDeviceClient] = useState(null)
  const [deviceForm, setDeviceForm] = useState({})
  const [devices, setDevices] = useState([])
  const [clientOrders, setClientOrders] = useState([])
  const save = async e => {
    e.preventDefault()
    const result = await act(editing ? `/clientes/${editing}` : '/clientes',
      editing ? 'PUT' : 'POST', form, editing ? 'Cliente atualizado.' : 'Cliente cadastrado.')
    if (result) { setForm({}); setEditing(null) }
  }
  const selectClient = async client => {
    setDeviceClient(client)
    try {
      const token = readSession()?.token
      const [d, o] = await Promise.all([
        api(`/clientes/${client.Id}/aparelhos`, { token }),
        api(`/clientes/${client.Id}/ordens-servico`, { token }),
      ])
      setDevices(d); setClientOrders(o)
    } catch { setDevices([]); setClientOrders([]) }
  }
  return <div className="grid two"><Card title={editing ? 'Editar cliente' : 'Novo cliente'}>
    <form onSubmit={save}><Inputs schema={fields.cliente} values={form} setValues={setForm} />
      <div className="actions"><button>Salvar</button>{editing && <button type="button" className="secondary" onClick={() => { setEditing(null); setForm({}) }}>Cancelar</button>}</div></form>
  </Card><Card title="Clientes"><div className="list">{data.clients.map(c => <div className="row" key={c.Id}>
    <div><strong>{c.Nome}</strong><small>{c.Email} · {c.Telefone} · {c.Ativo ? 'Ativo' : 'Inativo'}</small></div>
    <div className="row-actions"><button className="textbutton" onClick={() => selectClient(c)}>Aparelhos / OS</button>
      <button className="textbutton" onClick={() => { setEditing(c.Id); setForm({ nome: c.Nome, documento: c.Documento || '', email: c.Email, telefone: c.Telefone, endereco: c.Endereco || '' }) }}>Editar</button>
      {c.Ativo && <button className="textbutton danger" onClick={() => { if (window.confirm('Desativar este cliente?')) act(`/clientes/${c.Id}`, 'DELETE', undefined, 'Cliente desativado.') }}>Desativar</button>}</div>
  </div>)}</div></Card>
    {deviceClient && <Card title={`Aparelhos e OS · ${deviceClient.Nome}`} className="full">
      <h3>Novo aparelho</h3><form className="inline-form" onSubmit={async e => {
        e.preventDefault()
        const result = await act(`/clientes/${deviceClient.Id}/aparelhos`, 'POST', deviceForm, 'Aparelho cadastrado.')
        if (result) { setDeviceForm({}); selectClient(deviceClient) }
      }}><Inputs schema={[[ 'marca', 'Marca', 'text', true ], [ 'modelo', 'Modelo', 'text', true ], [ 'tipoAparelho', 'Tipo' ]]} values={deviceForm} setValues={setDeviceForm} /><button>Adicionar</button></form>
      <h3>Aparelhos</h3>{devices.length ? devices.map(d => <p key={d.Id}>#{d.Id} · {d.Marca} {d.Modelo}</p>) : <p className="muted">Nenhum aparelho.</p>}
      <h3>Ordens de serviço deste cliente</h3>{clientOrders.length ? clientOrders.map(o => <p key={o.Id}>OS #{o.Id} · {o.MarcaAparelho} {o.ModeloAparelho} · {statusLabel(o.Status)}</p>) : <p className="muted">Nenhuma OS.</p>}
    </Card>}
  </div>
}

function Employees({ data, act }) {
  const [form, setForm] = useState({})
  const [editing, setEditing] = useState(null)
  const save = async e => {
    e.preventDefault()
    const result = await act(editing ? `/funcionarios/${editing}` : '/funcionarios',
      editing ? 'PUT' : 'POST', { ...form, gerente: !!form.gerente, ativo: form.ativo !== false },
      editing ? 'Funcionário atualizado.' : 'Funcionário cadastrado.')
    if (result) { setForm({}); setEditing(null) }
  }
  return <div className="grid two"><Card title={editing ? 'Editar funcionário' : 'Novo funcionário'}>
    <form onSubmit={save}><Inputs schema={fields.funcionario} values={form} setValues={setForm} />
      {!editing && <Inputs schema={[[ 'senha', 'Senha (mínimo 10 caracteres)', 'password', true ]]} values={form} setValues={setForm} />}
      <label className="check"><input type="checkbox" checked={!!form.gerente} onChange={e => setForm({ ...form, gerente: e.target.checked })} /> Gerente</label>
      {editing && <label className="check"><input type="checkbox" checked={form.ativo !== false} onChange={e => setForm({ ...form, ativo: e.target.checked })} /> Ativo</label>}
      <div className="actions"><button>Salvar</button>{editing && <button type="button" className="secondary" onClick={() => { setEditing(null); setForm({}) }}>Cancelar</button>}</div>
    </form></Card><Card title="Equipe"><div className="list">{data.employees.map(f => <div className="row" key={f.Id}>
      <div><strong>{f.Nome}</strong><small>{f.Email} · {f.Gerente ? 'Gerente' : 'Funcionário'} · {f.Ativo ? 'Ativo' : 'Inativo'}</small></div>
      <div className="row-actions"><button className="textbutton" onClick={() => { setEditing(f.Id); setForm({ nome: f.Nome, documento: f.Documento, email: f.Email, telefone: f.Telefone || '', gerente: f.Gerente, ativo: f.Ativo }) }}>Editar</button>
        {f.Ativo && <button className="textbutton danger" onClick={() => { if (window.confirm('Desativar este funcionário?')) act(`/funcionarios/${f.Id}`, 'DELETE', undefined, 'Funcionário desativado.') }}>Desativar</button>}</div>
    </div>)}</div></Card></div>
}

function Assistance({ data, act, logout }) {
  const a = data.assistance
  const [form, setForm] = useState({ nome: a.Nome, documento: a.Documento, email: a.Email, telefone: a.Telefone || '', endereco: a.Endereco || '' })
  return <Card title="Dados da assistência" className="auth wide"><form onSubmit={e => { e.preventDefault(); act(`/assistencias/${a.Id}`, 'PUT', form, 'Assistência atualizada.') }}>
    <Inputs schema={fields.assistencia} values={form} setValues={setForm} /><button>Salvar alterações</button>
  </form><hr /><button className="danger-button" onClick={async () => {
    if (window.confirm('Desativar a assistência? O acesso da equipe será encerrado.')) {
      const result = await act(`/assistencias/${a.Id}`, 'DELETE', undefined, 'Assistência desativada.')
      if (result) logout()
    }
  }}>Desativar assistência</button></Card>
}

function Budgets({ data, act }) {
  const [newForm, setNewForm] = useState({ origem: 'LojaImediata' })
  const [devices, setDevices] = useState([])
  const [responses, setResponses] = useState({})
  const [decisions, setDecisions] = useState({})
  const selectClient = async value => {
    setNewForm({ ...newForm, clienteId: value, aparelhoId: '' })
    if (!value) { setDevices([]); return }
    try { setDevices(await api(`/clientes/${value}/aparelhos`, { token: readSession()?.token })) }
    catch { setDevices([]) }
  }
  return <div className="grid two"><Card title="Orçamento na loja">
    <form onSubmit={async e => {
      e.preventDefault()
      const result = await act('/orcamentos', 'POST', { ...newForm, clienteId: Number(newForm.clienteId),
        aparelhoId: Number(newForm.aparelhoId) }, 'Orçamento criado.')
      if (result) setNewForm({ origem: 'LojaImediata' })
    }}>
      <label>Cliente<select required value={newForm.clienteId || ''} onChange={e => selectClient(e.target.value)}>
        <option value="">Selecione</option>{data.clients.filter(c => c.Ativo).map(c => <option key={c.Id} value={c.Id}>{c.Nome}</option>)}
      </select></label>
      <label>Aparelho<select required value={newForm.aparelhoId || ''} onChange={e => setNewForm({ ...newForm, aparelhoId: e.target.value })}>
        <option value="">Selecione</option>{devices.map(d => <option key={d.Id} value={d.Id}>{d.Marca} {d.Modelo}</option>)}
      </select></label>
      <label>Tipo de atendimento<select value={newForm.origem} onChange={e => setNewForm({ ...newForm, origem: e.target.value })}>
        <option value="LojaImediata">Aprovação no atendimento</option><option value="LojaPosterior">Análise posterior por email</option>
      </select></label>
      <Inputs schema={[[ 'descricaoProblemaCliente', 'Defeito relatado', 'textarea', true ]]} values={newForm} setValues={setNewForm} />
      <button>Criar orçamento</button>
    </form></Card><Card title="Orçamentos" className="budget-list">{data.budgets.length ? data.budgets.map(b => <div className="budget" key={b.Id}>
      <div className="budget-head"><div><strong>#{b.Id} · {b.NomeCliente}</strong><small>{b.MarcaAparelho} {b.ModeloAparelho} · {originLabel(b.Origem)}</small></div><span className="pill">{statusLabel(b.Status)}</span></div>
      <p>{b.DescricaoProblemaCliente}</p>
      {b.Status === 'EmAnalise' && <form onSubmit={e => {
        e.preventDefault()
        act(`/orcamentos/${b.Id}/resposta`, 'PUT', responses[b.Id], 'Resposta salva. Link enviado quando necessário.')
      }}><Inputs schema={[
        ['diagnosticoFuncionario', 'Diagnóstico', 'textarea', true],
        ['valorMaoDeObra', 'Mão de obra (R$)', 'number', true],
        ['valorPecas', 'Peças (R$)', 'number', true],
        ['prazoConclusao', 'Previsão de conclusão', 'date', true],
      ]} values={responses[b.Id] || {}} setValues={v => setResponses({ ...responses, [b.Id]: v })} /><button>Responder orçamento</button></form>}
      {b.Status === 'AguardandoAprovacao' && <>
        <p className="muted">Total: {currency(Number(b.ValorMaoDeObra) + Number(b.ValorPecas))} · Até {formatDate(b.PrazoParaAprovacaoCliente)}</p>
        {b.Origem === 'LojaImediata' ? <div className="actions">
          <select value={decisions[b.Id] || ''} onChange={e => setDecisions({ ...decisions, [b.Id]: e.target.value })}>
            <option value="">Responsável pela OS: quem respondeu</option>
            {data.employees.filter(f => f.Ativo).map(f => <option key={f.Id} value={f.Id}>{f.Nome}</option>)}
          </select>
          <button onClick={() => act(`/orcamentos/${b.Id}/decisao`, 'POST', {
            aprovar: true, ...(decisions[b.Id] ? { funcionarioResponsavelId: Number(decisions[b.Id]) } : {}),
          }, 'Orçamento aprovado e OS criada.')}>Aprovar</button>
          <button className="secondary" onClick={() => act(`/orcamentos/${b.Id}/decisao`, 'POST', { aprovar: false }, 'Orçamento recusado.')}>Recusar</button>
        </div> : <button className="secondary" onClick={() => act(`/orcamentos/${b.Id}/reenviar`, 'POST', {}, 'Novo link enviado.')}>Reenviar link</button>}
      </>}
    </div>) : <p className="muted">Nenhum orçamento.</p>}</Card></div>
}

function Orders({ data, act }) {
  const [form, setForm] = useState({})
  return <div className="order-grid">{data.orders.length ? data.orders.map(o => <Card key={o.Id} title={`OS #${o.Id}`}>
    <div className="budget-head"><div><strong>{o.NomeCliente}</strong><small>{o.MarcaAparelho} {o.ModeloAparelho} · Orçamento #{o.IdOrcamento}</small></div><span className="pill">{statusLabel(o.Status)}</span></div>
    <p>{o.DescricaoProblemaCliente}</p>
    <p className="muted">Previsão: {formatDate(o.DataPrevisaoConclusao)}{o.DataEntregaAparelho ? ' · aparelho entregue' : ''}</p>
    <div className="actions">
      {o.Status === 'AguardandoAparelho' && <button onClick={() => act(`/ordens-servico/${o.Id}`, 'PUT', { acao: 'receber' }, 'Aparelho recebido.')}>Receber aparelho</button>}
      {o.Status === 'AguardandoReparo' && <button onClick={() => act(`/ordens-servico/${o.Id}`, 'PUT', { acao: 'iniciar' }, 'Reparo iniciado.')}>Iniciar reparo</button>}
      {o.Status === 'EmReparo' && <button onClick={() => act(`/ordens-servico/${o.Id}`, 'PUT', { acao: 'concluir' }, 'Reparo concluído.')}>Concluir reparo</button>}
      {(o.Status === 'ReparoConcluido' || o.Status === 'Paga') && !o.DataEntregaAparelho && <button className="secondary" onClick={() => act(`/ordens-servico/${o.Id}`, 'PUT', { acao: 'entregar' }, 'Aparelho entregue.')}>Registrar entrega</button>}
    </div>
    {o.Status !== 'Paga' && <form className="inline-form" onSubmit={e => {
      e.preventDefault()
      act(`/ordens-servico/${o.Id}`, 'PUT', { acao: 'atribuir', funcionarioResponsavelId: Number(form[o.Id]?.responsavel) }, 'Responsável atualizado.')
    }}><label>Responsável<select required value={form[o.Id]?.responsavel || ''} onChange={e => setForm({ ...form, [o.Id]: { ...form[o.Id], responsavel: e.target.value } })}>
      <option value="">Selecione</option>{data.employees.filter(f => f.Ativo).map(f => <option key={f.Id} value={f.Id}>{f.Nome}</option>)}
    </select></label><button className="secondary">Atribuir</button></form>}
    {o.Status !== 'Paga' && <form className="inline-form" onSubmit={e => {
      e.preventDefault()
      act(`/ordens-servico/${o.Id}`, 'PUT', { acao: 'previsao',
        dataPrevisaoConclusao: form[o.Id]?.previsao }, 'Previsão atualizada.')
    }}><label>Nova previsão<input type="date" required value={form[o.Id]?.previsao || ''}
      onChange={e => setForm({ ...form, [o.Id]: { ...form[o.Id], previsao: e.target.value } })} /></label>
      <button className="secondary">Atualizar previsão</button></form>}
    {o.Status === 'ReparoConcluido' && <form className="inline-form" onSubmit={e => {
      e.preventDefault()
      act(`/ordens-servico/${o.Id}/pagamentos`, 'POST', { valor: form[o.Id]?.valor, formaPagamento: form[o.Id]?.formaPagamento }, 'Pagamento registrado.')
    }}><label>Valor pago<input type="number" min="0.01" step="0.01" required value={form[o.Id]?.valor || ''} onChange={e => setForm({ ...form, [o.Id]: { ...form[o.Id], valor: e.target.value } })} /></label>
      <label>Forma de pagamento<input required value={form[o.Id]?.formaPagamento || ''} onChange={e => setForm({ ...form, [o.Id]: { ...form[o.Id], formaPagamento: e.target.value } })} /></label><button>Registrar pagamento</button></form>}
  </Card>) : <Card title="Ordens de serviço"><p className="muted">Nenhuma OS. Ela será criada quando um orçamento for aprovado.</p></Card>}</div>
}

function currency(value) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(value) || 0)
}
function formatDate(value) {
  if (!value) return '—'
  return new Date(value.length === 10 ? `${value}T12:00:00` : value).toLocaleString('pt-BR', value.length === 10 ? { dateStyle: 'short' } : { dateStyle: 'short', timeStyle: 'short' })
}
function statusLabel(value) {
  return ({ EmAnalise: 'Em análise', AguardandoAprovacao: 'Aguardando aprovação', Aprovado: 'Aprovado',
    Recusado: 'Recusado', Cancelado: 'Cancelado', AguardandoAparelho: 'Aguardando aparelho',
    AguardandoReparo: 'Aguardando reparo', EmReparo: 'Em reparo', ReparoConcluido: 'Reparo concluído',
    Paga: 'Paga' })[value] || value
}
function originLabel(value) {
  return ({ Online: 'Online', LojaImediata: 'Loja · imediato', LojaPosterior: 'Loja · posterior' })[value] || value
}

export default App
