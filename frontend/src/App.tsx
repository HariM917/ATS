import React, { useState, useEffect, useRef } from 'react';
import { 
  LayoutDashboard, Users, Briefcase, BarChart3, MessageSquare, 
  Settings, LogOut, Bell, Menu, X, 
  ChevronRight, Sparkles, User, Save, Upload, Loader2, 
  CheckCircle, Sliders, FileText, UserCircle, Shield, Brain, Puzzle, Target, Layers, Plus, Trash2, MapPin, DollarSign, Clock, Send, Search, Filter, ArrowRight, Zap
} from 'lucide-react';

// --- CONFIGURATION ---
const API_URL = "https://ats-ibwo.onrender.com/api";

// --- CUSTOM TOAST SYSTEM ---
export const CustomToast = {
  show: (message: string, type: 'success' | 'error' = 'success') => {
    window.dispatchEvent(new CustomEvent('app-toast', { detail: { message, type } }));
  }
};

// --- REUSABLE UI COMPONENTS ---

const Button = ({ children, variant = "primary", className = "", ...props }: any) => {
  const baseStyle = "inline-flex items-center justify-center rounded-xl px-5 py-2.5 text-sm font-bold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none active:scale-95";
  const variants: any = {
    primary: "bg-gradient-to-r from-indigo-600 to-indigo-700 text-white hover:shadow-xl hover:-translate-y-0.5 shadow-indigo-200",
    secondary: "bg-white text-gray-700 border border-gray-200 hover:bg-gray-50 hover:border-gray-300",
    ghost: "bg-transparent text-gray-600 hover:bg-gray-100",
    danger: "bg-red-50 text-red-600 hover:bg-red-100 border border-red-100",
    success: "bg-gradient-to-r from-emerald-500 to-emerald-600 text-white hover:shadow-lg shadow-emerald-200"
  };
  return <button className={`${baseStyle} ${variants[variant]} ${className}`} {...props}>{children}</button>;
};

const Card = ({ children, className = "", title = "", icon: Icon = null }: any) => (
  <div className={`bg-white rounded-3xl border border-gray-100 shadow-xl shadow-gray-200/40 overflow-hidden ${className}`}>
    {title && (
      <div className="px-6 py-4 border-b border-gray-50 flex items-center justify-between">
        <h3 className="font-black text-gray-900 flex items-center gap-2">
          {Icon && <Icon className="w-5 h-5 text-indigo-600" />} {title}
        </h3>
      </div>
    )}
    <div className="p-6">{children}</div>
  </div>
);

const Badge = ({ children, variant = "indigo" }: any) => {
  const colors: any = {
    indigo: "bg-indigo-50 text-indigo-600",
    emerald: "bg-emerald-50 text-emerald-600",
    amber: "bg-amber-50 text-amber-600",
    rose: "bg-rose-50 text-rose-600"
  };
  return <span className={`px-2.5 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider ${colors[variant]}`}>{children}</span>;
};

// --- FEATURE COMPONENTS (INLINED) ---

