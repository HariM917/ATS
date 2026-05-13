import React, { useState, useEffect, useRef } from 'react';
import { 
  LayoutDashboard, Users, Briefcase, BarChart3, MessageSquare, 
  Settings, LogOut, Bell, Menu, X, 
  ChevronRight, Sparkles, User, Save, Upload, Loader2, 
  CheckCircle, Sliders, FileText, UserCircle, Shield, Brain, Puzzle, Target, Layers, ArrowLeft, PieChart
} from 'lucide-react';
import TechQuiz from './TechQuiz';
import PuzzleGame from './PuzzleGame';
import ReactMarkdown from 'react-markdown';

// Robust environment detection for Vite
const API_URL = import.meta.env.PROD
  ? "https://ats-1-uscv.onrender.com/api"
  : "http://127.0.0.1:5000/api";

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

    try {
      const endpoint = mode === 'login' ? '/login' : '/register';
      console.log(`Attempting to connect to: ${API_URL}${endpoint}`);
      const response = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: 'include',
        body: JSON.stringify({ ...formData, role }),
      });
      const text = await response.text();
      console.log(`RAW ${mode.toUpperCase()} RESPONSE:`, text);
      const data = JSON.parse(text);
      
      if (response.ok && data.status === "success") {
        onLogin(data);
      } else {
        setError(data.message || `${mode === 'login' ? 'Authentication' : 'Registration'} failed`);
      }
    } catch (err) {
      console.error("Login connection error:", err);
      setError("Server connection failed. Ensure backend is running on port 5000.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 relative overflow-hidden font-sans">
      {/* Background Shapes */}
      <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-indigo-400/20 rounded-full blur-[100px] animate-pulse" />
      <div className="absolute bottom-[-5%] right-[-5%] w-[400px] h-[400px] bg-emerald-400/20 rounded-full blur-[100px] animate-pulse delay-1000" />

      <div className={`relative w-full max-w-md bg-white/80 backdrop-blur-xl p-8 rounded-3xl shadow-2xl border border-white/50 transition-all duration-500 ${role === 'candidate' ? 'border-emerald-100' : 'border-indigo-100'}`}>
        
        {/* Logo */}
        <div className={`w-16 h-16 mx-auto mb-6 rounded-2xl flex items-center justify-center text-white text-2xl shadow-lg transform -rotate-6 ${role === 'hr' ? 'bg-gradient-to-br from-indigo-600 to-violet-600 shadow-indigo-200' : 'bg-gradient-to-br from-emerald-500 to-teal-600 shadow-emerald-200'}`}>
          <Sparkles />
        </div>

        {/* Auth Mode Tabs */}
        <div className="flex justify-center gap-6 mb-8 text-sm font-medium">
          <button onClick={() => setMode('login')} className={`${mode === 'login' ? (role === 'hr' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-emerald-600 border-b-2 border-emerald-600') : 'text-gray-400'} pb-1 transition-all`}>Login</button>
          <button onClick={() => setMode('register')} className={`${mode === 'register' ? (role === 'hr' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-emerald-600 border-b-2 border-emerald-600') : 'text-gray-400'} pb-1 transition-all`}>Register</button>
        </div>

        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-900">{mode === 'login' ? 'Welcome Back' : 'Create Account'}</h2>
          <p className="text-gray-500 text-sm mt-1">{mode === 'login' ? 'Access your AI Career Portal' : 'Join the future of hiring'}</p>
        </div>

        {/* Role Toggle */}
        <div className={`relative flex bg-gray-100 p-1.5 rounded-xl mb-8 border border-gray-200`}>
          <div className={`absolute top-1.5 bottom-1.5 w-[calc(50%-6px)] bg-white rounded-lg shadow-sm transition-all duration-300 ease-out ${role === 'candidate' ? 'translate-x-[100%]' : 'translate-x-0'}`} />
          <button 
            onClick={() => setRole('hr')}
            className={`flex-1 flex items-center justify-center gap-2 py-2 text-sm font-medium relative z-10 transition-colors ${role === 'hr' ? 'text-indigo-600' : 'text-gray-500'}`}
          >
            <Briefcase className="w-4 h-4" /> Recruiter
          </button>
          <button 
            onClick={() => setRole('candidate')}
            className={`flex-1 flex items-center justify-center gap-2 py-2 text-sm font-medium relative z-10 transition-colors ${role === 'candidate' ? 'text-emerald-600' : 'text-gray-500'}`}
          >
            <User className="w-4 h-4" /> Candidate
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {error && <div className="p-3 bg-red-50 text-red-600 text-xs rounded-lg flex items-center"><Shield className="w-3 h-3 mr-2"/> {error}</div>}
          
          {role === 'hr' ? (
            <>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Full Name</label>
                <input 
                  required 
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                  placeholder="Enter your full name"
                  value={formData.username}
                  onChange={e => setFormData({...formData, username: e.target.value})}
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Email Address</label>
                <input 
                  type="email"
                  required 
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={e => setFormData({...formData, email: e.target.value})}
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Password</label>
                <input 
                  type="password"
                  required 
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={e => setFormData({...formData, password: e.target.value})}
                />
              </div>
            </>
          ) : (
            <>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Full Name</label>
                <input 
                  required 
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                  placeholder="Enter your full name"
                  value={formData.username}
                  onChange={e => setFormData({...formData, username: e.target.value})}
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Email Address</label>
                <input 
                  type="email"
                  required 
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={e => setFormData({...formData, email: e.target.value})}
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Password</label>
                <input 
                  type="password"
                  required 
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={e => setFormData({...formData, password: e.target.value})}
                />
              </div>
            </>
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



const JobManagement = () => {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [selectedJob, setSelectedJob] = useState<any>(null);
  const [applicants, setApplicants] = useState<any[]>([]);
  const [loadingApps, setLoadingApps] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  
  const [formData, setFormData] = useState({
    company_name: "",
    branch: "",
    job_title: "",
    description: "",
    location: "",
    job_type: "Full-time",
    salary: "",
    required_skills: "",
    experience_required: 0,
    hr_email: ""
  });

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const stored = localStorage.getItem('user');
      const auth = stored ? JSON.parse(stored) : {};
      
      const res = await fetch(`${API_URL}/jobs`, { 
        credentials: 'include',
        headers: {
          'X-Auth-Email': auth.email || '',
          'X-Auth-Role': auth.role || ''
        }
      });
      if (!res.ok) throw new Error(`Server Error: ${res.status}`);
      const text = await res.text();
      console.log("RAW JOBS RESPONSE:", text);
      const data = JSON.parse(text);
      if (data.status === "success") setJobs(data.jobs);
    } catch (e: any) {
      console.error("Fetch Jobs Failed:", e);
    } finally {
      setLoading(false);
    }
  };

  const fetchApplicants = async (jobId: number) => {
    setLoadingApps(true);
    try {
      const stored = localStorage.getItem('user');
      const auth = stored ? JSON.parse(stored) : {};

      const res = await fetch(`${API_URL}/jobs/${jobId}/applications`, { 
        credentials: 'include',
        headers: {
          'X-Auth-Email': auth.email || '',
          'X-Auth-Role': auth.role || ''
        }
      });
      if (!res.ok) throw new Error(`Server Error: ${res.status}`);
      const text = await res.text();
      console.log("RAW APPLICANTS RESPONSE:", text);
      const data = JSON.parse(text);
      if (data.status === "success") setApplicants(data.applications);
    } catch (e: any) {
      console.error("Fetch Applicants Failed:", e);
    } finally {
      setLoadingApps(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleStatusUpdate = async (appId: number, status: string) => {
    try {
      const stored = localStorage.getItem('user');
      const auth = stored ? JSON.parse(stored) : {};

      const res = await fetch(`${API_URL}/applications/${appId}/status`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          'X-Auth-Email': auth.email || '',
          'X-Auth-Role': auth.role || ''
        },
        credentials: 'include',
        body: JSON.stringify({ status })
      });
      const text = await res.text();
      console.log("RAW STATUS UPDATE RESPONSE:", text);
      if (res.ok) {
        fetchApplicants(selectedJob.id);
      }
    } catch (e) {
      setErrorMessage("Failed to update status");
      setSuccessMessage("");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
    const stored = localStorage.getItem('user');
    const auth = stored ? JSON.parse(stored) : {};

    const response = await fetch(`${API_URL}/jobs`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        'X-Auth-Email': auth.email || '',
        'X-Auth-Role': auth.role || ''
      },
      credentials: 'include',
      body: JSON.stringify(formData)
    });

    const text = await response.text();
    console.log("RAW JOB POST RESPONSE:", text);

    let data;
    try {
      data = JSON.parse(text);
    } catch (err) {
      console.error("JSON PARSE ERROR:", err);
      setErrorMessage("Server returned invalid response (HTML). Check console for details.");
      setLoading(false);
      return;
    }

    if (response.ok && (data.success || data.status === "success")) {
      setSuccessMessage("Job posted successfully");
      setErrorMessage("");
      setShowForm(false);
      setFormData({ 
        company_name: "",
        branch: "",
        job_title: "", 
        description: "", 
        location: "", 
        job_type: "Full-time", 
        salary: "", 
        required_skills: "", 
        experience_required: 0,
        hr_email: "" 
      });
      fetchJobs();
    } else {
      setErrorMessage(data.message || "Failed to post job");
    }
    } catch (e: any) {
      console.error("FATAL CONNECTION ERROR:", e);
      setErrorMessage("Connection failed. Try again.");
      setSuccessMessage("");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this job?")) return;
    try {
      const res = await fetch(`${API_URL}/jobs/${id}`, { method: "DELETE", credentials: 'include' });
      const text = await res.text();
      console.log("RAW DELETE RESPONSE:", text);
      fetchJobs();
    } catch (e) {
      setErrorMessage("Error deleting job");
      setSuccessMessage("");
    }
  };

  if (selectedJob) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="secondary" onClick={() => setSelectedJob(null)}><ArrowLeft className="w-4 h-4"/> Back</Button>
          <h2 className="text-2xl font-bold text-gray-900">{selectedJob.title} - Applicants</h2>
        </div>

        <Card className="overflow-hidden border-gray-100 shadow-xl shadow-gray-100/50">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-100">
                  <th className="p-4 text-xs font-bold text-gray-400 uppercase tracking-widest">Candidate</th>
                  <th className="p-4 text-xs font-bold text-gray-400 uppercase tracking-widest">AI Score</th>
                  <th className="p-4 text-xs font-bold text-gray-400 uppercase tracking-widest">Status</th>
                  <th className="p-4 text-xs font-bold text-gray-400 uppercase tracking-widest text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loadingApps ? (
                  <tr><td colSpan={4} className="p-10 text-center"><Loader2 className="animate-spin w-8 h-8 mx-auto text-indigo-500"/></td></tr>
                ) : applicants.length === 0 ? (
                  <tr><td colSpan={4} className="p-10 text-center text-gray-400">No applications yet.</td></tr>
                ) : applicants.map(app => (
                  <tr key={app.id} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                    <td className="p-4">
                      <div className="font-bold text-gray-900">{app.candidate_name}</div>
                      <div className="text-xs text-gray-500">{app.candidate_email}</div>
                    </td>
                    <td className="p-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold text-white ${app.score > 0.8 ? 'bg-emerald-500' : app.score > 0.4 ? 'bg-amber-400' : 'bg-red-400'}`}>
                        {(app.score * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded text-[10px] font-black uppercase tracking-tight ${app.status === 'Shortlisted' ? 'bg-emerald-50 text-emerald-600' : app.status === 'Rejected' ? 'bg-red-50 text-red-600' : 'bg-indigo-50 text-indigo-600'}`}>
                        {app.status}
                      </span>
                    </td>
                    <td className="p-4 text-right">
                       <div className="flex gap-2 justify-end">
                         <Button variant="secondary" onClick={() => handleStatusUpdate(app.id, 'Shortlisted')} className="text-[10px] px-3 py-1 bg-emerald-50 text-emerald-600 border-emerald-100 hover:bg-emerald-100">Accept</Button>
                         <Button variant="secondary" onClick={() => handleStatusUpdate(app.id, 'Rejected')} className="text-[10px] px-3 py-1 bg-red-50 text-red-600 border-red-100 hover:bg-red-100">Reject</Button>
                         <Button variant="secondary" onClick={() => window.open(`${API_URL.replace('/api', '')}/uploads/${app.resume_path.split('/').pop()}`)} className="text-[10px] px-3 py-1"><FileText className="w-3 h-3"/></Button>
                       </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Job Postings</h2>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "Create New Job"}
        </Button>
      </div>

      {showForm && (
        <Card className="p-6 animate-in slide-in-from-top-4 duration-300">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">Company Name</label>
                <input required className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl" value={formData.company_name} onChange={e => setFormData({...formData, company_name: e.target.value})} placeholder="e.g. Google" />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">Branch / Dept</label>
                <input required className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl" value={formData.branch} onChange={e => setFormData({...formData, branch: e.target.value})} placeholder="e.g. AI Research" />
              </div>
              <div className="col-span-2">
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">Job Title</label>
                <input required className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl" value={formData.job_title} onChange={e => setFormData({...formData, job_title: e.target.value})} placeholder="e.g. Senior Software Engineer" />
              </div>
              <div className="col-span-2">
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">Description</label>
                <textarea required className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl h-32" value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} placeholder="Describe the role..." />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">Location</label>
                <input className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl" value={formData.location} onChange={e => setFormData({...formData, location: e.target.value})} placeholder="Remote / NY / SF" />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">Job Type</label>
                <select className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl" value={formData.job_type} onChange={e => setFormData({...formData, job_type: e.target.value})}>
                  <option>Full-time</option>
                  <option>Part-time</option>
                  <option>Contract</option>
                  <option>Internship</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">Required Skills (Comma separated)</label>
                <input className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl" value={formData.required_skills} onChange={e => setFormData({...formData, required_skills: e.target.value})} placeholder="React, Node.js, TypeScript" />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">Exp Required (Years)</label>
                <input type="number" className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl" value={formData.experience_required} onChange={e => setFormData({...formData, experience_required: parseInt(e.target.value)})} />
              </div>
              <div className="col-span-2">
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">HR Contact Email (For Alerts)</label>
                <input required type="email" className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl" value={formData.hr_email} onChange={e => setFormData({...formData, hr_email: e.target.value})} placeholder="hr@company.com" />
              </div>
            </div>

            {successMessage && <div className="success-message">{successMessage}</div>}
            {errorMessage && <div className="error-message">{errorMessage}</div>}

            <Button type="submit" disabled={loading} className="w-full py-3 mt-4">
              {loading ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : "Post Job Opportunity"}
            </Button>
          </form>
        </Card>
      )}

      <div className="grid gap-4">
        {loading && jobs.length === 0 ? (
          <p className="text-center py-10 text-gray-400">Loading jobs...</p>
        ) : jobs.length === 0 ? (
          <p className="text-center py-10 text-gray-400">No jobs posted yet.</p>
        ) : (
          jobs.map(job => (
            <Card key={job.id} className="p-6">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-bold text-gray-900">{job.title}</h3>
                  <div className="flex gap-4 mt-1 text-sm text-gray-500 font-medium">
                    <span className="flex items-center gap-1"><Users className="w-4 h-4" /> Applicants</span>
                    <span className="flex items-center gap-1"><FileText className="w-4 h-4" /> {job.job_type}</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button variant="secondary" onClick={() => { setSelectedJob(job); fetchApplicants(job.id); }}>View Applicants</Button>
                  <Button variant="danger" onClick={() => handleDelete(job.id)}><X className="w-4 h-4" /></Button>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

const HRDashboard = () => {
  const [jd, setJd] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files);
    setFiles(prev => [...prev, ...droppedFiles]);
  };

  const handleProcess = async () => {
    if (files.length === 0 || jd.length < 15) return;
    setLoading(true);
    setErrorMessage("");
    setSuccessMessage("");
    
    const formData = new FormData();
    formData.append("jd", jd);
    files.forEach(file => formData.append("resumes", file));

    try {
      const response = await fetch(`${API_URL}/process_resumes`, {
        method: "POST",
        body: formData,
      });

      const text = await response.text();
      console.log("RAW HR BATCH RESPONSE:", text);
      
      const data = JSON.parse(text);
      
      if (data.success) {
        setResults(data.rankings);
        setSuccessMessage(`Successfully processed ${data.count} resumes`);
      } else {
        setErrorMessage(data.error || "Processing failed");
        console.warn("No ranked candidates returned from backend");
        setResults([]);
      }
      
    } catch (e) {
      console.error("Fetch Error:", e);
      setErrorMessage("Server connection failed. Ensure backend is running on port 5000.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid lg:grid-cols-12 gap-6 h-full">
      {/* Input Column */}
      <div className="lg:col-span-5 flex flex-col gap-6">
        <Card className="p-6 flex-1 flex flex-col shadow-lg">
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

          {successMessage && <div className="success-message mb-2">{successMessage}</div>}
          {errorMessage && <div className="error-message mb-2">{errorMessage}</div>}

          <Button 
            onClick={handleProcess} 
            disabled={loading || jd.length < 15 || files.length === 0} 
            className={`w-full py-4 text-lg font-bold shadow-xl transition-all duration-300 ${jd.length < 15 || files.length === 0 ? 'bg-gray-300 cursor-not-allowed grayscale' : 'bg-gradient-to-r from-indigo-600 to-violet-600 hover:scale-[1.02] active:scale-[0.98]'}`}
          >
            {loading ? (
              <span className="flex items-center gap-2"><Loader2 className="animate-spin w-5 h-5 mx-auto" /></span>
            ) : (
              <span className="flex items-center gap-2 justify-center"><Sparkles className="w-5 h-5" /> Rank Candidates</span>
            )}
          </Button>
          {(jd.length > 0 && jd.length < 15) && (
            <p className="text-[10px] text-red-500 mt-2 font-bold animate-pulse text-center">
              ⚠️ Job Description must be at least 15 characters for AI analysis.
            </p>
          )}
        </Card>
      </div>

      {/* Results Column */}
      <div className="lg:col-span-7 h-full">
        <Card className="h-full p-6 flex flex-col shadow-lg">
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
                        <p className="text-xs text-gray-500 font-medium">Experience: {c.experience_years || c.experience} Years</p>
                        
                        {Array.isArray(c.top_roles) && c.top_roles.length > 0 ? (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {c.top_roles.map((role: string, idx: number) => (
                              <span key={idx} className="flex items-center gap-1 text-[10px] text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-100">
                                <Target className="w-3 h-3" /> 
                                {role}
                              </span>
                            ))}
                          </div>
                        ) : c.predicted_role ? (
                          <div className="mt-1 flex items-center gap-1 text-xs text-emerald-600 font-semibold bg-emerald-50 px-2 py-0.5 rounded-md w-fit">
                            <Target className="w-3 h-3" /> 
                            Potential Role: {c.predicted_role}
                          </div>
                        ) : null}
                      </div>
                    </div>
                    <div className={`px-4 py-1.5 rounded-full text-sm font-bold text-white shadow-md ${c.final_score > 0.7 ? 'bg-emerald-500 shadow-emerald-200' : c.final_score > 0.4 ? 'bg-amber-400 shadow-amber-200' : 'bg-red-400 shadow-red-200'}`}>
                      {((typeof c.final_score === 'number' && !isNaN(c.final_score)) ? c.final_score * 100 : 0).toFixed(0)}%
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t border-gray-50">
                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">
                      Technical Skills
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {c.resume_skills && c.resume_skills.length > 0 ? (
                        c.resume_skills.slice(0, 12).map((skill: string, idx: number) => (
                          <span
                            key={idx}
                            className="px-2.5 py-0.5 text-[10px] font-bold rounded-full bg-purple-100 text-purple-700 border border-purple-200 transition-all hover:bg-purple-200"
                          >
                            {skill}
                          </span>
                        ))
                      ) : (
                        <p className="text-[10px] text-gray-400 italic">
                          No technical skills detected
                        </p>
                      )}
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

const JobBrowse = () => {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState<number | null>(null);
  const [selectedResumes, setSelectedResumes] = useState<{[key: number]: File}>({});
  const [analysis, setAnalysis] = useState<any>(null);
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const fetchAllJobs = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/all_jobs`, { credentials: 'include' });
      const text = await res.text();
      console.log("RAW ALL JOBS RESPONSE:", text);
      const data = JSON.parse(text);
      if (data.status === "success") setJobs(data.jobs);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllJobs();
  }, []);

  const handleApply = async (jobId: number) => {
    const resume = selectedResumes[jobId];
    if (!resume) {
      setErrorMessage(`Please select a resume for the ${jobId} role`);
      return;
    }
    setApplying(jobId);
    setErrorMessage("");
    setSuccessMessage("");
    setAnalysis(null);
    try {
      const fd = new FormData();
      fd.append("resume", resume);
      const token = localStorage.getItem('token');
      const auth = JSON.parse(localStorage.getItem('user') || '{}');

      const res = await fetch(`${API_URL}/jobs/${jobId}/apply`, {
        method: "POST",
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${token || auth.email || ''}`,
          'X-Auth-Email': auth.email || '',
          'X-Auth-Role': auth.role || '',
          'X-Auth-User': auth.user || ''
        },
        body: fd
      });
      const text = await res.text();
      console.log("RAW APPLY RESPONSE:", text);
      const data = JSON.parse(text);
      if (data.status === "success") {
        setAnalysis(data.analysis);
        setSuccessMessage("Application successful!");
      } else {
        setErrorMessage(data.message || "Failed to apply");
      }
    } catch (e) {
      setErrorMessage("Error applying");
    } finally {
      setApplying(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Available Opportunities</h2>
        <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">{jobs.length} Jobs Found</span>
      </div>

      {successMessage && <div className="success-message">{successMessage}</div>}
      {errorMessage && <div className="error-message">{errorMessage}</div>}

      <div className="grid lg:grid-cols-2 gap-6">
        {loading ? (
          <div className="col-span-2 text-center py-20 text-gray-400">
            <Loader2 className="w-10 h-10 animate-spin mx-auto mb-4" />
            <p>Fetching latest jobs...</p>
          </div>
        ) : jobs.length === 0 ? (
          <div className="col-span-2 text-center py-20 text-gray-400">
            <Briefcase className="w-16 h-16 mx-auto mb-4 opacity-20" />
            <p>No jobs available at the moment.</p>
          </div>
        ) : jobs.map(job => (
          <Card key={job.id} className="p-6 flex flex-col">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-xl font-bold text-gray-900">{job.title}</h3>
                <p className="text-indigo-600 font-semibold text-sm">
                  {(job.company_name && job.company_name !== "Company") ? job.company_name : (job.company || "TalentFlow Partner")}
                </p>
              </div>
              <span className="px-3 py-1 bg-emerald-50 text-emerald-700 rounded-full text-xs font-bold border border-emerald-100">
                {job.job_type}
              </span>
            </div>
            
            <p className="text-gray-600 text-sm line-clamp-3 mb-6 flex-1">
              {job.description}
            </p>

            <div className="space-y-4 pt-4 border-t border-gray-50 mt-auto">
              <div className="flex flex-wrap gap-2">
                {(job.required_skills || job.skills)?.split(',').map((s: string) => (
                  <span key={s} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-[10px] font-bold uppercase tracking-tight">
                    {s.trim()}
                  </span>
                ))}
              </div>

              <div className="flex items-center justify-between gap-4">
                <div className="text-xs text-gray-400">
                  <span className="font-bold text-gray-600">{job.experience_required}+ Years</span> Required
                </div>
                <div className="flex-1">
                   {applying === job.id ? (
                     <div className="flex items-center gap-2 text-xs text-indigo-600 font-bold justify-end">
                       <Loader2 className="w-4 h-4 animate-spin" /> Analyzing Resume...
                     </div>
                   ) : (
                     <div className="flex gap-2 justify-end">
                       <input 
                         type="file" 
                         id={`resume-${job.id}`} 
                         className="hidden" 
                         onChange={e => {
                          const file = e.target.files?.[0];
                          if (file) setSelectedResumes(prev => ({ ...prev, [job.id]: file }));
                        }} 
                       />
                       <label 
                         htmlFor={`resume-${job.id}`}
                         className={`px-4 py-2 rounded-xl text-xs font-bold cursor-pointer transition-all ${selectedResumes[job.id] ? 'bg-indigo-50 text-indigo-600 border border-indigo-200' : 'bg-gray-50 text-gray-400 border border-gray-200'}`}
                       >
                         {selectedResumes[job.id] ? "Resume Selected" : "Select Resume"}
                       </label>
                       <Button 
                         onClick={() => handleApply(job.id)}
                         disabled={!selectedResumes[job.id]}
                         className="px-6"
                       >
                         Apply Now
                       </Button>
                     </div>
                   )}
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {analysis && (
        <Card className="p-8 border-indigo-200 bg-indigo-50/30 animate-in zoom-in duration-500">
          <div className="text-center mb-6">
            <div className="w-20 h-20 bg-indigo-600 text-white rounded-full flex items-center justify-center text-2xl font-black mx-auto mb-4 shadow-xl shadow-indigo-200">
              {((typeof analysis.final_score === 'number' && !isNaN(analysis.final_score)) ? analysis.final_score * 100 : 0).toFixed(0)}%
            </div>
            <h3 className="text-xl font-bold text-gray-900">AI Match Result</h3>
            <p className="text-gray-500 text-sm">Based on your resume and job requirements</p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8">
            <div className="space-y-4">
              <h4 className="font-bold text-gray-700 flex items-center gap-2"><Sparkles className="w-4 h-4 text-indigo-500"/> AI Insights</h4>
              <p className="text-sm text-gray-600 bg-white p-4 rounded-xl border border-indigo-100 italic">
                "{analysis.summary_reasoning}"
              </p>
            </div>
            <div className="space-y-4">
              <h4 className="font-bold text-gray-700 flex items-center gap-2"><Target className="w-4 h-4 text-indigo-500"/> Skills Analysis</h4>
              <div className="flex flex-wrap gap-2">
                {analysis.all_skills?.slice(0, 10).map((s: string) => (
                  <span key={s} className="px-3 py-1 bg-white text-indigo-700 border border-indigo-100 rounded-lg text-xs font-semibold">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

const CandidateDashboard = () => {
  const [jd, setJd] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const handleAnalyze = async () => {
    if (!jd || !file) {
      setErrorMessage("Please provide both Job Description and Resume");
      return;
    }
    setLoading(true);
    setErrorMessage("");
    setSuccessMessage("");
    try {
      const fd = new FormData();
      fd.append('file', file);
      const upRes = await fetch(`${API_URL}/upload`, { method: 'POST', body: fd, credentials: 'include' });
      const upText = await upRes.text();
      const upData = JSON.parse(upText);

      if (upData.status !== 'success') {
          throw new Error(upData.message || "Upload failed");
      }

      const matchRes = await fetch(`${API_URL}/candidate/match`, {
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ filename: upData.filename, job_description: jd })
      });
      const matchText = await matchRes.text();
      console.log("RAW MATCH RESPONSE:", matchText);
      const data = JSON.parse(matchText);
      setResult(data);
    } catch (e: any) {
      console.error("❌ Analysis error:", e);
      setErrorMessage("Error analyzing: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const rawScore = result?.final_score;
  const score = (typeof rawScore === 'number' && !isNaN(rawScore)) ? Math.round(rawScore * 100) : 0;
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

            {successMessage && <div className="success-message">{successMessage}</div>}
            {errorMessage && <div className="error-message">{errorMessage}</div>}

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
              
              {/* UPDATED: Top Career Matches Display */}
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
                  <p className="font-bold text-gray-900">{result.experience_years || result.experience} Years</p>
                </div>
              </div>

              <div className="w-full text-left mt-6 pt-6 border-t border-gray-100">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-indigo-500" /> Professional Skills
                  </h3>
                  <span className="text-[10px] font-black bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full uppercase">
                    {result.total_skills || 0} Total Detected
                  </span>
                </div>
                
                <div className="flex flex-wrap gap-2">
                  {result.resume_skills && result.resume_skills.length > 0 ? result.resume_skills.map((s: string) => (
                    <span key={s} className="px-3 py-1 bg-white text-gray-700 rounded-lg text-sm font-medium border border-gray-200 shadow-sm hover:border-indigo-300 transition-colors">
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

const SettingsPage = () => {
  const [profile, setProfile] = useState<any>({});
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const fetchProfile = () => {
    fetch(`${API_URL}/profile`, { credentials: 'include' })
      .then(res => res.json())
      .then(data => setProfile(data))
      .catch(console.error);
  };

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setProfile(JSON.parse(storedUser));
    }
    fetchProfile();
  }, []);

  const handleSave = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_URL}/profile`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            firstName: profile.firstName,
            lastName: profile.lastName,
            email: profile.email,
            phone: profile.phone,
            city: profile.city,
            state: profile.state,
            bio: profile.bio,
            username: profile.username
          }),
        }
      );

      const text = await response.text();
      console.log("RAW PROFILE UPDATE RESPONSE:", text);

      let data;
      try {
        data = JSON.parse(text);
      } catch (err) {
        console.error("JSON PARSE ERROR:", err);
        setErrorMessage("Server returned invalid response (HTML). Check console for details.");
        setLoading(false);
        return;
      }

      if (data.success) {
        setSuccessMessage(data.message || "Profile updated successfully");
        setErrorMessage("");
        localStorage.setItem('user', JSON.stringify(profile));
        fetchProfile();
      } else {
        setErrorMessage(data.message || "Failed to save profile");
      }
    } catch (error: any) {
      console.error("FETCH ERROR:", error);
      setErrorMessage(error.message);
      setSuccessMessage("");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-6">
      <div className="flex items-start gap-8">
        {/* Settings Sidebar */}
        <div className="w-64 hidden lg:block space-y-1">
          <button className="w-full flex items-center gap-3 px-4 py-3 bg-white text-indigo-600 rounded-xl font-medium shadow-sm border border-gray-100">
            <UserCircle className="w-5 h-5" /> My Profile
          </button>
          <button className="w-full flex items-center gap-3 px-4 py-3 text-gray-500 hover:bg-white hover:text-gray-900 rounded-xl font-medium transition-colors">
            <Shield className="w-5 h-5" /> Security
          </button>
        </div>

        {/* Main Content */}
        <div className="flex-1 space-y-6">
          <Card className="overflow-hidden">
            {/* Header Banner */}
            <div className="h-32 bg-gradient-to-r from-indigo-500 to-purple-600 relative">
              <div className="absolute -bottom-10 left-8 flex items-end gap-4">
                <div className="w-24 h-24 rounded-full bg-white p-1 shadow-xl">
                  <div className="w-full h-full rounded-full bg-gray-200 flex items-center justify-center text-3xl font-bold text-gray-500 border-4 border-white">
                    {(profile.firstName?.charAt(0) || profile.username?.charAt(0) || "A").toUpperCase()}
                  </div>
                </div>
                <div className="mb-2">
                  <h2 className="text-xl font-bold text-white shadow-black drop-shadow-md">
                    {profile.firstName || profile.username || "Admin"} {profile.lastName || ""}
                  </h2>
                  <span className="px-2 py-0.5 bg-white/20 backdrop-blur-md text-white rounded text-xs font-medium border border-white/30 capitalize">{profile.role || 'User'}</span>
                </div>
              </div>
            </div>

            <div className="pt-16 p-8">
              <h3 className="text-lg font-bold text-gray-900 mb-6 border-b pb-2">Personal Information</h3>
              <div className="grid grid-cols-2 gap-6 mb-6">
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">First Name</label>
                  <input 
                    className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl" 
                    value={profile.firstName || profile.first_name || ""} 
                    placeholder="Enter first name"
                    onChange={e => setProfile({...profile, firstName: e.target.value})} 
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Last Name</label>
                  <input 
                    className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl" 
                    value={profile.lastName || profile.last_name || ""} 
                    placeholder="Enter last name"
                    onChange={e => setProfile({...profile, lastName: e.target.value})} 
                  />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Bio</label>
                  <textarea 
                    className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl h-24" 
                    value={profile.bio || ""} 
                    placeholder="Tell us about yourself"
                    onChange={e => setProfile({...profile, bio: e.target.value})} 
                  />
                </div>
              </div>

              <h3 className="text-lg font-bold text-gray-900 mb-6 border-b pb-2 pt-4">Contact Info</h3>
              <div className="grid grid-cols-2 gap-6 mb-8">
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Email Address</label>
                  <input 
                    type="email"
                    className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl" 
                    value={profile.email || ""} 
                    onChange={e => setProfile({...profile, email: e.target.value})} 
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Phone</label>
                  <input 
                    className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl" 
                    value={profile.phone || ""} 
                    placeholder="Enter phone number"
                    onChange={e => setProfile({...profile, phone: e.target.value})} 
                  />
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

              <div className="flex flex-col gap-4 pt-4">
                {successMessage && <div className="success-message mb-0">{successMessage}</div>}
                {errorMessage && <div className="error-message mb-0">{errorMessage}</div>}
                
                <div className="flex justify-end">
                  <Button onClick={handleSave} disabled={loading} className="px-8 py-3">
                    {loading ? "Saving..." : "Save Changes"}
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

const ChatPage = ({ messages, setMessages }: { messages: any[], setMessages: React.Dispatch<React.SetStateAction<any[]>> }) => {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const sendMessage = async () => {
    console.log("🚀 sendMessage triggered:", input);
    if (!input.trim() || loading) {
      console.warn("⚠️ sendMessage early return: input empty or already loading");
      return;
    }
    const userMsg = input;
    setMessages(prev => [...prev, { role: "user", text: userMsg }]);
    setInput("");
    setLoading(true);

    const SMART_FALLBACK = "I'm here to support your career journey! I can provide guidance on resume optimization, interview strategies, technical skill roadmaps, and career strategy. What specific area can I help you with right now?";

    try {
      console.log("📡 Calling API at:", `${API_URL}/chat`);
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 90000); // 90s timeout for complex RAG chains

      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: 'include',
        body: JSON.stringify({ message: userMsg }),
        signal: controller.signal,
      });
      clearTimeout(timeout);
      console.log("✅ Response status:", res.status);

      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`);
      }

      const data = await res.json();
      console.log("🧠 RAW BACKEND RESPONSE:", data);

      let aiText = "";
      if (typeof data.answer === "string" && data.answer.trim().length > 5) {
        aiText = data.answer.trim();
      } else if (typeof data.response === "string" && data.response.trim().length > 5) {
        aiText = data.response.trim();
      } else {
        console.warn("⚠️ Invalid LLM response format:", data);
        aiText = SMART_FALLBACK;
      }
      
      setMessages(prev => [...prev, { role: "ai", text: aiText }]);
    } catch (e: any) {
      console.error("❌ Chat error:", e);
      let errorMsg = SMART_FALLBACK;
      if (e.name === 'AbortError') {
        errorMsg = "The AI is taking longer than expected. Please try again in a moment.";
      } else if (e.message.includes("500") || e.message.includes("failed")) {
        errorMsg = "I'm experiencing some technical difficulties reaching the brain. Let's try again in a second!";
      }
      setMessages(prev => [...prev, { role: "ai", text: errorMsg }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div className="mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-100 rounded-lg">
              <Brain className="w-6 h-6 text-indigo-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Career Intelligence</h2>
              <p className="text-gray-500 text-sm">Real-time coaching powered by TalentFlow RAG</p>
            </div>
          </div>
        </div>
        
        <Card className="flex-1 flex flex-col overflow-hidden shadow-2xl border-gray-100 bg-white">
          <div className="p-4 bg-gradient-to-r from-indigo-600 to-indigo-800 flex justify-between items-center text-white shadow-md">
             <div className="flex items-center gap-2 font-bold tracking-tight">
                <Sparkles className="w-5 h-5 text-indigo-200" /> AI STRATEGIST
             </div>
             <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
                <span className="text-[10px] font-black uppercase opacity-80">Live Pipeline</span>
             </div>
          </div>
          
          <div className="flex-1 p-6 overflow-y-auto space-y-6 bg-slate-50/50 scroll-smooth">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'} animate-in slide-in-from-bottom-2 duration-300`}>
                <div className={`flex gap-3 max-w-[85%] ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold ${m.role === 'user' ? 'bg-indigo-100 text-indigo-600' : 'bg-indigo-600 text-white'}`}>
                    {m.role === 'user' ? 'ME' : 'AI'}
                  </div>
                  <div className={`p-4 rounded-2xl text-sm leading-relaxed shadow-sm ${m.role === 'user' ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-white border border-gray-100 text-gray-700 rounded-tl-none'}`}>
                    {m.role === 'user' ? (
                      <div className="whitespace-pre-wrap">{m.text}</div>
                    ) : (
                      <div className="markdown-content">
                        <ReactMarkdown>{m.text}</ReactMarkdown>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start animate-in fade-in duration-300">
                <div className="flex gap-3 max-w-[85%]">
                  <div className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center">
                    <Loader2 className="w-4 h-4 animate-spin" />
                  </div>
                  <div className="p-4 bg-white border border-gray-100 text-gray-400 rounded-2xl rounded-tl-none italic text-xs flex items-center gap-2">
                    <Sparkles className="w-3 h-3 animate-pulse" /> Strategizing your path...
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-4 bg-white border-t border-gray-100">
            <div className="flex gap-3">
                <input 
                  className="flex-1 border border-gray-200 rounded-xl px-5 py-4 text-sm focus:outline-none focus:border-indigo-600 focus:ring-2 focus:ring-indigo-100 transition-all bg-gray-50 focus:bg-white shadow-inner"
                  placeholder="Ask about resume tips, interview prep, or job matches..."
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && sendMessage()}
                  disabled={loading}
                />
                <button 
                  onClick={sendMessage} 
                  disabled={loading || !input.trim()}
                  className="px-5 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100 disabled:opacity-50 disabled:shadow-none hover:-translate-y-0.5 active:translate-y-0"
                >
                  <ChevronRight className="w-6 h-6" />
                </button>
            </div>
            <p className="text-[10px] text-gray-400 text-center mt-3 font-medium uppercase tracking-widest">Powered by TalentFlow Intelligence v1.9.4</p>
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
  
  // Global State for Persistence
  const [chatMessages, setChatMessages] = useState<any[]>([]);

  // ONE-TIME WELCOME: Ensures coaching starts professionally without duplication
  useEffect(() => {
    if (user && chatMessages.length === 0) {
      setChatMessages([
        { role: "ai", text: "Hi! I'm your TalentFlow AI career coach. Ask me anything about your career, jobs, or candidates." }
      ]);
    }
  }, [user]);

  // --- PERSISTENT CHAT HISTORY FETCH ---
  useEffect(() => {
    if (user && activeTab === 'chat') {
      fetch(`${API_URL}/chat_history`, { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
          if (data.history && data.history.length > 0) {
            const formatted = data.history.map((h: any) => ([
              { role: "user", text: h.user },
              { role: "ai", text: h.ai }
            ])).flat();
            setChatMessages(formatted);
          }
        })
        .catch(console.error);
    }
  }, [user, activeTab]);

  // --- Session Persistence Logic ---
  useEffect(() => {
    // Check if user is logged in
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const handleLoginSuccess = (userData: any) => {
    console.log("🔐 [AUTH] Login Success Received:", userData);
    setUser(userData);
    setMobileMenuOpen(false);
    
    // Ensure we store a complete object including email for settings
    const userToStore = {
      user: userData.user || userData.username,
      email: userData.email,
      role: userData.role,
      token: userData.token
    };
    
    localStorage.setItem('user', JSON.stringify(userToStore));
    if (userData.token) {
      console.log("🎟️ [AUTH] Storing Token:", userData.token);
      localStorage.setItem('token', userData.token);
    } else {
      console.error("🚨 [AUTH] NO TOKEN FOUND IN RESPONSE!");
    }
  };

  if (!user) return <LoginPage onLogin={handleLoginSuccess} />;

  const handleLogout = async () => {
    await fetch(`${API_URL}/api/logout`, { method: 'POST', credentials: 'include' });
    setUser(null);
    localStorage.removeItem('user');
  };

  const menuItems = user.role === 'hr' ? [
    { id: 'dashboard', label: 'Screening', icon: LayoutDashboard },
    { id: 'candidates', label: 'Candidates', icon: Users },
    { id: 'jobs', label: 'Job Posts', icon: Briefcase },
    { id: 'settings', label: 'Settings', icon: Settings },
  ] : [
    { id: 'dashboard', label: 'Career Analysis', icon: Sparkles },
    { id: 'jobs', label: 'Job Feed', icon: Briefcase },
    { id: 'chat', label: 'AI Coach', icon: MessageSquare },
    { id: 'puzzle', label: 'Brain Teasers', icon: Puzzle },
    { id: 'quiz', label: 'Tech Quizzes', icon: Brain },
    { id: 'settings', label: 'My Profile', icon: User },
  ];

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden font-sans text-gray-900">
      
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
                {user.user?.[0]?.toUpperCase() || "?"}
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
        {/* Header */}
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

        {/* Content */}
        <main className="flex-1 overflow-auto p-4 sm:p-6 lg:p-8 relative">
          <div className="max-w-7xl mx-auto h-full">
            {activeTab === 'dashboard' && (user.role === 'hr' ? <HRDashboard /> : <CandidateDashboard />)}
            {activeTab === 'settings' && <SettingsPage />}
            {activeTab === 'quiz' && <TechQuiz />}
            {activeTab === 'puzzle' && <PuzzleGame />}
            {activeTab === 'chat' && <ChatPage messages={chatMessages} setMessages={setChatMessages} />}
            {activeTab === 'candidates' && <div className="flex flex-col items-center justify-center h-full text-gray-400"><Users className="w-16 h-16 mb-4 opacity-50"/><p>Candidate List Management</p></div>}
            {activeTab === 'jobs' && (user.role === 'hr' ? <JobManagement /> : <JobBrowse />)}
          </div>
        </main>
      </div>
    </div>
  );
}