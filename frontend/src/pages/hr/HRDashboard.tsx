import React, { useState } from 'react';
import { apiClient } from '../../services/api';
import { Card, Button, ScoreBadge, SkeletonCard, EmptyState } from '../../components/ui';
import { 
  Sliders, Upload, Loader2, Sparkles, X, Users, Target, Briefcase 
} from 'lucide-react';
import { Helmet } from 'react-helmet-async';
import { MatchResult } from '../../types';

export const HRDashboard = () => {
  const [jd, setJd] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<MatchResult[]>([]);
  
  // Custom toast notification handler
  const [toast, setToast] = useState<{ type: 'success' | 'error', msg: string } | null>(null);
  const showToast = (type: 'success' | 'error', msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 4000);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setFiles(prev => [...prev, ...Array.from(e.dataTransfer.files)]);
  };

  const handleProcess = async () => {
    if (files.length === 0 || jd.trim().length < 3) return;
    setLoading(true);
    const formData = new FormData();
    formData.append("jd", jd);
    files.forEach(file => formData.append("resumes", file));
    
    try {
      const response = await apiClient.post('/process_resumes', formData, true);
      const data = await response.json();
      if (data.success) {
        // Sanitize match results using our front-end validation guard
        const sanitized = (data.rankings || []).map((r: any) => ({
          ...r,
          final_score: typeof r.final_score === 'number' && !isNaN(r.final_score) ? r.final_score : 0,
          match_percentage: typeof r.match_percentage === 'number' && !isNaN(r.match_percentage) ? r.match_percentage : 0,
          predicted_role: r.predicted_role || 'Unknown',
          resume_skills: Array.isArray(r.resume_skills) ? r.resume_skills : [],
          matched_skills: Array.isArray(r.matched_skills) ? r.matched_skills : [],
          top_roles: Array.isArray(r.top_roles) ? r.top_roles : [r.predicted_role || 'Unknown'],
          experience_years: typeof r.experience_years === 'number' ? r.experience_years : 0,
          experience: r.experience || 'Unknown'
        }));
        setResults(sanitized);
        showToast('success', `Processed ${data.count} resumes successfully`);
      } else {
        showToast('error', data.error || "Processing failed");
        setResults([]);
      }
    } catch {
      showToast('error', 'Server connection failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid lg:grid-cols-12 gap-6 h-full page-enter">
      <Helmet>
        <title>Candidate Screening | FlowATS</title>
        <meta name="description" content="AI-powered resume screening and candidate ranking." />
      </Helmet>
      {toast && (
        <div className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg text-white font-medium ${toast.type === 'success' ? 'bg-emerald-500' : 'bg-red-500'}`}>
          <span>{toast.msg}</span>
        </div>
      )}
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
              className="flex-1 border-2 border-dashed border-gray-300 rounded-xl bg-gray-50 flex flex-col items-center justify-center p-6 text-center cursor-pointer hover:bg-indigo-50 hover:border-indigo-400 transition-colors relative min-h-[120px]"
            >
              <input type="file" multiple className="absolute inset-0 opacity-0 cursor-pointer" onChange={e => e.target.files && setFiles(prev => [...prev, ...Array.from(e.target.files!)])} />
              <Upload className="w-10 h-10 text-gray-400 mb-3" />
              <p className="font-semibold text-gray-700">Drag & Drop Resumes</p>
              <p className="text-xs text-gray-400 mt-1">PDF, DOCX supported</p>
            </div>
            {files.length > 0 && (
              <div className="mt-4 max-h-32 overflow-y-auto space-y-2">
                {files.map((f, i) => (
                  <div key={i} className="flex justify-between items-center bg-gray-100 p-2 rounded-lg text-xs">
                    <span className="truncate max-w-[200px] font-medium">{f.name}</span>
                    <button type="button" onClick={() => setFiles(files.filter((_, idx) => idx !== i))} className="text-red-500 hover:bg-red-100 p-1 rounded"><X className="w-3 h-3" /></button>
                  </div>
                ))}
              </div>
            )}
          </div>
          <Button
            onClick={handleProcess}
            disabled={loading || jd.trim().length < 3 || files.length === 0}
            className={`w-full py-4 text-lg font-bold shadow-xl transition-all duration-300 ${jd.trim().length < 3 || files.length === 0 ? 'opacity-50 cursor-not-allowed' : 'hover:scale-[1.02] active:scale-[0.98]'}`}
          >
            {loading ? <Loader2 className="animate-spin w-5 h-5 mx-auto" /> : <><Sparkles className="w-5 h-5 mr-2" /> Rank Candidates</>}
          </Button>
          {(jd.length > 0 && jd.trim().length < 3) && (
            <p className="text-[10px] text-red-500 mt-2 font-bold animate-pulse text-center">Enter a job title or description (e.g. Data Analyst).</p>
          )}
        </Card>
      </div>

      <div className="lg:col-span-7 h-full">
        <Card className="h-full p-6 flex flex-col">
          <div className="flex justify-between items-center mb-6 pb-4 border-b border-gray-100">
            <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2"><Users className="w-5 h-5 text-indigo-600" /> Ranked Candidates</h3>
            <span className="px-3 py-1 bg-indigo-50 text-indigo-700 rounded-full text-xs font-bold border border-indigo-100">AI Powered</span>
          </div>
          <div className="flex-1 overflow-y-auto pr-2 space-y-4">
            {loading ? (
              <div className="h-full flex flex-col items-center justify-center text-gray-400">
                <Loader2 className="w-12 h-12 animate-spin text-indigo-500 mb-4" />
                <p>Analyzing resumes...</p>
              </div>
            ) : results.length === 0 ? (
              <EmptyState icon={Briefcase} title="Upload resumes to see rankings" subtitle="AI will score and rank candidates automatically" />
            ) : (
              results.map((c, i) => (
                <div key={i} className="group p-4 rounded-xl border border-gray-100 hover:border-indigo-200 hover:shadow-lg transition-all bg-white">
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex gap-4">
                      <div className="w-10 h-10 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold text-lg">{i + 1}</div>
                      <div>
                        <h4 className="font-bold text-gray-900">{c.candidate_name}</h4>
                        <p className="text-xs text-gray-500 font-medium">Experience: {c.experience_years || c.experience} Years</p>
                        {Array.isArray(c.top_roles) && c.top_roles.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {c.top_roles.map((role, idx) => (
                              <span key={idx} className="flex items-center gap-1 text-[10px] text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-100">
                                <Target className="w-3 h-3" /> {role}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                    <ScoreBadge score={c.final_score} />
                  </div>
                  <div className="mt-4 pt-4 border-t border-gray-50">
                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">Technical Skills</p>
                    <div className="flex flex-wrap gap-1.5">
                      {c.resume_skills && c.resume_skills.length > 0 ? (
                        c.resume_skills.slice(0, 12).map((skill, idx) => (
                          <span key={idx} className="px-2.5 py-0.5 text-[10px] font-bold rounded-full bg-purple-50 text-purple-700 border border-purple-100">{skill}</span>
                        ))
                      ) : (
                        <p className="text-[10px] text-gray-400 italic">No technical skills detected</p>
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
