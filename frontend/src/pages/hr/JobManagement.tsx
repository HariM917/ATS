import React, { useState, useEffect } from 'react';
import { apiClient, API_ORIGIN } from '../../services/api';
import { Card, Button, ScoreBadge, SkeletonCard, EmptyState } from '../../components/ui';
import { 
  Briefcase, ArrowLeft, Loader2, FileText, Building2, X 
} from 'lucide-react';
import { Helmet } from 'react-helmet-async';
import { Job, Application } from '../../types';

export const JobManagement = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [applicants, setApplicants] = useState<Application[]>([]);
  const [loadingApps, setLoadingApps] = useState(false);
  
  // Custom toast notification handler
  const [toast, setToast] = useState<{ type: 'success' | 'error' | 'info', msg: string } | null>(null);
  const showToast = (type: 'success' | 'error' | 'info', msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 4000);
  };
  
  const [formData, setFormData] = useState({
    company_name: "", branch: "", job_title: "", description: "",
    location: "", job_type: "Full-time", salary: "",
    required_skills: "", experience_required: 0, hr_email: ""
  });

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/jobs');
      if (!res.ok) throw new Error(`Server Error: ${res.status}`);
      const data = await res.json();
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
      const res = await apiClient.get(`/jobs/${jobId}/applications`);
      if (!res.ok) throw new Error(`Server Error: ${res.status}`);
      const data = await res.json();
      if (data.status === "success") setApplicants(data.applications);
    } catch (e: any) {
      console.error("Fetch Applicants Failed:", e);
    } finally {
      setLoadingApps(false);
    }
  };

  useEffect(() => { fetchJobs(); }, []);

  const handleStatusUpdate = async (appId: number, status: string) => {
    try {
      const res = await apiClient.post(`/applications/${appId}/status`, { status });
      if (res.ok) {
        showToast('success', `Candidate ${status.toLowerCase()} successfully`);
        fetchApplicants(selectedJob!.id);
      }
    } catch {
      showToast('error', 'Failed to update status');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await apiClient.post('/jobs', formData);
      const data = await response.json();
      if (response.ok && (data.success || data.status === "success")) {
        showToast('success', 'Job posted successfully!');
        setShowForm(false);
        setFormData({ company_name: "", branch: "", job_title: "", description: "", location: "", job_type: "Full-time", salary: "", required_skills: "", experience_required: 0, hr_email: "" });
        fetchJobs();
      } else {
        showToast('error', data.message || 'Failed to post job');
      }
    } catch {
      showToast('error', 'Connection failed. Try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this job and all its applications?")) return;
    try {
      await apiClient.delete(`/jobs/${id}`);
      showToast('info', 'Job deleted');
      fetchJobs();
    } catch {
      showToast('error', 'Error deleting job');
    }
  };

  if (selectedJob) {
    return (
      <div className="space-y-6 page-enter">
        {toast && (
          <div className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg text-white font-medium ${toast.type === 'success' ? 'bg-emerald-500' : toast.type === 'error' ? 'bg-red-500' : 'bg-indigo-500'}`}>
            <span>{toast.msg}</span>
          </div>
        )}
        <div className="flex items-center gap-4">
          <Button variant="secondary" onClick={() => setSelectedJob(null)}><ArrowLeft className="w-4 h-4 mr-1" /> Back</Button>
          <h2 className="text-2xl font-bold text-gray-900">{selectedJob.title} — Applicants</h2>
        </div>

        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50/80 border-b border-gray-100">
                  <th className="p-4 text-xs font-bold text-gray-400 uppercase tracking-widest">Candidate</th>
                  <th className="p-4 text-xs font-bold text-gray-400 uppercase tracking-widest">AI Score</th>
                  <th className="p-4 text-xs font-bold text-gray-400 uppercase tracking-widest">Status</th>
                  <th className="p-4 text-xs font-bold text-gray-400 uppercase tracking-widest text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loadingApps ? (
                  <tr><td colSpan={4} className="p-10 text-center"><Loader2 className="animate-spin w-8 h-8 mx-auto text-indigo-500" /></td></tr>
                ) : applicants.length === 0 ? (
                  <tr><td colSpan={4} className="p-10 text-center text-gray-400">No applications yet.</td></tr>
                ) : applicants.map(app => (
                  <tr key={app.id} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                    <td className="p-4">
                      <div className="font-bold text-gray-900">{app.candidate_name}</div>
                      <div className="text-xs text-gray-500">{app.candidate_email}</div>
                    </td>
                    <td className="p-4"><ScoreBadge score={app.score} /></td>
                    <td className="p-4">
                      <span className={`px-2.5 py-1 rounded-md text-[10px] font-black uppercase tracking-tight ${app.status === 'Shortlisted' ? 'bg-emerald-55 bg-emerald-50 text-emerald-600 border border-emerald-100' : app.status === 'Rejected' ? 'bg-red-50 text-red-600 border border-red-100' : 'bg-indigo-50 text-indigo-600 border border-indigo-100'}`}>
                        {app.status}
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <div className="flex gap-2 justify-end">
                        <Button variant="secondary" onClick={() => handleStatusUpdate(app.id, 'Shortlisted')} className="text-[10px] px-3 py-1 bg-emerald-50 text-emerald-600 border-emerald-100 hover:bg-emerald-100">Accept</Button>
                        <Button variant="secondary" onClick={() => handleStatusUpdate(app.id, 'Rejected')} className="text-[10px] px-3 py-1 bg-red-50 text-red-600 border-red-100 hover:bg-red-100">Reject</Button>
                        <Button variant="secondary" onClick={() => window.open(`${API_ORIGIN}/uploads/${app.resume_path?.split('/').pop()}`)} className="text-[10px] px-3 py-1"><FileText className="w-3 h-3" /></Button>
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
    <div className="space-y-6 page-enter">
      <Helmet>
        <title>Job Management | FlowATS</title>
        <meta name="description" content="Manage job postings and AI-ranked applicants." />
      </Helmet>
      {toast && (
        <div className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg text-white font-medium ${toast.type === 'success' ? 'bg-emerald-500' : toast.type === 'error' ? 'bg-red-500' : 'bg-indigo-500'}`}>
          <span>{toast.msg}</span>
        </div>
      )}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Job Postings</h2>
        <Button onClick={() => setShowForm(!showForm)}>{showForm ? "Cancel" : "Create New Job"}</Button>
      </div>

      {showForm && (
        <Card className="p-6 animate-in slide-in-from-top-4 duration-300">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">Company Name</label>
                <input required className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" value={formData.company_name} onChange={e => setFormData({ ...formData, company_name: e.target.value })} placeholder="e.g. Google" />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">Branch / Dept</label>
                <input required className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" value={formData.branch} onChange={e => setFormData({ ...formData, branch: e.target.value })} placeholder="e.g. AI Research" />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">Job Title</label>
                <input required className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" value={formData.job_title} onChange={e => setFormData({ ...formData, job_title: e.target.value })} placeholder="e.g. Senior Software Engineer" />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">Description</label>
                <textarea required className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none h-32 resize-none" value={formData.description} onChange={e => setFormData({ ...formData, description: e.target.value })} placeholder="Describe the role..." />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">Location</label>
                <input className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" value={formData.location} onChange={e => setFormData({ ...formData, location: e.target.value })} placeholder="Remote / NY / SF" />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">Job Type</label>
                <select className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" value={formData.job_type} onChange={e => setFormData({ ...formData, job_type: e.target.value })}>
                  <option>Full-time</option><option>Part-time</option><option>Contract</option><option>Internship</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">Required Skills</label>
                <input className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" value={formData.required_skills} onChange={e => setFormData({ ...formData, required_skills: e.target.value })} placeholder="React, Node.js, TypeScript" />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">Experience (Years)</label>
                <input type="number" min="0" className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" value={formData.experience_required} onChange={e => setFormData({ ...formData, experience_required: parseInt(e.target.value) || 0 })} />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1.5">HR Contact Email</label>
                <input required type="email" className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" value={formData.hr_email} onChange={e => setFormData({ ...formData, hr_email: e.target.value })} placeholder="hr@company.com" />
              </div>
            </div>
            <Button type="submit" disabled={loading} className="w-full py-3 mt-4">
              {loading ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : "Post Job Opportunity"}
            </Button>
          </form>
        </Card>
      )}

      <div className="grid gap-4">
        {loading && jobs.length === 0 ? (
          <>{[1,2,3].map(i => <SkeletonCard key={i} />)}</>
        ) : jobs.length === 0 ? (
          <EmptyState icon={Briefcase} title="No jobs posted yet" subtitle="Create your first job posting to get started" />
        ) : (
          jobs.map(job => (
            <Card key={job.id} className="p-6" hover>
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-bold text-gray-900">{job.title}</h3>
                  <div className="flex gap-4 mt-1 text-sm text-gray-500 font-medium">
                    {job.company_name && <span className="flex items-center gap-1"><Building2 className="w-4 h-4" /> {job.company_name}</span>}
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
