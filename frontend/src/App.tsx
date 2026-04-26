import React, { useState, useRef, useEffect } from 'react';
import { Shield, Zap, TrendingUp, Skull, Link } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface Log {
  agent: string;
  message: string;
}

interface Result {
  name: string;
  integrity_score: number;
  classification_list: string[];
  persona_label: string;
  brutal_roast: string;
  anchor_facts: string[];
  future_milestone: string;
  nemesis_persona: string;
  nemesis_rivalry: string;
}

const SafeRender = ({ value }: { value: any }) => {
  if (value === null || value === undefined) return null;
  if (typeof value === 'object') return <span>{JSON.stringify(value)}</span>;
  return <span>{String(value)}</span>;
};

function App() {
  const [name, setName] = useState('');
  const [context, setContext] = useState('');
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [logs, setLogs] = useState<Log[]>([]);
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    window.history.scrollRestoration = 'manual';
    window.scrollTo(0, 0);
  }, []);

  const scrollToBottom = () => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [logs]);

  const runAnalysis = async () => {
    setLoading(true);
    setLogs([]);
    setResult(null);
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';
    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, context, linkedin_url: linkedinUrl }),
      });
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) return;
      let pendingResult: any = null;
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'log') {
                setLogs(prev => [...prev, { agent: data.agent, message: data.message }]);
              } else if (data.type === 'result') {
                pendingResult = data;
              }
            } catch (e) { }
          }
        }
      }
      if (pendingResult) {
        setLogs(prev => [...prev, { agent: 'System', message: 'UPLINK_STABLE. VERDICT_REPORT_UNLOCKED.' }]);
        setResult(pendingResult);
      }
      setLoading(false);
    } catch (error) {
      setLogs(prev => [...prev, { agent: 'SYSTEM', message: 'CRITICAL_FAILURE: UPLINK_LOST' }]);
      setLoading(false);
    }
  };

  return (
    <div className="bg-[#0d1117] text-[#4ade80] font-mono p-6">
      <div className="max-w-6xl mx-auto space-y-10">
        
        {/* Header - No Absolute or Relative positioning */}
        <div className="text-center py-8 border-b border-[#4ade80]/20">
          <h1 className="text-4xl font-black tracking-tighter text-[#4ade80] uppercase flex items-center justify-center">
            <Shield className="w-10 h-10 mr-4 opacity-80" />
            VIBE_AUTOPSY
          </h1>
          <p className="mt-4 text-[0.7rem] tracking-[0.8em] text-[#4ade80]/30 font-bold uppercase">
             Forensic_Uplink_Established
          </p>
        </div>

        {/* Input Area - Simple Block Elements */}
        <div className="bg-[#161b22] border border-[#4ade80]/20 p-10">
          
          <div className="mb-8">
            <label className="block text-[0.65rem] font-black text-[#4ade80]/40 uppercase tracking-[0.4em] mb-3">Target_Identifier</label>
            <input
              type="text"
              className="w-full bg-[#0d1117] border border-[#4ade80]/20 p-5 text-[#4ade80] outline-none focus:border-[#4ade80] font-bold text-xl cursor-text"
              placeholder="NAME"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className="mb-8">
            <label className="block text-[0.65rem] font-black text-[#4ade80]/40 uppercase tracking-[0.4em] mb-3">Context_Anchor</label>
            <input
              type="text"
              className="w-full bg-[#0d1117] border border-[#4ade80]/20 p-5 text-[#4ade80] outline-none focus:border-[#4ade80] font-bold text-xl cursor-text"
              placeholder="ANCHOR"
              value={context}
              onChange={(e) => setContext(e.target.value)}
            />
          </div>

          <div className="mb-2">
            <label className="block text-[0.65rem] font-black text-[#4ade80]/40 uppercase tracking-[0.4em] mb-3">LinkedIn_Record</label>
            <div className="flex flex-col md:flex-row gap-6">
              <input
                type="text"
                className="flex-1 bg-[#0d1117] border border-[#4ade80]/20 p-5 text-[#4ade80] outline-none focus:border-[#4ade80] font-bold text-lg cursor-text"
                placeholder="HTTPS://LINKEDIN.COM/IN/PROFILE"
                value={linkedinUrl}
                onChange={(e) => setLinkedinUrl(e.target.value)}
              />
              <button
                onClick={runAnalysis}
                disabled={loading || !name}
                className="bg-[#4ade80] text-[#0d1117] px-12 py-5 font-black uppercase text-sm tracking-[0.4em] hover:bg-white transition-all disabled:opacity-30 active:scale-95 whitespace-nowrap"
              >
                {loading ? 'ANALYZING...' : 'RUN_SCAN'}
              </button>
            </div>
          </div>

        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
          {/* Logs */}
          <div className="border border-[#4ade80]/20 bg-[#0d1117] flex flex-col h-[700px]">
            <div className="bg-[#4ade80]/5 border-b border-[#4ade80]/20 px-6 py-3 text-[0.7rem] font-black uppercase tracking-[0.3em]">
              Agent_Protocol_Dialogue.sys
            </div>
            <div className="p-8 overflow-y-auto space-y-6 text-[0.95rem] flex-1 scrollbar-hide font-bold">
              {logs.map((log, i) => (
                <div key={i} className="flex space-x-4 border-l-2 border-[#4ade80]/10 pl-4">
                  <span className={`text-[0.75rem] uppercase shrink-0 mt-1 font-black ${
                    log.agent === 'Agent_Scout' ? 'text-cyan-400' : 
                    log.agent === 'Agent_Vibe' ? 'text-orange-400' : 'text-[#4ade80]/40'
                  }`}>{log.agent}:</span>
                  <span className="opacity-95 text-[#f0f0f0] italic uppercase font-bold"><SafeRender value={log.message} /></span>
                </div>
              ))}
              <div ref={logEndRef} />
            </div>
          </div>

          {/* Report */}
          <div className="border border-[#4ade80]/20 bg-[#0d1117] flex flex-col h-[700px] shadow-2xl">
            <div className="bg-[#4ade80]/5 border-b border-[#4ade80]/20 px-6 py-3 text-[0.7rem] font-black uppercase text-center tracking-[0.3em]">
              Forensic_Manifest_Report
            </div>
            <div className="p-10 overflow-y-auto space-y-16 flex-1 scrollbar-hide">
              {result && (
                <div className="space-y-16 font-bold animate-in fade-in duration-1000">
                  <div className="border-b border-[#4ade80]/10 pb-12">
                    <div className="text-[0.65rem] text-[#4ade80]/40 uppercase mb-4 font-black tracking-widest uppercase text-xs">Digital Persona Identification</div>
                    <div className="text-3xl font-black text-[#0d1117] bg-[#4ade80] px-6 py-2 inline-block uppercase mb-12 shadow-[10px_10px_0_rgba(74,222,128,0.1)]">
                      <SafeRender value={result.persona_label} />
                    </div>
                    
                    <div className="space-y-6">
                        <div className="text-[0.65rem] text-[#4ade80]/40 uppercase mb-3 font-black tracking-widest uppercase text-xs">Persona Sync Index</div>
                        <div className="flex items-center space-x-12">
                          <div className={`text-6xl font-black ${result.integrity_score > 70 ? 'text-[#4ade80]' : 'text-orange-500'} tracking-tighter tabular-nums`}>
                            {result.integrity_score}<span className="text-3xl opacity-30 ml-4 font-black">%</span>
                          </div>
                          <div className="text-[0.8rem] text-[#e0e0e0]/60 uppercase leading-relaxed border-l-2 border-[#4ade80]/20 pl-8 font-bold max-w-[300px]">
                            How well you're lying to LinkedIn vs. reality.
                          </div>
                        </div>
                    </div>
                  </div>

                  <div className="space-y-6">
                    <div className="text-lg font-black uppercase text-[#4ade80] tracking-[0.3em] border-b border-[#4ade80]/10 pb-2 uppercase text-xs">Digital Classification</div>
                    <ul className="space-y-4 pl-4">
                      {result.classification_list?.map((c, i) => (
                        <li key={i} className="text-[1.1rem] flex items-start">
                          <span className="text-[#4ade80] mr-5 font-black mt-1 uppercase text-lg">»</span>
                          <span className="text-[#f0f0f0] uppercase font-bold"><SafeRender value={c} /></span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="bg-orange-500/5 border-l-4 border-orange-500 p-12 relative shadow-lg">
                    <div className="text-[0.8rem] text-orange-500 font-black uppercase mb-6 tracking-[0.5em] text-xs">Subliminal Observation</div>
                    <p className="text-[1.2rem] italic leading-relaxed text-orange-50 font-bold antialiased leading-loose uppercase">
                      "<SafeRender value={result.brutal_roast} />"
                    </p>
                  </div>

                  <div className="grid grid-cols-1 gap-12">
                    <div className="border border-purple-500/20 bg-purple-500/5 p-10 shadow-xl">
                      <div className="flex items-center space-x-4 text-purple-400 mb-8 uppercase text-[0.8rem] font-black tracking-[0.5em] text-xs">
                        <TrendingUp className="w-7 h-7" />
                        <span>Destiny Manifest 2040</span>
                      </div>
                      <div className="text-[1.2rem] text-purple-100 font-bold uppercase underline decoration-purple-500/20 underline-offset-8 leading-relaxed italic antialiased tracking-tight">
                        <SafeRender value={result.future_milestone} />
                      </div>
                    </div>

                    <div className="border border-red-500/20 bg-red-500/5 p-10 shadow-xl">
                      <div className="flex items-center space-x-4 text-red-500 mb-8 uppercase text-[0.8rem] font-black tracking-[0.5em] text-xs">
                        <Skull className="w-7 h-7" />
                        <span>Adversary Signature</span>
                      </div>
                      <div className="space-y-8">
                        <div className="text-[0.7rem] text-red-500/50 uppercase font-black tracking-widest italic mb-2 uppercase text-xs">The professional plotting to out-curate you.</div>
                        <div className="text-xl text-red-100 font-black uppercase tracking-widest border-b border-red-500/10 pb-6 uppercase">
                            <SafeRender value={result.nemesis_persona} />
                        </div>
                        <p className="text-[1.1rem] text-red-200 italic font-bold leading-relaxed uppercase">
                          <SafeRender value={result.nemesis_rivalry} />
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-8 pb-16">
                    <div className="text-base text-[#4ade80]/20 font-black uppercase tracking-[0.8em] flex items-center justify-center text-xs">
                       --- Verified_Nodes ---
                    </div>
                    <div className="flex flex-wrap gap-6 justify-center">
                      {result.anchor_facts?.map((f, i) => (
                        <div key={i} className="text-[0.8rem] border border-[#4ade80]/10 px-6 py-3 bg-black/40 text-[#4ade80]/60 tracking-tighter font-black uppercase hover:text-[#4ade80] hover:border-[#4ade80]/40 transition-all cursor-crosshair">
                          {'>'} <SafeRender value={f} />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
