import { useCallback, useEffect, useMemo, useState } from "react";
import { BrowserRouter, Routes, Route, Link, useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import { QRCodeSVG } from "qrcode.react";
import { ArrowLeft, Check, ChevronRight, Copy, FileText, Heart, Home as HomeIcon, KeyRound, Mail, Menu, MessageCircle, MoreHorizontal, Percent, QrCode, Search, Share2, Sparkles, Star, Trash2, UserRound, WandSparkles, Youtube } from "lucide-react";
import "@/App.css";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const tools = [
  { id:"whatsapp", name:"Responder WhatsApp", desc:"Respostas naturais para qualquer mensagem", icon:MessageCircle, color:"coral", group:"Mais usadas" },
  { id:"improve_text", name:"Melhorar texto", desc:"Mais claro, profissional ou simples", icon:WandSparkles, color:"lime", group:"Mais usadas" },
  { id:"correct_pt", name:"Corrigir português", desc:"Ortografia, gramática e pontuação", icon:Check, color:"blue", group:"Mais usadas" },
  { id:"summarize", name:"Resumir texto", desc:"O essencial em poucos segundos", icon:FileText, color:"gold", group:"Mais usadas" },
  { id:"create_email", name:"Criar e-mail", desc:"Assuntos e corpos prontos", icon:Mail, color:"pink", group:"Texto e trabalho" },
  { id:"create_caption", name:"Criar legenda", desc:"Ideias que combinam com seu post", icon:HashIcon, color:"coral", group:"Redes sociais" },
  { id:"youtube_titles", name:"Títulos para YouTube", desc:"10 ideias para seu próximo vídeo", icon:Youtube, color:"red", group:"Redes sociais" },
  { id:"qrcode", name:"QR Code", desc:"Transforme qualquer link em QR", icon:QrCode, color:"lime", group:"Utilidades" },
  { id:"password_gen", name:"Gerador de senhas", desc:"Senhas fortes em um clique", icon:KeyRound, color:"blue", group:"Utilidades" },
  { id:"percentage_calc", name:"Calculadora de porcentagem", desc:"Conta rápida, sem complicação", icon:Percent, color:"gold", group:"Utilidades" },
];
const toolMap = Object.fromEntries(tools.map(t=>[t.id,t]));
const soon = [{name:"Transcrever áudio", icon:MessageCircle},{name:"Traduzir",icon:WandSparkles},{name:"Calculadora de desconto",icon:Percent},{name:"Criar currículo",icon:FileText}];
const slug = value => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-zA-Z0-9]+/g, "-").replace(/^-|-$/g, "").toLowerCase();
const getToken = () => localStorage.getItem("facilita_token");
const getUser = () => { try { return JSON.parse(localStorage.getItem("facilita_user") || "null"); } catch { return null; } };
const authHeaders = () => { const t = getToken(); return t ? { Authorization: `Bearer ${t}` } : {}; };
const isPremium = (u = getUser()) => u?.subscription?.plan === "premium";

