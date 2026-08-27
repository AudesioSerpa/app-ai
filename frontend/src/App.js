import { useCallback, useEffect, useMemo, useState } from "react";
import { BrowserRouter, Routes, Route, Link, useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import { QRCodeSVG } from "qrcode.react";
import { ArrowLeft, Check, ChevronRight, Copy, Download, FileText, Heart, Home as HomeIcon, ImagePlus, KeyRound, Mail, Menu, MessageCircle, Mic, MoreHorizontal, Pause, Percent, Play, QrCode, Search, Share2, Shield, Sparkles, Star, Trash2, UserRound, Volume2, WandSparkles, Youtube } from "lucide-react";
import "@/App.css";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const tools = [
  { id:"whatsapp", name:"Responder WhatsApp", desc:"Respostas naturais para qualquer mensagem", icon:MessageCircle, color:"coral", group:"Mais usadas" },
  { id:"improve_text", name:"Melhorar texto", desc:"Mais claro, profissional ou simples", icon:WandSparkles, color:"lime", group:"Mais usadas" },
  { id:"correct_pt", name:"Corrigir português", desc:"Ortografia, gramática e pontuação", icon:Check, color:"blue", group:"Mais usadas" },
  { id:"summarize", name:"Resumir texto", desc:"O essencial em poucos segundos", icon:FileText, color:"gold", group:"Mais usadas" },
  { id:"image_gen", name:"Gerador de imagens IA", desc:"Crie imagens a partir de uma descrição", icon:ImagePlus, color:"pink", group:"Mais usadas" },
  { id:"audio_gen", name:"Gerador de áudio IA", desc:"Transforme texto em voz natural em pt-BR", icon:Volume2, color:"coral", group:"Mais usadas" },
  { id:"create_email", name:"Criar e-mail", desc:"Assuntos e corpos prontos", icon:Mail, color:"pink", group:"Texto e trabalho" },
  { id:"create_caption", name:"Criar legenda", desc:"Ideias que combinam com seu post", icon:HashIcon, color:"coral", group:"Redes sociais" },
  { id:"youtube_titles", name:"Títulos para YouTube", desc:"10 ideias para seu próximo vídeo", icon:Youtube, color:"red", group:"Redes sociais" },
  { id:"qrcode", name:"QR Code", desc:"Transforme qualquer link em QR", icon:QrCode, color:"lime", group:"Utilidades" },
  { id:"password_gen", name:"Gerador de senhas", desc:"Senhas fortes em um clique", icon:KeyRound, color:"blue", group:"Utilidades" },
  { id:"percentage_calc", name:"Calculadora de porcentagem", desc:"Conta rápida, sem complicação", icon:Percent, color:"gold", group:"Utilidades" },
];
const toolMap = Object.fromEntries(tools.map(t=>[t.id,t]));
const soon = [{name:"Traduzir",icon:WandSparkles},{name:"Calculadora de desconto",icon:Percent},{name:"Criar currículo",icon:FileText},{name:"Transcrever áudio",icon:Mic}];
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
    if (!getToken()) { setUsage(null); return; }
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
  // Enquanto não há SDK de anúncios integrado, não mostrar placeholder técnico ao usuário.
  // Quando o AdMob (ou similar) for conectado, este container renderiza o slot real.
  return null;
}

function UsageBadge({ usage, onUpgrade }){
  if (!usage) return null;
  if (usage.is_premium) return <span className="usage-badge premium" data-testid="usage-badge-premium"><Sparkles size={13}/> Premium ativo</span>;
  const { remaining, limit } = usage;
  let text;
  if (remaining >= limit) text = `Você tem ${limit} ${limit===1?"uso":"usos"} grátis hoje`;
  else if (remaining <= 0) text = `Você usou seus ${limit} acessos gratuitos de hoje`;
  else text = `${remaining} ${remaining===1?"uso restante":"usos restantes"} hoje`;
  const low = remaining <= Math.max(1, Math.floor(limit * 0.34));
  return <button type="button" className={`usage-badge ${low?"low":""} ${remaining<=0?"empty":""}`} onClick={onUpgrade} data-testid="usage-badge">
    <Sparkles size={13}/>
    <span>{text}</span>
  </button>
}

function GraceBanner({ usage }){
  if (!usage?.in_grace_period) return null;
  const days = usage.grace_days_left || 3;
  return <Link to="/premium" className="grace-banner" data-testid="grace-banner">
    <span className="grace-icon">⚠</span>
    <div className="grace-copy">
      <strong>Não conseguimos cobrar seu cartão</strong>
      <small>Seu Premium continua ativo por mais {days} {days===1?"dia":"dias"}. Atualize seu cartão para não perder o acesso.</small>
    </div>
    <ChevronRight size={18}/>
  </Link>
}
function BottomNav({active="home"}){return <nav className="bottom-nav" data-testid="bottom-navigation">
  <Link className={active==="home"?"active":""} to="/" data-testid="nav-home"><HomeIcon size={22}/><span>Início</span></Link>
  <Link className={active==="tools"?"active":""} to="/ferramentas" data-testid="nav-tools"><Menu size={22}/><span>Ferramentas</span></Link>
  <Link className={active==="history"?"active":""} to="/historico" data-testid="nav-history"><MoreHorizontal size={22}/><span>Histórico</span></Link>
  <Link className={active==="profile"?"active":""} to="/perfil" data-testid="nav-profile"><UserRound size={22}/><span>Perfil</span></Link>
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
  const [welcomeOpen, setWelcomeOpen] = useState(false);
  const filtered=tools.filter(t=>`${t.name} ${t.desc}`.toLowerCase().includes(query.toLowerCase()));

  // Modal de boas-vindas com CTA de cadastro para visitantes deslogados
  useEffect(() => {
    if (getToken()) return;
    if (localStorage.getItem("facilita_welcome_dismissed") === "1") return;
    const t = setTimeout(() => setWelcomeOpen(true), 900);
    return () => clearTimeout(t);
  }, []);

  const dismissWelcome = () => {
    localStorage.setItem("facilita_welcome_dismissed", "1");
    setWelcomeOpen(false);
  };

  return <div className="app-shell"><header className="topbar"><Logo/><Link to="/perfil" className="profile-dot" data-testid="header-profile-button"><UserRound size={18}/></Link></header><main className="page home-page">
  <GraceBanner usage={usage}/>
  <section className="welcome"><p className="eyebrow">BOM TE VER POR AQUI <span>✦</span></p><h1>O que você precisa<br/><em>resolver</em> hoje?</h1><p className="tagline">Sua IA para resolver o dia a dia.</p><label className="searchbox"><Search size={19}/><input data-testid="home-search-input" placeholder="O que você precisa fazer?" value={query} onChange={e=>setQuery(e.target.value)}/><kbd>⌘ K</kbd></label>
    <div className="usage-row"><UsageBadge usage={usage} onUpgrade={()=>nav("/premium")}/></div>
  </section>
  {favorites.length>0 && !query && <section className="section"><SectionTitle title="Meus favoritos"/><div className="tool-list">{tools.filter(t=>favorites.includes(t.id)).map(t=><ToolCard key={t.id} tool={t} favorite onFavorite={()=>toggle(t.id)}/>)}</div></section>}
  <AdBanner/><section className="section"><SectionTitle title={query?"Resultados":"Mais usadas"} action={query?null:<Link to="/ferramentas" data-testid="see-all-tools">Ver todas</Link>}/><div className="tool-list">{filtered.slice(0,query?20:6).map(t=><ToolCard key={t.id} tool={t} favorite={favorites.includes(t.id)} onFavorite={()=>toggle(t.id)}/>)}</div></section>
  {!query && <><ToolGroup title="Texto e trabalho" items={tools.filter(t=>t.group==="Texto e trabalho")} favorites={favorites} toggle={toggle}/><ToolGroup title="Redes sociais" items={tools.filter(t=>t.group==="Redes sociais")} favorites={favorites} toggle={toggle}/><ToolGroup title="Utilidades" items={tools.filter(t=>t.group==="Utilidades")} favorites={favorites} toggle={toggle}/><section className="section"><SectionTitle title="Em breve"/><div className="soon-grid">{soon.map((x,i)=>{const Icon=x.icon;return <div className="soon-item" key={x.name} data-testid={`coming-soon-${i}`}><Icon size={18}/><span>{x.name}</span><small>Em breve</small></div>})}</div></section></>}
  </main>
  {welcomeOpen && <div className="modal-overlay" onClick={dismissWelcome} data-testid="welcome-modal">
    <div className="modal-card limit-modal" onClick={e=>e.stopPropagation()}>
      <div className="limit-icon"><Sparkles size={24}/></div>
      <h3>Bem-vindo ao Facilita AI ✨</h3>
      <p>Crie sua conta grátis em 30 segundos e ganhe <strong>3 usos de IA por dia</strong> para responder WhatsApp, corrigir textos, criar legendas e muito mais.</p>
      <div className="limit-actions">
        <button className="primary-action" onClick={()=>{ dismissWelcome(); nav("/login?mode=register"); }} data-testid="welcome-register-button"><Sparkles size={18}/> Criar conta grátis</button>
        <button className="ghost-action" onClick={()=>{ dismissWelcome(); nav("/login"); }} data-testid="welcome-login-button">Já tenho conta</button>
        <button className="text-action" onClick={dismissWelcome} data-testid="welcome-dismiss-button">Ver o app antes</button>
      </div>
    </div>
  </div>}
  <BottomNav/></div>
}

