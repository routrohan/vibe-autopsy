import { useState, useRef, useEffect } from 'react';
import { Shield, TrendingUp, Skull } from 'lucide-react';

const Github = ({ className }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
    <path d="M9 18c-4.51 2-5-2-7-2" />
  </svg>
);

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
  const [logs, setLogs] = useState<Log[]>([]);
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'logs' | 'report'>('logs');
  const logEndRef = useRef<HTMLDivElement>(null);
  const gridRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    window.history.scrollRestoration = 'manual';
    window.scrollTo(0, 0);
  }, []);

  useEffect(() => {
    if (result) {
      setActiveTab('report');
      setTimeout(() => {
        gridRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
  }, [result]);

  const scrollToBottom = () => {
    if (logs.length > 0) {
      logEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  };

  useEffect(scrollToBottom, [logs]);

  const runAnalysis = async () => {
    setLoading(true);
    setLogs([]);
    setResult(null);
    setActiveTab('logs');
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';
    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, context }),
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
    <div className="bg-[#0d1117] min-h-screen text-[#4ade80] font-mono p-4 md:p-6 relative">
      <div className="max-w-6xl mx-auto space-y-10">
        
        {/* Header */}
        <div className="text-center py-8 border-b border-[#4ade80]/20">
          <h1 className="text-3xl md:text-5xl font-black tracking-tighter text-[#4ade80] uppercase flex items-center justify-center">
            <Shield className="w-8 h-8 md:w-10 md:h-10 mr-3 md:mr-4 opacity-80" />
            HUMBLE ME
          </h1>
          <div className="mt-8 flex flex-col items-center justify-center gap-3">
             <span className="text-xs md:text-sm tracking-[0.5em] text-[#4ade80]/40 font-black uppercase">
               ALGORITHM AUTHORED BY
             </span>
             <div className="flex flex-col md:flex-row flex-wrap items-center justify-center gap-3 md:gap-4">
               <a href="https://rohanrout.com" target="_blank" rel="noopener noreferrer" className="group relative px-6 py-2 border border-orange-500/50 bg-orange-500/5 text-orange-500 hover:bg-orange-500 hover:text-[#0d1117] transition-all duration-300 font-black text-sm tracking-[0.3em] uppercase cursor-pointer shadow-[0_0_15px_rgba(249,115,22,0.15)] hover:shadow-[0_0_25px_rgba(249,115,22,0.4)]">
                 <span className="block group-hover:hidden">ROHAN ROUT</span>
                 <span className="hidden group-hover:block animate-pulse">UNMASK CREATOR ➔</span>
               </a>
               <a href="https://github.com/routrohan/vibe-autopsy" target="_blank" rel="noopener noreferrer" className="flex items-center justify-center gap-2 px-6 py-2 border border-[#4ade80]/40 bg-[#4ade80]/5 text-[#4ade80]/70 hover:bg-[#4ade80] hover:text-[#0d1117] transition-all duration-300 font-black text-sm tracking-[0.2em] uppercase cursor-pointer">
                 <Github className="w-4 h-4" />
                 <span>PROJECT REPO</span>
               </a>
             </div>
          </div>
        </div>

        {/* Input Area */}
        <div className="bg-[#161b22] border border-[#4ade80]/20 p-6 md:p-10">
          
          <div className="mb-10 p-4 border border-yellow-500/30 bg-yellow-500/5 text-yellow-500/80 text-xs md:text-sm font-black uppercase tracking-[0.2em] leading-relaxed text-center">
            [SYSTEM WARNING]: If the algorithm roasts a completely different person despite you dropping 5 anchors... there are just too many of you out there. Be more original.
          </div>
          
          <div className="mb-8">
            <label className="block text-xs md:text-sm font-black text-[#4ade80]/40 uppercase tracking-[0.4em] mb-3">Target_Identifier</label>
            <input
              type="text"
              className="w-full bg-[#0d1117] border border-[#4ade80]/20 p-5 text-[#4ade80] outline-none focus:border-[#4ade80] font-bold text-xl cursor-text"
              placeholder="NAME"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className="mb-2">
            <label className="block text-xs md:text-sm font-black text-[#4ade80]/40 uppercase tracking-[0.4em] mb-3">Context_Anchor</label>
            <div className="flex flex-col md:flex-row gap-6">
              <input
                type="text"
                className="flex-1 w-full bg-[#0d1117] border border-[#4ade80]/20 p-5 text-[#4ade80] outline-none focus:border-[#4ade80] font-bold text-xl cursor-text"
                placeholder="COMPANY, UNIVERSITY, OR CITY"
                value={context}
                onChange={(e) => setContext(e.target.value)}
              />
              <button
                onClick={runAnalysis}
                disabled={loading || !name}
                className="bg-[#4ade80] text-[#0d1117] px-12 py-5 font-black uppercase text-sm tracking-[0.4em] hover:bg-white transition-all disabled:opacity-30 active:scale-95 whitespace-nowrap"
              >
                {loading ? 'ANALYZING...' : 'RUN_SCAN'}
              </button>
            </div>
            <div className="mt-3 text-[0.65rem] md:text-xs text-[#4ade80]/30 font-black uppercase tracking-widest">
              [NOTE]: Drop a company, university, or city here so the algorithm locks onto the right person.
            </div>
          </div>
        </div>

        {/* Main Grid Area */}
        <div ref={gridRef} className="space-y-4">
          {/* Mobile Tab Switcher */}
          <div className="flex lg:hidden border border-[#4ade80]/20 bg-[#161b22] p-1">
            <button 
              onClick={() => setActiveTab('logs')}
              className={`flex-1 py-3 font-black text-[0.7rem] tracking-[0.3em] transition-all ${activeTab === 'logs' ? 'bg-[#4ade80] text-[#0d1117]' : 'text-[#4ade80]/40'}`}
            >
              THE ROAST LOG
            </button>
            <button 
              onClick={() => setActiveTab('report')}
              className={`flex-1 py-3 font-black text-[0.7rem] tracking-[0.3em] transition-all ${activeTab === 'report' ? 'bg-[#4ade80] text-[#0d1117]' : 'text-[#4ade80]/40'} flex items-center justify-center gap-2`}
            >
              REALITY CHECK {result && <span className="w-2 h-2 bg-orange-500 rounded-full animate-pulse" />}
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
            {/* Logs */}
            <div className={`${activeTab === 'logs' ? 'flex' : 'hidden'} lg:flex border border-[#4ade80]/20 bg-[#0d1117] flex-col h-[500px] md:h-[700px]`}>
              <div className="bg-[#4ade80]/5 border-b border-[#4ade80]/20 px-6 py-3 text-xs md:text-sm font-black uppercase tracking-[0.3em]">
                THE ROAST LOG
              </div>
              <div className="p-8 overflow-y-auto space-y-6 text-base md:text-lg flex-1 scrollbar-hide font-bold">
                {logs.map((log, i) => (
                  <div key={i} className="flex space-x-4 border-l-2 border-[#4ade80]/10 pl-4">
                    <span className={`text-sm md:text-base uppercase shrink-0 mt-1 font-black ${
                      log.agent === 'Agent_Scout' ? 'text-cyan-400' : 
                      log.agent === 'Agent_Vibe' ? 'text-orange-400' : 'text-[#4ade80]/40'
                    }`}>{log.agent}:</span>
                    <span className="opacity-95 text-[#f0f0f0] font-medium leading-relaxed tracking-normal"><SafeRender value={log.message} /></span>
                  </div>
                ))}
                <div ref={logEndRef} />
              </div>
            </div>

            {/* Report */}
            <div className={`${activeTab === 'report' ? 'flex' : 'hidden'} lg:flex border border-[#4ade80]/20 bg-[#0d1117] flex-col h-[600px] md:h-[700px] shadow-2xl`}>
              <div className="bg-[#4ade80]/5 border-b border-[#4ade80]/20 px-6 py-3 text-xs md:text-sm font-black uppercase text-center tracking-[0.3em]">
                REALITY CHECK
              </div>
              <div className="p-6 md:p-10 overflow-y-auto space-y-12 md:space-y-16 flex-1 scrollbar-hide">
                {!result ? (
                  <div className="h-full flex flex-col items-center justify-center space-y-6 opacity-20">
                    <Skull className="w-16 h-16" />
                    <div className="text-xs font-black tracking-[0.5em] uppercase text-center">Waiting_for_Uplink...</div>
                  </div>
                ) : (
                  <div className="space-y-16 font-bold animate-in fade-in duration-1000">
                    <div className="border-b border-[#4ade80]/10 pb-12">
                      <div className="text-xs md:text-sm text-[#4ade80]/40 uppercase mb-4 font-black tracking-widest uppercase">Digital Persona Identification</div>
                      <div className="text-3xl font-black text-[#0d1117] bg-[#4ade80] px-6 py-2 inline-block uppercase mb-12 shadow-[10px_10px_0_rgba(74,222,128,0.1)]">
                        <SafeRender value={result.persona_label} />
                      </div>
                      
                      <div className="space-y-6">
                          <div className="text-xs md:text-sm text-[#4ade80]/40 uppercase mb-3 font-black tracking-widest uppercase">Persona Sync Index</div>
                          <div className="flex flex-col md:flex-row items-start md:items-center space-y-4 md:space-y-0 md:space-x-12">
                            <div className={`text-5xl md:text-6xl font-black ${result.integrity_score > 70 ? 'text-[#4ade80]' : 'text-orange-500'} tracking-tighter tabular-nums`}>
                              {result.integrity_score}<span className="text-2xl md:text-3xl opacity-30 ml-2 md:ml-4 font-black">%</span>
                            </div>
                            <div className="text-sm md:text-base text-[#e0e0e0]/60 leading-relaxed border-l-2 border-[#4ade80]/20 pl-6 md:pl-8 font-medium max-w-[300px] tracking-normal">
                              Alignment between your curated profile and actual digital footprint.
                            </div>
                          </div>
                      </div>
                    </div>

                    <div className="space-y-6">
                      <div className="text-lg font-black uppercase text-[#4ade80] tracking-[0.3em] uppercase">Digital Classification</div>
                      <div className="text-xs md:text-sm text-[#4ade80]/40 uppercase mb-4 font-black tracking-widest border-b border-[#4ade80]/10 pb-4 mt-2">HOW THE ALGORITHM CATEGORIZES YOUR DIGITAL FOOTPRINT.</div>
                      <ul className="space-y-4 pl-4">
                        {result.classification_list?.map((c, i) => (
                          <li key={i} className="text-[1.1rem] flex items-start">
                            <span className="text-[#4ade80] mr-5 font-black mt-1 uppercase text-lg">»</span>
                            <span className="text-[#f0f0f0] font-medium capitalize tracking-normal"><SafeRender value={c} /></span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="bg-orange-500/5 border-l-4 border-orange-500 p-6 md:p-12 relative shadow-lg">
                      <div className="text-sm md:text-base text-orange-500 font-black uppercase tracking-[0.5em]">Subliminal Observation</div>
                      <div className="text-xs md:text-sm text-orange-500/60 uppercase font-black tracking-widest italic mb-6 mt-2">THE UNFILTERED TAKEAWAY FROM YOUR CAREER HISTORY.</div>
                      <p className="text-[1.2rem] leading-relaxed text-orange-50 font-medium antialiased tracking-normal">
                        "<SafeRender value={result.brutal_roast} />"
                      </p>
                    </div>

                    <div className="grid grid-cols-1 gap-12">
                      <div className="border border-purple-500/20 bg-purple-500/5 p-6 md:p-10 shadow-xl">
                        <div className="mb-8">
                          <div className="flex items-center space-x-4 text-purple-400 uppercase text-sm md:text-base font-black tracking-[0.5em] text-xs mb-2">
                            <TrendingUp className="w-7 h-7" />
                            <span>Destiny Manifest 2040</span>
                          </div>
                          <div className="text-xs md:text-sm text-purple-400/60 uppercase font-black tracking-widest italic pl-11">WHERE YOUR CURRENT TRAJECTORY WILL INEVITABLY LEAD.</div>
                        </div>
                        <div className="text-[1.1rem] text-purple-100 font-medium leading-relaxed antialiased tracking-normal">
                          <SafeRender value={result.future_milestone} />
                        </div>
                      </div>

                      <div className="border border-red-500/20 bg-red-500/5 p-6 md:p-10 shadow-xl">
                        <div className="flex items-center space-x-4 text-red-500 mb-8 uppercase text-sm md:text-base font-black tracking-[0.5em]">
                          <Skull className="w-7 h-7" />
                          <span>Adversary Signature</span>
                        </div>
                        <div className="space-y-8">
                          <div className="text-xs md:text-sm text-red-500/50 uppercase font-black tracking-widest italic mb-2 uppercase">Your ultimate corporate rival based on your career.</div>
                          <div className="text-xl text-red-100 font-black uppercase tracking-widest border-b border-red-500/10 pb-6 uppercase">
                              <SafeRender value={result.nemesis_persona} />
                          </div>
                          <p className="text-[1.1rem] text-red-200 font-medium leading-relaxed tracking-normal">
                            <SafeRender value={result.nemesis_rivalry} />
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-8 pb-16">
                      <div className="text-center">
                          <div className="text-base text-[#4ade80]/20 font-black uppercase tracking-[0.8em] inline-block text-xs mb-2">
                             --- Verified_Nodes ---
                          </div>
                          <div className="text-xs md:text-sm text-[#4ade80]/20 uppercase font-black tracking-widest italic block">THE HARD FACTS PULLED FROM YOUR PUBLIC FOOTPRINT.</div>
                      </div>
                      <div className="flex flex-wrap gap-6 justify-center">
                        {result.anchor_facts?.map((f, i) => (
                          <div key={i} className="text-sm md:text-base border border-[#4ade80]/10 px-6 py-3 bg-black/40 text-[#4ade80]/60 tracking-tighter font-black uppercase hover:text-[#4ade80] hover:border-[#4ade80]/40 transition-all cursor-crosshair">
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
    </div>
  );
}

export default App;