function HashIcon(props){return <span className="hash-icon" {...props}>#</span>}
function Logo(){return <Link to="/" className="brand" data-testid="brand-home"><span className="brand-mark"><Sparkles size={17}/></span><span>facilita<span>ai</span></span></Link>}

function useAppSettings(){
  const [settings, setSettings] = useState(null);
  useEffect(() => {
    axios.get(`${API}/settings`).then(r => setSettings(r.data)).catch(() => setSettings({ads_enabled:true, banner_enabled:true, interstitial_enabled:false}));
  }, []);
  return settings;
}

function useUsage(){
  const [usage, setUsage] = useState(null);
  const refresh = useCallback(() => {
    axios.get(`${API}/me/usage`, { headers: authHeaders() }).then(r => setUsage(r.data)).catch(() => setUsage(null));
  }, []);
  useEffect(() => { refresh(); }, [refresh]);
  return [usage, refresh];
}

function AdBanner({ variant = "banner" }){
  const settings = useAppSettings();
  if (isPremium()) return null;
  if (!settings?.ads_enabled) return null;
  if (variant === "banner" && !settings.banner_enabled) return null;
  return <div className="ad-banner" data-testid={`ad-${variant}-placeholder`}>
    <span>ESPAÇO PUBLICITÁRIO</span>
    <small>anúncios aparecem no plano gratuito · <Link to="/premium" className="ad-upgrade" data-testid="ad-upgrade-link">remover</Link></small>
  </div>
}

function UsageBadge({ usage, onUpgrade }){
  if (!usage) return null;
  if (usage.is_premium) return <span className="usage-badge premium" data-testid="usage-badge-premium"><Sparkles size={13}/> Premium ativo</span>;
  const low = usage.remaining <= Math.max(1, Math.floor(usage.limit * 0.2));
  return <button type="button" className={`usage-badge ${low?"low":""}`} onClick={onUpgrade} data-testid="usage-badge">
    <Sparkles size={13}/>
    <span>{usage.remaining} de {usage.limit} usos de IA hoje</span>
  </button>
}
function BottomNav({active="home"}){return <nav className="bottom-nav" data-testid="bottom-navigation">
  <Link className={active==="home"?"active":""} to="/" data-testid="nav-home"><HomeIcon size={19}/><span>Início</span></Link>
  <Link className={active==="tools"?"active":""} to="/ferramentas" data-testid="nav-tools"><Menu size={19}/><span>Ferramentas</span></Link>
  <Link className={active==="favorites"?"active":""} to="/favoritos" data-testid="nav-favorites"><Star size={19}/><span>Favoritos</span></Link>
  <Link className={active==="history"?"active":""} to="/historico" data-testid="nav-history"><MoreHorizontal size={19}/><span>Histórico</span></Link>
  <Link className={active==="profile"?"active":""} to="/perfil" data-testid="nav-profile"><UserRound size={19}/><span>Perfil</span></Link>
</nav>}

function ToolCard({tool, favorite, onFavorite}){const Icon=tool.icon; return <div className="tool-card" data-testid={`tool-card-${tool.id}`}>
  <Link to={`/ferramenta/${tool.id}`} className="tool-main" data-testid={`tool-open-${tool.id}`}><span className={`tool-icon ${tool.color}`}><Icon size={21}/></span><span className="tool-copy"><strong>{tool.name}</strong><small>{tool.desc}</small></span><ChevronRight className="tool-arrow" size={18}/></Link>
  <button className={`favorite-btn ${favorite?"is-favorite":""}`} onClick={onFavorite} aria-label="Favoritar" data-testid={`favorite-${tool.id}`}>{favorite?<Heart size={17} fill="currentColor"/>:<Star size={17}/>}</button>
</div>}

function useFavorites(){
  const [favorites, setFavorites] = useState(() => JSON.parse(localStorage.getItem("facilita_favorites") || "[]"));
  const persist = (next) => { setFavorites(next); localStorage.setItem("facilita_favorites", JSON.stringify(next)); };

  useEffect(() => {
    if (!getToken()) return;
    axios.get(`${API}/favorites`, { headers: authHeaders() })
      .then(r => persist(r.data.map(x => x.tool_id)))
      .catch(() => {});
  }, []);

  const toggle = useCallback(async (id) => {
    const isFav = favorites.includes(id);
    const next = isFav ? favorites.filter(x => x !== id) : [...favorites, id];
    persist(next);
    if (getToken()) {
      try {
        if (isFav) await axios.delete(`${API}/favorites/${id}`, { headers: authHeaders() });
        else await axios.post(`${API}/favorites`, { tool_id: id }, { headers: authHeaders() });
      } catch { /* keep local state */ }
    }
  }, [favorites]);

  return [favorites, toggle];
}

function Home(){
  const [query,setQuery]=useState("");
  const [favorites,toggle]=useFavorites();
  const [usage] = useUsage();
  const nav = useNavigate();
  const filtered=tools.filter(t=>`${t.name} ${t.desc}`.toLowerCase().includes(query.toLowerCase()));
  return <div className="app-shell"><header className="topbar"><Logo/><Link to="/perfil" className="profile-dot" data-testid="header-profile-button"><UserRound size={18}/></Link></header><main className="page home-page">
  <section className="welcome"><p className="eyebrow">BOM TE VER POR AQUI <span>✦</span></p><h1>O que você precisa<br/><em>resolver</em> hoje?</h1><p className="tagline">Sua IA para resolver o dia a dia.</p><label className="searchbox"><Search size={19}/><input data-testid="home-search-input" placeholder="O que você precisa fazer?" value={query} onChange={e=>setQuery(e.target.value)}/><kbd>⌘ K</kbd></label>
    <div className="usage-row"><UsageBadge usage={usage} onUpgrade={()=>nav("/premium")}/></div>
  </section>
  {favorites.length>0 && !query && <section className="section"><SectionTitle title="Meus favoritos"/><div className="tool-list">{tools.filter(t=>favorites.includes(t.id)).map(t=><ToolCard key={t.id} tool={t} favorite onFavorite={()=>toggle(t.id)}/>)}</div></section>}
  <AdBanner/><section className="section"><SectionTitle title={query?"Resultados":"Mais usadas"} action={query?null:<Link to="/ferramentas" data-testid="see-all-tools">Ver todas</Link>}/><div className="tool-list">{filtered.slice(0,query?20:4).map(t=><ToolCard key={t.id} tool={t} favorite={favorites.includes(t.id)} onFavorite={()=>toggle(t.id)}/>)}</div></section>
  {!query && <><ToolGroup title="Texto e trabalho" items={tools.filter(t=>t.group==="Texto e trabalho")} favorites={favorites} toggle={toggle}/><ToolGroup title="Redes sociais" items={tools.filter(t=>t.group==="Redes sociais")} favorites={favorites} toggle={toggle}/><ToolGroup title="Utilidades" items={tools.filter(t=>t.group==="Utilidades")} favorites={favorites} toggle={toggle}/><section className="section"><SectionTitle title="Em breve"/><div className="soon-grid">{soon.map((x,i)=>{const Icon=x.icon;return <div className="soon-item" key={x.name} data-testid={`coming-soon-${i}`}><Icon size={18}/><span>{x.name}</span><small>Em breve</small></div>})}</div></section></>}
  </main><BottomNav/></div>
}

function SectionTitle({title,action}){return <div className="section-title"><h2>{title}</h2>{action}</div>}
function ToolGroup({title,items,favorites,toggle}){return <section className="section"><SectionTitle title={title}/><div className="tool-list">{items.map(t=><ToolCard key={t.id} tool={t} favorite={favorites.includes(t.id)} onFavorite={()=>toggle(t.id)}/>)}</div></section>}

function Tools(){const [favorites,toggle]=useFavorites();return <div className="app-shell"><header className="topbar"><Logo/><span className="page-label">Ferramentas</span></header><main className="page"><section className="page-intro"><p className="eyebrow">CENTRAL DE UTILIDADES</p><h1>Tudo para deixar<br/><em>mais fácil.</em></h1></section><div className="tool-list">{tools.map(t=><ToolCard key={t.id} tool={t} favorite={favorites.includes(t.id)} onFavorite={()=>toggle(t.id)}/>)}</div><section className="section"><SectionTitle title="Em breve"/><div className="soon-grid">{soon.map((x,i)=><div className="soon-item" key={x.name} data-testid={`tools-soon-${i}`}><x.icon size={18}/><span>{x.name}</span><small>Em breve</small></div>)}</div></section></main><BottomNav active="tools"/></div>}

function ToolPage(){
  const {id}=useParams();
  const tool=tools.find(t=>t.id===id)||tools[0];
  const [result,setResult]=useState("");
  const [loading,setLoading]=useState(false);
  const [copied,setCopied]=useState(false);
  const [limitReached, setLimitReached] = useState(false);
  const [usage, refreshUsage] = useUsage();
  const nav = useNavigate();
  const [fields,setFields]=useState({message:"",text:"",topic:"",tone:"😊 Amigável",mode:"Resumo normal",style:"Profissional",platform:"Instagram",emoji:"Com emojis",value:"500",percentage:"20",length:16,letters:true,numbers:true,symbols:true});
  const update=(key,value)=>setFields(f=>({...f,[key]:value}));
  const inputField = id==="whatsapp" ? "message" : (id==="create_email"||id==="create_caption"||id==="youtube_titles") ? "topic" : "text";
  const inputValue = fields[inputField];
  const isAi = ["whatsapp","improve_text","correct_pt","summarize","create_email","create_caption","youtube_titles"].includes(id);

  const generate = async () => {
    setLoading(true); setCopied(false);
    try {
      const res = await axios.post(`${API}/generate`, { tool: id, payload: fields }, { headers: authHeaders() });
      setResult(res.data.result);
      if (isAi) refreshUsage();
    } catch (e) {
      if (e.response?.status === 402) { setLimitReached(true); }
      else setResult(e.response?.data?.detail || "Não foi possível concluir agora.");
    }
    setLoading(false);
  };

  const formText = id==="whatsapp"?"Cole abaixo a mensagem que você recebeu.":id==="create_email"?"Sobre o que é o e-mail?":(id==="create_caption"||id==="youtube_titles")?"Sobre o que é sua publicação?":id==="qrcode"?"Cole o link ou texto que virará QR":"Cole seu texto aqui";
  const showTextarea = id!=="percentage_calc" && id!=="password_gen";
  const options = id==="whatsapp"?["😊 Amigável","💼 Profissional","❤️ Carinhoso","😂 Engraçado","🎯 Direto","🙏 Educado"]:id==="improve_text"?["Corrigir erros","Deixar mais claro","Deixar profissional","Deixar mais simples","Deixar mais educado","Deixar mais curto"]:id==="summarize"?["Resumo curto","Resumo normal","Pontos principais","Explicar de forma simples"]:[];

  return <div className="app-shell">
    <header className="tool-header"><Link to="/" data-testid="tool-back-button"><ArrowLeft size={20}/></Link><span>Facilita AI</span><button data-testid="tool-more-button"><MoreHorizontal size={21}/></button></header>
    <main className="page tool-page">
      <div className={`tool-hero ${tool.color}`}><span className="tool-icon"><tool.icon size={25}/></span><div><p className="eyebrow">FERRAMENTA FACILITA</p><h1>{tool.name}</h1><p>{tool.desc}</p></div></div>
      {isAi && <div className="usage-row"><UsageBadge usage={usage} onUpgrade={()=>nav("/premium")}/></div>}
      <div className="form-section">
        {showTextarea && <>
          <label className="field-label">{formText}</label>
          <textarea data-testid={`${id}-input`} value={inputValue} onChange={e=>update(inputField, e.target.value)} placeholder="Escreva ou cole aqui..."/>
        </>}
        {id==="percentage_calc" && <div className="calc-row"><input data-testid="percentage-value-input" type="number" value={fields.value} onChange={e=>update("value",e.target.value)}/><span>é</span><input data-testid="percentage-percent-input" type="number" value={fields.percentage} onChange={e=>update("percentage",e.target.value)}/><span>%</span></div>}
        {id==="password_gen" && <div className="password-options"><label>Tamanho <input data-testid="password-length-input" type="number" min="6" max="64" value={fields.length} onChange={e=>update("length",e.target.value)}/></label>{[["letters","Letras"],["numbers","Números"],["symbols","Especiais"]].map(([k,l])=><label key={k}><input data-testid={`password-${k}-toggle`} type="checkbox" checked={fields[k]} onChange={e=>update(k,e.target.checked)}/>{l}</label>)}</div>}
        {options.length>0 && <div className="chips" data-testid={`${id}-options`}>{options.map(o=><button className={(fields.tone===o||fields.mode===o)?"selected":""} key={o} onClick={()=>update(id==="whatsapp"?"tone":"mode",o)} data-testid={`${id}-option-${slug(o)}`}>{o}</button>)}</div>}
        {id==="create_email" && <div className="chips"><span className="field-label">Qual estilo?</span>{["Profissional","Amigável","Formal","Direto"].map(o=><button className={fields.style===o?"selected":""} key={o} onClick={()=>update("style",o)} data-testid={`email-style-${o.toLowerCase()}`}>{o}</button>)}</div>}
        {id==="create_caption" && <div className="chips">{["Instagram","TikTok","Facebook","LinkedIn","Com emojis","Sem emojis","Curta","Normal"].map(o=><button className={(fields.platform===o||fields.emoji===o||fields.style===o)?"selected":""} key={o} onClick={()=>update(["Instagram","TikTok","Facebook","LinkedIn"].includes(o)?"platform":o.includes("emoji")?"emoji":"style",o)} data-testid={`caption-option-${o.toLowerCase().replaceAll(" ","-")}`}>{o}</button>)}</div>}
        <button className="primary-action" onClick={generate} disabled={loading} data-testid={`${id}-generate-button`}><Sparkles size={18}/>{loading?"Preparando...":id==="percentage_calc"?"Calcular":id==="password_gen"?"Gerar senha":id==="qrcode"?"Gerar QR Code":`Gerar ${id==="whatsapp"?"respostas":"resultado"}`}</button>
      </div>
      {id==="qrcode" && fields.text && <div className="qr-result" data-testid="qrcode-preview"><QRCodeSVG value={fields.text} size={180}/><p className="qr-caption">Aponte a câmera do celular para testar</p></div>}
      {result && <section className="result-panel" data-testid={`${id}-result`}>
        <div className="result-top"><div><p className="eyebrow">SEU RESULTADO</p><h2>{id==="whatsapp"?"Escolha a que combina mais":"Pronto para usar"}</h2></div>
        <button onClick={()=>{navigator.clipboard?.writeText(result);setCopied(true)}} data-testid={`${id}-copy-button`}><Copy size={17}/>{copied?"Copiado":"Copiar"}</button></div>
        <div className="result-text">{result}</div>
        <div className="result-actions"><button onClick={generate} data-testid={`${id}-retry-button`}><WandSparkles size={16}/> Tentar outra</button><button onClick={()=>navigator.share?.({text:result})} data-testid={`${id}-share-button`}><Share2 size={16}/> Compartilhar</button></div>
      </section>}
      {id==="percentage_calc" && !result && <p className="helper">Exemplo: quanto é 20% de R$ 500?</p>}
      <AdBanner/>
    </main>
    {limitReached && <div className="modal-overlay" onClick={()=>setLimitReached(false)} data-testid="limit-reached-modal">
      <div className="modal-card limit-modal" onClick={e=>e.stopPropagation()}>
        <div className="limit-icon"><Sparkles size={24}/></div>
        <h3>Você chegou ao limite gratuito de hoje ✨</h3>
        <p>No plano grátis você tem {usage?.limit ?? 10} usos de IA por dia. Volte amanhã ou assine o Premium para continuar agora mesmo.</p>
        <div className="limit-actions">
          <button className="primary-action" onClick={()=>{setLimitReached(false); nav("/premium");}} data-testid="limit-upgrade-button"><Sparkles size={18}/> Ver Premium</button>
          <button className="ghost-action" onClick={()=>setLimitReached(false)} data-testid="limit-dismiss-button">Agora não</button>
        </div>
      </div>
    </div>}
    <BottomNav active="tools"/>
  </div>
}

function Auth(){const [mode,setMode]=useState("login");const [email,setEmail]=useState("admin@facilita.ai");const [password,setPassword]=useState("Facilita@123");const [message,setMessage]=useState("");const nav=useNavigate();const submit=async e=>{e.preventDefault();try{const r=await axios.post(`${API}/auth/${mode}`,{email,password,name:""});localStorage.setItem("facilita_token",r.data.token);localStorage.setItem("facilita_user",JSON.stringify(r.data.user));nav("/")}catch(err){setMessage(err.response?.data?.detail||"Confira seus dados")}};return <div className="auth-page"><div className="auth-brand"><Logo/></div><main className="auth-box"><p className="eyebrow">FACILITA AI</p><h1>{mode==="login"?"Bem-vindo de volta.":"Crie sua conta."}</h1><p>{mode==="login"?"Entre para guardar seus resultados e favoritos.":"Comece a resolver seu dia em poucos cliques."}</p><form onSubmit={submit}><label>E-mail<input data-testid="auth-email-input" type="email" value={email} onChange={e=>setEmail(e.target.value)} required/></label><label>Senha<input data-testid="auth-password-input" type="password" value={password} onChange={e=>setPassword(e.target.value)} required/></label>{message&&<div className="error-message" data-testid="auth-error-message">{message}</div>}<button className="primary-action" data-testid="auth-submit-button">{mode==="login"?"Entrar":"Criar conta"}</button></form><button className="google-button" data-testid="google-login-button" onClick={()=>setMessage("Login Google será conectado no painel administrativo.")}>Continuar com Google</button><button className="switch-auth" onClick={()=>setMode(mode==="login"?"register":"login")} data-testid="auth-mode-switch">{mode==="login"?"Ainda não tenho conta":"Já tenho uma conta"}</button></main></div>}

function Favorites(){
  const [favorites, toggle] = useFavorites();
  return <div className="app-shell">
    <header className="topbar"><Logo/><span className="page-label">Favoritos</span></header>
    <main className="page">
      <section className="page-intro compact"><p className="eyebrow">SEU JEITO DE USAR</p><h1>O que você<br/><em>mais gosta.</em></h1></section>
      {favorites.length ? <div className="tool-list">{tools.filter(t=>favorites.includes(t.id)).map(t=><ToolCard key={t.id} tool={t} favorite onFavorite={()=>toggle(t.id)}/>)}</div> : <Empty icon={Star} text="Você ainda não favoritou nenhuma ferramenta."/>}
    </main>
    <BottomNav active="favorites"/>
  </div>
}

function History(){
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [openItem, setOpenItem] = useState(null);
  const nav = useNavigate();

  const load = useCallback(async () => {
    if (!getToken()) { setLoading(false); setError("guest"); return; }
    setLoading(true);
    try {
      const r = await axios.get(`${API}/history`, { headers: authHeaders() });
      setItems(r.data);
      setError("");
    } catch (e) {
      setError(e.response?.data?.detail || "Não foi possível carregar o histórico.");
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const remove = async (item_id) => {
    setItems(items.filter(x => x.id !== item_id));
    try { await axios.delete(`${API}/history/${item_id}`, { headers: authHeaders() }); } catch { /* keep optimistic */ }
  };

  const groupByDay = useMemo(() => {
    const g = {};
    for (const it of items) {
      const d = new Date(it.created_at);
      const key = d.toLocaleDateString("pt-BR", { day: "2-digit", month: "long" });
      (g[key] = g[key] || []).push(it);
    }
    return Object.entries(g);
  }, [items]);

  return <div className="app-shell">
    <header className="topbar"><Logo/><span className="page-label">Histórico</span></header>
    <main className="page">
      <section className="page-intro compact"><p className="eyebrow">SUAS ÚLTIMAS IDEIAS</p><h1>Volte quando<br/><em>quiser.</em></h1></section>
      {error === "guest" ? <div className="empty-state" data-testid="history-guest-state"><span><FileText size={27}/></span><p>Entre na sua conta para guardar e revisitar suas gerações.</p><Link to="/login" className="outline-button" data-testid="history-login-cta">Entrar agora</Link></div>
        : loading ? <p className="helper" data-testid="history-loading">Carregando seu histórico...</p>
        : error ? <p className="helper" data-testid="history-error">{error}</p>
        : items.length === 0 ? <Empty icon={FileText} text="Seu histórico aparece aqui depois da primeira geração."/>
        : <div className="history-list" data-testid="history-list">{groupByDay.map(([day, entries]) => (
            <div className="history-day" key={day}>
              <p className="history-day-label">{day}</p>
              {entries.map(it => (
                <div className="history-item" key={it.id} data-testid={`history-item-${it.id}`}>
                  <button className="history-open" onClick={() => setOpenItem(it)} data-testid={`history-open-${it.id}`}>
                    <span className={`tool-icon ${toolMap[it.tool]?.color||"blue"}`}>{(() => { const T = toolMap[it.tool]?.icon||FileText; return <T size={18}/>; })()}</span>
                    <span className="history-copy"><strong>{toolMap[it.tool]?.name||it.tool}</strong><small>{(it.result||"").slice(0,60)}...</small></span>
                    <ChevronRight size={16}/>
                  </button>
                  <button className="history-delete" onClick={() => remove(it.id)} aria-label="Excluir" data-testid={`history-delete-${it.id}`}><Trash2 size={16}/></button>
                </div>
              ))}
            </div>
          ))}</div>}
      {openItem && <div className="modal-overlay" onClick={()=>setOpenItem(null)} data-testid="history-modal">
        <div className="modal-card" onClick={e=>e.stopPropagation()}>
          <div className="modal-head"><h3>{toolMap[openItem.tool]?.name||openItem.tool}</h3><button onClick={()=>setOpenItem(null)} data-testid="history-modal-close">Fechar</button></div>
          <div className="result-text">{openItem.result}</div>
          <div className="result-actions">
            <button onClick={()=>{navigator.clipboard?.writeText(openItem.result)}} data-testid="history-modal-copy"><Copy size={16}/> Copiar</button>
            <button onClick={()=>{ setOpenItem(null); nav(`/ferramenta/${openItem.tool}`); }} data-testid="history-modal-reopen"><WandSparkles size={16}/> Abrir ferramenta</button>
          </div>
        </div>
      </div>}
    </main>
    <BottomNav active="history"/>
  </div>
}

function Profile(){
  const user = getUser();
  const [usage] = useUsage();
  const premium = isPremium(user);
  const logout = () => { localStorage.removeItem("facilita_token"); localStorage.removeItem("facilita_user"); localStorage.removeItem("facilita_favorites"); window.location.href = "/"; };
  return <div className="app-shell">
    <header className="topbar"><Logo/><span className="page-label">Perfil</span></header>
    <main className="page">
      <section className="profile-card"><span className="avatar"><UserRound size={25}/></span><div><p className="eyebrow">SEU PERFIL {premium && <span className="plan-tag" data-testid="plan-tag-premium">PREMIUM</span>}</p><h2>{user?.name||"Visitante"}</h2><p>{user?.email||"Use sem cadastro ou entre para sincronizar"}</p></div></section>
      {usage && <div className="usage-summary" data-testid="profile-usage-summary"><span>Usos de IA hoje</span><strong>{usage.used} / {usage.limit}</strong><small>{premium ? "Plano Premium" : "Plano Grátis"}</small></div>}
      {!premium && <Link className="premium-strip" to="/premium" data-testid="premium-card"><span><Sparkles size={20}/></span><div><strong>Facilita AI Premium</strong><small>Mais usos, sem anúncios e recursos avançados</small></div><ChevronRight/></Link>}
      {premium && <Link className="premium-strip active" to="/premium" data-testid="premium-card-active"><span><Sparkles size={20}/></span><div><strong>Você é Premium</strong><small>Ver benefícios e gerenciar sua assinatura</small></div><ChevronRight/></Link>}
      <div className="settings-list">
        {user ? <button onClick={logout} data-testid="profile-logout-button"><UserRound size={18}/> Sair da conta<ChevronRight size={17}/></button>
              : <Link to="/login" data-testid="profile-login-link"><UserRound size={18}/> Entrar ou criar conta<ChevronRight size={17}/></Link>}
        <Link to="/termos" data-testid="terms-link"><FileText size={18}/> Termos e privacidade<ChevronRight size={17}/></Link>
      </div>
    </main>
    <BottomNav active="profile"/>
  </div>
}

function Premium(){
  const nav = useNavigate();
  const settings = useAppSettings();
  const [checkoutMsg, setCheckoutMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const user = getUser();
  const premium = isPremium(user);

  const subscribe = async () => {
    if (!getToken()) { nav("/login"); return; }
    setLoading(true);
    try {
      const r = await axios.post(`${API}/checkout/premium`, {}, { headers: authHeaders() });
      setCheckoutMsg(r.data?.message || "Pagamento em preparação.");
    } catch (e) {
      setCheckoutMsg(e.response?.data?.detail || "Não foi possível iniciar a assinatura agora.");
    }
    setLoading(false);
  };

  const price = settings?.premium_price_brl?.toFixed(2).replace(".", ",") ?? "19,90";
  const freeLimit = settings?.free_daily_limit ?? 10;
  const premiumLimit = settings?.premium_daily_limit ?? 500;

  return <div className="app-shell">
    <header className="tool-header"><Link to="/perfil" data-testid="premium-back-button"><ArrowLeft size={20}/></Link><span>Facilita AI Premium</span><span/></header>
    <main className="page premium-page">
      <section className="premium-hero">
        <p className="eyebrow">FACILITA AI PREMIUM</p>
        <h1>Menos limites,<br/><em>zero anúncios.</em></h1>
        <p className="tagline">A mesma simplicidade do Facilita, agora sem interrupções e com muito mais IA.</p>
      </section>
      <div className="plan-compare">
        <div className="plan-card" data-testid="plan-free">
          <div className="plan-head"><h2>Grátis</h2><span className="plan-price">R$ 0<small>/mês</small></span></div>
          <ul>
            <li><Check size={15}/> Ferramentas locais ilimitadas</li>
            <li><Check size={15}/> {freeLimit} usos de IA por dia</li>
            <li className="muted"><Check size={15}/> Com anúncios discretos</li>
            <li className="muted"><Check size={15}/> Histórico básico</li>
          </ul>
          <button className="ghost-action" disabled data-testid="plan-free-button">Você está aqui</button>
        </div>
        <div className="plan-card featured" data-testid="plan-premium">
          <div className="plan-head"><h2>Premium <Sparkles size={17}/></h2><span className="plan-price">R$ {price}<small>/mês</small></span></div>
          <ul>
            <li><Check size={15}/> Sem anúncios em nenhum lugar</li>
            <li><Check size={15}/> {premiumLimit} usos de IA por dia</li>
            <li><Check size={15}/> Histórico ampliado</li>
            <li><Check size={15}/> Acesso a recursos Premium futuros</li>
          </ul>
          {premium ? <button className="primary-action" disabled data-testid="premium-active-button">Assinatura ativa</button>
                   : <button className="primary-action" onClick={subscribe} disabled={loading} data-testid="premium-subscribe-button"><Sparkles size={18}/> {loading?"Preparando...":"Assinar Premium"}</button>}
        </div>
      </div>
      {checkoutMsg && <div className="checkout-note" data-testid="checkout-note">{checkoutMsg}</div>}
      <p className="helper premium-fineprint">O pagamento será processado por um gateway externo assim que a integração for concluída. Nenhuma cobrança é feita neste momento.</p>
    </main>
    <BottomNav active="profile"/>
  </div>
}
function Empty({icon:Icon,text}){return <div className="empty-state" data-testid="empty-state"><span><Icon size={27}/></span><p>{text}</p><Link to="/ferramentas" className="outline-button" data-testid="empty-state-action">Explorar ferramentas</Link></div>}
function Legal(){return <div className="app-shell"><header className="tool-header"><Link to="/perfil" data-testid="legal-back-button"><ArrowLeft size={20}/></Link><span>Privacidade</span></header><main className="page legal"><p className="eyebrow">FACILITA AI</p><h1>Termos e privacidade</h1><p>O Facilita AI foi criado para simplificar seu dia. Textos enviados às ferramentas de inteligência artificial podem ser processados por provedores externos para gerar o resultado solicitado.</p><h2>Uso responsável</h2><p>Não envie dados sensíveis, senhas ou informações pessoais que não sejam necessárias. O app registra apenas métricas de uso e histórico quando você escolhe estar conectado.</p><h2>Contato</h2><p>Fale com a equipe em contato@facilita.ai</p></main></div>}

function App(){return <BrowserRouter><Routes><Route path="/" element={<Home/>}/><Route path="/ferramentas" element={<Tools/>}/><Route path="/ferramenta/:id" element={<ToolPage/>}/><Route path="/login" element={<Auth/>}/><Route path="/favoritos" element={<Favorites/>}/><Route path="/historico" element={<History/>}/><Route path="/perfil" element={<Profile/>}/><Route path="/premium" element={<Premium/>}/><Route path="/termos" element={<Legal/>}/></Routes></BrowserRouter>}
export default App;