const TechQuiz = () => {
  const [currentQ, setCurrentQ] = useState(0);
  const [score, setScore] = useState(0);
  const [finished, setFinished] = useState(false);
  const [started, setStarted] = useState(false);

  const questions = [
    { q: "What is the primary benefit of React's Virtual DOM?", a: ["Direct DOM manipulation", "Efficient re-rendering by calculating diffs", "Automatic SEO optimization"], correct: 1 },
    { q: "Which Python library is most used for BERT-based embeddings?", a: ["Flask", "Sentence-Transformers", "Pandas"], correct: 1 },
    { q: "In machine learning, what does 'Cosine Similarity' measure?", a: ["The length of a vector", "The angle/orientation between two vectors", "The distance between points"], correct: 1 }
  ];

  const handleAnswer = (idx: number) => {
    if (idx === questions[currentQ].correct) setScore(score + 1);
    if (currentQ < questions.length - 1) setCurrentQ(currentQ + 1);
    else setFinished(true);
  };

  if (!started) return (
    <Card className="text-center py-12">
      <Brain className="w-16 h-16 text-indigo-600 mx-auto mb-4" />
      <h2 className="text-2xl font-black mb-2">Technical Skill Hub</h2>
      <p className="text-gray-500 mb-8 max-w-sm mx-auto">Validate your expertise and boost your match score with AI-driven assessments.</p>
      <Button onClick={() => setStarted(true)}>Take Assessment</Button>
    </Card>
  );

  if (finished) return (
    <Card className="text-center py-12">
      <div className="text-5xl font-black text-emerald-500 mb-4">{Math.round((score/questions.length)*100)}%</div>
      <h2 className="text-xl font-bold mb-6">Assessment Complete!</h2>
      <Button onClick={() => {setStarted(false); setFinished(false); setCurrentQ(0); setScore(0);}}>Back to Hub</Button>
    </Card>
  );

  return (
    <Card title={`Question ${currentQ + 1} of ${questions.length}`}>
      <p className="text-lg font-bold text-gray-800 mb-8">{questions[currentQ].q}</p>
      <div className="space-y-3">
        {questions[currentQ].a.map((opt, i) => (
          <button key={i} onClick={() => handleAnswer(i)} className="w-full text-left p-4 rounded-2xl border border-gray-100 hover:border-indigo-300 hover:bg-indigo-50 transition-all font-medium text-gray-700">
            {opt}
          </button>
        ))}
      </div>
    </Card>
  );
};

const PuzzleGame = () => {
  const [tiles, setTiles] = useState([1, 2, 3, 4, 5, 6, 7, 8, null]);
  return (
    <Card title="Logical Reasoning" icon={Puzzle}>
      <p className="text-sm text-gray-500 mb-6">Solve the slide puzzle to demonstrate problem-solving speed.</p>
      <div className="grid grid-cols-3 gap-3 p-4 bg-gray-50 rounded-3xl border border-gray-100">
        {tiles.map((t, i) => (
          <div key={i} className={`h-20 rounded-2xl flex items-center justify-center text-xl font-black ${t ? 'bg-white shadow-sm text-indigo-600 border border-gray-100' : 'bg-transparent'}`}>
            {t}
          </div>
        ))}
      </div>
      <p className="text-center mt-6 text-xs font-black text-gray-400 uppercase tracking-widest animate-pulse">Initializing Logic Engine...</p>
    </Card>
  );
};

// --- AUTH PAGES ---

const LoginPage = ({ onLogin }: any) => {
  const [role, setRole] = useState<'hr' | 'candidate'>('hr');
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({ username: '', password: '', email: '' });
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...formData, role, mode }),
      });
      const data = await res.json();
      if (res.ok && data.status === "success") onLogin(data);
      else setError(data.message || "Authentication failed.");
    } catch (err) {
      setError("Backend connection timed out. If you are on Render Free tier, please wait 30 seconds for the engine to wake up.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 relative overflow-hidden p-6">
      <div className="absolute top-[-10%] left-[-10%] w-[600px] h-[600px] bg-indigo-500/10 rounded-full blur-[120px]" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[400px] h-[400px] bg-emerald-500/10 rounded-full blur-[100px]" />
      
      <Card className="w-full max-w-md p-8 relative z-10 border-white/50 backdrop-blur-sm shadow-2xl">
        <div className="flex justify-center mb-8">
          <div className="flex bg-gray-100 p-1 rounded-2xl w-full">
            <button onClick={() => setRole('hr')} className={`flex-1 py-2.5 rounded-xl text-sm font-black transition-all ${role === 'hr' ? 'bg-white shadow-sm text-indigo-600' : 'text-gray-400'}`}>RECRUITER</button>
            <button onClick={() => setRole('candidate')} className={`flex-1 py-2.5 rounded-xl text-sm font-black transition-all ${role === 'candidate' ? 'bg-white shadow-sm text-emerald-600' : 'text-gray-400'}`}>CANDIDATE</button>
          </div>
        </div>

        <div className="text-center mb-8">
          <h2 className="text-3xl font-black text-gray-900 tracking-tight">{mode === 'login' ? 'Welcome Back' : 'Get Started'}</h2>
          <p className="text-gray-500 mt-2 font-medium">Your AI-powered career starts here.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <div className="p-4 bg-red-50 text-red-600 text-xs rounded-2xl font-bold border border-red-100 flex items-center gap-3"><Shield className="w-4 h-4" /> {error}</div>}
          <div className="space-y-1">
            <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-1">Account Identifier</label>
            <input required className="w-full px-5 py-4 bg-gray-50 border border-gray-100 rounded-2xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all font-medium" placeholder="Username or Email" value={formData.username} onChange={e => setFormData({...formData, username: e.target.value})} />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-1">Security Key</label>
            <input type="password" required className="w-full px-5 py-4 bg-gray-50 border border-gray-100 rounded-2xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all font-medium" placeholder="••••••••" value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} />
          </div>
          <Button type="submit" disabled={loading} className="w-full py-4 text-base shadow-lg mt-4">
            {loading ? <Loader2 className="animate-spin" /> : (mode === 'login' ? 'Sign In' : 'Create Profile')}
          </Button>
        </form>

        <button onClick={() => setMode(mode === 'login' ? 'register' : 'login')} className="w-full text-center text-sm font-bold text-indigo-600 mt-8 hover:underline">
          {mode === 'login' ? "Don't have an account? Sign up" : "Already have an account? Log in"}
        </button>
      </Card>
    </div>
  );
};