function SectionTitle({title,action}){return <div className="section-title"><h2>{title}</h2>{action}</div>}
function ToolGroup({title,items,favorites,toggle}){return <section className="section"><SectionTitle title={title}/><div className="tool-list">{items.map(t=><ToolCard key={t.id} tool={t} favorite={favorites.includes(t.id)} onFavorite={()=>toggle(t.id)}/>)}</div></section>}

function Tools(){const [favorites,toggle]=useFavorites();return <div className="app-shell"><header className="topbar"><Logo/><span className="page-label">Ferramentas</span></header><main className="page"><section className="page-intro"><p className="eyebrow">CENTRAL DE UTILIDADES</p><h1>Tudo para deixar<br/><em>mais fácil.</em></h1></section><div className="tool-list">{tools.map(t=><ToolCard key={t.id} tool={t} favorite={favorites.includes(t.id)} onFavorite={()=>toggle(t.id)}/>)}</div><section className="section"><SectionTitle title="Em breve"/><div className="soon-grid">{soon.map((x,i)=><div className="soon-item" key={x.name} data-testid={`tools-soon-${i}`}><x.icon size={18}/><span>{x.name}</span><small>Em breve</small></div>)}</div></section></main><BottomNav active="tools"/></div>}

function ImageGenPage(){
  const tool = toolMap["image_gen"];
  const nav = useNavigate();
  const [usage, refreshUsage] = useUsage();
  const [prompt, setPrompt] = useState("");
  const [aspect, setAspect] = useState("1:1");
  const [loading, setLoading] = useState(false);
  const [imageUrl, setImageUrl] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [limitReached, setLimitReached] = useState(false);
  const [authRequired, setAuthRequired] = useState(false);
  const [shared, setShared] = useState(false);

  const remaining = usage?.image_remaining;
  const limit = usage?.image_limit ?? 3;
  const premium = usage?.is_premium;

  const generate = async () => {
    if (!getToken()) { setAuthRequired(true); return; }
    if (!prompt.trim()) { setErrorMsg("Descreva a imagem que você quer criar."); return; }
    setLoading(true); setErrorMsg(""); setImageUrl(""); setShared(false);
    try {
      const r = await axios.post(`${API}/generate-image`, { prompt: prompt.trim(), aspect_ratio: aspect }, { headers: authHeaders() });
      setImageUrl(r.data.image_url);
      refreshUsage();
    } catch (e) {
      if (e.response?.status === 401) setAuthRequired(true);
      else if (e.response?.status === 402) setLimitReached(true);
      else setErrorMsg(e.response?.data?.detail || "Não foi possível gerar a imagem agora.");
    }
    setLoading(false);
  };

  const download = async () => {
    if (!imageUrl) return;
    try {
      const resp = await fetch(imageUrl);
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = `facilita-ai-${Date.now()}.png`;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    } catch {
      window.open(imageUrl, "_blank");
    }
  };

  const share = async () => {
    if (!imageUrl) return;
    if (navigator.share) {
      try {
        const resp = await fetch(imageUrl);
        const blob = await resp.blob();
        const file = new File([blob], "facilita-ai.png", { type: blob.type || "image/png" });
        if (navigator.canShare && navigator.canShare({ files: [file] })) {
          await navigator.share({ files: [file], title: "Facilita AI", text: prompt });
          setShared(true);
          return;
        }
        await navigator.share({ title: "Facilita AI", text: prompt, url: imageUrl });
        setShared(true);
      } catch { /* usuário cancelou */ }
    } else {
      navigator.clipboard?.writeText(imageUrl);
      setShared(true);
    }
  };

  return <div className="app-shell">
    <header className="tool-header"><Link to="/" data-testid="tool-back-button"><ArrowLeft size={20}/></Link><span>Facilita AI</span><button data-testid="tool-more-button"><MoreHorizontal size={21}/></button></header>
    <main className="page tool-page">
      <div className={`tool-hero ${tool.color}`}><span className="tool-icon"><tool.icon size={25}/></span><div><p className="eyebrow">FERRAMENTA FACILITA</p><h1>{tool.name}</h1><p>{tool.desc}</p></div></div>
      <div className="usage-row"><UsageBadge usage={usage ? {is_premium: premium, remaining, limit} : null} onUpgrade={()=>nav("/premium")}/></div>
      <div className="form-section">
        <label className="field-label">Descreva a imagem que quer criar</label>
        <textarea data-testid="image_gen-input" value={prompt} onChange={e=>setPrompt(e.target.value.slice(0,1000))} placeholder="Ex.: um gato astronauta flutuando no espaço, arte digital, cores vibrantes" maxLength={1000}/>
        <div className="char-counter" data-testid="image_gen-char-counter"><span>{prompt.length}/1000</span></div>
        <div className="chips" data-testid="image_gen-options">
          {[["1:1","Quadrada"],["9:16","Retrato"],["16:9","Paisagem"]].map(([v,l]) => (
            <button key={v} className={aspect===v?"selected":""} onClick={()=>setAspect(v)} data-testid={`image_gen-aspect-${v.replace(":","x")}`}>
              <span className={`aspect-preview a-${v.replace(":","x")}`}/> {l} <small>{v}</small>
            </button>
          ))}
        </div>
        {errorMsg && <div className="error-message" data-testid="image_gen-error">{errorMsg}</div>}
        <button className="primary-action" onClick={generate} disabled={loading || !prompt.trim()} data-testid="image_gen-generate-button">
          <Sparkles size={18}/>{loading ? "Criando sua imagem..." : "Gerar imagem"}
        </button>
      </div>
      {loading && <div className="image-loading" data-testid="image_gen-loading"><div className="image-loading-inner"><Sparkles size={22}/><p>Criando sua imagem no FLUX.1 Schnell — leva ~5 segundos</p></div></div>}
      {imageUrl && !loading && <section className="result-panel image-result" data-testid="image_gen-result">
        <div className="result-top"><div><p className="eyebrow">SUA IMAGEM</p><h2>Pronta para usar</h2></div></div>
        <div className={`image-preview aspect-${aspect.replace(":","x")}`}><img src={imageUrl} alt={prompt} data-testid="image_gen-image"/></div>
        <div className="result-actions">
          <button onClick={download} data-testid="image_gen-download-button"><Download size={16}/> Baixar</button>
          <button onClick={share} data-testid="image_gen-share-button"><Share2 size={16}/> {shared ? "Compartilhado" : "Compartilhar"}</button>
          <button onClick={generate} data-testid="image_gen-retry-button" disabled={loading}><WandSparkles size={16}/> Gerar de novo</button>
        </div>
      </section>}
      <AdBanner/>
    </main>
    {limitReached && <div className="modal-overlay" onClick={()=>setLimitReached(false)} data-testid="limit-reached-modal">
      <div className="modal-card limit-modal" onClick={e=>e.stopPropagation()}>
        <div className="limit-icon"><ImagePlus size={24}/></div>
        <h3>Você chegou ao limite de imagens de hoje ✨</h3>
        <p>Você usou suas {limit} imagens gratuitas de hoje. Volte amanhã ou assine o Premium para gerar mais agora mesmo.</p>
        <div className="limit-actions">
          <button className="primary-action" onClick={()=>{setLimitReached(false); nav("/premium");}} data-testid="limit-upgrade-button"><Sparkles size={18}/> Assinar Premium</button>
          <button className="ghost-action" onClick={()=>setLimitReached(false)} data-testid="limit-dismiss-button">Agora não</button>
        </div>
      </div>
    </div>}
    {authRequired && <div className="modal-overlay" onClick={()=>setAuthRequired(false)} data-testid="auth-required-modal">
      <div className="modal-card limit-modal" onClick={e=>e.stopPropagation()}>
        <div className="limit-icon"><UserRound size={24}/></div>
        <h3>Crie sua conta grátis para usar o Facilita AI</h3>
        <p>Com uma conta você guarda seu histórico, favoritos e recebe imagens grátis por dia.</p>
        <div className="limit-actions">
          <button className="primary-action" onClick={()=>nav("/login?mode=register")} data-testid="auth-required-register-button"><Sparkles size={18}/> Criar conta grátis</button>
          <button className="ghost-action" onClick={()=>nav("/login")} data-testid="auth-required-login-button">Entrar</button>
        </div>
      </div>
    </div>}
    <BottomNav active="tools"/>
  </div>
}

