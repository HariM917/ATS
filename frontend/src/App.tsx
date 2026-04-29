import React, { useState, useEffect, useRef } from 'react';
import { 
  LayoutDashboard, Users, Briefcase, BarChart3, MessageSquare, 
  Settings, LogOut, Bell, Menu, X, 
  ChevronRight, Sparkles, User, Save, Upload, Loader2, 
  CheckCircle, Sliders, FileText, UserCircle, Shield, Brain, Puzzle, Target, Layers, ArrowLeft, PieChart
} from 'lucide-react';
import TechQuiz from './TechQuiz';
import PuzzleGame from './PuzzleGame';

// Standardized to port 5000 as per deployment hardening plan
const API_URL = "http://127.0.0.1:5000/api";

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
      console.log(`Attempting to connect to: ${API_URL}/login`);
      const res = await fetch(`${API_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...formData, role, mode }),
      });
      const data = await res.json();
      
      if (res.ok && data.status === "success") {
        onLogin(data);
      } else {
        setError(data.message || "Authentication failed");
      }
    } catch (err) {
      console.error("Login connection error:", err);
      setError("Server connection failed. Ensure backend is running on port 8000.");
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

        <div className="mt-6 text-center text-xs text-gray-400">
          {role === 'hr' ? 'Demo: admin / password123' : 'Enter details to start demo'}
        </div>
      </div>
    </div>
  );
};

const AnalyticsDashboard = () => {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_URL}/hr/analytics`);
      const data = await res.json();
      if (data.status === "success") setStats(data.analytics);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="animate-spin w-10 h-10 text-indigo-600"/></div>;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Hiring Analytics</h2>
      
      <div className="grid md:grid-cols-4 gap-4">
        <Card className="p-6 bg-indigo-600 text-white">
          <p className="text-xs font-bold uppercase opacity-80">Total Jobs</p>
          <h3 className="text-3xl font-black">{stats?.total_jobs}</h3>
        </Card>
        <Card className="p-6 bg-emerald-500 text-white">
          <p className="text-xs font-bold uppercase opacity-80">Total Applicants</p>
          <h3 className="text-3xl font-black">{stats?.total_applicants}</h3>
        </Card>
        <Card className="p-6 bg-amber-400 text-white">
          <p className="text-xs font-bold uppercase opacity-80">Avg. Match Score</p>
          <h3 className="text-3xl font-black">{stats?.average_score}%</h3>
        </Card>
        <Card className="p-6 bg-white border-gray-200">
          <p className="text-xs font-bold uppercase text-gray-400">Hiring Velocity</p>
          <h3 className="text-3xl font-black text-gray-900">Fast</h3>
        </Card>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="font-bold mb-4 flex items-center gap-2"><PieChart className="w-5 h-5 text-indigo-600"/> Pipeline Breakdown</h3>
          <div className="space-y-4">
            {Object.entries(stats?.status_breakdown || {}).map(([status, count]: any) => (
              <div key={status} className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-600">{status}</span>
                <div className="flex items-center gap-3 flex-1 mx-4">
                  <div className="h-2 bg-gray-100 rounded-full flex-1 overflow-hidden">
                    <div className="h-full bg-indigo-500" style={{width: `${(count / stats.total_applicants) * 100}%`}}></div>
                  </div>
                  <span className="text-xs font-bold text-gray-900 w-8">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
        
        <Card className="p-6 flex flex-col items-center justify-center text-center space-y-2 opacity-50">
          <BarChart3 className="w-12 h-12 text-gray-300" />
          <p className="text-sm font-medium text-gray-400">Advanced Skills Heatmap Coming Soon</p>
        </Card>
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
  
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    location: "",
    job_type: "Full-time",
    salary: "",
    skills: "",
    experience_required: 0,
    hr_email: ""
  });

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/jobs`);
      const data = await res.json();
      if (data.status === "success") setJobs(data.jobs);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const fetchApplicants = async (jobId: number) => {
    setLoadingApps(true);
    try {
      const res = await fetch(`${API_URL}/jobs/${jobId}/applications`);
      const data = await res.json();
      if (data.status === "success") setApplicants(data.applications);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingApps(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleStatusUpdate = async (appId: number, status: string) => {
    try {
      const res = await fetch(`${API_URL}/applications/${appId}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status })
      });
      if (res.ok) {
        fetchApplicants(selectedJob.id);
      }
    } catch (e) {
      alert("Failed to update status");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_URL}/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      if (data.status === "success") {
        alert("Job Posted!");
        setShowForm(false);
        setFormData({ title: "", description: "", location: "", job_type: "Full-time", salary: "", skills: "", experience_required: 0, hr_email: "" });
        fetchJobs();
      }
    } catch (e) {
      alert("Error posting job");
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this job?")) return;
    try {
      await fetch(`${API_URL}/jobs/${id}`, { method: "DELETE" });
      fetchJobs();
    } catch (e) {
      alert("Error deleting job");
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
                         <Button variant="secondary" onClick={() => window.open(`${API_URL}/uploads/${app.resume_path.split('/').pop()}`)} className="text-[10px] px-3 py-1"><FileText className="w-3 h-3"/></Button>
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
              <div className="col-span-2">
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">Job Title</label>
                <input required className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl" value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} placeholder="e.g. Senior React Developer" />
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
                <input className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl" value={formData.skills} onChange={e => setFormData({...formData, skills: e.target.value})} placeholder="React, Node.js, TypeScript" />
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
            <Button type="submit" className="w-full py-3 mt-4">Post Job Opportunity</Button>
          </form>
        </Card>
      )}

      <div className="grid gap-4">
        {loading ? <p className="text-center py-10 text-gray-400">Loading jobs...</p> : jobs.length === 0 ? <p className="text-center py-10 text-gray-400">No jobs posted yet.</p> : jobs.map(job => (
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
        ))}
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
    if (!jd || files.length === 0) return alert("Please provide JD and Resumes");
    setLoading(true);
    setResults([]); // Clear previous results while loading
    
    try {
      // 1. Upload Loop
      const uploadedInfo = [];
      for (let file of files) {
        const fd = new FormData();
        fd.append('file', file);
        const res = await fetch(`${API_URL}/upload`, { method: 'POST', body: fd });
        const data = await res.json();
        if (data.status === 'success') {
          uploadedInfo.push({ filename: data.filename, original_name: file.name });
        }
      }

      // 2. Batch Match
      const res = await fetch(`${API_URL}/batch_match`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidates: uploadedInfo, job_description: jd })
      });
      
      const data = await res.json();
      
      if (data.ranked_candidates) {
        setResults(data.ranked_candidates);
      } else {
        console.warn("No ranked candidates returned from backend");
        setResults([]);
      }
      
    } catch (e) {
      console.error("Error processing resumes:", e);
      alert("Error processing. Please check console for details.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid lg:grid-cols-12 gap-6 h-full">
      {/* Input Column */}
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

      {/* Results Column */}
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
                        <p className="text-xs text-gray-500 font-medium">Experience: {c.experience_years || c.experience} Years</p>
                        
                        {/* ROBUST: Handle missing or non-array top_roles gracefully */}
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
                          // Fallback if top_roles is missing but predicted_role exists
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

const JobBrowse = () => {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState<number | null>(null);
  const [resume, setResume] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);

  const fetchAllJobs = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/all_jobs`);
      const data = await res.json();
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
    if (!resume) return alert("Please select a resume");
    setApplying(jobId);
    setAnalysis(null);
    try {
      const fd = new FormData();
      fd.append("resume", resume);
      const res = await fetch(`${API_URL}/jobs/${jobId}/apply`, {
        method: "POST",
        body: fd
      });
      const data = await res.json();
      if (data.status === "success") {
        setAnalysis(data.analysis);
        alert("Application Successful! AI Score: " + (data.score * 100).toFixed(0) + "%");
      } else {
        alert(data.message || "Failed to apply");
      }
    } catch (e) {
      alert("Error applying");
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
                <p className="text-indigo-600 font-semibold text-sm">{job.company_name}</p>
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
                {job.skills?.split(',').map((s: string) => (
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
                         onChange={e => setResume(e.target.files?.[0] || null)} 
                       />
                       <label 
                         htmlFor={`resume-${job.id}`}
                         className={`px-4 py-2 rounded-xl text-xs font-bold cursor-pointer transition-all ${resume ? 'bg-indigo-50 text-indigo-600 border border-indigo-200' : 'bg-gray-50 text-gray-400 border border-gray-200'}`}
                       >
                         {resume ? "Resume Selected" : "Select Resume"}
                       </label>
                       <Button 
                         onClick={() => handleApply(job.id)}
                         disabled={!resume}
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
              {(analysis.final_score * 100).toFixed(0)}%
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

  const handleAnalyze = async () => {
    if (!jd || !file) return alert("Missing Info");
    setLoading(true);
    try {
      // 1. Upload
      const fd = new FormData();
      fd.append('file', file);
      const upRes = await fetch(`${API_URL}/upload`, { method: 'POST', body: fd });
      const upData = await upRes.json();

      // 2. Match
      const matchRes = await fetch(`${API_URL}/candidate/match`, {
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: upData.filename, job_description: jd })
      });
      const data = await matchRes.json();
      setResult(data);
    } catch (e) {
      alert("Error analyzing");
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
                    <Sparkles className="w-4 h-4 text-indigo-500" /> Skills Detected
                  </h3>
                  {result.total_skills > 0 && (
                    <span className="text-[10px] font-black bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full uppercase">
                      {result.total_skills} Total
                    </span>
                  )}
                </div>
                
                <div className="flex flex-wrap gap-2">
                  {result.all_skills && result.all_skills.length > 0 ? result.all_skills.map((s: string) => (
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

  // Helper to fetch profile data
  const fetchProfile = () => {
    fetch(`${API_URL}/profile`)
      .then(res => res.json())
      .then(data => setProfile(data))
      .catch(console.error);
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const handleSave = async () => {
    setLoading(true);
    try {
      await fetch(`${API_URL}/update_profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      });
      alert("Profile Saved!");
      // Re-fetch profile data to ensure UI is in sync with DB
      fetchProfile();
    } catch (e) {
      alert("Error saving");
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
                    {profile.username?.[0]?.toUpperCase()}
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

const ChatPage = ({ messages, setMessages }: { messages: any[], setMessages: React.Dispatch<React.SetStateAction<any[]>> }) => {
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
      // PRO FIX: Direct targeted API call to port 5000
      const res = await fetch("http://127.0.0.1:5000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMsg }),
      });
      const data = await res.json();
      console.log("API RESPONSE:", data); // Standardize debugging as per requested fix
      
      setMessages(prev => [
        ...prev, 
        { role: "ai", text: data.answer || data.response || "I'm sorry, I couldn't generate a response." }
      ]);
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
                <div className={`max-w-[80%] p-4 rounded-2xl text-sm shadow-sm ${m.role === 'user' ? 'bg-indigo-600 text-white rounded-br-none' : 'bg-white border border-gray-100 text-gray-700 rounded-bl-none'}`}>
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
  
  // Global State for Persistence
  const [chatMessages, setChatMessages] = useState([
    { role: "ai", text: "Ask me anything about your career, jobs, or candidates." }
  ]);

  // --- Session Persistence Logic ---
  useEffect(() => {
    // Check if user is logged in
    const storedUser = localStorage.getItem('ats_user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const handleLoginSuccess = (userData: any) => {
    setUser(userData);
    setMobileMenuOpen(false);
    // Save to localStorage
    localStorage.setItem('ats_user', JSON.stringify(userData));
  };

  if (!user) return <LoginPage onLogin={handleLoginSuccess} />;

  const handleLogout = async () => {
    await fetch(`${API_URL}/logout`, { method: 'POST' });
    setUser(null);
    localStorage.removeItem('ats_user');
  };

  const menuItems = user.role === 'hr' ? [
    { id: 'dashboard', label: 'Screening', icon: LayoutDashboard },
    { id: 'candidates', label: 'Candidates', icon: Users },
    { id: 'jobs', label: 'Job Posts', icon: Briefcase },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Settings },
  ] : [
    { id: 'dashboard', label: 'Career Analysis', icon: Sparkles },
    { id: 'jobs', label: 'Job Feed', icon: Briefcase },
    { id: 'chat', label: 'AI Coach', icon: MessageSquare },
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
            {activeTab === 'analytics' && (user.role === 'hr' ? <AnalyticsDashboard /> : <div className="flex flex-col items-center justify-center h-full text-gray-400"><BarChart3 className="w-16 h-16 mb-4 opacity-50"/><p>Personal Analytics Coming Soon</p></div>)}
          </div>
        </main>
      </div>
    </div>
  );
}