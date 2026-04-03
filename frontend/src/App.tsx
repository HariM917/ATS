import React, { useState, useEffect, useRef } from 'react';
import { 
  LayoutDashboard, Users, Briefcase, BarChart3, MessageSquare, 
  Settings, LogOut, Bell, Menu, X, 
  ChevronRight, Sparkles, User, Save, Upload, Loader2, 
  CheckCircle, Sliders, FileText, UserCircle, Shield, Brain, Puzzle, Target, Layers, Plus, Trash2, MapPin, DollarSign, Clock
} from 'lucide-react';
import TechQuiz from './TechQuiz';
import PuzzleGame from './PuzzleGame';

// Dynamically connect to the backend based on how you access the frontend
const API_URL = `https://ats-ibwo.onrender.com`;

// --- Custom Global Toast System ---
export const CustomToast = {
  show: (message: string, type: 'success' | 'error' = 'success') => {
    window.dispatchEvent(new CustomEvent('app-toast', { detail: { message, type } }));
  }
};

// --- Components ---

const Button = ({ children, variant = "primary", className = "", ...props }: any) => {
  const baseStyle = "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none";
  const variants: any = {
    primary: "bg-gradient-to-r from-indigo-600 to-indigo-700 text-white hover:shadow-lg hover:-translate-y-0.5 shadow-indigo-200",
    secondary: "bg-white text-gray-700 border border-gray-200 hover:bg-gray-50",
    ghost: "bg-transparent text-gray-600 hover:bg-gray-100 hover:text-gray-900",
    danger: "bg-red-50 text-red-600 hover:bg-red-100",
    success: "bg-gradient-to-r from-emerald-500 to-emerald-600 text-white hover:shadow-lg shadow-emerald-200"
  };
  return <button className={`${baseStyle} ${variants[variant]} ${className}`} {...props}>{children}</button>;
};

const Card = ({ children, className = "" }: any) => (
  <div className={`bg-white rounded-2xl border border-gray-100 shadow-xl shadow-gray-200/50 ${className}`}>{children}</div>
);