// --- MAIN DASHBOARDS ---

const HRDashboard = () => {
  const [jd, setJd] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleAnalysis = async () => {
    if (!jd) return CustomToast.show("Please enter job requirements.", "error");
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/score`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          job_description: jd, 
          resume_text: "Senior Software Engineer with experience in Python, Flask, React, and BERT embeddings." 
        })
      });
      const data = await res.json();
      setResults([{ name: "Hari Murali", score: data.score/100, role: data.match_level, exp: 5, skills: ["Python", "React", "AI"] }]);
    } catch (e) {
      CustomToast.show("Backend connection failed.", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
      <div className="lg:col-span-5 space-y-6">
        <Card title="Candidate Screening" icon={Sliders}>
          <textarea className="w-full p-5 bg-gray-50 border border-gray-100 rounded-3xl h-60 text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all mb-4" placeholder="Paste the Job Description (JD) here to start AI matching..." value={jd} onChange={e => setJd(e.target.value)} />
          <div className="p-10 border-2 border-dashed border-indigo-100 rounded-3xl text-center bg-indigo-50/20 hover:bg-indigo-50 transition-all cursor-pointer group mb-6">
            <Upload className="w-10 h-10 mx-auto mb-3 text-indigo-200 group-hover:text-indigo-400 group-hover:scale-110 transition-all" />
            <p className="text-xs font-black text-indigo-400 tracking-widest uppercase">Drop Candidate Resumes</p>
          </div>
          <Button onClick={handleAnalysis} disabled={loading} className="w-full py-4 text-base">
            {loading ? <Loader2 className="animate-spin" /> : "Run Smart Analysis"}
          </Button>
        </Card>
      </div>
      <div className="lg:col-span-7">
        <Card title="Analysis & Rankings" icon={BarChart3} className="h-full">
          {results.length > 0 ? (
            <div className="space-y-4">
              {results.map((c, i) => (
                <div key={i} className="flex items-center justify-between p-6 bg-gray-50 rounded-3xl border border-transparent hover:border-indigo-100 hover:bg-white transition-all shadow-sm group">
                  <div className="flex items-center gap-5">
                    <div className="w-14 h-14 bg-indigo-600 rounded-2xl flex items-center justify-center text-2xl font-black text-white shadow-lg shadow-indigo-100">{c.name[0]}</div>
                    <div>
                      <h4 className="font-black text-gray-900 text-lg">{c.name}</h4>
                      <div className="flex gap-2 mt-1">
                        <Badge variant="emerald">{c.role} MATCH</Badge>
                        <Badge variant="indigo">{c.exp}Y EXP</Badge>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-black text-indigo-600 tracking-tight">{Math.round(c.score * 100)}%</div>
                    <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mt-1">AI Score</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-gray-300 py-24">
              <Sparkles className="w-16 h-16 opacity-10 mb-4" />
              <p className="text-sm font-black uppercase tracking-widest opacity-40">AI analysis data will appear here</p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

const CandidateDashboard = () => {
  const [jd, setJd] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!jd) return CustomToast.show("Please input a Job Description.", "error");
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/score`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_description: jd, resume_text: "Sample profile content." })
      });
      setResult(await res.json());
    } catch (e) {
      CustomToast.show("Analysis failed.", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { label: "AI PROFILE SCORE", value: "92%", icon: Sparkles, color: "bg-indigo-600" },
          { label: "JOBS MATCHED", value: "48", icon: Target, color: "bg-emerald-500" },
          { label: "RANK POSITION", value: "#3", icon: BarChart3, color: "bg-amber-500" },
        ].map((stat, i) => (
          <Card key={i} className="flex items-center gap-5">
            <div className={`p-4 rounded-2xl text-white ${stat.color} shadow-lg shadow-gray-200`}><stat.icon className="w-6 h-6" /></div>
            <div>
              <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">{stat.label}</p>
              <p className="text-2xl font-black text-gray-900">{stat.value}</p>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-5">
          <Card title="Resume Optimization" icon={Zap}>
            <textarea className="w-full p-5 bg-gray-50 border border-gray-100 rounded-3xl h-48 text-sm outline-none focus:ring-2 focus:ring-emerald-500 mb-4" placeholder="Paste the job description you are targeting..." value={jd} onChange={e => setJd(e.target.value)} />
            <div className="p-8 border-2 border-dashed border-emerald-100 rounded-3xl text-center bg-emerald-50/10 mb-6">
              <Upload className="w-8 h-8 mx-auto mb-2 text-emerald-200" />
              <p className="text-xs font-black text-emerald-400 uppercase tracking-widest">Select Resume</p>
            </div>
            <Button onClick={handleAnalyze} disabled={loading} className="w-full py-4" variant="success">
              {loading ? <Loader2 className="animate-spin" /> : "Check Match Compatibility"}
            </Button>
          </Card>
        </div>
        <div className="lg:col-span-7">
          <Card title="Analysis Insights" className="h-full">
            {result ? (
              <div className="text-center animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="w-40 h-40 bg-indigo-50 rounded-full flex items-center justify-center mx-auto mb-6 border-[6px] border-white shadow-2xl">
                  <span className="text-5xl font-black text-indigo-600">{Math.round(result.score)}%</span>
                </div>
                <h3 className="text-2xl font-black text-gray-900">{result.match_level} Compatibility</h3>
                <p className="text-gray-500 mt-2 max-w-sm mx-auto font-medium">Your profile shows strong alignment with these requirements based on semantic BERT analysis.</p>
                <div className="grid grid-cols-2 gap-4 mt-8 text-left">
                  <div className="p-5 bg-emerald-50 rounded-3xl border border-emerald-100">
                    <p className="text-[10px] font-black text-emerald-600 uppercase tracking-widest mb-1">Status</p>
                    <p className="font-black text-emerald-900">Highly Recommended</p>
                  </div>
                  <div className="p-5 bg-indigo-50 rounded-3xl border border-indigo-100">
                    <p className="text-[10px] font-black text-indigo-600 uppercase tracking-widest mb-1">Visibility</p>
                    <p className="font-black text-indigo-900">Top 5% of Pool</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-gray-300 py-24">
                <Target className="w-16 h-16 opacity-10 mb-4" />
                <p className="text-sm font-black uppercase tracking-widest opacity-40">Compatibility results will appear here</p>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};

// --- CHATBOT UI ---

const ChatbotUI = () => {
  const [messages, setMessages] = useState([{ text: "👋 Hi! I'm your AI Career Coach. Ask me about resume writing, interview prep, or tech roadmaps!", sender: 'ai' }]);
  const [input, setInput] = useState("");
  const scrollRef = useRef<any>(null);

  useEffect(() => { scrollRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMsg = input;
    setMessages(prev => [...prev, { text: userMsg, sender: 'user' }]);
    setInput("");
    
    // Simulate AI response logic (Local for now to ensure reliability)
    setTimeout(() => {
      setMessages(prev => [...prev, { text: "That's a great question. In a professional context, you should focus on quantifying your impact using the STAR method.", sender: 'ai' }]);
    }, 1000);
  };

  return (
    <Card className="flex flex-col h-[600px] max-w-3xl mx-auto" title="Career AI Coach" icon={MessageSquare}>
      <div className="flex-1 overflow-y-auto space-y-4 p-4 scrollbar-hide">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] p-4 rounded-2xl font-medium text-sm ${m.sender === 'user' ? 'bg-indigo-600 text-white rounded-tr-none shadow-indigo-100' : 'bg-gray-100 text-gray-800 rounded-tl-none shadow-sm'}`}>
              {m.text}
            </div>
          </div>
        ))}
        <div ref={scrollRef} />
      </div>
      <div className="mt-4 pt-4 border-t flex gap-3">
        <input className="flex-1 bg-gray-50 border border-gray-100 rounded-2xl px-5 outline-none focus:ring-2 focus:ring-indigo-500 font-medium text-sm" placeholder="Ask about resumes, interviews, roadmaps..." value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSend()} />
        <Button onClick={handleSend} className="p-3"><Send className="w-5 h-5" /></Button>
      </div>
    </Card>
  );
};

// --- APP ROOT ---

export default function App() {
  const [user, setUser] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [toast, setToast] = useState<any>(null);

  useEffect(() => {
    const stored = localStorage.getItem('ats_user');
    if (stored) setUser(JSON.parse(stored));
    
    const handleToast = (e: any) => {
      setToast(e.detail);
      setTimeout(() => setToast(null), 4000);
    };
    window.addEventListener('app-toast', handleToast);
    return () => window.removeEventListener('app-toast', handleToast);
  }, []);

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('ats_user');
    CustomToast.show("Signed out safely.");
  };

  if (!user) return <LoginPage onLogin={(u: any) => { setUser(u); localStorage.setItem('ats_user', JSON.stringify(u)); }} />;

  const tabs = user.role === 'hr' ? [
    { id: 'dashboard', label: 'Screening', icon: LayoutDashboard },
    { id: 'jobs', label: 'My Jobs', icon: Briefcase },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Settings },
  ] : [
    { id: 'dashboard', label: 'Dashboard', icon: Sparkles },
    { id: 'hub', label: 'Skill Hub', icon: Brain },
    { id: 'chat', label: 'AI Coach', icon: MessageSquare },
    { id: 'puzzle', label: 'Logic Game', icon: Puzzle },
    { id: 'settings', label: 'My Profile', icon: UserCircle },
  ];

  return (
    <div className="flex h-screen bg-gray-50 font-sans text-gray-900 overflow-hidden">
      {toast && (
        <div className={`fixed top-8 right-8 z-[60] p-5 rounded-3xl shadow-2xl border-4 text-white font-black animate-in slide-in-from-right-4 duration-300 ${toast.type === 'success' ? 'bg-emerald-500 border-emerald-400 shadow-emerald-200' : 'bg-red-500 border-red-400 shadow-red-200'}`}>
          {toast.message}
        </div>
      )}

      {/* SIDEBAR */}
      <aside className={`bg-white border-r border-gray-100 flex flex-col transition-all duration-300 shadow-2xl z-50 ${sidebarOpen ? 'w-72' : 'w-24'}`}>
        <div className="p-8 flex items-center gap-4">
          <div className="w-12 h-12 bg-indigo-600 rounded-2xl flex items-center justify-center text-white shadow-xl shadow-indigo-100 shrink-0 transform rotate-6 hover:rotate-0 transition-transform cursor-pointer">
            <Target className="w-7 h-7" />
          </div>
          {sidebarOpen && <span className="font-black text-2xl tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-violet-600">TalentFlow</span>}
        </div>
        
        <nav className="flex-1 px-5 space-y-3 mt-4">
          {tabs.map((tab) => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`w-full flex items-center gap-4 p-4 rounded-2xl font-black transition-all ${activeTab === tab.id ? 'bg-indigo-50 text-indigo-600 shadow-sm' : 'text-gray-400 hover:bg-gray-50 hover:text-gray-600'}`}>
              <tab.icon className="w-6 h-6 shrink-0" />
              {sidebarOpen && <span className="text-sm tracking-wide">{tab.label.toUpperCase()}</span>}
              {activeTab === tab.id && sidebarOpen && <ChevronRight className="w-4 h-4 ml-auto opacity-30" />}
            </button>
          ))}
        </nav>

        <div className="p-6 mt-auto border-t border-gray-50">
          <button onClick={handleLogout} className="w-full flex items-center gap-4 p-4 rounded-2xl font-black text-red-500 hover:bg-red-50 transition-all">
            <LogOut className="w-6 h-6" />
            {sidebarOpen && <span className="text-sm tracking-wide uppercase">Sign Out</span>}
          </button>
        </div>
      </aside>

      {/* CONTENT AREA */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-24 bg-white/80 backdrop-blur-xl border-b border-gray-100 flex items-center justify-between px-12 shrink-0 z-40">
          <div className="flex items-center gap-6">
            <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-3 bg-gray-50 hover:bg-white border border-gray-100 rounded-2xl text-gray-400 hover:text-indigo-600 transition-all shadow-sm"><Menu className="w-5 h-5" /></button>
            <h1 className="text-2xl font-black text-gray-900 tracking-tight">
              {tabs.find(t => t.id === activeTab)?.label}
            </h1>
          </div>
          <div className="flex items-center gap-8">
            <div className="relative group cursor-pointer"><Bell className="w-6 h-6 text-gray-300 group-hover:text-indigo-600 transition-colors" /><span className="absolute top-0 right-0 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white"></span></div>
            <div className="h-10 w-px bg-gray-100 hidden sm:block"></div>
            <div className="flex items-center gap-4 group cursor-pointer">
              <div className="text-right hidden md:block">
                <p className="text-sm font-black text-gray-900 group-hover:text-indigo-600 transition-colors">{user.username || 'System Admin'}</p>
                <p className="text-[10px] uppercase font-black text-gray-400 tracking-widest leading-none mt-1">{user.role}</p>
              </div>
              <div className="w-12 h-12 bg-gray-100 rounded-2xl flex items-center justify-center border-2 border-white shadow-lg overflow-hidden transition-all group-hover:scale-105 group-hover:border-indigo-100">
                <UserCircle className="w-8 h-8 text-gray-400" />
              </div>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-12 bg-gray-50/40">
          <div className="max-w-7xl mx-auto h-full animate-in fade-in duration-700">
            {activeTab === 'dashboard' && (user.role === 'hr' ? <HRDashboard /> : <CandidateDashboard />)}
            {activeTab === 'hub' && <TechQuiz />}
            {activeTab === 'chat' && <ChatbotUI />}
            {activeTab === 'puzzle' && <PuzzleGame />}
            {activeTab === 'analytics' && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                <Card title="Hiring Velocity" icon={Clock}><p className="text-3xl font-black">4.2 Days</p><p className="text-xs text-gray-400 mt-2 font-bold uppercase tracking-widest">Avg. Time to Screen</p></Card>
                <Card title="Talent Pipeline" icon={Layers}><p className="text-3xl font-black">1,204</p><p className="text-xs text-gray-400 mt-2 font-bold uppercase tracking-widest">Active Candidates</p></Card>
                <Card title="Match Precision" icon={Target}><p className="text-3xl font-black">89%</p><p className="text-xs text-gray-400 mt-2 font-bold uppercase tracking-widest">AI Prediction Accuracy</p></Card>
              </div>
            )}
            {activeTab === 'settings' && (
              <Card className="max-w-2xl mx-auto text-center py-12" title="System Configuration">
                <div className="w-24 h-24 bg-indigo-50 rounded-3xl mx-auto flex items-center justify-center text-indigo-200 mb-8 border border-indigo-100 shadow-inner"><UserCircle className="w-16 h-16" /></div>
                <h2 className="text-2xl font-black mb-2">Portal Settings</h2>
                <p className="text-gray-500 mb-10 font-medium px-12">Manage your AI Career profile, connected accounts, and search visibility preferences.</p>
                <div className="grid grid-cols-2 gap-4 px-12">
                  <Button variant="secondary" className="py-4">Update Profile</Button>
                  <Button variant="secondary" className="py-4">Access Keys</Button>
                </div>
              </Card>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}