import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Sparkles,
  Upload,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Briefcase,
  Target,
  FileCheck,
  Check,
  Layers,
  Award,
  AlertCircle,
  HelpCircle,
  Info,
  ChevronRight,
  TrendingUp,
} from 'lucide-react';
import { resumesApi } from '../api/resumes';
import { matchingApi } from '../api/matching';
import { jobsApi } from '../api/jobs';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';
import { Resume, MatchResult, Job, ResumeQualityAnalysis, JobSuggestion } from '../types';

export const CareerAnalysis: React.FC = () => {
  const routerLocation = useLocation();
  const preselectedJobId = (routerLocation.state as any)?.preselectedJobId;

  const [resumes, setResumes] = useState<Resume[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<string>('');
  const [jobDescription, setJobDescription] = useState<string>('');

  const [isUploading, setIsUploading] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evalResult, setEvalResult] = useState<MatchResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [resumesList, jobsList] = await Promise.all([
        resumesApi.getMyResumes().catch(() => []),
        jobsApi.getJobs().catch(() => []),
      ]);
      setResumes(resumesList);

      if (resumesList.length > 0) {
        setSelectedResumeId(resumesList[0].id);
      }

      // If user navigated from a live job in Job Feed
      if (preselectedJobId && jobsList.length > 0) {
        const found = jobsList.find((j: Job) => j.id === preselectedJobId);
        if (found) {
          setJobDescription(found.description || '');
        }
      }
    } catch (e: any) {
      console.error('Failed to load initial data:', e);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setError(null);
    try {
      const uploaded = await resumesApi.upload(file);
      setResumes((prev) => [uploaded, ...prev]);
      setSelectedResumeId(uploaded.id);
    } catch (err: any) {
      setError(err.message || 'Failed to upload resume. Please check the file format.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleRunEvaluation = async () => {
    setError(null);
    const resume = resumes.find((r) => r.id === selectedResumeId);
    if (!resume) {
      setError('Please select or upload an active resume first.');
      return;
    }

    setIsEvaluating(true);
    try {
      const result = await matchingApi.evaluate({
        resume_id: resume.id,
        resume_text: resume.raw_text || '',
        job_description: jobDescription.trim(),
      });
      setEvalResult(result);
    } catch (err: any) {
      setError(err.message || 'Analysis failed. Please check the resume or server connection.');
    } finally {
      setIsEvaluating(false);
    }
  };

  const activeResume = resumes.find((r) => r.id === selectedResumeId);

  // Quality data resolution strictly from evaluation result (or active resume metadata)
  const quality: ResumeQualityAnalysis | undefined =
    evalResult?.resume_quality ||
    activeResume?.quality_analysis ||
    activeResume?.health_analysis?.quality_analysis;

  // Job Match details resolution
  const jobMatch = evalResult?.job_match;
  const hasSufficientJd =
    evalResult?.has_sufficient_jd === true &&
    jobMatch?.has_sufficient_jd === true &&
    jobMatch?.overall !== null &&
    jobMatch?.overall !== undefined;

  // Granular subscores resolution - strict values, zero optimistic defaults
  const subscores = quality?.subscores || {
    ats_readability: 0,
    formatting_layout: 0,
    section_structure: 0,
    bullet_quality: 0,
    grammar_spelling: 0,
    typography: 0,
    consistency: 0,
    contact_information: 0,
  };

  const subscoreItems = [
    { label: 'ATS Readability', val: subscores.ats_readability ?? 0 },
    { label: 'Formatting & Layout', val: subscores.formatting_layout ?? subscores.layout ?? 0 },
    { label: 'Section Structure', val: subscores.section_structure ?? subscores.structure ?? 0 },
    { label: 'Bullet Quality', val: subscores.bullet_quality ?? 0 },
    { label: 'Grammar & Spelling', val: subscores.grammar_spelling ?? 0 },
    { label: 'Typography', val: subscores.typography ?? 0 },
    { label: 'Consistency', val: subscores.consistency ?? 0 },
    { label: 'Contact Info', val: subscores.contact_information ?? 0 },
  ];

  const overallScoreVal = evalResult?.overall_score ?? (quality?.formatting_score ?? null);

  const jobSuggestions: JobSuggestion[] = evalResult?.job_suggestions || [];

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-2 mb-1.5">
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 uppercase tracking-wider">
            TalentFlow ATS Intelligence
          </span>
        </div>
        <h1 className="text-3xl font-black tracking-tight text-gray-900">Career & Resume Analysis</h1>
        <p className="text-sm text-gray-500 mt-1 max-w-3xl">
          Evaluate resume formatting quality, discover strong job suggestions directly from your skills, and inspect match compatibility against employer job descriptions.
        </p>
      </div>

      {error && (
        <Alert type="error" title="Analysis Notice">
          {error}
        </Alert>
      )}

      {/* INPUTS SECTION: Resume Selection & Job Description */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Active Resume & Quick Upload */}
        <div className="space-y-4">
          <Card padding="lg" className="border-t-4 border-t-emerald-600">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-base font-bold text-gray-900">Select Active Resume</h3>
              <span className="text-xs text-gray-500 font-semibold">{resumes.length} available</span>
            </div>

            {resumes.length === 0 ? (
              <div className="py-6 text-center bg-gray-50 rounded-2xl border border-gray-100">
                <FileText className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                <p className="text-sm font-semibold text-gray-600">No resumes uploaded</p>
                <p className="text-xs text-gray-400 mt-0.5">Upload a PDF or DOCX file to begin.</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                {resumes.map((r) => {
                  const isSelected = selectedResumeId === r.id;
                  const formatScore = r.health_analysis?.formatting_score ?? r.ats_score;
                  return (
                    <div
                      key={r.id}
                      onClick={() => setSelectedResumeId(r.id)}
                      className={`p-3 rounded-xl border flex items-center justify-between transition-all cursor-pointer ${
                        isSelected
                          ? 'border-emerald-500 bg-emerald-50/50 ring-2 ring-emerald-100'
                          : 'border-gray-200 hover:border-gray-300 bg-white'
                      }`}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <FileText className={`w-5 h-5 flex-shrink-0 ${isSelected ? 'text-emerald-600' : 'text-gray-400'}`} />
                        <div className="truncate">
                          <p className="text-sm font-bold text-gray-900 truncate">{r.original_filename}</p>
                          <p className="text-xs text-gray-500">
                            v{r.version} • {r.extracted_skills?.length || 0} skills
                            {formatScore !== undefined && formatScore > 0 ? ` • ${Math.round(formatScore)}/100` : ''}
                          </p>
                        </div>
                      </div>
                      <Badge variant={isSelected ? 'success' : 'secondary'}>
                        {isSelected ? 'Active' : `v${r.version}`}
                      </Badge>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Quick Upload Action */}
            <div className="mt-4 pt-3 border-t border-gray-100">
              <label className="block w-full">
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full justify-center text-xs"
                  isLoading={isUploading}
                  leftIcon={<Upload className="w-3.5 h-3.5 text-emerald-600" />}
                  onClick={() => document.getElementById('resume-file-input')?.click()}
                >
                  Upload New Version
                </Button>
                <input
                  id="resume-file-input"
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>
            </div>
          </Card>
        </div>

        {/* Right 2 Columns: Job Description Input & Analyze Button */}
        <div className="lg:col-span-2">
          <Card padding="lg" className="h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <div>
                  <h3 className="text-base font-bold text-gray-900">Job Description</h3>
                  <p className="text-xs text-gray-500">
                    Paste an employer job description to calculate detailed Job Match compatibility.
                  </p>
                </div>
                {jobDescription && (
                  <button
                    onClick={() => setJobDescription('')}
                    className="text-xs text-gray-400 hover:text-gray-600 font-medium"
                  >
                    Clear text
                  </button>
                )}
              </div>

              <textarea
                rows={7}
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste complete job description here (responsibilities, qualifications, required skills, tools, and experience)..."
                className="block w-full rounded-xl border border-gray-200 p-3.5 text-sm text-gray-900 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 focus:outline-none transition-all placeholder:text-gray-400 font-sans"
              />

              <div className="flex items-center justify-between mt-2 text-[11px] text-gray-400 font-medium">
                <span>
                  {jobDescription.trim().split(/\s+/).filter(Boolean).length} words • {jobDescription.length} characters
                </span>
                <span>Job Description optional for resume suggestions & formatting analysis</span>
              </div>
            </div>

            <div className="mt-5 pt-3 border-t border-gray-100 flex items-center justify-end">
              <Button
                variant="emerald"
                size="lg"
                isLoading={isEvaluating}
                onClick={handleRunEvaluation}
                leftIcon={<Sparkles className="w-5 h-5" />}
                className="font-bold px-6 shadow-md shadow-emerald-200"
              >
                Analyze Resume
              </Button>
            </div>
          </Card>
        </div>
      </div>

      {/* PROMPT STATE: When user has not clicked Analyze Resume yet */}
      {!evalResult && (
        <Card padding="lg" className="border-dashed border-2 border-gray-200 bg-gray-50/50 text-center py-12">
          <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto mb-3 shadow-xs">
            <Sparkles className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-gray-900">Ready to Analyze</h3>
          <p className="text-xs text-gray-500 max-w-md mx-auto mt-1 mb-4">
            Select an active resume and optionally paste an employer job description, then click <strong>Analyze Resume</strong> to inspect formatting quality, ATS compliance, role suggestions, and match scores.
          </p>
        </Card>
      )}

      {/* RESULTS SECTION: Shown ONLY when analysis has been executed */}
      {evalResult && (
        <div className="space-y-8 pt-2">
          {/* Extraction Error Notice if text was unreadable */}
          {evalResult.resume_text_available === false && (
            <Alert type="error" title="Extraction Notice">
              {evalResult.error || 'Resume text could not be extracted or is empty. Please upload a valid readable PDF, DOCX, or text file.'}
            </Alert>
          )}

          {/* ========================================================================= */}
          {/* RESULT 5: OVERALL RESUME SCORE BANNER                                     */}
          {/* ========================================================================= */}
          <div className="rounded-3xl bg-gradient-to-r from-emerald-900 via-teal-900 to-slate-900 text-white p-6 sm:p-8 shadow-xl shadow-emerald-950/20 border border-emerald-800/40">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div className="space-y-2 max-w-2xl">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-400/30 text-emerald-300 text-xs font-bold uppercase tracking-wider">
                  <Award className="w-3.5 h-3.5 text-emerald-400" />
                  Overall ATS Compatibility Score
                </div>
                <h2 className="text-3xl sm:text-4xl font-black tracking-tight text-white">
                  Score: {overallScoreVal !== null ? overallScoreVal : '—'} <span className="text-2xl text-emerald-300 font-bold">/ 100</span>
                </h2>
                <p className="text-sm text-emerald-100/90 font-mono bg-emerald-950/60 px-3.5 py-2 rounded-xl border border-emerald-700/30 inline-block">
                  {evalResult.formula_breakdown ||
                    (hasSufficientJd && jobMatch?.overall !== null && jobMatch?.overall !== undefined
                      ? `Formula: (Job Match: ${jobMatch.overall} × 70%) + (Resume Quality: ${quality?.formatting_score || 0} × 30%) = ${overallScoreVal}`
                      : `Overall Score: ${overallScoreVal ?? 0} / 100 based on Resume Quality (Paste a Job Description above to compute weighted Job Match).`)}
                </p>
              </div>

              {/* Badges / Metrics cluster */}
              <div className="flex flex-wrap md:flex-col items-start md:items-end gap-2.5">
                <span className="px-3.5 py-1.5 rounded-xl bg-white/10 backdrop-blur-md text-xs font-semibold text-white border border-white/10">
                  Document: {quality?.document_type?.toUpperCase() || 'PDF'} ({quality?.page_count || 1} {quality?.page_count === 1 ? 'Page' : 'Pages'})
                </span>
                <span className="px-3.5 py-1.5 rounded-xl bg-white/10 backdrop-blur-md text-xs font-semibold text-white border border-white/10">
                  Total Words: {quality?.word_count ?? 0}
                </span>
                <span className={`px-3.5 py-1.5 rounded-xl text-xs font-bold border ${
                  quality?.is_ats_friendly
                    ? 'bg-emerald-500/20 border-emerald-400 text-emerald-200'
                    : 'bg-amber-500/20 border-amber-400 text-amber-200'
                }`}>
                  {quality?.is_ats_friendly ? '✓ ATS Parser Friendly' : '⚠ Formatting Improvements Needed'}
                </span>
              </div>
            </div>
          </div>

          {/* ========================================================================= */}
          {/* RESULT 1: JOB SUGGESTIONS FROM RESUME ALONE                                */}
          {/* ========================================================================= */}
          <Card padding="lg" className="border-t-4 border-t-teal-600">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-3 border-b border-gray-100">
              <div>
                <div className="flex items-center gap-2">
                  <Briefcase className="w-5 h-5 text-teal-600" />
                  <h3 className="text-lg font-black text-gray-900">Top Job Suggestions</h3>
                </div>
                <p className="text-xs text-gray-500 mt-0.5">
                  High-alignment career roles identified directly from your resume's technical skills, experience, and projects.
                </p>
              </div>
              <span className="text-xs font-bold text-teal-700 bg-teal-50 px-3 py-1 rounded-full border border-teal-200 self-start sm:self-auto">
                Independent of Job Description
              </span>
            </div>

            {jobSuggestions.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {jobSuggestions.map((sug, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-2xl bg-gradient-to-b from-gray-50 to-white border border-gray-200 hover:border-teal-300 hover:shadow-sm transition-all"
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <h4 className="text-sm font-black text-gray-900 leading-tight">{sug.role}</h4>
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-black bg-teal-100 text-teal-800 flex-shrink-0">
                        {sug.score}% Fit
                      </span>
                    </div>

                    <div className="w-full bg-gray-100 h-1.5 rounded-full overflow-hidden mb-3">
                      <div
                        className="h-full bg-teal-600 rounded-full"
                        style={{ width: `${sug.score}%` }}
                      />
                    </div>

                    {sug.matching_skills && sug.matching_skills.length > 0 && (
                      <div className="space-y-1">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                          Matching Skills
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {sug.matching_skills.map((skill, skIdx) => (
                            <span
                              key={skIdx}
                              className="text-[11px] font-medium bg-white text-gray-700 px-2 py-0.5 rounded-md border border-gray-200"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-6 text-center bg-gray-50 rounded-xl text-xs text-gray-400">
                Run analysis to view top job suggestions tailored to your resume skills.
              </div>
            )}
          </Card>

          {/* ========================================================================= */}
          {/* RESULT 2: JOB MATCH (RESUME ↔ JOB DESCRIPTION)                            */}
          {/* ========================================================================= */}
          <Card padding="lg" className="border-t-4 border-t-emerald-600">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5 pb-3 border-b border-gray-100">
              <div>
                <div className="flex items-center gap-2">
                  <Target className="w-5 h-5 text-emerald-600" />
                  <h3 className="text-lg font-black text-gray-900">Job Description Match Analysis</h3>
                </div>
                <p className="text-xs text-gray-500 mt-0.5">
                  Multi-dimensional alignment between your resume and the supplied employer job description.
                </p>
              </div>

              {hasSufficientJd && jobMatch?.overall !== null && jobMatch?.overall !== undefined && (
                <div className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-900 text-xs font-black border border-emerald-200 self-start sm:self-auto">
                  Job Match: {jobMatch.overall}%
                </div>
              )}
            </div>

            {hasSufficientJd ? (
              <div className="space-y-6">
                {/* 5-Dimension Component Breakdown Cards */}
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                  <div className="p-3.5 rounded-2xl bg-gray-50 border border-gray-100 text-center">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500">
                      Semantic Context
                    </span>
                    <p className="text-xl font-black text-gray-900 mt-1">
                      {jobMatch?.semantic !== null && jobMatch?.semantic !== undefined ? `${jobMatch.semantic}%` : 'N/A'}
                    </p>
                  </div>

                  <div className="p-3.5 rounded-2xl bg-gray-50 border border-gray-100 text-center">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500">
                      Skill Overlap
                    </span>
                    <p className="text-xl font-black text-gray-900 mt-1">
                      {jobMatch?.skills !== null && jobMatch?.skills !== undefined ? `${jobMatch.skills}%` : 'N/A'}
                    </p>
                  </div>

                  <div className="p-3.5 rounded-2xl bg-gray-50 border border-gray-100 text-center">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500">
                      Experience Fit
                    </span>
                    <p className="text-xl font-black text-gray-900 mt-1">
                      {jobMatch?.experience !== null && jobMatch?.experience !== undefined ? `${jobMatch.experience}%` : 'N/A'}
                    </p>
                  </div>

                  <div className="p-3.5 rounded-2xl bg-gray-50 border border-gray-100 text-center">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500">
                      Education Credentials
                    </span>
                    <p className="text-xl font-black text-gray-900 mt-1">
                      {jobMatch?.education !== null && jobMatch?.education !== undefined ? `${jobMatch.education}%` : 'N/A'}
                    </p>
                  </div>

                  <div className="p-3.5 rounded-2xl bg-gray-50 border border-gray-100 text-center col-span-2 sm:col-span-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500">
                      Responsibilities
                    </span>
                    <p className="text-xl font-black text-gray-900 mt-1">
                      {jobMatch?.responsibility !== null && jobMatch?.responsibility !== undefined ? `${jobMatch.responsibility}%` : 'N/A'}
                    </p>
                  </div>
                </div>

                {/* Matched vs Missing Skills */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Matched Skills */}
                  <div className="p-4 bg-emerald-50/40 rounded-2xl border border-emerald-100">
                    <div className="flex items-center gap-2 mb-2 text-emerald-900">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                      <h4 className="text-xs font-bold uppercase tracking-wider">
                        Matched Skills ({evalResult.matched_skills?.length || 0})
                      </h4>
                    </div>
                    {evalResult.matched_skills && evalResult.matched_skills.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {evalResult.matched_skills.map((s, i) => (
                          <span
                            key={i}
                            className="text-xs font-semibold bg-white border border-emerald-200 text-emerald-800 px-2.5 py-1 rounded-lg shadow-2xs"
                          >
                            ✓ {s}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-400 bg-white p-3 rounded-xl">
                        No direct keyword overlap found for this job description.
                      </p>
                    )}
                  </div>

                  {/* Missing Skills */}
                  <div className="p-4 bg-amber-50/40 rounded-2xl border border-amber-100">
                    <div className="flex items-center gap-2 mb-2 text-amber-900">
                      <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                      <h4 className="text-xs font-bold uppercase tracking-wider">
                        Missing Skills to Address ({evalResult.missing_skills?.length || 0})
                      </h4>
                    </div>
                    {evalResult.missing_skills && evalResult.missing_skills.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {evalResult.missing_skills.map((s, i) => (
                          <span
                            key={i}
                            className="text-xs font-semibold bg-white border border-amber-200 text-amber-800 px-2.5 py-1 rounded-lg shadow-2xs"
                          >
                            + {s}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-emerald-800 font-semibold bg-white p-3 rounded-xl border border-emerald-100">
                        Excellent: All explicit skills from this job description are mentioned in your resume!
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              /* Insufficient JD Alert - Clean, transparent handling */
              <div className="p-5 rounded-2xl bg-amber-50/80 border border-amber-200 flex items-start gap-3.5">
                <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-amber-950">
                    Insufficient Job Description
                  </h4>
                  <p className="text-xs text-amber-800 leading-relaxed">
                    {jobMatch?.reason || jobMatch?.message || 'Please provide a complete job description containing responsibilities, required skills, qualifications, and experience requirements to calculate a reliable Job Match score.'}
                  </p>
                  <p className="text-[11px] text-amber-700/80 font-medium pt-1">
                    Your Overall Score is currently calculated from your comprehensive Resume Formatting & Quality analysis.
                  </p>
                </div>
              </div>
            )}
          </Card>

          {/* ========================================================================= */}
          {/* RESULT 3: RESUME QUALITY & ATS COMPLIANCE                                 */}
          {/* ========================================================================= */}
          {quality && (
            <Card padding="lg" className="border-t-4 border-t-indigo-600">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-gray-100">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-2xl bg-indigo-100 text-indigo-700 flex items-center justify-center font-black">
                    <FileCheck className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-lg font-black text-gray-900">
                      Resume Quality & ATS Document Compliance
                    </h3>
                    <p className="text-xs text-gray-500">
                      Deep deterministic document inspection across 8 core dimensions of recruiter and parser readability.
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-start sm:self-auto">
                  <Badge variant={quality.is_ats_friendly ? 'success' : 'warning'}>
                    {quality.is_ats_friendly ? '✓ ATS Parser Friendly' : '⚠ Needs Formatting Optimization'}
                  </Badge>
                  <span className="px-3.5 py-1 bg-indigo-50 text-indigo-800 text-xs font-black rounded-full border border-indigo-200">
                    Quality: {quality.formatting_score}% (Grade {quality.grade})
                  </span>
                </div>
              </div>

              {/* 8 Granular Subscores Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2.5 mb-6">
                {subscoreItems.map((item, idx) => (
                  <div key={idx} className="p-3 bg-gray-50 rounded-2xl border border-gray-100 text-center">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500 line-clamp-1">
                      {item.label}
                    </span>
                    <p className="text-lg font-black text-gray-900 mt-1">{item.val}%</p>
                    <div className="w-full bg-gray-200 h-1.5 rounded-full mt-2 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          item.val >= 80 ? 'bg-emerald-500' : item.val >= 60 ? 'bg-amber-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${item.val}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Detected Sections Checklist */}
              {quality.detected_sections && quality.detected_sections.length > 0 && (
                <div className="p-3.5 bg-gray-50 rounded-2xl border border-gray-100 mb-6">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500 block mb-2">
                    Standard ATS Sections Detected
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {quality.detected_sections.map((sec, i) => (
                      <span
                        key={i}
                        className="text-xs font-semibold bg-white border border-gray-200 text-gray-800 px-2.5 py-1 rounded-lg"
                      >
                        ✓ {sec.charAt(0).toUpperCase() + sec.slice(1)}
                      </span>
                    ))}
                    {quality.missing_sections?.map((sec, i) => (
                      <span
                        key={i}
                        className="text-xs font-medium bg-amber-50 border border-amber-200 text-amber-800 px-2.5 py-1 rounded-lg"
                      >
                        Missing: {sec.charAt(0).toUpperCase() + sec.slice(1)}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* ========================================================================= */}
              {/* RESULT 4: FORMATTING ISSUES & GOOD PRACTICES                              */}
              {/* ========================================================================= */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 pt-2">
                {/* Issues Found */}
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    <h4 className="text-xs font-bold uppercase tracking-wider text-amber-950">
                      Formatting & Quality Issues ({quality.issues?.length || 0})
                    </h4>
                  </div>

                  {quality.issues && quality.issues.length > 0 ? (
                    <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
                      {quality.issues.map((iss, i) => {
                        const isHigh = iss.severity === 'high' || iss.severity === 'critical';
                        const isMed = iss.severity === 'medium' || iss.severity === 'warning';
                        return (
                          <div
                            key={i}
                            className={`p-3.5 rounded-xl border text-xs space-y-1.5 ${
                              isHigh
                                ? 'bg-red-50/50 border-red-200'
                                : isMed
                                ? 'bg-amber-50/50 border-amber-200'
                                : 'bg-blue-50/50 border-blue-200'
                            }`}
                          >
                            <div className="flex items-center justify-between gap-2">
                              <span className="font-bold text-gray-900">
                                {iss.problem || iss.message}
                              </span>
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-black uppercase flex-shrink-0 ${
                                  isHigh
                                    ? 'bg-red-100 text-red-800'
                                    : isMed
                                    ? 'bg-amber-100 text-amber-800'
                                    : 'bg-blue-100 text-blue-800'
                                }`}
                              >
                                {iss.severity}
                              </span>
                            </div>

                            {iss.evidence && (
                              <p className="text-gray-600 font-mono text-[11px] bg-white/80 p-1.5 rounded border border-gray-200/60">
                                Evidence: "{iss.evidence}"
                              </p>
                            )}

                            {iss.why_it_matters && (
                              <p className="text-gray-600">
                                <span className="font-semibold text-gray-700">Why it matters:</span> {iss.why_it_matters}
                              </p>
                            )}

                            {iss.recommendation && (
                              <p className="text-emerald-800 font-semibold pt-0.5">
                                → {iss.recommendation}
                              </p>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="p-4 bg-emerald-50 rounded-2xl border border-emerald-100 text-xs font-semibold text-emerald-800">
                      ✓ No document formatting or parsing issues detected!
                    </div>
                  )}
                </div>

                {/* Positive Findings / Good Practices */}
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-950">
                      Good Practices Detected ({quality.good_practices?.length || 0})
                    </h4>
                  </div>

                  {quality.good_practices && quality.good_practices.length > 0 ? (
                    <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                      {quality.good_practices.map((gp, i) => (
                        <div
                          key={i}
                          className="p-3 bg-emerald-50/50 rounded-xl border border-emerald-100 text-xs text-emerald-900 flex items-start gap-2.5"
                        >
                          <Check className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                          <span className="font-medium">{gp}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-4 bg-gray-50 rounded-2xl border border-gray-100 text-xs text-gray-500">
                      Standard ATS structure applied.
                    </div>
                  )}
                </div>
              </div>
            </Card>
          )}

          {/* ========================================================================= */}
          {/* RESULT 6: SYNTHESIZED RESUME IMPROVEMENT SUGGESTIONS                      */}
          {/* ========================================================================= */}
          {evalResult.resume_suggestions && evalResult.resume_suggestions.length > 0 && (
            <Card padding="lg" className="border-t-4 border-t-amber-500 bg-gradient-to-b from-amber-50/20 to-white">
              <div className="flex items-center gap-2 mb-3 pb-2 border-b border-gray-100">
                <Sparkles className="w-5 h-5 text-amber-600" />
                <h3 className="text-base font-black text-gray-900">
                  Actionable Resume Improvement Plan
                </h3>
              </div>
              <p className="text-xs text-gray-500 mb-4">
                Prioritized recommendations addressing skill gaps, accomplishment impact, and ATS readability:
              </p>

              <div className="space-y-2.5">
                {evalResult.resume_suggestions.map((sug, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 bg-white rounded-xl border border-gray-200 flex items-start gap-3 shadow-2xs hover:border-amber-300 transition-all"
                  >
                    <span className="w-5 h-5 rounded-full bg-amber-100 text-amber-800 text-xs font-black flex items-center justify-center flex-shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <span className="text-xs font-medium text-gray-800 leading-relaxed">
                      {sug}
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  );
};