// --- Pages ---

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

    const payload = {
      ...formData,
      username: formData.username.trim(),
      email: formData.email.trim().toLowerCase(),
      role,
      mode
    };

    try {
      const res = await fetch(`${API_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include", 
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      
      if (res.ok && data.status === "success") {
        onLogin(data);
      } else {
        setError(data.message || "Authentication failed");
      }
    } catch (err) {
      setError("Server connection failed. Ensure backend is running on port 5001.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 relative overflow-hidden font-sans">
      <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-indigo-400/20 rounded-full blur-[100px] animate-pulse" />
      <div className="absolute bottom-[-5%] right-[-5%] w-[400px] h-[400px] bg-emerald-400/20 rounded-full blur-[100px] animate-pulse delay-1000" />

      <div className={`relative w-full max-w-md bg-white/80 backdrop-blur-xl p-8 rounded-3xl shadow-2xl border border-white/50 transition-all duration-500 ${role === 'candidate' ? 'border-emerald-100' : 'border-indigo-100'}`}>
        
        <div className={`w-16 h-16 mx-auto mb-6 rounded-2xl flex items-center justify-center text-white text-2xl shadow-lg transform -rotate-6 ${role === 'hr' ? 'bg-gradient-to-br from-indigo-600 to-violet-600 shadow-indigo-200' : 'bg-gradient-to-br from-emerald-500 to-teal-600 shadow-emerald-200'}`}>
          <Sparkles />
        </div>

        <div className="flex justify-center gap-6 mb-8 text-sm font-medium">
          <button type="button" onClick={() => { setMode('login'); setError(''); }} className={`${mode === 'login' ? (role === 'hr' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-emerald-600 border-b-2 border-emerald-600') : 'text-gray-400'} pb-1 transition-all`}>Login</button>
          <button type="button" onClick={() => { setMode('register'); setError(''); }} className={`${mode === 'register' ? (role === 'hr' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-emerald-600 border-b-2 border-emerald-600') : 'text-gray-400'} pb-1 transition-all`}>Register</button>
        </div>

        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-900">{mode === 'login' ? 'Welcome Back' : 'Create Account'}</h2>
          <p className="text-gray-500 text-sm mt-1">{mode === 'login' ? 'Access your AI Career Portal' : 'Join the future of hiring'}</p>
        </div>

        <div className={`relative flex bg-gray-100 p-1.5 rounded-xl mb-8 border border-gray-200`}>
          <div className={`absolute top-1.5 bottom-1.5 w-[calc(50%-6px)] bg-white rounded-lg shadow-sm transition-all duration-300 ease-out ${role === 'candidate' ? 'translate-x-[100%]' : 'translate-x-0'}`} />
          <button 
            type="button"
            onClick={() => setRole('hr')}
            className={`flex-1 flex items-center justify-center gap-2 py-2 text-sm font-medium relative z-10 transition-colors ${role === 'hr' ? 'text-indigo-600' : 'text-gray-500'}`}
          >
            <Briefcase className="w-4 h-4" /> Recruiter
          </button>
          <button 
            type="button"
            onClick={() => setRole('candidate')}
            className={`flex-1 flex items-center justify-center gap-2 py-2 text-sm font-medium relative z-10 transition-colors ${role === 'candidate' ? 'text-emerald-600' : 'text-gray-500'}`}
          >
            <User className="w-4 h-4" /> Candidate
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {error && (
            <div className="p-3 bg-red-50 border border-red-100 text-red-600 text-xs rounded-xl flex flex-col gap-2 shadow-sm animate-in fade-in">
              <div className="flex items-start">
                <Shield className="w-4 h-4 mr-2 shrink-0 mt-0.5 text-red-500"/> 
                <span className="leading-relaxed font-medium">{error}</span>
              </div>
              {error.includes("register first") && (
                <button type="button" onClick={() => { setMode('register'); setError(''); }} className="ml-6 w-fit text-red-700 font-bold hover:underline transition-all">Go to Registration &rarr;</button>
              )}
              {(error.includes("already registered") || error.includes("already exists")) && (
                <button type="button" onClick={() => { setMode('login'); setError(''); }} className="ml-6 w-fit text-red-700 font-bold hover:underline transition-all">Go to Login &rarr;</button>
              )}
            </div>
          )}
          
          {mode === 'login' ? (
            role === 'hr' ? (
              <>
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Username</label>
                  <input required className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all" placeholder="Enter username" value={formData.username} onChange={e => setFormData({...formData, username: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Password</label>
                  <input type="password" required className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all" placeholder="••••••••" value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} />
                </div>
              </>
            ) : (
              <>
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Email Address</label>
                  <input type="email" required className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all" placeholder="Enter your registered email" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} />
                </div>
              </>
            )
          ) : (
            role === 'hr' ? (
              <>
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Username</label>
                  <input required className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all" placeholder="Choose a username" value={formData.username} onChange={e => setFormData({...formData, username: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Email Address</label>
                  <input type="email" required className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all" placeholder="Work email address" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Create Password</label>
                  <input type="password" required className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all" placeholder="••••••••" value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} />
                </div>
              </>
            ) : (
              <>
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Full Name</label>
                  <input required className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all" placeholder="" value={formData.username} onChange={e => setFormData({...formData, username: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Email Address</label>
                  <input type="email" required className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all" placeholder="" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} />
                </div>
              </>
            )
          )}

          <button 
            type="submit" 
            disabled={loading}
            className={`w-full py-3.5 rounded-xl text-white font-semibold shadow-xl hover:-translate-y-0.5 transition-all duration-200 ${role === 'hr' ? 'bg-gradient-to-r from-indigo-600 to-violet-600 shadow-indigo-200' : 'bg-gradient-to-r from-emerald-500 to-teal-600 shadow-emerald-200'}`}
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : (mode === 'login' ? 'Sign In' : 'Create Account')}
          </button>
        </form>
      </div>
    </div>
  );
};

const HRDashboard = () => {
  const [jd, setJd] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files) {
      setFiles(prev => [...prev, ...Array.from(e.dataTransfer.files)]);
    }
  };

  const handleProcess = async () => {
    if (!jd || files.length === 0) return CustomToast.show("Please provide both a Job Description and Resumes.", "error");
    setLoading(true);
    setResults([]); 
    
    try {
      const uploadedInfo = [];
      for (let file of files) {
        const fd = new FormData();
        fd.append('file', file);
        const res = await fetch(`${API_URL}/upload`, { 
          method: 'POST', 
          credentials: 'include',
          body: fd 
        });
        const data = await res.json();
        if (data.status === 'success') {
          uploadedInfo.push({ filename: data.filename, original_name: file.name });
        }
      }

      const res = await fetch(`${API_URL}/batch_match`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ candidates: uploadedInfo, job_description: jd })
      });
      
      const data = await res.json();
      
      if (data.ranked_candidates) {
        setResults(data.ranked_candidates);
      } else {
        setResults([]);
      }
      
    } catch (e) {
      CustomToast.show("Error processing candidates. Check connection.", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid lg:grid-cols-12 gap-6 h-full">
      <div className="lg:col-span-5 flex flex-col gap-6">
        <Card className="p-6 flex-1 flex flex-col">
          <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Sliders className="w-5 h-5 text-indigo-600" /> Screening Parameters
          </h3>
          
          <div className="mb-4">
            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Job Description</label>
            <textarea 
              className="w-full p-4 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none resize-none h-40 text-sm"
              placeholder="Paste job description here..."
              value={jd}
              onChange={e => setJd(e.target.value)}
            />
          </div>

          <div className="mb-6 flex-1 flex flex-col">
            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Candidate Resumes</label>
            <div 
              onDrop={handleDrop}
              onDragOver={e => e.preventDefault()}
              className="flex-1 border-2 border-dashed border-gray-300 rounded-xl bg-gray-50 flex flex-col items-center justify-center p-6 text-center cursor-pointer hover:bg-indigo-50 hover:border-indigo-400 transition-colors relative"
            >
              <input 
                type="file" 
                multiple 
                className="absolute inset-0 opacity-0 cursor-pointer" 
                onChange={e => e.target.files && setFiles(prev => [...prev, ...Array.from(e.target.files!)])} 
              />
              <Upload className="w-10 h-10 text-gray-400 mb-3" />
              <p className="font-semibold text-gray-700">Drag & Drop Resumes</p>
              <p className="text-xs text-gray-400 mt-1">PDF, DOCX supported</p>
            </div>
            
            {files.length > 0 && (
              <div className="mt-4 max-h-32 overflow-y-auto space-y-2">
                {files.map((f, i) => (
                  <div key={i} className="flex justify-between items-center bg-gray-100 p-2 rounded-lg text-xs">
                    <span className="truncate max-w-[200px]">{f.name}</span>
                    <button onClick={() => setFiles(files.filter((_, idx) => idx !== i))} className="text-red-500 hover:bg-red-100 p-1 rounded"><X className="w-3 h-3"/></button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <Button onClick={handleProcess} disabled={loading} className="w-full py-3">
            {loading ? <Loader2 className="animate-spin w-5 h-5" /> : "Rank Candidates"}
          </Button>
        </Card>
      </div>

      <div className="lg:col-span-7 h-full">
        <Card className="h-full p-6 flex flex-col">
          <div className="flex justify-between items-center mb-6 pb-4 border-b border-gray-100">
            <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <Users className="w-5 h-5 text-indigo-600" /> Ranked Candidates
            </h3>
            <span className="px-3 py-1 bg-indigo-50 text-indigo-700 rounded-full text-xs font-bold">AI Powered</span>
          </div>

          <div className="flex-1 overflow-y-auto pr-2 space-y-4">
            {loading ? (
              <div className="h-full flex flex-col items-center justify-center text-gray-400">
                <Loader2 className="w-12 h-12 animate-spin text-indigo-500 mb-4" />
                <p>Analyzing resumes...</p>
              </div>
            ) : results.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-gray-400 opacity-50">
                <Briefcase className="w-16 h-16 mb-4" />
                <p>Upload resumes to see rankings</p>
              </div>
            ) : (
              results.map((c, i) => (
                <div key={i} className="group p-4 rounded-xl border border-gray-100 hover:border-indigo-500 hover:shadow-lg transition-all bg-white">
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex gap-4">
                      <div className="w-10 h-10 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold text-lg">
                        {i + 1}
                      </div>
                      <div>
                        <h4 className="font-bold text-gray-900">{c.candidate_name}</h4>
                        <p className="text-xs text-gray-500 font-medium">Experience: {c.experience_years} Years</p>
                        
                        {Array.isArray(c.top_roles) && c.top_roles.length > 0 ? (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {c.top_roles.map((role: string, idx: number) => (
                              <span key={idx} className="flex items-center gap-1 text-[10px] text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-100">
                                <Target className="w-3 h-3" /> 
                                {role}
                              </span>
                            ))}
                          </div>
                        ) : (
                          c.predicted_role ? (
                            <div className="mt-1 flex items-center gap-1 text-xs text-emerald-600 font-semibold bg-emerald-50 px-2 py-0.5 rounded-md w-fit">
                              <Target className="w-3 h-3" /> 
                              Potential Role: {c.predicted_role}
                            </div>
                          ) : null
                        )}
                      </div>
                    </div>
                    <div className={`px-4 py-1.5 rounded-full text-sm font-bold text-white shadow-md ${c.final_score > 0.7 ? 'bg-emerald-500 shadow-emerald-200' : c.final_score > 0.4 ? 'bg-amber-400 shadow-amber-200' : 'bg-red-400 shadow-red-200'}`}>
                      {(c.final_score * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div className="pl-14">
                    <p className="text-xs font-bold text-gray-400 uppercase mb-2">Matched Skills</p>
                    <div className="flex flex-wrap gap-2">
                      {c.found_skills && c.found_skills.length > 0 ? c.found_skills.slice(0, 8).map((s: string) => (
                        <span key={s} className="px-2 py-1 bg-indigo-50 text-indigo-700 rounded-md text-xs font-semibold border border-indigo-100">
                          {s}
                        </span>
                      )) : <span className="text-xs text-gray-400 italic">No specific skills found</span>}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};

const CandidateDashboard = () => {
  const [jd, setJd] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleAnalyze = async () => {
    if (!jd || !file) return CustomToast.show("Please provide a Job Description and upload your Resume.", "error");
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const upRes = await fetch(`${API_URL}/upload`, { 
        method: 'POST', 
        credentials: 'include',
        body: fd 
      });
      const upData = await upRes.json();

      const matchRes = await fetch(`${API_URL}/candidate/match`, {
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ filename: upData.filename, job_description: jd })
      });
      const data = await matchRes.json();
      setResult(data);
    } catch (e) {
      CustomToast.show("Error analyzing profile. Please try again.", "error");
    } finally {
      setLoading(false);
    }
  };

  const score = result ? Math.round(result.final_score * 100) : 0;
  const strokeDash = `${score}, 100`;
  const strokeColor = score > 70 ? '#10b981' : score > 40 ? '#f59e0b' : '#ef4444';

  return (
    <div className="grid lg:grid-cols-2 gap-8 max-w-5xl mx-auto">
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Career Analysis</h2>
          <p className="text-gray-500">Upload your details for an instant AI evaluation.</p>
        </div>
        
        <Card className="p-6">
          <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-indigo-600" /> Application Details
          </h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Job Description</label>
              <textarea 
                className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none h-32 text-sm"
                placeholder="Paste JD here..."
                value={jd}
                onChange={e => setJd(e.target.value)}
              />
            </div>
            
            <div>
              <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Your Resume</label>
              <div className="border-2 border-dashed border-gray-300 rounded-xl p-6 text-center hover:bg-indigo-50 transition-colors relative">
                <input type="file" className="absolute inset-0 opacity-0 cursor-pointer" onChange={e => e.target.files && setFile(e.target.files[0])} />
                {file ? (
                  <div className="text-emerald-600 font-medium flex items-center justify-center gap-2">
                    <CheckCircle className="w-5 h-5" /> {file.name}
                  </div>
                ) : (
                  <div className="text-gray-500">
                    <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                    <span className="text-sm">Click to upload PDF/DOCX</span>
                  </div>
                )}
              </div>
            </div>

            <Button onClick={handleAnalyze} disabled={loading} className="w-full py-3">
              {loading ? <Loader2 className="animate-spin" /> : "Analyze Profile"}
            </Button>
          </div>
        </Card>
      </div>

      <div className="flex flex-col h-full">
        <Card className="flex-1 p-8 flex flex-col items-center justify-center relative overflow-hidden">
          {result ? (
            <div className="text-center w-full animate-in fade-in duration-700">
              <div className="relative w-48 h-48 mx-auto mb-6">
                <svg viewBox="0 0 36 36" className="w-full h-full transform -rotate-90 drop-shadow-xl">
                  <path className="text-gray-100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" />
                  <path 
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" 
                    fill="none" 
                    stroke={strokeColor} 
                    strokeWidth="3" 
                    strokeDasharray={strokeDash} 
                    className="transition-all duration-1000 ease-out"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center flex-col">
                  <span className="text-4xl font-black text-gray-900">{score}%</span>
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Match</span>
                </div>
              </div>
              
              {Array.isArray(result.top_roles) && result.top_roles.length > 0 ? (
                <div className="mb-6 w-full max-w-sm mx-auto">
                  <p className="text-xs font-bold text-gray-400 uppercase mb-3 text-center">Top Career Matches</p>
                  <div className="flex flex-col gap-2">
                    {result.top_roles.map((role: string, index: number) => (
                      <div key={index} className="flex items-center justify-between p-2 bg-indigo-50 rounded-lg border border-indigo-100">
                        <span className="flex items-center gap-2 text-sm font-semibold text-indigo-900">
                          <Target className="w-4 h-4 text-indigo-500" /> {role}
                        </span>
                        <span className="text-xs font-bold text-indigo-400">
                          #{index + 1}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : result.predicted_role ? (
                <div className="mb-4 text-center">
                  <span className="inline-flex items-center gap-2 px-3 py-1 bg-indigo-50 text-indigo-700 rounded-full text-sm font-bold border border-indigo-100 animate-in zoom-in slide-in-from-bottom-2">
                    <Brain className="w-4 h-4" /> Recommended Role: {result.predicted_role}
                  </span>
                </div>
              ) : null}

              <div className="bg-gray-50 rounded-xl p-4 mb-6 inline-flex items-center gap-3 border border-gray-100">
                <div className="bg-indigo-100 p-2 rounded-lg text-indigo-600"><Briefcase className="w-4 h-4" /></div>
                <div className="text-left">
                  <p className="text-xs text-gray-500 font-bold uppercase">Experience</p>
                  <p className="font-bold text-gray-900">{result.experience_years} Years Detected</p>
                </div>
              </div>

              <div className="w-full text-left">
                <p className="text-xs font-bold text-gray-400 uppercase mb-3 text-center">Skills Identified</p>
                <div className="flex flex-wrap justify-center gap-2">
                  {result.found_skills && result.found_skills.length > 0 ? result.found_skills.map((s: string) => (
                    <span key={s} className="px-3 py-1 bg-indigo-50 text-indigo-700 rounded-full text-sm font-medium border border-indigo-100 shadow-sm">
                      {s}
                    </span>
                  )) : <span className="text-xs text-gray-400 italic">No specific skills found</span>}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-400 opacity-60">
              <div className="w-24 h-24 bg-gray-100 rounded-full mx-auto mb-4 flex items-center justify-center">
                <Sparkles className="w-10 h-10 text-gray-300" />
              </div>
              <p className="font-medium">AI Analysis Results will appear here</p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

// --- Job Feed for Candidates ---
const JobFeed = () => {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [appliedJobs, setAppliedJobs] = useState<Set<number>>(new Set());

  const [applyingJobId, setApplyingJobId] = useState<number | null>(null);
  const [applyForm, setApplyForm] = useState({ name: '', email: '', phone: '' });
  const [applyFile, setApplyFile] = useState<File | null>(null);
  const [applyLoading, setApplyLoading] = useState(false);

  useEffect(() => {
    const fetchFeed = async () => {
      try {
        const res = await fetch(`${API_URL}/all_jobs`, { credentials: 'include' });
        const data = await res.json();
        if (data.status === 'success') {
          setJobs(data.jobs);
        }
      } catch (e) {
        console.error("Failed to load job feed");
      } finally {
        setLoading(false);
      }
    };
    fetchFeed();
  }, []);

  const handleApplySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!applyingJobId || !applyFile) {
      return CustomToast.show("Please ensure all fields are filled out and a resume is uploaded.", "error");
    }
    
    setApplyLoading(true);
    try {
      const fd = new FormData();
      fd.append('job_id', applyingJobId.toString());
      fd.append('name', applyForm.name);
      fd.append('email', applyForm.email);
      fd.append('phone', applyForm.phone);
      fd.append('resume', applyFile);

      console.log(`Sending application request to backend...`);

      const res = await fetch(`${API_URL}/jobs/${applyingJobId}/apply`, {
        method: 'POST',
        credentials: 'include',
        body: fd
      });
      
      const data = await res.json().catch(() => ({}));
      
      if (res.ok && data.status === 'success') {
          setAppliedJobs(prev => new Set(prev).add(applyingJobId));
          CustomToast.show("Application submitted successfully! Check your email.", "success");
          
          // Clear the form
          setApplyingJobId(null);
          setApplyForm({ name: '', email: '', phone: '' });
          setApplyFile(null);
      } else {
          // Backend returned an error!
          console.error("Backend Error:", data);
          CustomToast.show(data.message || "The server rejected the application. Are you logged in?", "error");
      }

    } catch (e) {
      console.error("Fetch request failed completely:", e);
      CustomToast.show("Network Error: Could not connect to the backend server.", "error");
    } finally {
      setApplyLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 h-full overflow-y-auto pb-10 relative">
      
      {applyingJobId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/60 backdrop-blur-sm p-4">
          <Card className="w-full max-w-md p-6 relative shadow-2xl animate-in fade-in zoom-in-95 duration-200 border-0">
            <button 
              onClick={() => setApplyingJobId(null)} 
              className="absolute top-4 right-4 p-1.5 text-gray-400 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
            
            <h3 className="text-xl font-bold text-gray-900 mb-1">Apply for Position</h3>
            <p className="text-sm text-gray-500 mb-6 line-clamp-1">
              Submit your details for the <span className="font-semibold text-gray-700">{jobs.find(j => j.id === applyingJobId)?.title}</span> role.
            </p>
            
            <form onSubmit={handleApplySubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">Full Name</label>
                <input required className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm transition-all" placeholder="" value={applyForm.name} onChange={e => setApplyForm({...applyForm, name: e.target.value})} />
              </div>
              
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">Email Address</label>
                <input required type="email" className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm transition-all" placeholder="" value={applyForm.email} onChange={e => setApplyForm({...applyForm, email: e.target.value})} />
              </div>
              
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">Phone Number</label>
                <input required type="tel" className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm transition-all" placeholder="" value={applyForm.phone} onChange={e => setApplyForm({...applyForm, phone: e.target.value})} />
              </div>
              
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">Resume (PDF/DOCX)</label>
                <div className="border-2 border-dashed border-gray-300 rounded-xl p-4 text-center hover:bg-indigo-50 transition-colors relative bg-gray-50">
                  <input required type="file" accept=".pdf,.doc,.docx" className="absolute inset-0 opacity-0 cursor-pointer" onChange={e => setApplyFile(e.target.files ? e.target.files[0] : null)} />
                  {applyFile ? (
                    <div className="text-emerald-600 font-medium flex items-center justify-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 shrink-0" /> <span className="truncate">{applyFile.name}</span>
                    </div>
                  ) : (
                    <div className="text-gray-500 text-sm flex flex-col items-center">
                      <Upload className="w-5 h-5 mb-1 text-gray-400" />
                      <span>Click or drag to upload resume</span>
                    </div>
                  )}
                </div>
              </div>
              
              <div className="pt-2">
                <Button type="submit" disabled={applyLoading} className="w-full py-3.5 shadow-md text-base">
                  {applyLoading ? <Loader2 className="animate-spin w-5 h-5 mx-auto" /> : "Submit Application"}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      <div>
        <h2 className="text-2xl font-bold text-gray-900">Job Board</h2>
        <p className="text-gray-500">Discover your next career move from top companies.</p>
      </div>
      
      {loading ? (
         <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-indigo-500" /></div>
      ) : jobs.length === 0 ? (
         <Card className="p-12 text-center text-gray-400">
           <Briefcase className="w-12 h-12 mx-auto mb-4 opacity-50" />
           <p>No jobs posted yet. Check back later!</p>
         </Card>
      ) : (
        <div className="space-y-4">
          {jobs.map(job => {
            const isApplied = appliedJobs.has(job.id);
            return (
              <Card key={job.id} className="p-6 hover:shadow-lg transition-shadow border border-gray-100">
                <div className="flex items-start gap-4 mb-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white flex items-center justify-center font-bold text-xl uppercase shadow-md shrink-0">
                      {job.company_name?.[0] || 'C'}
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-gray-900">{job.title}</h3>
                      <p className="text-sm font-bold text-indigo-600">{job.company_name}</p>
                      <p className="text-xs text-gray-500 mt-1 flex gap-3 font-medium">
                          <span className="flex items-center gap-1"><MapPin className="w-3 h-3"/> {job.location || 'Remote'}</span>
                          <span className="flex items-center gap-1"><Clock className="w-3 h-3"/> {new Date(job.created_at).toLocaleDateString()}</span>
                      </p>
                    </div>
                </div>
                <div className="flex flex-wrap gap-2 mb-4">
                  {job.job_type && <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs font-bold uppercase">{job.job_type}</span>}
                  {job.salary && <span className="px-2 py-1 bg-emerald-50 text-emerald-700 rounded text-xs font-bold uppercase">{job.salary}</span>}
                </div>
                <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">{job.description}</p>
                <div className="mt-5 pt-4 border-t border-gray-100 flex justify-end">
                  <Button 
                    className="px-6 py-2 shadow-md"
                    variant={isApplied ? "success" : "primary"}
                    onClick={() => setApplyingJobId(job.id)}
                    disabled={isApplied}
                  >
                    {isApplied ? "Applied ✓" : "Apply Now"}
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

// --- Job Management for HR ---
const JobManagement = () => {
  const [jobs, setJobs] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    title: '', description: '', location: '', job_type: 'Full-time', salary: ''
  });

  const fetchJobs = async () => {
    try {
      const res = await fetch(`${API_URL}/jobs`, { credentials: 'include' });
      const data = await res.json();
      if (data.status === 'success') {
        setJobs(data.jobs);
      }
    } catch (e) {
      console.error("Failed to fetch jobs");
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      if (data.status === 'success') {
        setShowForm(false);
        setFormData({ title: '', description: '', location: '', job_type: 'Full-time', salary: '' });
        fetchJobs();
        CustomToast.show("Job posted successfully!", "success");
      } else {
        CustomToast.show(data.message, "error");
      }
    } catch (e) {
      CustomToast.show("Error posting job", "error");
    } finally {
      setLoading(false);
    }
  };

  const confirmDelete = async () => {
    if (!deletingId) return;
    try {
      await fetch(`${API_URL}/jobs/${deletingId}`, { method: 'DELETE', credentials: 'include' });
      fetchJobs();
      CustomToast.show("Job deleted successfully.", "success");
    } catch (e) {
      CustomToast.show("Error deleting job", "error");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-6 h-full overflow-y-auto pb-10 relative">
      
      {/* Custom Delete Confirmation Modal */}
      {deletingId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/60 backdrop-blur-sm p-4">
          <Card className="w-full max-w-sm p-6 relative shadow-2xl animate-in fade-in zoom-in-95 duration-200 border-0">
            <h3 className="text-xl font-bold text-gray-900 mb-2">Delete Job Post</h3>
            <p className="text-sm text-gray-500 mb-6">Are you sure you want to delete this job posting? This action cannot be undone.</p>
            <div className="flex justify-end gap-3">
              <Button variant="secondary" onClick={() => setDeletingId(null)}>Cancel</Button>
              <Button variant="danger" onClick={confirmDelete}>Delete</Button>
            </div>
          </Card>
        </div>
      )}

      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Job Postings</h2>
          <p className="text-gray-500">Manage open positions at your company.</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)} className="gap-2">
          {showForm ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
          {showForm ? "Cancel" : "Post New Job"}
        </Button>
      </div>

      {showForm && (
        <Card className="p-6 animate-in fade-in slide-in-from-top-4">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Create Job Posting</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Job Title</label>
                <input required className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="e.g. Senior React Developer" value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Location</label>
                <input className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="e.g. Remote, New York" value={formData.location} onChange={e => setFormData({...formData, location: e.target.value})} />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Job Type</label>
                <select className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" value={formData.job_type} onChange={e => setFormData({...formData, job_type: e.target.value})}>
                  <option>Full-time</option>
                  <option>Part-time</option>
                  <option>Contract</option>
                  <option>Internship</option>
                </select>
              </div>
              <div className="col-span-2">
                <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Salary Range</label>
                <input className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="e.g. $100k - $120k / year" value={formData.salary} onChange={e => setFormData({...formData, salary: e.target.value})} />
              </div>
              <div className="col-span-2">
                <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Job Description</label>
                <textarea required className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl h-32 focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="Describe the role, responsibilities, and requirements..." value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} />
              </div>
            </div>
            <div className="flex justify-end pt-2">
              <Button type="submit" disabled={loading}>
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Publish Job"}
              </Button>
            </div>
          </form>
        </Card>
      )}

      <div className="grid md:grid-cols-2 gap-4">
        {jobs.length === 0 && !loading && !showForm && (
          <div className="col-span-2 flex flex-col items-center justify-center p-12 text-gray-400 bg-white rounded-2xl border border-dashed border-gray-200">
            <Briefcase className="w-12 h-12 mb-3 opacity-50" />
            <p>No jobs posted yet. Click 'Post New Job' to get started.</p>
          </div>
        )}
        {jobs.map((job) => (
          <Card key={job.id} className="p-5 flex flex-col relative group">
            <button onClick={() => setDeletingId(job.id)} className="absolute top-4 right-4 p-2 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors opacity-0 group-hover:opacity-100">
              <Trash2 className="w-4 h-4" />
            </button>
            <h4 className="text-lg font-bold text-gray-900 pr-8">{job.title}</h4>
            <div className="flex flex-wrap gap-2 mt-2 mb-4">
              {job.location && <span className="inline-flex items-center gap-1 text-xs font-medium bg-gray-100 text-gray-600 px-2 py-1 rounded-md"><MapPin className="w-3 h-3"/> {job.location}</span>}
              {job.job_type && <span className="inline-flex items-center gap-1 text-xs font-medium bg-indigo-50 text-indigo-600 px-2 py-1 rounded-md"><Clock className="w-3 h-3"/> {job.job_type}</span>}
              {job.salary && <span className="inline-flex items-center gap-1 text-xs font-medium bg-emerald-50 text-emerald-600 px-2 py-1 rounded-md"><DollarSign className="w-3 h-3"/> {job.salary}</span>}
            </div>
            <p className="text-sm text-gray-600 line-clamp-3 mb-4 flex-1 whitespace-pre-wrap">{job.description}</p>
            
            {/* Displays candidates who applied to this specific job */}
            <div className="mt-4 pt-4 border-t border-gray-100">
               <h5 className="text-xs font-bold text-gray-500 uppercase mb-3 flex items-center gap-2">
                 <Users className="w-4 h-4"/> Applicants ({job.applications?.length || 0})
               </h5>
               {job.applications && job.applications.length > 0 ? (
                 <div className="space-y-2 max-h-32 overflow-y-auto pr-2">
                   {job.applications.map((app: any, idx: number) => (
                     <div key={idx} className="flex items-center gap-3 bg-gray-50 p-2 rounded-lg">
                       <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-xs">
                         {app.candidate_name?.[0]?.toUpperCase() || 'U'}
                       </div>
                       <div className="overflow-hidden">
                         <p className="text-sm font-bold text-gray-900 truncate">{app.candidate_name}</p>
                         <p className="text-xs text-gray-500 truncate">{app.candidate_email}</p>
                       </div>
                     </div>
                   ))}
                 </div>
               ) : (
                 <p className="text-xs text-gray-400 italic">No candidates have applied yet.</p>
               )}
            </div>

            <div className="text-xs text-gray-400 font-medium mt-4 pt-2 border-t border-gray-50">
              Posted: {new Date(job.created_at).toLocaleDateString()}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

const SettingsPage = ({ user }: any) => {
  const [profile, setProfile] = useState<any>({
    username: user?.user || '',
    email: user?.email || '',
    role: user?.role || ''
  });
  const [loading, setLoading] = useState(false);

  const fetchProfile = () => {
    fetch(`${API_URL}/profile`, { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        setProfile({
          ...profile,
          ...data,
          username: data.username || user?.user,
          email: data.email || user?.email,
          role: data.role || user?.role
        });
      })
      .catch(console.error);
  };

  useEffect(() => {
    fetchProfile();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSave = async () => {
    setLoading(true);
    try {
      await fetch(`${API_URL}/update_profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: 'include', 
        body: JSON.stringify(profile),
      });
      CustomToast.show("Profile Saved Successfully!", "success");
      fetchProfile();
    } catch (e) {
      CustomToast.show("Failed to save profile.", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-6 h-full overflow-y-auto">
      <div className="flex items-start gap-8">
        <div className="w-64 hidden lg:block space-y-1">
          <button className="w-full flex items-center gap-3 px-4 py-3 bg-white text-indigo-600 rounded-xl font-medium shadow-sm border border-gray-100">
            <UserCircle className="w-5 h-5" /> My Profile
          </button>
          <button className="w-full flex items-center gap-3 px-4 py-3 text-gray-500 hover:bg-white hover:text-gray-900 rounded-xl font-medium transition-colors">
            <Shield className="w-5 h-5" /> Security
          </button>
        </div>

        <div className="flex-1 space-y-6">
          <Card className="overflow-hidden">
            <div className="h-32 bg-gradient-to-r from-indigo-500 to-purple-600 relative">
              <div className="absolute -bottom-10 left-8 flex items-end gap-4">
                <div className="w-24 h-24 rounded-full bg-white p-1 shadow-xl">
                  <div className="w-full h-full rounded-full bg-gray-200 flex items-center justify-center text-3xl font-bold text-gray-500 border-4 border-white">
                    {profile.username?.[0]?.toUpperCase() || <UserCircle className="w-10 h-10" />}
                  </div>
                </div>
                <div className="mb-2">
                  <h2 className="text-xl font-bold text-white shadow-black drop-shadow-md">{profile.username}</h2>
                  <span className="px-2 py-0.5 bg-white/20 backdrop-blur-md text-white rounded text-xs font-medium border border-white/30 capitalize">{profile.role || 'User'}</span>
                </div>
              </div>
            </div>

            <div className="pt-16 p-8">
              <h3 className="text-lg font-bold text-gray-900 mb-6 border-b pb-2">Personal Information</h3>
              <div className="grid grid-cols-2 gap-6 mb-6">
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">First Name</label>
                  <input className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl" value={profile.first_name || ""} onChange={e => setProfile({...profile, first_name: e.target.value})} />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Last Name</label>
                  <input className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl" value={profile.last_name || ""} onChange={e => setProfile({...profile, last_name: e.target.value})} />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Bio</label>
                  <textarea className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl h-24" value={profile.bio || ""} onChange={e => setProfile({...profile, bio: e.target.value})} />
                </div>
              </div>

              <h3 className="text-lg font-bold text-gray-900 mb-6 border-b pb-2 pt-4">Contact Info</h3>
              <div className="grid grid-cols-2 gap-6 mb-8">
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Email (Read Only)</label>
                  <input className="w-full p-3 bg-gray-100 border border-gray-200 rounded-xl text-gray-500 cursor-not-allowed" value={profile.email || ""} disabled />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Phone</label>
                  <input className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl" value={profile.phone || ""} onChange={e => setProfile({...profile, phone: e.target.value})} />
                </div>
                <div className="col-span-2">
                   <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Street Address</label>
                   <input className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl" value={profile.street || ""} onChange={e => setProfile({...profile, street: e.target.value})} />
                </div>
                <div>
                   <label className="block text-xs font-bold text-gray-500 uppercase mb-2">City</label>
                   <input className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl" value={profile.city || ""} onChange={e => setProfile({...profile, city: e.target.value})} />
                </div>
                <div>
                   <label className="block text-xs font-bold text-gray-500 uppercase mb-2">State</label>
                   <input className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl" value={profile.state || ""} onChange={e => setProfile({...profile, state: e.target.value})} />
                </div>
              </div>

              <div className="flex justify-end pt-4">
                <Button onClick={handleSave} disabled={loading} className="px-8 py-3">
                  {loading ? "Saving..." : "Save Changes"}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

const ChatPage = () => {
  const [messages, setMessages] = useState([{ role: "ai", text: "Hi! I'm your AI hiring assistant. Ask me anything!" }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg = input;
    setMessages(prev => [...prev, { role: "user", text: userMsg }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ message: userMsg }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: "ai", text: data.response }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: "ai", text: "Error connecting to AI." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900">AI Assistant</h2>
          <p className="text-gray-500">Your personal career coach and guide.</p>
        </div>
        
        <Card className="flex-1 flex flex-col overflow-hidden shadow-lg border-gray-200">
          <div className="p-4 bg-gradient-to-r from-indigo-600 to-violet-600 flex justify-between items-center text-white">
             <div className="flex items-center gap-2 font-semibold">
                <Sparkles className="w-5 h-5 text-yellow-300" /> AI Coach
             </div>
          </div>
          
          <div className="flex-1 p-6 overflow-y-auto space-y-6 bg-gray-50/50">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] p-4 rounded-2xl text-sm shadow-sm whitespace-pre-wrap ${m.role === 'user' ? 'bg-indigo-600 text-white rounded-br-none' : 'bg-white border border-gray-100 text-gray-700 rounded-bl-none'}`}>
                  {m.text}
                </div>
              </div>
            ))}
            {loading && <div className="text-xs text-gray-400 text-center animate-pulse">AI is thinking...</div>}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-4 bg-white border-t">
            <div className="flex gap-2">
                <input 
                  className="flex-1 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600 transition-all bg-gray-50 focus:bg-white"
                  placeholder="Type your message..."
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && sendMessage()}
                />
                <button onClick={sendMessage} className="p-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors shadow-md shadow-indigo-200"><ChevronRight className="w-5 h-5" /></button>
            </div>
          </div>
        </Card>
    </div>
  );
};

// --- Layout & Main App ---

export default function App() {
  const [user, setUser] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [toast, setToast] = useState<{message: string, type: 'success'|'error'} | null>(null);

  useEffect(() => {
    const handleToast = (e: any) => {
      setToast(e.detail);
      setTimeout(() => setToast(null), 5000); 
    };
    window.addEventListener('app-toast', handleToast);
    return () => window.removeEventListener('app-toast', handleToast);
  }, []);

  useEffect(() => {
    const storedUser = localStorage.getItem('ats_user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const handleLoginSuccess = (userData: any) => {
    setUser(userData);
    setMobileMenuOpen(false);
    localStorage.setItem('ats_user', JSON.stringify(userData));
  };

  if (!user) return <LoginPage onLogin={handleLoginSuccess} />;

  const handleLogout = async () => {
    await fetch(`${API_URL}/logout`, { 
      method: 'POST',
      credentials: 'include' 
    });
    setUser(null);
    localStorage.removeItem('ats_user');
  };

  const menuItems = user.role === 'hr' ? [
    { id: 'dashboard', label: 'Screening', icon: LayoutDashboard },
    { id: 'jobs', label: 'Job Posts', icon: Briefcase },
    { id: 'settings', label: 'Settings', icon: Settings },
  ] : [
    { id: 'dashboard', label: 'Career Analysis', icon: Sparkles },
    { id: 'jobs', label: 'Job Board', icon: Briefcase },
    { id: 'quiz', label: 'Skill Assessment', icon: Brain },
    { id: 'puzzle', label: 'Logic Puzzle', icon: Puzzle },
    { id: 'chat', label: 'AI Coach', icon: MessageSquare },
    { id: 'settings', label: 'My Profile', icon: User },
  ];

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden font-sans text-gray-900 relative">
      
      {/* Global Toast Notification UI */}
      {toast && (
        <div className={`fixed top-6 right-6 z-50 p-4 min-w-[300px] rounded-xl shadow-2xl flex items-start gap-3 border ${toast.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'} animate-in slide-in-from-top-5 duration-300`}>
           {toast.type === 'success' ? <CheckCircle className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" /> : <Shield className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />}
           <p className="font-semibold text-sm flex-1">{toast.message}</p>
           <button onClick={() => setToast(null)} className="text-gray-400 hover:text-gray-600 shrink-0"><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* Sidebar */}
      <>
        {mobileMenuOpen && <div className="fixed inset-0 z-20 bg-gray-900/50 lg:hidden" onClick={() => setMobileMenuOpen(false)} />}
        <div className={`fixed inset-y-0 left-0 z-30 w-64 bg-white border-r border-gray-200 transform lg:static lg:translate-x-0 transition-transform duration-300 ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}`}>
          <div className="flex h-20 items-center px-6 border-b border-gray-100">
            <span className={`text-xl font-black bg-clip-text text-transparent ${user.role === 'hr' ? 'bg-gradient-to-r from-indigo-600 to-violet-600' : 'bg-gradient-to-r from-emerald-500 to-teal-600'}`}>
              TalentFlow
            </span>
          </div>
          <div className="p-4 space-y-1">
            {menuItems.map((item) => (
              <button
                key={item.id}
                onClick={() => { setActiveTab(item.id); setMobileMenuOpen(false); }}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 ${activeTab === item.id 
                  ? (user.role === 'hr' ? 'bg-indigo-50 text-indigo-700 shadow-sm' : 'bg-emerald-50 text-emerald-700 shadow-sm') 
                  : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'}`}
              >
                <item.icon className={`w-5 h-5 ${activeTab === item.id ? (user.role === 'hr' ? 'text-indigo-600' : 'text-emerald-600') : 'text-gray-400'}`} /> {item.label}
              </button>
            ))}
          </div>
          <div className="absolute bottom-0 left-0 w-full p-4 border-t border-gray-100 bg-gray-50/50">
            <div className="flex items-center gap-3 mb-3 px-2">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold shadow-md ${user.role === 'hr' ? 'bg-gradient-to-r from-indigo-500 to-violet-500' : 'bg-gradient-to-r from-emerald-500 to-teal-500'}`}>
                {user.user[0].toUpperCase()}
              </div>
              <div className="overflow-hidden">
                <p className="text-sm font-bold text-gray-900 truncate">{user.user}</p>
                <p className="text-xs text-gray-500 capitalize">{user.role}</p>
              </div>
            </div>
            <button onClick={handleLogout} className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-gray-200 rounded-lg text-xs font-bold text-gray-600 hover:bg-white hover:text-red-500 hover:border-red-100 transition-all">
              <LogOut className="w-3 h-3" /> Sign Out
            </button>
          </div>
        </div>
      </>

      {/* Main Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-20 bg-white/80 backdrop-blur-md border-b border-gray-200 px-6 flex items-center justify-between sticky top-0 z-10">
          <div className="flex items-center gap-4">
            <button onClick={() => setMobileMenuOpen(true)} className="lg:hidden text-gray-500 hover:text-gray-900"><Menu className="w-6 h-6" /></button>
            <h2 className="text-lg font-bold text-gray-800 capitalize hidden sm:block">
              {menuItems.find(i => i.id === activeTab)?.label}
            </h2>
          </div>
          <div className="flex items-center gap-4">
            <button className="p-2 text-gray-400 hover:text-indigo-600 transition-colors relative">
              <Bell className="w-6 h-6" />
              <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full ring-2 ring-white"></span>
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-auto p-4 sm:p-6 lg:p-8 relative">
          <div className="max-w-7xl mx-auto h-full">
            <div className={activeTab === 'dashboard' ? 'h-full block' : 'hidden'}>
              {user.role === 'hr' ? <HRDashboard /> : <CandidateDashboard />}
            </div>
            <div className={activeTab === 'settings' ? 'h-full block' : 'hidden'}>
              <SettingsPage user={user} />
            </div>
            <div className={activeTab === 'quiz' ? 'h-full block' : 'hidden'}>
              <TechQuiz />
            </div>
            <div className={activeTab === 'puzzle' ? 'h-full block' : 'hidden'}>
              <PuzzleGame />
            </div>
            <div className={activeTab === 'chat' ? 'h-full block' : 'hidden'}>
              <ChatPage />
            </div>
            <div className={activeTab === 'jobs' ? 'h-full block' : 'hidden'}>
              {user.role === 'hr' ? <JobManagement /> : <JobFeed />}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}