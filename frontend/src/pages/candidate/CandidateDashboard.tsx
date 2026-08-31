import React, { useState, useEffect } from 'react';
import { apiClient } from '../../services/api';
import { Card, Button, EmptyState } from '../../components/ui';
import { 
  FileText, Upload, CheckCircle, Loader2, Target, Briefcase, Sparkles, User, Link, Clipboard,
  Code, Database, Cloud, Wrench, Brain, Users, Layers, ChevronDown, ChevronUp, Award
} from 'lucide-react';
import { Helmet } from 'react-helmet-async';
import { MatchResult, ResumeExtraction } from '../../types';

// Skill category colors and icons
const CATEGORY_CONFIG: Record<string, { color: string; bg: string; border: string; icon: React.ElementType }> = {
  'Languages': { color: 'text-blue-700', bg: 'bg-blue-50', border: 'border-blue-200', icon: Code },
  'Frameworks': { color: 'text-violet-700', bg: 'bg-violet-50', border: 'border-violet-200', icon: Layers },
  'Libraries': { color: 'text-purple-700', bg: 'bg-purple-50', border: 'border-purple-200', icon: Layers },
  'Tools': { color: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200', icon: Wrench },
  'Cloud': { color: 'text-sky-700', bg: 'bg-sky-50', border: 'border-sky-200', icon: Cloud },
  'Cloud Platforms': { color: 'text-sky-700', bg: 'bg-sky-50', border: 'border-sky-200', icon: Cloud },
  'Databases': { color: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200', icon: Database },
  'Concepts': { color: 'text-rose-700', bg: 'bg-rose-50', border: 'border-rose-200', icon: Brain },
  'Soft Skills': { color: 'text-teal-700', bg: 'bg-teal-50', border: 'border-teal-200', icon: Users },
  'Skills': { color: 'text-indigo-700', bg: 'bg-indigo-50', border: 'border-indigo-200', icon: Sparkles },
  'Other': { color: 'text-gray-700', bg: 'bg-gray-50', border: 'border-gray-200', icon: Sparkles },
};

const getCategoryStyle = (category: string) => {
  return CATEGORY_CONFIG[category] || CATEGORY_CONFIG['Other'];
};

export const CandidateDashboard = () => {
  // Main Dashboard States
  const [jd, setJd] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MatchResult | null>(null);

  // Resume Extraction States
  const [extraction, setExtraction] = useState<ResumeExtraction | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  // Onboarding & Profile States
  const [profile, setProfile] = useState<any>(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [submittingOnboarding, setSubmittingOnboarding] = useState(false);
  const [onboardingForm, setOnboardingForm] = useState({
    branch: '',
    graduation_year: '',
    resume_file: null as File | null,
    linkedin: '',
    portfolio: '',
    skills: ''
  });

  // Custom local toast notification handler
  const [toast, setToast] = useState<{ type: 'success' | 'error', msg: string } | null>(null);
  const showToast = (type: 'success' | 'error', msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 4000);
  };

  const fetchProfile = async () => {
    try {
      const res = await apiClient.get('/profile');
      const data = await res.json();
      setProfile(data);
      if (data) {
        setOnboardingForm({
          branch: data.branch || '',
          graduation_year: data.graduation_year ? String(data.graduation_year) : '',
          resume_file: null,
          linkedin: '',
          portfolio: '',
          skills: data.bio && data.bio.startsWith('Skills: ') ? data.bio.replace('Skills: ', '') : ''
        });
      }
    } catch (e) {
      console.error("[PROFILE] Fetch failed:", e);
    } finally {
      setProfileLoading(false);
    }
  };

  // Fetch previously extracted skills on mount
  const fetchExtractedSkills = async () => {
    try {
      const res = await apiClient.get('/resume/skills');
      const data = await res.json();
      if (data && data.extracted_skills && data.extracted_skills.length > 0) {
        setExtraction({
          status: 'success',
          extracted_skills: data.extracted_skills,
          skill_categories: data.skill_categories || {},
          predicted_role: data.predicted_role || 'Unknown',
          top_roles: [data.predicted_role || 'Unknown'],
          experience_years: 0,
          experience: 'Unknown',
          total_skills: data.total_skills || data.extracted_skills.length,
          sections_found: [],
          links: [],
          extraction_quality: 'good',
          word_count: 0,
        });
      }
    } catch {
      // Silently fail — not critical
    }
  };

  useEffect(() => {
    fetchProfile();
    fetchExtractedSkills();
  }, []);

  const toggleCategory = (cat: string) => {
    setExpandedCategories(prev => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat);
      else next.add(cat);
      return next;
    });
  };

  const handleOnboardingSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!onboardingForm.branch || !onboardingForm.graduation_year) {
      showToast('error', 'Please fill in all required fields.');
      return;
    }
    
    // Resume is required to finish onboarding first time
    if (!profile?.resume_path && !onboardingForm.resume_file) {
      showToast('error', 'Please upload your resume to complete onboarding.');
      return;
    }

    setSubmittingOnboarding(true);
    setExtracting(true);
    try {
      let resume_path = profile?.resume_path || "";
      let extractionResult: ResumeExtraction | null = null;
      
      // 1. Upload resume + extract skills using the new unified endpoint
      if (onboardingForm.resume_file) {
        const fd = new FormData();
        fd.append('file', onboardingForm.resume_file);
        
        const upRes = await apiClient.post('/upload_and_extract', fd, true);
        const upData = await upRes.json();
        
        if (upData.status === 'error' && !upData.filename) {
          throw new Error(upData.message || "Resume upload failed");
        }
        
        resume_path = upData.filename;
        extractionResult = upData as ResumeExtraction;
        setExtraction(extractionResult);
      }

      // 2. Save complete profile details
      const response = await apiClient.put('/profile', {
        email: profile.email,
        username: profile.username,
        role: profile.role,
        branch: onboardingForm.branch,
        graduation_year: parseInt(onboardingForm.graduation_year) || undefined,
        resume_path: resume_path,
        bio: onboardingForm.skills ? `Skills: ${onboardingForm.skills}` : profile.bio
      });

      const data = await response.json();
      if (response.ok && data.success) {
        const skillCount = extractionResult?.total_skills || 0;
        showToast('success', skillCount > 0 
          ? `Profile completed! ${skillCount} skills extracted from your resume.`
          : 'Profile completed! Welcome to your Dashboard.'
        );
        fetchProfile();
      } else {
        showToast('error', data.message || 'Failed to update profile details.');
      }
    } catch (err: any) {
      showToast('error', err.message || 'Onboarding submission failed.');
    } finally {
      setSubmittingOnboarding(false);
      setExtracting(false);
    }
  };

  const handleAnalyze = async () => {
    if (!jd || !file) { 
      showToast('error', 'Please provide both Job Description and Resume'); 
      return; 
    }
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      
      // Use upload_and_extract to get skills immediately
      const upRes = await apiClient.post('/upload_and_extract', fd, true);
      const upData = await upRes.json();
      if (!upData.filename) throw new Error(upData.message || "Upload failed");

      // Set extraction result immediately for skill display
      if (upData.status === 'success' || upData.extracted_skills) {
        setExtraction(upData as ResumeExtraction);
      }

      const matchRes = await apiClient.post('/candidate/match', { 
        filename: upData.filename, 
        job_description: jd 
      });
      const data = await matchRes.json();
      
      // Sanitize result
      const sanitized: MatchResult = {
        final_score: typeof data.final_score === 'number' && !isNaN(data.final_score) ? data.final_score : 0,
        match_percentage: typeof data.match_percentage === 'number' && !isNaN(data.match_percentage) ? data.match_percentage : 0,
        predicted_role: data.predicted_role || 'Unknown',
        resume_skills: Array.isArray(data.resume_skills) ? data.resume_skills : [],
        matched_skills: Array.isArray(data.matched_skills) ? data.matched_skills : [],
        missing_skills: Array.isArray(data.missing_skills) ? data.missing_skills : [],
        all_skills: Array.isArray(data.all_skills) ? data.all_skills : [],
        summary_reasoning: data.summary_reasoning || 'Analysis complete.',
        experience: data.experience || 'Unknown',
        experience_years: data.experience_years || 0,
        total_skills: data.total_skills || 0,
        top_roles: Array.isArray(data.top_roles) ? data.top_roles : [data.predicted_role || 'Unknown'],
      };
      
      setResult(sanitized);
      showToast('success', 'Analysis complete!');
    } catch (e: any) {
      showToast('error', "Error analyzing: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  // Check if candidate needs onboarding
  const needsOnboarding = profile && (!profile.branch || !profile.graduation_year || !profile.resume_path);

  if (profileLoading) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-indigo-600" />
      </div>
    );
  }

  // ============================================
  // Render Onboarding Step
  // ============================================
  if (needsOnboarding) {
    return (
      <div className="max-w-2xl mx-auto py-8 px-4 page-enter">
        <Helmet>
          <title>Complete Profile | FlowATS</title>
        </Helmet>
        
        {toast && (
          <div className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg text-white font-medium ${toast.type === 'success' ? 'bg-emerald-500' : 'bg-red-500'}`}>
            <span>{toast.msg}</span>
          </div>
        )}

        <div className="text-center mb-8 space-y-2">
          <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center mx-auto shadow-sm">
            <User className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900">Complete Professional Profile</h2>
          <p className="text-gray-500 text-sm max-w-md mx-auto">
            Tell us about your background to unlock AI-powered match analysis and instant interview feedback.
          </p>
        </div>

        <Card className="p-6 sm:p-8">
          <form onSubmit={handleOnboardingSubmit} className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              
              {/* Branch / Dept */}
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">
                  Branch / Department <span className="text-red-500">*</span>
                </label>
                <input
                  required
                  className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none text-sm transition-all"
                  placeholder="e.g. Computer Science"
                  value={onboardingForm.branch}
                  onChange={e => setOnboardingForm({ ...onboardingForm, branch: e.target.value })}
                />
              </div>

              {/* Graduation Year */}
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">
                  Graduation Year <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  required
                  min="2000"
                  max="2035"
                  className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none text-sm transition-all"
                  placeholder="e.g. 2026"
                  value={onboardingForm.graduation_year}
                  onChange={e => setOnboardingForm({ ...onboardingForm, graduation_year: e.target.value })}
                />
              </div>
            </div>

            {/* Optional Skills tags input */}
            <div>
              <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5 flex justify-between">
                <span>Key Technical Skills</span>
                <span className="text-gray-400 capitalize normal-case font-normal">(Optional)</span>
              </label>
              <div className="relative">
                <Clipboard className="w-4 h-4 text-gray-400 absolute left-3.5 top-3.5" />
                <input
                  className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none text-sm transition-all"
                  placeholder="e.g. React, Node.js, Python (comma-separated)"
                  value={onboardingForm.skills}
                  onChange={e => setOnboardingForm({ ...onboardingForm, skills: e.target.value })}
                />
              </div>
            </div>

            {/* Optional Links */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">LinkedIn Profile Link</label>
                <div className="relative">
                  <Link className="w-4 h-4 text-gray-400 absolute left-3.5 top-3.5" />
                  <input
                    type="url"
                    className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none text-sm transition-all"
                    placeholder="https://linkedin.com/in/..."
                    value={onboardingForm.linkedin}
                    onChange={e => setOnboardingForm({ ...onboardingForm, linkedin: e.target.value })}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Portfolio URL</label>
                <div className="relative">
                  <Link className="w-4 h-4 text-gray-400 absolute left-3.5 top-3.5" />
                  <input
                    type="url"
                    className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none text-sm transition-all"
                    placeholder="https://yourportfolio.com"
                    value={onboardingForm.portfolio}
                    onChange={e => setOnboardingForm({ ...onboardingForm, portfolio: e.target.value })}
                  />
                </div>
              </div>
            </div>

            {/* Resume Upload (Required for onboarding completion) */}
            <div>
              <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">
                Upload Resume (PDF/DOCX/TXT) <span className="text-red-500">*</span>
              </label>
              <div className="border-2 border-dashed border-gray-300 rounded-xl p-6 text-center hover:bg-indigo-50/50 hover:border-indigo-400 transition-colors relative cursor-pointer">
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                  onChange={e => e.target.files && setOnboardingForm({ ...onboardingForm, resume_file: e.target.files[0] })}
                />
                {onboardingForm.resume_file ? (
                  <div className="text-emerald-600 font-semibold flex items-center justify-center gap-2">
                    <CheckCircle className="w-5 h-5 animate-bounce" /> {onboardingForm.resume_file.name}
                  </div>
                ) : (
                  <div className="text-gray-500">
                    <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                    <span className="text-xs font-semibold">Click or drag resume file to upload</span>
                  </div>
                )}
              </div>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={submittingOnboarding}
              className="w-full py-3.5 text-base font-bold shadow-lg"
            >
              {submittingOnboarding ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  {extracting ? 'Extracting Skills...' : 'Saving...'}
                </span>
              ) : (
                <><Sparkles className="w-4 h-4 mr-2" /> Save & Extract Skills</>
              )}
            </Button>
          </form>
        </Card>

        {/* Show extraction results during onboarding */}
        {extraction && extraction.extracted_skills.length > 0 && (
          <Card className="mt-6 p-6 animate-in fade-in duration-500">
            <SkillExtractionDisplay extraction={extraction} expandedCategories={expandedCategories} toggleCategory={toggleCategory} />
          </Card>
        )}
      </div>
    );
  }

  // ============================================
  // Render Dashboard content (if onboarding complete)
  // ============================================
  const score = result ? Math.round((result.final_score || 0) * 100) : 0;
  const strokeDash = `${score}, 100`;
  const strokeColor = score > 70 ? '#10b981' : score > 40 ? '#f59e0b' : '#ef4444';

  return (
    <div className="space-y-8 max-w-5xl mx-auto page-enter">
      <Helmet>
        <title>Career Analysis | FlowATS</title>
        <meta name="description" content="Analyze resumes and get AI-powered career recommendations." />
      </Helmet>
      
      {toast && (
        <div className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg text-white font-medium ${toast.type === 'success' ? 'bg-emerald-500' : 'bg-red-500'}`}>
          <span>{toast.msg}</span>
        </div>
      )}

      {/* Resume Intelligence Card — Always visible if skills exist */}
      {extraction && extraction.extracted_skills.length > 0 && (
        <Card className="p-6 animate-in fade-in duration-500">
          <SkillExtractionDisplay extraction={extraction} expandedCategories={expandedCategories} toggleCategory={toggleCategory} />
        </Card>
      )}

      <div className="grid lg:grid-cols-2 gap-8">
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Career Analysis</h2>
            <p className="text-gray-500">Upload job details for an instant AI evaluation against your profile.</p>
          </div>
          <Card className="p-6">
            <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5 text-indigo-600" /> Job Details
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Job Description</label>
                <textarea 
                  className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none h-32 text-sm resize-none" 
                  placeholder="Paste Job Description here..." 
                  value={jd} 
                  onChange={e => setJd(e.target.value)} 
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-2">Resume for Match Screen</label>
                <div className="border-2 border-dashed border-gray-300 rounded-xl p-6 text-center hover:bg-indigo-50 hover:border-indigo-400 transition-colors relative">
                  <input 
                    type="file" 
                    className="absolute inset-0 opacity-0 cursor-pointer w-full h-full" 
                    onChange={e => e.target.files && setFile(e.target.files[0])} 
                  />
                  {file ? (
                    <div className="text-emerald-600 font-medium flex items-center justify-center gap-2">
                      <CheckCircle className="w-5 h-5" /> {file.name}
                    </div>
                  ) : (
                    <div className="text-gray-500 text-xs">
                      <Upload className="w-6 h-6 mx-auto mb-2 text-gray-400" />
                      <span>Upload a specific resume (defaults to your base onboarding resume if left blank)</span>
                    </div>
                  )}
                </div>
              </div>
              <Button onClick={handleAnalyze} disabled={loading} className="w-full py-3">
                {loading ? <Loader2 className="animate-spin mx-auto" /> : "Analyze Match Score"}
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
                    <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke={strokeColor} strokeWidth="3" strokeDasharray={strokeDash} className="score-ring-animated" />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center flex-col">
                    <span className="text-4xl font-black text-gray-900">{score}%</span>
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Match</span>
                  </div>
                </div>

                {Array.isArray(result.top_roles) && result.top_roles.length > 0 && (
                  <div className="mb-6 w-full max-w-sm mx-auto">
                    <p className="text-xs font-bold text-gray-400 uppercase mb-3 text-center">Top Career Matches</p>
                    <div className="flex flex-col gap-2">
                      {result.top_roles.map((role, index) => (
                        <div key={index} className="flex items-center justify-between p-2.5 bg-indigo-50 rounded-lg border border-indigo-100">
                          <span className="flex items-center gap-2 text-sm font-semibold text-indigo-900">
                            <Target className="w-4 h-4 text-indigo-500" /> {role}
                          </span>
                          <span className="text-xs font-bold text-indigo-400">#{index + 1}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="bg-gray-50 rounded-xl p-4 mb-6 inline-flex items-center gap-3 border border-gray-100">
                  <div className="bg-indigo-100 p-2 rounded-lg text-indigo-600">
                    <Briefcase className="w-4 h-4" />
                  </div>
                  <div className="text-left">
                    <p className="text-xs text-gray-500 font-bold uppercase">Experience</p>
                    <p className="font-bold text-gray-900">{result.experience_years || result.experience} Years</p>
                  </div>
                </div>

                {/* Matched vs Missing Skills */}
                {result.matched_skills && result.matched_skills.length > 0 && (
                  <div className="w-full text-left mt-4 pt-4 border-t border-gray-100">
                    <h3 className="text-sm font-bold text-emerald-700 flex items-center gap-2 mb-3">
                      <CheckCircle className="w-4 h-4" /> Matched Skills ({result.matched_skills.length})
                    </h3>
                    <div className="flex flex-wrap gap-1.5 mb-4">
                      {result.matched_skills.map(s => (
                        <span key={s} className="px-2.5 py-1 bg-emerald-50 text-emerald-700 rounded-lg text-xs font-semibold border border-emerald-200">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {result.missing_skills && result.missing_skills.length > 0 && (
                  <div className="w-full text-left mt-2">
                    <h3 className="text-sm font-bold text-amber-700 flex items-center gap-2 mb-3">
                      <Target className="w-4 h-4" /> Skills to Develop ({result.missing_skills.length})
                    </h3>
                    <div className="flex flex-wrap gap-1.5">
                      {result.missing_skills.map(s => (
                        <span key={s} className="px-2.5 py-1 bg-amber-50 text-amber-700 rounded-lg text-xs font-semibold border border-amber-200">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="w-full text-left mt-6 pt-6 border-t border-gray-100">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-indigo-500" /> All Detected Skills
                    </h3>
                    <span className="text-[10px] font-black bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full uppercase">
                      {result.total_skills || 0} Found
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {result.resume_skills && result.resume_skills.length > 0 ? (
                      result.resume_skills.map(s => (
                        <span key={s} className="px-3 py-1 bg-white text-gray-700 rounded-lg text-sm font-medium border border-gray-200 shadow-sm hover:border-indigo-300 transition-colors">
                          {s}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-gray-400 italic">No specific skills found</span>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <EmptyState icon={Sparkles} title="AI Analysis Results" subtitle="Provide the Job details above to screen your match score" />
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};


// ============================================
// Skill Extraction Display Component
// ============================================
const SkillExtractionDisplay = ({
  extraction,
  expandedCategories,
  toggleCategory
}: {
  extraction: ResumeExtraction;
  expandedCategories: Set<string>;
  toggleCategory: (cat: string) => void;
}) => {
  const categories = extraction.skill_categories || {};
  const categoryNames = Object.keys(categories);

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <h3 className="font-bold text-gray-900 flex items-center gap-2">
          <Award className="w-5 h-5 text-indigo-600" /> Resume Intelligence
        </h3>
        <div className="flex items-center gap-3">
          {extraction.predicted_role && extraction.predicted_role !== 'Unknown' && (
            <span className="text-xs font-bold bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full">
              {extraction.predicted_role}
            </span>
          )}
          <span className="text-xs font-black bg-emerald-100 text-emerald-700 px-3 py-1 rounded-full">
            {extraction.total_skills} Skills Detected
          </span>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
        <div className="bg-indigo-50 rounded-xl p-3 text-center border border-indigo-100">
          <p className="text-2xl font-black text-indigo-700">{extraction.total_skills}</p>
          <p className="text-[10px] font-bold text-indigo-500 uppercase">Total Skills</p>
        </div>
        <div className="bg-violet-50 rounded-xl p-3 text-center border border-violet-100">
          <p className="text-2xl font-black text-violet-700">{categoryNames.length}</p>
          <p className="text-[10px] font-bold text-violet-500 uppercase">Categories</p>
        </div>
        <div className="bg-emerald-50 rounded-xl p-3 text-center border border-emerald-100">
          <p className="text-2xl font-black text-emerald-700">{extraction.experience_years || 0}</p>
          <p className="text-[10px] font-bold text-emerald-500 uppercase">Years Exp</p>
        </div>
        <div className="bg-amber-50 rounded-xl p-3 text-center border border-amber-100">
          <p className="text-2xl font-black text-amber-700 capitalize">{extraction.extraction_quality}</p>
          <p className="text-[10px] font-bold text-amber-500 uppercase">Quality</p>
        </div>
      </div>

      {/* Categorized Skills */}
      {categoryNames.length > 0 ? (
        <div className="space-y-2">
          {categoryNames.map(cat => {
            const style = getCategoryStyle(cat);
            const Icon = style.icon;
            const skills = categories[cat];
            const isExpanded = expandedCategories.has(cat);
            const displaySkills = isExpanded ? skills : skills.slice(0, 8);
            const hasMore = skills.length > 8;

            return (
              <div key={cat} className={`rounded-xl border ${style.border} overflow-hidden`}>
                <button
                  type="button"
                  onClick={() => hasMore && toggleCategory(cat)}
                  className={`w-full flex items-center justify-between px-4 py-2.5 ${style.bg} cursor-pointer`}
                >
                  <span className={`flex items-center gap-2 text-sm font-bold ${style.color}`}>
                    <Icon className="w-4 h-4" /> {cat}
                    <span className="text-xs font-normal opacity-70">({skills.length})</span>
                  </span>
                  {hasMore && (
                    isExpanded 
                      ? <ChevronUp className={`w-4 h-4 ${style.color}`} />
                      : <ChevronDown className={`w-4 h-4 ${style.color}`} />
                  )}
                </button>
                <div className="px-4 py-3 flex flex-wrap gap-1.5">
                  {displaySkills.map(skill => (
                    <span
                      key={skill}
                      className={`px-2.5 py-1 ${style.bg} ${style.color} rounded-lg text-xs font-semibold border ${style.border} hover:shadow-sm transition-shadow`}
                    >
                      {skill}
                    </span>
                  ))}
                  {!isExpanded && hasMore && (
                    <span className={`px-2.5 py-1 ${style.color} text-xs font-bold opacity-60`}>
                      +{skills.length - 8} more
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* Flat list fallback */
        <div className="flex flex-wrap gap-2">
          {extraction.extracted_skills.map(s => (
            <span key={s} className="px-3 py-1 bg-white text-gray-700 rounded-lg text-sm font-medium border border-gray-200 shadow-sm">
              {s}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
