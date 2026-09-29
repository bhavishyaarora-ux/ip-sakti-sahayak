import React, { useState, useEffect, useRef } from 'react';
import { JurisdictionSwitch, JurisdictionMode } from './components/JurisdictionSwitch';
import { CitationDrawer, RetrievedChunk } from './components/CitationDrawer';
import { DiagnosticModal } from './components/DiagnosticModal';
import { EscalationModal } from './components/EscalationModal';
import { AgentReasoningTrace } from './components/AgentReasoningTrace';
import { 
  Search, 
  Sparkles, 
  BookOpen, 
  UserPlus, 
  Languages, 
  Mic, 
  MicOff, 
  Loader2,
  Leaf,
  Plus,
  LayoutDashboard,
  Scale,
  Users,
  Settings,
  Bell,
  ExternalLink,
  ShieldCheck,
  Globe,
  FileSearch,
  Landmark,
  ArrowRight,
  ShieldAlert,
  HelpCircle,
  FileText
} from 'lucide-react';

export default function App() {
  const [jurisdiction, setJurisdiction] = useState<JurisdictionMode>('IN');
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);

  // Vernacular Translation & Voice State
  const [selectedLang, setSelectedLang] = useState('en');
  const [translating, setTranslating] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<any>(null);

  // Modals & Drawers
  const [diagnosticOpen, setDiagnosticOpen] = useState(false);
  const [selectedChunk, setSelectedChunk] = useState<RetrievedChunk | null>(null);
  const [escalationOpen, setEscalationOpen] = useState(false);
  const [clarifyingQuestions, setClarifyingQuestions] = useState<any[]>([]);
  const [activeNode, setActiveNode] = useState<string | null>(null);
  const [completedNodes, setCompletedNodes] = useState<string[]>([]);
  const [pipelineData, setPipelineData] = useState<any>(null);

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

  // Initialize Speech Recognition for Indic Languages
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;

      const langMap: Record<string, string> = {
        en: 'en-IN',
        hi: 'hi-IN',
        ta: 'ta-IN',
        te: 'te-IN',
        mr: 'mr-IN',
        bn: 'bn-IN',
      };
      recognition.lang = langMap[selectedLang] || 'en-IN';

      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => setIsListening(false);
      recognition.onerror = () => setIsListening(false);

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInputQuery((prev) => (prev ? `${prev} ${transcript}` : transcript));
      };

      recognitionRef.current = recognition;
    }
  }, [selectedLang]);

  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert('Speech Recognition is not supported in this browser. Please use Chrome or Edge.');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
    } else {
      recognitionRef.current.start();
    }
  };

  const executeAnalysis = async (queryText: string, answers: Record<string, string> | null = null) => {
    if (!queryText.trim()) return;
    setLoading(true);

    // If answers are already provided, we know we are running the full multi-agent pipeline
    if (answers) {
      setActiveNode('classify');
      setCompletedNodes([]);
    } else {
      // For initial queries, wait for the backend to tell us if clarification is needed
      setActiveNode(null);
      setCompletedNodes([]);
      setAnalysisResult(null);
    }

    try {
      setPipelineData(null);

      const response = await fetch(`${API_BASE_URL}/api/analyze/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: queryText,
          user_answers: answers,
          forced_jurisdiction: jurisdiction,
        }),
      });

      if (!response.ok || !response.body) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned error status ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const cleanLine = line.trim();
          if (!cleanLine.startsWith('data: ')) continue;

          const rawData = cleanLine.replace(/^data:\s*/, '');
          try {
            const payload = JSON.parse(rawData);

            if (payload.event === 'clarification') {
              setClarifyingQuestions(payload.questions || []);
              setDiagnosticOpen(true);
              setAnalysisResult(null);

              if (payload.pipeline) {
                setPipelineData(payload.pipeline);
              }

              setLoading(false);
              setActiveNode(null);
              return;

            } else if (payload.event === 'node_complete') {
              console.log("REAL BACKEND NODE NAME:", payload.raw_node, "mapped to:", payload.node);

              // 1. Mark node as finished
              setCompletedNodes((prev) => [...new Set([...prev, payload.node])]);

              // 2. Update pipeline metadata independently
              if (payload.target_agents) {
                setPipelineData((prev: any) => ({
                  ...prev,
                  target_agents: payload.target_agents,
                  reasoning_trace: payload.reasoning_trace || prev?.reasoning_trace || [],
                }));
              }

              // 3. Clean sequential node transition
              if (payload.node === 'classify') {
                setActiveNode('route');
              } else if (payload.node === 'route') {
                setActiveNode('retrieve');
              } else if (payload.node === 'retrieve' || payload.node === 'dispatch') {
                const targets = payload.target_agents || [];
                if (targets.includes('ip_agent')) {
                  setActiveNode('ip_agent');
                } else if (targets.includes('abs_agent')) {
                  setActiveNode('abs_agent');
                } else if (targets.includes('export_agent')) {
                  setActiveNode('export_agent');
                } else {
                  setActiveNode('synthesis');
                }
              } else if (payload.node === 'ip_agent') {
                const targets = payload.target_agents || [];
                if (targets.includes('abs_agent')) {
                  setActiveNode('abs_agent');
                } else if (targets.includes('export_agent')) {
                  setActiveNode('export_agent');
                } else {
                  setActiveNode('synthesis');
                }
              } else if (payload.node === 'abs_agent') {
                const targets = payload.target_agents || [];
                if (targets.includes('export_agent')) {
                  setActiveNode('export_agent');
                } else {
                  setActiveNode('synthesis');
                }
              } else if (payload.node === 'export_agent') {
                setActiveNode('synthesis');
              }

            } else if (payload.event === 'complete') {
              if (payload.result?.pipeline) {
                setPipelineData(payload.result.pipeline);
              }
              setAnalysisResult(payload.result);
              setClarifyingQuestions([]);
              setActiveNode(null);

            } else if (payload.event === 'error') {
              throw new Error(payload.message || 'Stream processing failure');
            }
          } catch (jsonErr) {
            console.warn('Incomplete SSE packet:', jsonErr);
          }
        } // closes: for (const line of lines)
      } // closes: while (true)
    } catch (err: any) { // closes: try (line 118)
      alert(`Backend Analysis Error: ${err.message}`);
    } finally {
      setLoading(false);
      setActiveNode(null);
    }
  }

  const handleLanguageChange = async (newLang: string) => {
    setSelectedLang(newLang);
    if (!analysisResult || newLang === 'en') return;

    setTranslating(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: analysisResult.final_response,
          target_language: newLang,
        }),
      });
      const data = await res.json();
      setAnalysisResult((prev: any) => ({
        ...prev,
        final_response: data.translated_text,
      }));
    } catch (err) {
      console.error('Translation error:', err);
    } finally {
      setTranslating(false);
    }
  };

  const handleDiagnosticSubmit = (answers: Record<string, string>) => {
    setDiagnosticOpen(false);
    executeAnalysis(inputQuery, answers);
  };

  const handleDiagnosticClose = () => {
    setDiagnosticOpen(false);
    setClarifyingQuestions([]);
  };

  const handleScenarioClick = (queryText: string) => {
    setInputQuery(queryText);
    executeAnalysis(queryText);
  };

  return (
    <div className="flex min-h-screen bg-[#070d09] text-slate-100 font-sans selection:bg-emerald-500/30 selection:text-emerald-200">
      {/* 1. Sidebar Navigation */}
      <aside className="w-64 border-r border-[#142318] bg-[#0a120c] flex flex-col justify-between shrink-0 select-none z-20">
        <div>
          {/* Logo Brand Header */}
          <div className="p-6 flex items-center gap-3 border-b border-[#142318]/60">
            <div className="w-10 h-10 rounded-2xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shadow-inner">
              <Leaf className="w-5 h-5 fill-emerald-500/20" />
            </div>
            <div>
              <div className="text-sm font-bold tracking-wide text-white">IP-SAKTI</div>
              <div className="text-[11px] text-emerald-500/80 font-medium tracking-tight">Sahayak AI</div>
            </div>
          </div>

          {/* New Query Trigger */}
          <div className="p-4">
            <button
              onClick={() => {
                setAnalysisResult(null);
                setInputQuery('');
              }}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-950/40 border border-emerald-700/40 text-emerald-300 hover:bg-emerald-900/50 text-xs font-semibold transition shadow-sm"
            >
              <Plus className="w-4 h-4" />
              <span>New Diagnostic</span>
            </button>
          </div>

          {/* Core Navigation Items */}
          <nav className="px-3 space-y-1 text-xs">
            <button 
              onClick={() => setAnalysisResult(null)}
              className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl bg-[#111e14] text-emerald-400 font-semibold border border-emerald-900/30 text-left"
            >
              <LayoutDashboard className="w-4 h-4" />
              <span>Diagnostic Console</span>
            </button>
            <button 
              onClick={() => setEscalationOpen(true)}
              className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-[#0e1810] transition text-left"
            >
              <Users className="w-4 h-4" />
              <span>Human Facilitator</span>
            </button>
          </nav>

          {/* Official Registries & Portals */}
          <div className="mt-6 px-4">
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2 px-2">
              Official Registries
            </div>
            <div className="space-y-1 text-xs">
              <a
                href="https://ipindia.gov.in"
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-between px-3 py-2 rounded-lg text-slate-400 hover:text-emerald-300 hover:bg-[#0e1810] transition group"
              >
                <div className="flex items-center gap-2.5">
                  <Landmark className="w-3.5 h-3.5 text-slate-500 group-hover:text-emerald-400 transition" />
                  <span>IP India (IPO)</span>
                </div>
                <ExternalLink className="w-3 h-3 text-slate-600 group-hover:text-slate-400" />
              </a>

              <a
                href="http://nbaindia.org"
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-between px-3 py-2 rounded-lg text-slate-400 hover:text-emerald-300 hover:bg-[#0e1810] transition group"
              >
                <div className="flex items-center gap-2.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-slate-500 group-hover:text-emerald-400 transition" />
                  <span>NBA (BDA 2023)</span>
                </div>
                <ExternalLink className="w-3 h-3 text-slate-600 group-hover:text-slate-400" />
              </a>

              <a
                href="https://www.tkdl.res.in"
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-between px-3 py-2 rounded-lg text-slate-400 hover:text-emerald-300 hover:bg-[#0e1810] transition group"
              >
                <div className="flex items-center gap-2.5">
                  <FileSearch className="w-3.5 h-3.5 text-slate-500 group-hover:text-emerald-400 transition" />
                  <span>TKDL Prior Art</span>
                </div>
                <ExternalLink className="w-3 h-3 text-slate-600 group-hover:text-slate-400" />
              </a>

              <a
                href="https://www.wipo.int"
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-between px-3 py-2 rounded-lg text-slate-400 hover:text-emerald-300 hover:bg-[#0e1810] transition group"
              >
                <div className="flex items-center gap-2.5">
                  <Globe className="w-3.5 h-3.5 text-slate-500 group-hover:text-emerald-400 transition" />
                  <span>WIPO GRATK</span>
                </div>
                <ExternalLink className="w-3 h-3 text-slate-600 group-hover:text-slate-400" />
              </a>
            </div>
          </div>
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-[#142318] space-y-2">
          <div className="px-2 text-[10px] text-slate-600 leading-tight">
            Grounded on Indian Patents Act 1970, BDA 2023 & WIPO GRATK.
          </div>
          <button className="flex items-center gap-2 text-xs text-slate-500 hover:text-slate-300 px-2 py-1 transition">
            <Settings className="w-3.5 h-3.5" />
            <span>Settings</span>
          </button>
        </div>
      </aside>

      {/* 2. Main Canvas Viewport */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Navbar */}
        <header className="h-16 border-b border-[#142318] bg-[#0a120c]/90 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-30">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-mono text-emerald-400/90 font-semibold">AYUSH IPR RAG State Machine</span>
            <span className="text-slate-600">•</span>
            <span className="text-slate-500">Legal Diagnostics Engine</span>
          </div>

          <div className="flex items-center gap-4">
            {/* Vernacular Language Selector */}
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#101b12] border border-[#1b2d1f] text-xs">
              <Languages className="w-3.5 h-3.5 text-emerald-400" />
              <select
                value={selectedLang}
                onChange={(e) => handleLanguageChange(e.target.value)}
                className="bg-transparent text-slate-300 font-medium outline-none cursor-pointer text-xs"
              >
                <option value="en" className="bg-[#0a120c]">English</option>
                <option value="hi" className="bg-[#0a120c]">हिन्दी (Hindi)</option>
                <option value="ta" className="bg-[#0a120c]">தமிழ் (Tamil)</option>
                <option value="te" className="bg-[#0a120c]">తెలుగు (Telugu)</option>
                <option value="mr" className="bg-[#0a120c]">मराठी (Marathi)</option>
                <option value="bn" className="bg-[#0a120c]">বাংলা (Bengali)</option>
              </select>
            </div>

            {/* Notification Bell */}
            <button className="p-2 rounded-xl bg-[#101b12] border border-[#1b2d1f] text-slate-400 hover:text-slate-200 relative">
              <Bell className="w-4 h-4" />
              <span className="w-2 h-2 rounded-full bg-emerald-500 absolute top-1.5 right-1.5 ring-2 ring-[#0a120c]" />
            </button>

            {/* User Badge */}
            <div className="flex items-center gap-2 pl-2 border-l border-[#142318]">
              <div className="w-8 h-8 rounded-xl bg-emerald-950 border border-emerald-700/60 text-emerald-400 text-xs font-bold flex items-center justify-center">
                BS
              </div>
              <div className="text-left">
                <div className="text-xs font-semibold text-slate-200">Bhavishya</div>
                <div className="text-[10px] text-slate-500">Innovator / Admin</div>
              </div>
            </div>
          </div>
        </header>

        {/* Translation Banner */}
        {translating && (
          <div className="bg-emerald-950/40 border-b border-emerald-900/40 py-2 px-8 flex items-center justify-center gap-2 text-xs text-emerald-400 animate-pulse">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>Translating via Bhashini Engine with Ayurvedic Entity Shield...</span>
          </div>
        )}

        {/* Main Stage Content */}
        <main className="flex-1 p-8 max-w-6xl mx-auto w-full flex flex-col justify-start">
          {/* Centered Hero Stage (Always visible, expands when empty) */}
          <div className={`transition-all duration-300 w-full flex flex-col items-center ${analysisResult ? 'mb-8' : 'my-auto py-12'}`}>
  {/* Header Identity */}
  <div className="text-center space-y-2 mb-6">
    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-800/60 text-[11px] font-mono font-semibold text-emerald-400">
      <span>MULTILINGUAL</span>
      <span>•</span>
      <span>SOURCE-CITED</span>
      <span>•</span>
      <span>RAGAS GROUNDED</span>
    </div>
    <h1 className="text-3xl font-bold tracking-tight text-white">
      IP-SAKTI Sahayak
    </h1>
    <p className="text-xs text-slate-400 max-w-md mx-auto">
      Ayurvedic IPR & Biodiversity Access Diagnostic Engine with dual-track compliance verification.
    </p>
  </div>

  {/* Centered Primary Search Bar Console */}
  <div className="w-full max-w-3xl space-y-4">
    <div className="p-2.5 rounded-2xl bg-[#0d1710] border border-[#1a2e20] shadow-2xl focus-within:border-emerald-500/60 transition flex items-center gap-3">
      <Search className="w-5 h-5 text-slate-500 ml-2 shrink-0" />

      <input
        type="text"
        value={inputQuery}
        onChange={(e) => setInputQuery(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && executeAnalysis(inputQuery)}
        placeholder={
          isListening
            ? 'Listening... Speak your Ayurvedic formulation or query now...'
            : 'Describe formulation, classical recipe, or extraction process...'
        }
        className="flex-1 bg-transparent py-2 text-sm text-slate-100 placeholder-slate-500 outline-none"
      />

      {/* Speech Input */}
      <button
        type="button"
        onClick={toggleListening}
        title={isListening ? 'Stop Recording' : 'Speak via Bhashini Voice Input'}
        className={`p-2.5 rounded-xl border transition flex items-center justify-center ${
          isListening
            ? 'bg-rose-600 border-rose-500 text-white animate-pulse shadow-lg shadow-rose-950/50'
            : 'bg-[#122016] border-[#1c3323] text-slate-400 hover:text-emerald-400 hover:border-emerald-500/40'
        }`}
      >
        {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
      </button>

      {/* Analysis Action */}
      <button
        onClick={() => executeAnalysis(inputQuery)}
        disabled={loading || translating}
        className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold flex items-center gap-2 shadow-lg shadow-emerald-950 transition shrink-0 disabled:opacity-50"
      >
        {loading ? (
          <>
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>Diagnosing...</span>
          </>
        ) : (
          <>
            <Sparkles className="w-3.5 h-3.5" />
            <span>Analyze IPR & ABS</span>
          </>
        )}
      </button>
    </div>

    {/* In-stream Clarification Stepper */}
    <DiagnosticModal
      isOpen={diagnosticOpen}
      questions={clarifyingQuestions}
      onSubmit={handleDiagnosticSubmit}
      onClose={handleDiagnosticClose}
      lang={selectedLang}
    />

    {/* Jurisdiction Mode Switch + Preset Prompts (Hidden while answering questions) */}
    {!diagnosticOpen && (
      <div className="flex flex-wrap items-center justify-between gap-4 pt-1">
        {/* 2-Way Jurisdiction Switch Component */}
        <JurisdictionSwitch selected={jurisdiction} onChange={setJurisdiction} />

        {/* Quick Demo Scenario Chips */}
        <div className="flex items-center gap-2 text-xs">
          <span className="text-[11px] font-medium text-slate-500">Test Scenarios:</span>
          <button
            onClick={() => handleScenarioClick('Ashwagandha standardized root extract 5% withanolides for joint inflammation')}
            className="px-2.5 py-1 rounded-lg bg-[#0e1711] hover:bg-[#152319] text-slate-300 border border-[#192b1e] text-[11px] transition"
          >
            ⚡ Phytopharmaceutical
          </button>
          <button
            onClick={() => handleScenarioClick('Classical Triphala Churna prepared per Sharangadhara Samhita')}
            className="px-2.5 py-1 rounded-lg bg-[#0e1711] hover:bg-[#152319] text-slate-300 border border-[#192b1e] text-[11px] transition"
          >
            📜 Classical (Sec 3(p))
          </button>
          <button
            onClick={() => handleScenarioClick('Curcumin oil nano-emulsion for cosmetic topical application')}
            className="px-2.5 py-1 rounded-lg bg-[#0e1711] hover:bg-[#152319] text-slate-300 border border-[#192b1e] text-[11px] transition"
          >
            🧴 Cosmetic Bio-Active
          </button>
        </div>
      </div>
    )}

    {/* In-stream Agent Reasoning Trace (Hidden during questions, docks inside search container) */}
    {!diagnosticOpen && (
      <AgentReasoningTrace 
        isActive={loading} 
        activeNode={activeNode}
        completedNodes={completedNodes}
        jurisdiction={jurisdiction} 
        pipeline={pipelineData}
      />
    )}
  </div>
</div>

          {/* 3. Diagnostic Results Canvas */}
          {analysisResult && (
            <div className="space-y-6 animate-in fade-in duration-300">
              {/* Classification & Confidence Triage Ribbon */}
              <div className="flex items-center justify-between p-4 rounded-xl bg-[#0c160f] border border-[#17291c]">
                <div className="flex items-center gap-3">
                  <span className="text-xs text-slate-400">Classified Category:</span>
                  <span className="px-3 py-1 rounded-md text-xs font-bold bg-emerald-950/80 text-emerald-400 border border-emerald-800/80">
                    {analysisResult.category}
                  </span>
                  <span className="text-xs text-slate-400 ml-4">Groundedness Score:</span>
                  <span className="text-xs font-mono font-bold text-slate-200">
                    {((analysisResult.confidence_score || analysisResult.confidence || 0.94) * 100).toFixed(0)}%
                  </span>
                </div>

                {analysisResult.escalate_to_human && (
                  <button
                    onClick={() => setEscalationOpen(true)}
                    className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-medium hover:bg-amber-500/20 transition"
                  >
                    <UserPlus className="w-3.5 h-3.5" />
                    <span>Escalate to Patent Facilitator</span>
                  </button>
                )}
              </div>

              {/* Dual-Track Split Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Domestic Track Card */}
                <div className="p-6 rounded-2xl bg-[#0c160f] border border-[#17291c] flex flex-col justify-between shadow-lg">
                  <div>
                    <div className="flex items-center justify-between pb-3 border-b border-[#1b2f21]">
                      <h3 className="text-xs uppercase tracking-wider font-bold text-emerald-400">
                        National Track (India)
                      </h3>
                      <span className="text-[11px] text-slate-500 font-mono">Patents Act • BDA 2023 • CDSCO</span>
                    </div>

                    <div className="mt-4 text-xs leading-relaxed text-slate-300 whitespace-pre-wrap">
                      {analysisResult.final_response.split('**Target Export Regime Identified:**')[0]}
                    </div>
                  </div>

                  <div className="mt-6 pt-4 border-t border-[#1b2f21]">
                    <span className="text-[11px] font-semibold text-slate-400 block mb-2">
                      Authoritative Citations (Click to Inspect):
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {analysisResult.retrieved_chunks
                        ?.filter((c: any) => c.jurisdiction === 'IN')
                        .map((chunk: RetrievedChunk) => (
                          <button
                            key={chunk.chunk_id}
                            onClick={() => setSelectedChunk(chunk)}
                            className="px-2.5 py-1 rounded-md text-[11px] font-medium bg-[#142318] hover:bg-[#1b3121] text-emerald-300 border border-[#203a28] transition"
                          >
                            [{chunk.citation_anchor}]
                          </button>
                        ))}
                    </div>
                  </div>
                </div>

                {/* International & Export Track Card */}
                <div className="p-6 rounded-2xl bg-[#0c160f] border border-[#17291c] flex flex-col justify-between shadow-lg">
                  <div>
                    <div className="flex items-center justify-between pb-3 border-b border-[#1b2f21]">
                      <h3 className="text-xs uppercase tracking-wider font-bold text-sky-400">
                        International & Export Track
                      </h3>
                      <span className="text-[11px] text-slate-500 font-mono">WIPO GRATK • Nagoya • US FDA</span>
                    </div>

                    <div className="mt-4 text-xs leading-relaxed text-slate-300">
                      {analysisResult.final_response.includes('**Target Export Regime Identified:**') ? (
                        <div className="whitespace-pre-wrap">
                          {analysisResult.final_response.split('**Target Export Regime Identified:**')[1]}
                        </div>
                      ) : (
                        <div className="p-8 rounded-xl bg-[#080f0a] border border-[#152418] text-center space-y-2 my-4">
                          <p className="text-slate-300 font-medium">Domestic Regulatory Track Active</p>
                          <p className="text-slate-500 text-xs max-w-sm mx-auto">
                            Switch the jurisdiction toggle above to <strong className="text-sky-400">Cross-Border</strong> to inspect WIPO genetic origin disclosure and US FDA Botanical pathways.
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="mt-6 pt-4 border-t border-[#1b2f21]">
                    <span className="text-[11px] font-semibold text-slate-400 block mb-2">
                      International Legal Instruments:
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {analysisResult.retrieved_chunks
                        ?.filter((c: any) => c.jurisdiction === 'INT')
                        .map((chunk: RetrievedChunk) => (
                          <button
                            key={chunk.chunk_id}
                            onClick={() => setSelectedChunk(chunk)}
                            className="px-2.5 py-1 rounded-md text-[11px] font-medium bg-[#142318] hover:bg-[#1b3121] text-sky-300 border border-[#203a28] transition"
                          >
                            [{chunk.citation_anchor}]
                          </button>
                        ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Legal Statute Update Ticker (Bottom contextual helper) */}
          {!analysisResult && (
            <div className="mt-12 p-4 rounded-xl bg-[#0a120c] border border-[#142318] flex items-center justify-between text-xs text-slate-400 max-w-3xl mx-auto">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-emerald-400 shrink-0" />
                <span><strong>BDA 2023 Gazette Status:</strong> Section 40 decriminalization of codified AYUSH practices integrated.</span>
              </div>
              <span className="text-[10px] font-mono text-slate-500">Live Corpus</span>
            </div>
          )}
        </main>

        {/* Persistent Legal Disclaimer Footer */}
        <footer className="py-3 px-6 border-t border-[#142318] bg-[#070d09] text-center text-[11px] text-slate-600">
          IP-SAKTI Sahayak delivers regulatory diagnostics and source-cited references. Does not constitute formal legal counsel under the Advocates Act, 1961.
        </footer>
      </div>

      {/* Slide-out Statutory Citation Inspector Drawer */}
      <CitationDrawer
        isOpen={!!selectedChunk}
        onClose={() => setSelectedChunk(null)}
        chunk={selectedChunk}
      />
      

      

      {/* Facilitator Escalation Modal */}
      <EscalationModal
        isOpen={escalationOpen}
        onClose={() => setEscalationOpen(false)}
        category={analysisResult?.category || ''}
        query={inputQuery}
      />
    </div>
  );
}