import React, { useState, useEffect } from 'react';
import { apiClient } from '../../services/api';
import { Card, Button, ScoreBadge, SkeletonCard, EmptyState } from '../../components/ui';
import { 
  Briefcase, Building2, FileText, Upload, Sparkles, Loader2, Target, CheckCircle2, ChevronRight 
} from 'lucide-react';
import { Helmet } from 'react-helmet-async';
import { Job, MatchResult } from '../../types';

export const JobBrowse = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState<number | null>(null);
  const [selectedResumes, setSelectedResumes] = useState<Record<number, File>>({});
  const [analysis, setAnalysis] = useState<MatchResult | null>(null);
  
  // Custom toast notification handler
  const [toast, setToast] = useState<{ type: 'success' | 'error', msg: string } | null>(null);
  const showToast = (type: 'success' | 'error', msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 4000);
  };

  const fetchAllJobs = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/all_jobs');
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
    const resume = selectedResumes[jobId];
    if (!resume) { showToast('error', 'Please select a resume first'); return; }
    setApplying(jobId);
    setAnalysis(null);
    try {
      const fd = new FormData();
      fd.append("resume", resume);
      const res = await apiClient.post(`/jobs/${jobId}/apply`, fd, true);
      const data = await res.json();
      if (data.status === "success") {
        // Sanitize the analysis results
        const sanitized: MatchResult = {
          final_score: typeof data.analysis?.final_score === 'number' && !isNaN(data.analysis.final_score) ? data.analysis.final_score : 0,
          match_percentage: typeof data.analysis?.match_percentage === 'number' && !isNaN(data.analysis.match_percentage) ? data.analysis.match_percentage : 0,
          predicted_role: data.analysis?.predicted_role || 'Unknown',
          resume_skills: Array.isArray(data.analysis?.resume_skills) ? data.analysis.resume_skills : [],
          matched_skills: Array.isArray(data.analysis?.matched_skills) ? data.analysis.matched_skills : [],
          missing_skills: Array.isArray(data.analysis?.missing_skills) ? data.analysis.missing_skills : [],
          all_skills: Array.isArray(data.analysis?.all_skills) ? data.analysis.all_skills : [],
          summary_reasoning: data.analysis?.summary_reasoning || 'Analysis complete.',
          experience: data.analysis?.experience || 'Unknown',
          experience_years: data.analysis?.experience_years || 0,
          total_skills: data.analysis?.total_skills || 0,
        };
        setAnalysis(sanitized);
        showToast('success', 'Application submitted successfully!');
      } else {
        showToast('error', data.message || 'Failed to apply');
      }
    } catch {
      showToast('error', 'Error applying');
    } finally {
      setApplying(null);
    }
  };

  return (
    <div className="space-y-6 page-enter">
      <Helmet>
        <title>Job Feed | FlowATS</title>
        <meta name="description" content="Browse AI-matched jobs and apply instantly." />
      </Helmet>
      {toast && (
        <div className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg text-white font-medium ${toast.type === 'success' ? 'bg-emerald-500' : 'bg-red-500'}`}>
          <span>{toast.msg}</span>
        </div>
      )}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Career Feed</h2>
        <span className="px-3 py-1 bg-emerald-50 text-emerald-700 rounded-full text-xs font-bold border border-emerald-100">Live Roles</span>
      </div>

      <div className="grid lg:grid-cols-12 gap-6">
        <div className={analysis ? "lg:col-span-7 space-y-4" : "lg:col-span-12 space-y-4"}>
          {loading && jobs.length === 0 ? (
            <>{[1, 2, 3].map(i => <SkeletonCard key={i} />)}</>
          ) : jobs.length === 0 ? (
            <EmptyState icon={Briefcase} title="No jobs available" subtitle="Check back later for new career opportunities" />
          ) : (
            jobs.map(job => (
              <Card key={job.id} className="p-6 transition-all border border-gray-100 hover:border-indigo-100" hover>
                <div className="flex flex-col md:flex-row justify-between gap-4 items-start md:items-center">
                  <div className="space-y-2 flex-1">
                    <h3 className="text-lg font-bold text-gray-900">{job.title}</h3>
                    <div className="flex flex-wrap gap-4 text-xs text-gray-500 font-medium">
                      {job.company_name && <span className="flex items-center gap-1"><Building2 className="w-4 h-4" /> {job.company_name}</span>}
                      <span className="flex items-center gap-1"><FileText className="w-4 h-4" /> {job.job_type}</span>
                      {job.location && <span className="flex items-center gap-1">📍 {job.location}</span>}
                      {job.salary && <span className="flex items-center gap-1">💰 {job.salary}</span>}
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-2 pt-1">{job.description}</p>
                    {job.required_skills && (
                      <div className="flex flex-wrap gap-1 pt-1">
                        {job.required_skills.split(',').map((s, idx) => (
                          <span key={idx} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-[10px] font-semibold">{s.trim()}</span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="flex flex-col gap-2 w-full md:w-auto items-end">
                    <div className="relative w-full md:w-44 flex items-center bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 text-xs font-semibold cursor-pointer">
                      <input 
                        type="file" 
                        accept=".pdf,.docx,.txt" 
                        className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                        onChange={e => e.target.files && setSelectedResumes(prev => ({ ...prev, [job.id]: e.target.files![0] }))}
                      />
                      <Upload className="w-4 h-4 text-gray-400 mr-2" />
                      <span className="truncate max-w-[120px]">{selectedResumes[job.id]?.name || "Upload Resume"}</span>
                    </div>
                    <Button 
                      onClick={() => handleApply(job.id)} 
                      disabled={applying === job.id || !selectedResumes[job.id]}
                      className="w-full md:w-auto"
                    >
                      {applying === job.id ? <Loader2 className="animate-spin w-4 h-4 mx-auto" /> : "Apply with AI"}
                    </Button>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>

        {analysis && (
          <div className="lg:col-span-5 animate-in slide-in-from-right-4 duration-300">
            <Card className="p-6 border-indigo-100 sticky top-6">
              <div className="flex justify-between items-center mb-6 pb-4 border-b border-gray-100">
                <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2"><Sparkles className="w-5 h-5 text-indigo-600" /> Match Report</h3>
                <button type="button" onClick={() => setAnalysis(null)} className="text-gray-400 hover:text-gray-600 font-bold">X</button>
              </div>

              <div className="flex flex-col items-center py-6 bg-slate-50/50 rounded-2xl border border-dashed border-gray-100 mb-6">
                <ScoreBadge score={analysis.final_score} size="lg" />
                <h4 className="font-bold text-gray-800 text-lg mt-3">{analysis.predicted_role}</h4>
                <p className="text-xs text-gray-400 font-medium">Experience Detected: {analysis.experience}</p>
              </div>

              <div className="space-y-4">
                <div>
                  <h5 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2 flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-emerald-500" /> Matched Skills</h5>
                  <div className="flex flex-wrap gap-1">
                    {analysis.matched_skills && analysis.matched_skills.length > 0 ? (
                      analysis.matched_skills.map((s, idx) => (
                        <span key={idx} className="px-2 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-100 rounded text-[10px] font-semibold">{s}</span>
                      ))
                    ) : <span className="text-xs text-gray-400 italic">No matches detected.</span>}
                  </div>
                </div>

                <div>
                  <h5 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2 flex items-center gap-1.5"><ChevronRight className="w-4 h-4 text-indigo-500" /> Missing Skills</h5>
                  <div className="flex flex-wrap gap-1">
                    {analysis.missing_skills && analysis.missing_skills.length > 0 ? (
                      analysis.missing_skills.map((s, idx) => (
                        <span key={idx} className="px-2 py-0.5 bg-indigo-50 text-indigo-700 border border-indigo-100 rounded text-[10px] font-semibold">{s}</span>
                      ))
                    ) : <span className="text-xs text-gray-400 italic">None detected.</span>}
                  </div>
                </div>

                <div className="pt-4 border-t border-gray-100">
                  <h5 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2 flex items-center gap-1.5">📝 RAG Feedback</h5>
                  <p className="text-xs text-gray-600 leading-relaxed bg-indigo-50/30 p-3 rounded-xl border border-indigo-50/50">{analysis.summary_reasoning}</p>
                </div>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};