function ToolRouter(){
  const {id} = useParams();
  if (id === "image_gen") return <ImageGenPage/>;
  if (id === "audio_gen") return <AudioGenPage/>;
  return <ToolPage/>;
}

function AudioGenPage(){
  const tool = toolMap["audio_gen"];
  const nav = useNavigate();
  const [usage, refreshUsage] = useUsage();
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState("");
  const [audioInfo, setAudioInfo] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [limitReached, setLimitReached] = useState(false);
  const [authRequired, setAuthRequired] = useState(false);
  const [shared, setShared] = useState(false);
  const [voices, setVoices] = useState([]);
  const [voiceFilter, setVoiceFilter] = useState("all"); // all | female | male
  const [selectedVoiceId, setSelectedVoiceId] = useState("");
  const [playingPreviewId, setPlayingPreviewId] = useState("");

  const usedSec = usage?.audio_used_seconds ?? 0;
  const limitSec = usage?.audio_limit_seconds ?? 60;
  const remainingSec = usage?.audio_remaining_seconds ?? 60;
  const maxGenSec = usage?.audio_max_seconds_per_gen ?? 60;
  const chars = text.length;
  const estimatedSec = Math.round((chars / 15) * 10) / 10; // pré-visualização apenas
  const overGen = estimatedSec > maxGenSec;
  const overDaily = estimatedSec > remainingSec;
  const selectedVoice = voices.find(v => v.voice_id === selectedVoiceId) || voices[0];
  const filteredVoices = voices.filter(v => voiceFilter === "all" || v.gender === voiceFilter);

  useEffect(() => () => { if (audioUrl) URL.revokeObjectURL(audioUrl); }, [audioUrl]);

  useEffect(() => {
    axios.get(`${API}/voices`).then(r => {
      const list = r.data?.voices || [];
      setVoices(list);
      if (list.length > 0 && !selectedVoiceId) setSelectedVoiceId(list[0].voice_id);
    }).catch(() => { /* fallback: usa a padrão do backend */ });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const playPreview = (v) => {
    if (!v.preview_url) return;
    // Para preview em andamento se clicar outra
    if (window._facilitaPreviewAudio) { try { window._facilitaPreviewAudio.pause(); } catch {} }
    const a = new Audio(v.preview_url);
    window._facilitaPreviewAudio = a;
    setPlayingPreviewId(v.voice_id);
    a.play().catch(() => setPlayingPreviewId(""));
    a.onended = () => setPlayingPreviewId("");
    a.onerror = () => setPlayingPreviewId("");
  };

  const generate = async () => {
    if (!getToken()) { setAuthRequired(true); return; }
    if (!text.trim()) { setErrorMsg("Digite o texto que você quer transformar em áudio."); return; }
    if (overGen) { setErrorMsg(`Este texto excede o limite de ${maxGenSec}s por geração. Reduza o texto.`); return; }
    if (overDaily) { setLimitReached(true); return; }
    setLoading(true); setErrorMsg(""); setShared(false);
    if (audioUrl) { URL.revokeObjectURL(audioUrl); setAudioUrl(""); setAudioInfo(null); }
    try {
      const body = { text: text.trim() };
      if (selectedVoiceId) body.voice_id = selectedVoiceId;
      const resp = await axios.post(`${API}/generate-audio`, body, {
        headers: authHeaders(),
        responseType: "blob",
      });
      const blob = resp.data;
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
      setAudioInfo({
        charsSent: resp.headers["x-chars-sent"],
        creditsBilled: resp.headers["x-credits-billed"] || null,
        durationReal: resp.headers["x-duration-real"] || null,
        durationEstimated: resp.headers["x-duration-estimated"],
        costUsdEstimated: resp.headers["x-cost-usd-estimated"],
        costUsdReal: resp.headers["x-cost-usd-real"],
        minSaleBrl: resp.headers["x-min-sale-brl"],
        voiceName: selectedVoice?.name || "padrão",
      });
      refreshUsage();
    } catch (e) {
      const status = e.response?.status;
      let detail = "";
      try {
        if (e.response?.data instanceof Blob) {
          const txt = await e.response.data.text();
          detail = JSON.parse(txt)?.detail || txt;
        } else {
          detail = e.response?.data?.detail || "";
        }
      } catch { detail = ""; }
      if (status === 401) setAuthRequired(true);
      else if (status === 402) setLimitReached(true);
      else if (status === 413) setErrorMsg(detail || "Texto excede o limite permitido.");
      else if (status === 503) setErrorMsg(detail || "Geração de áudio ainda não configurada.");
      else setErrorMsg(detail || "Não foi possível gerar o áudio agora.");
    }
    setLoading(false);
  };

  const download = () => {
    if (!audioUrl) return;
    const a = document.createElement("a");
    a.href = audioUrl; a.download = `facilita-ai-${Date.now()}.mp3`;
    document.body.appendChild(a); a.click(); a.remove();
  };

  const share = async () => {
    if (!audioUrl) return;
    if (navigator.share) {
      try {
        const resp = await fetch(audioUrl);
        const blob = await resp.blob();
        const file = new File([blob], "facilita-ai.mp3", { type: "audio/mpeg" });
        if (navigator.canShare && navigator.canShare({ files: [file] })) {
          await navigator.share({ files: [file], title: "Facilita AI", text: text });
          setShared(true); return;
        }
        await navigator.share({ title: "Facilita AI", text });
        setShared(true);
      } catch { /* cancelado */ }
    }
  };

  return <div className="app-shell">
    <header className="tool-header"><Link to="/" data-testid="tool-back-button"><ArrowLeft size={20}/></Link><span>Facilita AI</span><button data-testid="tool-more-button"><MoreHorizontal size={21}/></button></header>
    <main className="page tool-page">
      <div className={`tool-hero ${tool.color}`}><span className="tool-icon"><tool.icon size={25}/></span><div><p className="eyebrow">FERRAMENTA FACILITA</p><h1>{tool.name}</h1><p>{tool.desc}</p></div></div>
      <div className="usage-row" data-testid="audio_gen-usage">
        <span className="usage-pill"><Volume2 size={14}/> {remainingSec.toFixed?.(0) ?? remainingSec}s restantes hoje <small>({usedSec}s / {limitSec}s)</small></span>
      </div>

      {voices.length > 0 && <div className="voice-picker" data-testid="voice-picker">
        <div className="voice-picker-head">
          <label className="field-label">Escolha uma voz</label>
          <div className="voice-filter" data-testid="voice-filter">
            {[["all","Todas"],["female","Femininas"],["male","Masculinas"]].map(([v,l]) => (
              <button
                key={v}
                className={voiceFilter===v?"selected":""}
                onClick={()=>setVoiceFilter(v)}
                data-testid={`voice-filter-${v}`}
              >{l}</button>
            ))}
          </div>
        </div>
        {filteredVoices.length === 0 ? <p className="hint-message" data-testid="voice-empty">Nenhuma voz {voiceFilter==="female"?"feminina":voiceFilter==="male"?"masculina":""} disponível no momento.</p> :
        <div className="voice-list">
          {filteredVoices.map(v => {
            const isSel = v.voice_id === selectedVoiceId;
            const isPlaying = playingPreviewId === v.voice_id;
            return <div key={v.voice_id} className={`voice-card ${isSel?"selected":""}`} data-testid={`voice-card-${v.voice_id}`}>
              <div className="voice-info">
                <strong>{v.name}</strong>
                <small>{v.gender === "female" ? "Feminina" : v.gender === "male" ? "Masculina" : "Voz"} · {v.language || "pt-BR"}{v.accent?` · ${v.accent}`:""}</small>
                {v.description && <span className="voice-desc">{v.description}</span>}
              </div>
              <div className="voice-actions">
                {v.preview_url && <button
                  className="voice-preview-btn"
                  onClick={()=>playPreview(v)}
                  data-testid={`voice-preview-${v.voice_id}`}
                  aria-label={`Ouvir prévia de ${v.name}`}
                >{isPlaying ? <Pause size={14}/> : <Play size={14}/>} {isPlaying?"Ouvindo…":"Ouvir"}</button>}
                <button
                  className={`voice-select-btn ${isSel?"selected":""}`}
                  onClick={()=>setSelectedVoiceId(v.voice_id)}
                  data-testid={`voice-select-${v.voice_id}`}
                >{isSel ? "Selecionada" : "Selecionar"}</button>
              </div>
            </div>
          })}
        </div>}
      </div>}

      <div className="form-section">
        <label className="field-label">Digite o texto que virará áudio (pt-BR)</label>
        <textarea
          data-testid="audio_gen-input"
          value={text}
          onChange={e=>setText(e.target.value.slice(0,3000))}
          placeholder="Ex.: Olá! Este é um lembrete: sua reunião começa em 15 minutos."
          maxLength={3000}
          rows={5}
        />
        <div className="char-counter" data-testid="audio_gen-char-counter">
          <span>{chars}/3000 caracteres</span>
          <span className={overGen || overDaily ? "over" : ""}>≈ {estimatedSec}s de áudio (estimado)</span>
        </div>
        {selectedVoice && <p className="voice-selected-line" data-testid="voice-selected-line">
          Voz selecionada: <strong>{selectedVoice.name}</strong> <small>({selectedVoice.gender === "female" ? "Feminina" : selectedVoice.gender === "male" ? "Masculina" : "voz"})</small>
        </p>}
        {errorMsg && <div className="error-message" data-testid="audio_gen-error">{errorMsg}</div>}
        <button
          className="primary-action"
          onClick={generate}
          disabled={loading || !text.trim() || overGen || overDaily}
          data-testid="audio_gen-generate-button"
        >
          <Sparkles size={18}/>{loading ? "Gerando áudio..." : "Gerar áudio"}
        </button>
        {(overGen || overDaily) && !errorMsg && <p className="hint-message" data-testid="audio_gen-hint">
          {overGen ? `Reduza o texto para caber em ${maxGenSec}s por geração.` : `Você tem ${remainingSec.toFixed?.(0) ?? remainingSec}s restantes hoje. Reduza o texto ou volte amanhã.`}
        </p>}
      </div>
      {loading && <div className="image-loading" data-testid="audio_gen-loading"><div className="image-loading-inner"><Sparkles size={22}/><p>Sintetizando voz com ElevenLabs Flash — alguns segundos…</p></div></div>}
      {audioUrl && !loading && <section className="result-panel image-result" data-testid="audio_gen-result">
        <div className="result-top"><div><p className="eyebrow">SEU ÁUDIO</p><h2>Pronto para ouvir</h2></div></div>
        <audio controls src={audioUrl} data-testid="audio_gen-player" style={{width:"100%",marginTop:"12px"}}/>
        {audioInfo && <div className="audio-meta audio-meta-grid" data-testid="audio_gen-meta">
          <div><small>Voz</small><strong>{audioInfo.voiceName}</strong></div>
          <div><small>Duração real</small><strong>{audioInfo.durationReal ? `${parseFloat(audioInfo.durationReal).toFixed(2)}s` : `~${audioInfo.durationEstimated}s`}</strong></div>
          <div><small>Caracteres enviados</small><strong>{audioInfo.charsSent}</strong></div>
          {audioInfo.creditsBilled && <div><small>Créditos ElevenLabs</small><strong>{audioInfo.creditsBilled}</strong></div>}
          {audioInfo.costUsdEstimated && <div><small>Custo estimado</small><strong>US$ {parseFloat(audioInfo.costUsdEstimated).toFixed(6)}</strong></div>}
          {audioInfo.costUsdReal && <div><small>Custo real</small><strong>US$ {parseFloat(audioInfo.costUsdReal).toFixed(6)}</strong></div>}
        </div>}
        <div className="result-actions">
          <button onClick={download} data-testid="audio_gen-download-button"><Download size={16}/> Baixar MP3</button>
          <button onClick={share} data-testid="audio_gen-share-button"><Share2 size={16}/> {shared ? "Compartilhado" : "Compartilhar"}</button>
          <button onClick={generate} data-testid="audio_gen-retry-button" disabled={loading}><WandSparkles size={16}/> Gerar de novo</button>
        </div>
      </section>}
      <AdBanner/>
    </main>
    {limitReached && <div className="modal-overlay" onClick={()=>setLimitReached(false)} data-testid="audio-limit-modal">
      <div className="modal-card limit-modal" onClick={e=>e.stopPropagation()}>
        <div className="limit-icon"><Volume2 size={24}/></div>
        <h3>Você chegou ao limite de áudio de hoje ✨</h3>
        <p>Você usou seus {limitSec} segundos de áudio grátis de hoje. Volte amanhã ou assine o Premium para gerar mais agora mesmo.</p>
        <div className="limit-actions">
          <button className="primary-action" onClick={()=>{setLimitReached(false); nav("/premium");}} data-testid="audio-limit-upgrade-button"><Sparkles size={18}/> Assinar Premium</button>
          <button className="ghost-action" onClick={()=>setLimitReached(false)} data-testid="audio-limit-dismiss-button">Agora não</button>
        </div>
      </div>
    </div>}
    {authRequired && <div className="modal-overlay" onClick={()=>setAuthRequired(false)} data-testid="audio-auth-required-modal">
      <div className="modal-card limit-modal" onClick={e=>e.stopPropagation()}>
        <div className="limit-icon"><UserRound size={24}/></div>
        <h3>Crie sua conta grátis para gerar áudios</h3>
        <p>Com uma conta você tem 60 segundos grátis por dia e guarda seu histórico.</p>
        <div className="limit-actions">
          <button className="primary-action" onClick={()=>nav("/login?mode=register")} data-testid="audio-auth-register-button"><Sparkles size={18}/> Criar conta grátis</button>
          <button className="ghost-action" onClick={()=>nav("/login")} data-testid="audio-auth-login-button">Entrar</button>
        </div>
      </div>
    </div>}
    <BottomNav active="tools"/>
  </div>
}

function ToolPage(){
  const {id}=useParams();
  const tool=tools.find(t=>t.id===id)||tools[0];
  const [result,setResult]=useState("");
  const [loading,setLoading]=useState(false);
  const [copied,setCopied]=useState(false);
  const [limitReached, setLimitReached] = useState(false);
  const [authRequired, setAuthRequired] = useState(false);
  const [usage, refreshUsage] = useUsage();
  const nav = useNavigate();
  const [fields,setFields]=useState({message:"",text:"",topic:"",tone:"😊 Amigável",mode:"Resumo normal",style:"Profissional",platform:"Instagram",emoji:"Com emojis",value:"500",percentage:"20",length:16,letters:true,numbers:true,symbols:true});
  const update=(key,value)=>setFields(f=>({...f,[key]:value}));
  const inputField = id==="whatsapp" ? "message" : (id==="create_email"||id==="create_caption"||id==="youtube_titles") ? "topic" : "text";
  const inputValue = fields[inputField];
  const isAi = ["whatsapp","improve_text","correct_pt","summarize","create_email","create_caption","youtube_titles"].includes(id);

  const generate = async () => {
    // Todas as ferramentas exigem cadastro/login antes do uso.
    if (!getToken()) { setAuthRequired(true); return; }
    setLoading(true); setCopied(false);
    try {
      const res = await axios.post(`${API}/generate`, { tool: id, payload: fields }, { headers: authHeaders() });
      setResult(res.data.result);
      if (isAi) refreshUsage();
    } catch (e) {
      if (e.response?.status === 401) { setAuthRequired(true); }
      else if (e.response?.status === 402) { setLimitReached(true); }
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
        <p>Você usou seus {usage?.limit ?? 3} acessos gratuitos de hoje. Volte amanhã ou assine o Premium para continuar agora mesmo.</p>
        <div className="limit-actions">
          <button className="primary-action" onClick={()=>{setLimitReached(false); nav("/premium");}} data-testid="limit-upgrade-button"><Sparkles size={18}/> Assinar Premium</button>
          <button className="ghost-action" onClick={()=>setLimitReached(false)} data-testid="limit-dismiss-button">Agora não</button>
        </div>
      </div>
    </div>}
    {authRequired && <div className="modal-overlay" onClick={()=>setAuthRequired(false)} data-testid="auth-required-modal">
      <div className="modal-card limit-modal" onClick={e=>e.stopPropagation()}>
        <div className="limit-icon"><UserRound size={24}/></div>
        <h3>Crie sua conta grátis para usar o Facilita AI</h3>
        <p>Com uma conta você guarda seu histórico, favoritos e recebe 3 usos de IA por dia sem pagar nada.</p>
        <div className="limit-actions">
          <button className="primary-action" onClick={()=>nav("/login?mode=register")} data-testid="auth-required-register-button"><Sparkles size={18}/> Criar conta grátis</button>
          <button className="ghost-action" onClick={()=>nav("/login")} data-testid="auth-required-login-button">Entrar</button>
        </div>
      </div>
    </div>}
    <BottomNav active="tools"/>
  </div>
}

function Auth(){
  const initial = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("mode") === "register" ? "register" : "login";
  const [mode,setMode]=useState(initial);
  const [email,setEmail]=useState(initial==="register"?"":"admin@facilita.ai");
  const [password,setPassword]=useState(initial==="register"?"":"Facilita@123");
  const [name,setName]=useState("");
  const [message,setMessage]=useState("");
  const nav=useNavigate();
  const submit=async e=>{
    e.preventDefault();
    try{
      const r=await axios.post(`${API}/auth/${mode}`,{email,password,name});
      localStorage.setItem("facilita_token",r.data.token);
      localStorage.setItem("facilita_user",JSON.stringify(r.data.user));
      nav("/");
    }catch(err){setMessage(err.response?.data?.detail||"Confira seus dados")}
  };
  return <div className="auth-page"><div className="auth-brand"><Logo/></div><main className="auth-box"><p className="eyebrow">FACILITA AI</p><h1>{mode==="login"?"Bem-vindo de volta.":"Crie sua conta grátis."}</h1><p>{mode==="login"?"Entre para guardar seus resultados e favoritos.":"Comece a resolver seu dia em poucos cliques."}</p><form onSubmit={submit}>{mode==="register" && <label>Nome<input data-testid="auth-name-input" value={name} onChange={e=>setName(e.target.value)}/></label>}<label>E-mail<input data-testid="auth-email-input" type="email" value={email} onChange={e=>setEmail(e.target.value)} required/></label><label>Senha<input data-testid="auth-password-input" type="password" value={password} onChange={e=>setPassword(e.target.value)} required minLength={6}/></label>{message&&<div className="error-message" data-testid="auth-error-message">{message}</div>}<button className="primary-action" data-testid="auth-submit-button">{mode==="login"?"Entrar":"Criar conta grátis"}</button></form><button className="google-button" data-testid="google-login-button" onClick={()=>setMessage("Login Google será conectado no painel administrativo.")}>Continuar com Google</button><button className="switch-auth" onClick={()=>setMode(mode==="login"?"register":"login")} data-testid="auth-mode-switch">{mode==="login"?"Ainda não tenho conta":"Já tenho uma conta"}</button></main></div>
}

function Favorites(){
  const [favorites, toggle] = useFavorites();
  return <div className="app-shell">
    <header className="topbar"><Logo/><span className="page-label">Favoritos</span></header>
    <main className="page">
      <section className="page-intro compact"><p className="eyebrow">SEU JEITO DE USAR</p><h1>O que você<br/><em>mais gosta.</em></h1></section>
      {favorites.length ? <div className="tool-list">{tools.filter(t=>favorites.includes(t.id)).map(t=><ToolCard key={t.id} tool={t} favorite onFavorite={()=>toggle(t.id)}/>)}</div> : <Empty icon={Star} text="Você ainda não favoritou nenhuma ferramenta."/>}
    </main>
    <BottomNav active="tools"/>
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
                    <span className="history-copy"><strong>{toolMap[it.tool]?.name||it.tool}</strong><small>{it.tool === "image_gen" ? (it.prompt?.prompt || "Imagem gerada") : it.tool === "audio_gen" ? ((it.prompt?.text||"").slice(0,60)+"...") + ` • ${(it.duration_seconds||0).toFixed?.(1) ?? it.duration_seconds}s` : (it.result||"").slice(0,60)+"..."}</small></span>
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
          {openItem.tool === "image_gen"
            ? <div className="image-preview" data-testid="history-modal-image-preview"><img src={openItem.result} alt="Imagem gerada"/></div>
            : openItem.tool === "audio_gen"
            ? <div className="result-text" data-testid="history-modal-audio">
                <p><strong>Texto:</strong> {openItem.prompt?.text}</p>
                <p><strong>Duração:</strong> {(openItem.duration_seconds||0).toFixed?.(2) ?? openItem.duration_seconds}s</p>
                <p><strong>Caracteres:</strong> enviados {openItem.prompt?.chars_sent} · cobrados {openItem.prompt?.chars_billed ?? openItem.prompt?.chars_sent}</p>
                <p className="hint-message">O arquivo de áudio não é armazenado no histórico. Gere novamente para ouvir.</p>
              </div>
            : <div className="result-text">{openItem.result}</div>}
          <div className="result-actions">
            {openItem.tool === "image_gen"
              ? <a href={openItem.result} target="_blank" rel="noreferrer" className="history-modal-open" data-testid="history-modal-open-image"><Download size={16}/> Abrir imagem</a>
              : openItem.tool === "audio_gen"
              ? null
              : <button onClick={()=>{navigator.clipboard?.writeText(openItem.result)}} data-testid="history-modal-copy"><Copy size={16}/> Copiar</button>}
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
  const premium = isPremium(user) || usage?.is_premium;
  const [invoices, setInvoices] = useState(null);
  const logout = () => { localStorage.removeItem("facilita_token"); localStorage.removeItem("facilita_user"); localStorage.removeItem("facilita_favorites"); window.location.href = "/"; };

  useEffect(() => {
    if (!getToken()) return;
    axios.get(`${API}/subscription/invoices`, { headers: authHeaders() }).then(r => setInvoices(r.data.invoices || [])).catch(() => setInvoices([]));
  }, []);

  const fmtDate = (iso) => { try { return new Date(iso).toLocaleDateString("pt-BR"); } catch { return "-"; } };
  const fmtBRL = (v) => `R$ ${Number(v||0).toFixed(2).replace(".", ",")}`;
  const statusLabel = (s) => ({approved:"Pago", rejected:"Recusado", pending:"Aguardando", in_process:"Aguardando", cancelled:"Cancelado", refunded:"Reembolsado"}[s] || s);

  return <div className="app-shell">
    <header className="topbar"><Logo/><span className="page-label">Perfil</span></header>
    <main className="page">
      <GraceBanner usage={usage}/>
      <section className="profile-card"><span className="avatar"><UserRound size={25}/></span><div><p className="eyebrow">SEU PERFIL {premium && <span className="plan-tag" data-testid="plan-tag-premium">PREMIUM</span>}</p><h2>{user?.name||"Visitante"}</h2><p>{user?.email||"Use sem cadastro ou entre para sincronizar"}</p></div></section>
      {usage && <div className="usage-summary" data-testid="profile-usage-summary"><span>Usos de IA hoje</span><strong>{usage.used} / {usage.limit}</strong><small>{premium ? "Plano Premium" : "Plano Grátis"}</small></div>}
      {!premium && <Link className="premium-strip" to="/premium" data-testid="premium-card"><span><Sparkles size={20}/></span><div><strong>Facilita AI Premium</strong><small>Mais usos, sem anúncios e recursos avançados</small></div><ChevronRight/></Link>}
      {premium && <Link className="premium-strip active" to="/premium" data-testid="premium-card-active"><span><Sparkles size={20}/></span><div><strong>Você é Premium</strong><small>Ver benefícios e gerenciar sua assinatura</small></div><ChevronRight/></Link>}

      {user && invoices !== null && invoices.length > 0 && <section className="section">
        <div className="section-title"><h2>Faturas</h2><small>últimas cobranças</small></div>
        <div className="invoice-list" data-testid="invoice-list">
          {invoices.map(inv => <div key={inv.id} className="invoice-row" data-testid={`invoice-${inv.id}`}>
            <div className="invoice-main">
              <strong>{fmtBRL(inv.amount)}</strong>
              <small>{fmtDate(inv.date)}</small>
            </div>
            <span className={`invoice-status ${inv.status}`} data-testid={`invoice-status-${inv.id}`}>{statusLabel(inv.status)}</span>
          </div>)}
        </div>
      </section>}
      {user && invoices !== null && invoices.length === 0 && <p className="helper" data-testid="invoice-empty">Nenhuma cobrança registrada ainda.</p>}

      <div className="settings-list">
        {user?.role === "admin" && <Link to="/admin" data-testid="profile-admin-link"><Shield size={18}/> Painel administrativo<ChevronRight size={17}/></Link>}
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
  const [status, setStatus] = useState({ tone: "", text: "" });
  const [loading, setLoading] = useState(false);
  const [subscription, setSubscription] = useState(null);
  const user = getUser();
  const premium = isPremium(user) || subscription?.is_premium;

  // Carrega estado da assinatura (para mostrar botão cancelar / próxima cobrança)
  useEffect(() => {
    if (!getToken()) return;
    axios.get(`${API}/subscription`, { headers: authHeaders() }).then(r => setSubscription(r.data)).catch(() => {});
  }, []);

  // Reconcilia retorno do checkout de assinatura do Mercado Pago
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const preapprovalId = params.get("preapproval_id");
    if (!preapprovalId) return;

    setStatus({ tone: "info", text: "Confirmando sua assinatura no Mercado Pago..." });
    let attempts = 0;
    const check = async () => {
      attempts++;
      try {
        const r = await axios.get(`${API}/subscription`, { headers: authHeaders() });
        setSubscription(r.data);
        if (r.data.preapproval_status === "authorized") {
          setStatus({ tone: "success", text: "Assinatura ativada! Seu Premium está liberado e renova todo mês." });
          try {
            const me = await axios.get(`${API}/auth/me`, { headers: authHeaders() });
            localStorage.setItem("facilita_user", JSON.stringify(me.data));
            setTimeout(() => window.location.reload(), 1300);
          } catch { /* ignore */ }
          return;
        }
        if (r.data.preapproval_status === "cancelled" || r.data.preapproval_status === "canceled") {
          setStatus({ tone: "error", text: "A assinatura não foi autorizada. Tente novamente." });
          return;
        }
        if (attempts < 6) setTimeout(check, 2500);
        else setStatus({ tone: "info", text: "Ainda processando com o Mercado Pago. Recarregue em instantes." });
      } catch {
        if (attempts < 4) setTimeout(check, 2500);
        else setStatus({ tone: "error", text: "Não conseguimos confirmar sua assinatura agora. Recarregue em instantes." });
      }
    };
    check();
    const url = new URL(window.location.href);
    ["preapproval_id","payment_id","status","external_reference","merchant_order_id","preference_id","payment_type","collection_id","collection_status"].forEach(k=>url.searchParams.delete(k));
    window.history.replaceState({}, "", url.toString());
  }, []);

  const subscribe = async () => {
    if (!getToken()) { nav("/login"); return; }
    setLoading(true);
    setStatus({ tone: "", text: "" });
    try {
      const r = await axios.post(`${API}/checkout/premium`, {}, { headers: authHeaders() });
      if (r.data?.init_point) {
        window.location.assign(r.data.init_point);
        return;
      }
      setStatus({ tone: "error", text: "Não recebemos o link de checkout. Tente novamente." });
    } catch (e) {
      setStatus({ tone: "error", text: e.response?.data?.detail || "Não foi possível iniciar a assinatura agora." });
    }
    setLoading(false);
  };

  const cancel = async () => {
    if (!window.confirm("Tem certeza que deseja cancelar sua assinatura? Você mantém o Premium até o fim do ciclo atual.")) return;
    setLoading(true); setStatus({ tone: "", text: "" });
    try {
      const r = await axios.post(`${API}/subscription/cancel`, {}, { headers: authHeaders() });
      setStatus({ tone: "success", text: r.data.message || "Assinatura cancelada." });
      const sub = await axios.get(`${API}/subscription`, { headers: authHeaders() });
      setSubscription(sub.data);
      try {
        const me = await axios.get(`${API}/auth/me`, { headers: authHeaders() });
        localStorage.setItem("facilita_user", JSON.stringify(me.data));
      } catch { /* ignore */ }
    } catch (e) {
      setStatus({ tone: "error", text: e.response?.data?.detail || "Não foi possível cancelar agora." });
    }
    setLoading(false);
  };

  const price = settings?.premium_price_brl?.toFixed(2).replace(".", ",") ?? "9,90";
  const freeLimit = settings?.free_daily_limit ?? 10;
  const premiumLimit = settings?.premium_daily_limit ?? 500;

  return <div className="app-shell">
    <header className="tool-header"><Link to="/perfil" data-testid="premium-back-button"><ArrowLeft size={20}/></Link><span>Facilita AI Premium</span><span/></header>
    <main className="page premium-page">
      <GraceBanner usage={{in_grace_period: subscription?.in_grace_period, grace_days_left: subscription?.grace_days_left}}/>
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
            <li><Check size={15}/> Cancele quando quiser, sem multa</li>
          </ul>
          {premium
            ? <>
                {subscription?.next_payment_date && subscription.preapproval_status === "authorized" && <p className="next-charge" data-testid="next-charge">Próxima cobrança: {new Date(subscription.next_payment_date).toLocaleDateString("pt-BR")}</p>}
                {subscription?.preapproval_status === "authorized"
                  ? <button className="ghost-action" onClick={cancel} disabled={loading} data-testid="premium-cancel-button">{loading?"Processando...":"Cancelar assinatura"}</button>
                  : <button className="primary-action" disabled data-testid="premium-active-button">Assinatura ativa</button>}
              </>
            : <button className="primary-action" onClick={subscribe} disabled={loading} data-testid="premium-subscribe-button"><Sparkles size={18}/> {loading?"Abrindo checkout...":"Assinar Premium"}</button>}
        </div>
      </div>
      {status.text && <div className={`checkout-note ${status.tone}`} data-testid="checkout-note">{status.text}</div>}
      <p className="helper premium-fineprint">Assinatura mensal recorrente processada com segurança pelo Mercado Pago. Você pode cancelar quando quiser pelo próprio app.</p>
    </main>
    <BottomNav active="profile"/>
  </div>
}
function Empty({icon:Icon,text}){return <div className="empty-state" data-testid="empty-state"><span><Icon size={27}/></span><p>{text}</p><Link to="/ferramentas" className="outline-button" data-testid="empty-state-action">Explorar ferramentas</Link></div>}
function Legal(){return <div className="app-shell"><header className="tool-header"><Link to="/perfil" data-testid="legal-back-button"><ArrowLeft size={20}/></Link><span>Privacidade</span></header><main className="page legal"><p className="eyebrow">FACILITA AI</p><h1>Termos e privacidade</h1><p>O Facilita AI foi criado para simplificar seu dia. Textos enviados às ferramentas de inteligência artificial podem ser processados por provedores externos para gerar o resultado solicitado.</p><h2>Uso responsável</h2><p>Não envie dados sensíveis, senhas ou informações pessoais que não sejam necessárias. O app registra apenas métricas de uso e histórico quando você escolhe estar conectado.</p><h2>Contato</h2><p>Fale com a equipe em contato@facilita.ai</p></main></div>}

function AdminSlider({ label, value, onChange, min, max, step = 1, suffix = "", testid }){
  const [local, setLocal] = useState(value);
  useEffect(() => { setLocal(value); }, [value]);
  useEffect(() => {
    if (local === value) return;
    const t = setTimeout(() => onChange(local), 350);
    return () => clearTimeout(t);
  }, [local, onChange, value]);
  return <label className="admin-slider">
    <span className="admin-slider-top"><strong>{label}</strong><span className="admin-slider-value" data-testid={`${testid}-value`}>{local}{suffix}</span></span>
    <input type="range" min={min} max={max} step={step} value={local} onChange={e=>setLocal(Number(e.target.value))} data-testid={testid}/>
    <span className="admin-slider-range"><small>{min}{suffix}</small><small>{max}{suffix}</small></span>
  </label>
}
function AdminSwitch({ label, hint, checked, onChange, testid }){
  return <label className="admin-switch">
    <div><strong>{label}</strong>{hint && <small>{hint}</small>}</div>
    <span className={`switch ${checked?"on":""}`} onClick={()=>onChange(!checked)} data-testid={testid}><span className="switch-dot"/></span>
  </label>
}

function Admin(){
  const nav = useNavigate();
  const user = getUser();
  const [settings, setSettings] = useState(null);
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState("");
  const [savedAt, setSavedAt] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user || user.role !== "admin") { nav("/"); return; }
    Promise.all([
      axios.get(`${API}/admin/settings`, { headers: authHeaders() }),
      axios.get(`${API}/admin/stats`, { headers: authHeaders() }),
      axios.get(`${API}/admin/users`, { headers: authHeaders() }),
    ]).then(([s, st, u]) => { setSettings(s.data); setStats(st.data); setUsers(u.data); })
     .catch(e => setError(e.response?.data?.detail || "Falha ao carregar painel"));
  }, [nav, user]);

  const saveSettings = async (patch) => {
    setSaving(true); setError("");
    try {
      const r = await axios.put(`${API}/admin/settings`, patch, { headers: authHeaders() });
      setSettings(r.data);
      setSavedAt(new Date());
    } catch (e) { setError(e.response?.data?.detail || "Não foi possível salvar."); }
    setSaving(false);
  };

  const searchUsers = async (q) => {
    setSearch(q);
    try {
      const r = await axios.get(`${API}/admin/users${q?`?search=${encodeURIComponent(q)}`:""}`, { headers: authHeaders() });
      setUsers(r.data);
    } catch { /* ignore */ }
  };

  const setPlan = async (u, plan) => {
    try {
      const r = await axios.post(`${API}/admin/users/${u.id}/subscription`, { plan }, { headers: authHeaders() });
      setUsers(users.map(x => x.id === u.id ? r.data.user : x));
    } catch (e) { setError(e.response?.data?.detail || "Falha ao alterar assinatura"); }
  };

  if (!settings) return <div className="app-shell"><header className="tool-header"><Link to="/perfil"><ArrowLeft size={20}/></Link><span>Painel administrativo</span><span/></header><main className="page"><p className="helper">{error||"Carregando painel..."}</p></main></div>;

  return <div className="app-shell">
    <header className="tool-header"><Link to="/perfil" data-testid="admin-back-button"><ArrowLeft size={20}/></Link><span>Painel administrativo</span><span/></header>
    <main className="page admin-page">
      <section className="page-intro compact"><p className="eyebrow">FACILITA AI · ADMIN</p><h1>Configure seu<br/><em>Facilita AI.</em></h1></section>

      {stats && <div className="admin-stats">
        <div className="admin-stat" data-testid="admin-stat-users"><small>Usuários</small><strong>{stats.users}</strong></div>
        <div className="admin-stat" data-testid="admin-stat-gens"><small>Gerações totais</small><strong>{stats.generations}</strong></div>
        <div className="admin-stat" data-testid="admin-stat-tools"><small>Ferramentas ativas</small><strong>{stats.tools?.length||0}</strong></div>
      </div>}

      <section className="admin-card">
        <div className="admin-card-head"><h2>Limites de IA</h2><small>Aplicado imediatamente para todos os usuários.</small></div>
        <AdminSlider testid="admin-slider-free-limit" label="Usos diários no plano Grátis" value={settings.free_daily_limit} min={0} max={100} onChange={v=>saveSettings({free_daily_limit:v})} suffix=" usos"/>
        <AdminSlider testid="admin-slider-premium-limit" label="Usos diários no plano Premium" value={settings.premium_daily_limit} min={10} max={2000} step={10} onChange={v=>saveSettings({premium_daily_limit:v})} suffix=" usos"/>
      </section>

      <section className="admin-card">
        <div className="admin-card-head"><h2>Limites de imagens (fal.ai)</h2><small>Geração de imagens FLUX.1 tem custo por chamada. Ajuste o teto por plano.</small></div>
        <AdminSlider testid="admin-slider-free-image-limit" label="Imagens diárias no plano Grátis" value={settings.free_daily_image_limit ?? 3} min={0} max={30} onChange={v=>saveSettings({free_daily_image_limit:v})} suffix=" imgs"/>
        <AdminSlider testid="admin-slider-premium-image-limit" label="Imagens diárias no plano Premium" value={settings.premium_daily_image_limit ?? 50} min={5} max={500} step={5} onChange={v=>saveSettings({premium_daily_image_limit:v})} suffix=" imgs"/>
      </section>

      <section className="admin-card">
        <div className="admin-card-head"><h2>Preço do Premium</h2><small>Valor cobrado mensalmente (assinatura recorrente via Mercado Pago).</small></div>
        <AdminSlider testid="admin-slider-price" label="Preço em BRL" value={settings.premium_price_brl} min={4.9} max={99.9} step={0.1} onChange={v=>saveSettings({premium_price_brl:Number(v.toFixed(2))})} suffix=" R$"/>
      </section>

      <section className="admin-card">
        <div className="admin-card-head"><h2>Publicidade</h2><small>Todos os anúncios são desligados automaticamente para assinantes Premium.</small></div>
        <AdminSwitch testid="admin-switch-ads" label="Publicidade global" hint="Desativa todos os formatos com um clique" checked={settings.ads_enabled} onChange={v=>saveSettings({ads_enabled:v})}/>
        <AdminSwitch testid="admin-switch-banner" label="Banners" hint="Faixas discretas no topo/rodapé" checked={settings.banner_enabled} onChange={v=>saveSettings({banner_enabled:v})}/>
        <AdminSwitch testid="admin-switch-interstitial" label="Intersticiais" hint="Anúncios em transições, sem interromper resultado" checked={settings.interstitial_enabled} onChange={v=>saveSettings({interstitial_enabled:v})}/>
      </section>

      <section className="admin-card">
        <div className="admin-card-head"><h2>Assinantes</h2><small>Promova ou rebaixe manualmente. Busque por e-mail.</small></div>
        <label className="searchbox admin-search"><Search size={18}/><input value={search} onChange={e=>searchUsers(e.target.value)} placeholder="Buscar por e-mail" data-testid="admin-user-search"/></label>
        <div className="admin-user-list">
          {users.map(u => {
            const uPremium = u?.subscription?.plan === "premium" && (!u.subscription.expires_at || new Date(u.subscription.expires_at) > new Date());
            return <div className="admin-user" key={u.id} data-testid={`admin-user-${u.id}`}>
              <div><strong>{u.name || u.email}</strong><small>{u.email} · {u.role}{uPremium?" · PREMIUM":""}</small></div>
              <div className="admin-user-actions">
                {uPremium
                  ? <button className="ghost-action" onClick={()=>setPlan(u,"free")} data-testid={`admin-user-downgrade-${u.id}`}>Remover Premium</button>
                  : <button className="primary-action tiny" onClick={()=>setPlan(u,"premium")} data-testid={`admin-user-upgrade-${u.id}`}><Sparkles size={14}/> Tornar Premium</button>}
              </div>
            </div>;
          })}
          {users.length === 0 && <p className="helper">Nenhum usuário encontrado.</p>}
        </div>
      </section>

      <div className="admin-footer">
        {error && <span className="admin-error" data-testid="admin-error">{error}</span>}
        {saving && <span className="admin-saving">Salvando...</span>}
        {savedAt && !saving && <span className="admin-saved" data-testid="admin-saved">Alterações salvas • {savedAt.toLocaleTimeString("pt-BR").slice(0,5)}</span>}
      </div>
    </main>
  </div>
}

function App(){return <BrowserRouter><Routes><Route path="/" element={<Home/>}/><Route path="/ferramentas" element={<Tools/>}/><Route path="/ferramenta/:id" element={<ToolRouter/>}/><Route path="/login" element={<Auth/>}/><Route path="/favoritos" element={<Favorites/>}/><Route path="/historico" element={<History/>}/><Route path="/perfil" element={<Profile/>}/><Route path="/premium" element={<Premium/>}/><Route path="/admin" element={<Admin/>}/><Route path="/termos" element={<Legal/>}/></Routes></BrowserRouter>}
export default App;
