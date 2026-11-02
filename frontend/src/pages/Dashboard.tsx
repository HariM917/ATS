import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  Briefcase,
  FileText,
  Layers,
  ArrowRight,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertCircle,
  Building,
  MapPin,
  Plus,
} from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { candidatesApi } from '../api/candidates';
import { jobsApi } from '../api/jobs';
import { resumesApi } from '../api/resumes';
import { analyticsApi } from '../api/analytics';
import { applicationsApi } from '../api/applications';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Spinner } from '../components/ui/Spinner';
import { Job, Application, Resume, isRecruiter } from '../types';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const isHR = isRecruiter(user);

  const [loading, setLoading] = useState(true);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [hrOverview, setHrOverview] = useState<any>(null);

  useEffect(() => {
    const loadDashboardData = async () => {
      setLoading(true);
      try {
        if (isHR) {
          const [jobsData, appsData, analyticsData] = await Promise.all([
            jobsApi.getJobs({ hr_only: true }).catch(() => []),
            applicationsApi.getApplications().catch(() => []),
            analyticsApi.getRecruiterOverview().catch(() => null),
          ]);
          setJobs(jobsData);
          setApplications(appsData);
          setHrOverview(analyticsData);
        } else {
          const [jobsData, appsData, resumesData] = await Promise.all([
            jobsApi.getJobs().catch(() => []),
            candidatesApi.getApplications().catch(() => []),
            resumesApi.getMyResumes().catch(() => []),
          ]);
          setJobs(jobsData);
          setApplications(appsData);
          setResumes(resumesData);
        }
      } catch (e) {
        console.error('Error loading dashboard:', e);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, [isHR]);

  if (loading) {
    return <Spinner label="Loading dashboard..." className="h-96" />;
  }

  if (isHR) {
    return (
      <div className="space-y-6">
        {/* Recruiter Banner */}
        <div className="bg-gradient-to-r from-indigo-900 via-indigo-800 to-indigo-950 rounded-3xl p-8 text-white relative overflow-hidden shadow-xl shadow-indigo-100">
          <div className="relative z-10 max-w-2xl">
            <span className="px-3 py-1 bg-white/10 text-indigo-200 text-xs font-bold rounded-full backdrop-blur-sm inline-block mb-3">
              Recruiter Command Center
            </span>
            <h1 className="text-3xl font-black tracking-tight mb-2">
              Welcome back, {user?.name || user?.user || 'Recruiter'}
            </h1>
            <p className="text-sm text-indigo-200 leading-relaxed mb-6">
              Track applicant pipelines, evaluate candidates with occupational classification, and manage job openings.
            </p>
            <div className="flex flex-wrap gap-3">
              <Button
                variant="primary"
                onClick={() => navigate('/hr/jobs')}
                leftIcon={<Plus className="w-4 h-4" />}
                className="bg-white text-indigo-900 hover:bg-indigo-50 shadow-none font-bold"
              >
                Post New Job
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate('/hr/applications')}
                leftIcon={<Layers className="w-4 h-4" />}
                className="bg-white/10 border-white/20 text-white hover:bg-white/20"
              >
                Review Applications ({applications.length})
              </Button>
            </div>
          </div>
        </div>

        {/* HR Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card padding="md">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Active Jobs</span>
              <div className="w-9 h-9 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
                <Briefcase className="w-5 h-5" />
              </div>
            </div>
            <p className="text-2xl font-black text-gray-900 mt-2">{jobs.length}</p>
            <p className="text-xs text-gray-400 mt-1">Available for applicants</p>
          </Card>

          <Card padding="md">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Total Applications</span>
              <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                <Layers className="w-5 h-5" />
              </div>
            </div>
            <p className="text-2xl font-black text-gray-900 mt-2">{applications.length}</p>
            <p className="text-xs text-gray-400 mt-1">Received candidates</p>
          </Card>

          <Card padding="md">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Shortlisted</span>
              <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
                <Clock className="w-5 h-5" />
              </div>
            </div>
            <p className="text-2xl font-black text-gray-900 mt-2">
              {applications.filter((a) => a.stage === 'shortlisted' || a.stage === 'interview').length}
            </p>
            <p className="text-xs text-gray-400 mt-1">In review & interview</p>
          </Card>

          <Card padding="md">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Hired</span>
              <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5" />
              </div>
            </div>
            <p className="text-2xl font-black text-gray-900 mt-2">
              {applications.filter((a) => a.stage === 'hired' || a.stage === 'offer').length}
            </p>
            <p className="text-xs text-gray-400 mt-1">Offers extended / accepted</p>
          </Card>
        </div>

        {/* Recent Job Postings */}
        <Card padding="lg">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-gray-900">Recent Job Openings</h3>
            <Button variant="ghost" size="sm" onClick={() => navigate('/hr/jobs')} rightIcon={<ArrowRight className="w-4 h-4" />}>
              View All Jobs
            </Button>
          </div>

          <div className="divide-y divide-gray-100">
            {jobs.length === 0 ? (
              <p className="text-sm text-gray-400 py-6 text-center">No active job postings found. Click "Post New Job" to begin.</p>
            ) : (
              jobs.slice(0, 5).map((job) => (
                <div key={job.id} className="py-4 flex items-center justify-between gap-4">
                  <div>
                    <h4 className="text-sm font-bold text-gray-900">{job.title}</h4>
                    <div className="flex items-center gap-3 text-xs text-gray-500 mt-1">
                      <span>{job.company_name}</span>
                      <span>•</span>
                      <span>{job.location}</span>
                      <span>•</span>
                      <span>{job.job_type}</span>
                    </div>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => navigate('/hr/jobs')}>
                    Manage Job
                  </Button>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>
    );
  }

  // Candidate Dashboard View
  const currentResume = resumes.find((r) => r.is_current) || resumes[0];

  return (
    <div className="space-y-6">
      {/* Candidate Banner */}
      <div className="bg-gradient-to-r from-emerald-800 via-teal-800 to-emerald-950 rounded-3xl p-8 text-white relative overflow-hidden shadow-xl shadow-emerald-100">
        <div className="relative z-10 max-w-2xl">
          <span className="px-3 py-1 bg-white/10 text-emerald-200 text-xs font-bold rounded-full backdrop-blur-sm inline-block mb-3">
            Career Analysis Portal
          </span>
          <h1 className="text-3xl font-black tracking-tight mb-2">
            Welcome back, {user?.name || user?.user || 'Candidate'}
          </h1>
          <p className="text-sm text-emerald-100 leading-relaxed mb-6">
            Upload your resume, unlock multidimensional ATS matching, and discover jobs tailored to your skills.
          </p>
          <div className="flex flex-wrap gap-3">
            <Button
              variant="primary"
              onClick={() => navigate('/career-analysis')}
              leftIcon={<Sparkles className="w-4 h-4" />}
              className="bg-white text-emerald-900 hover:bg-emerald-50 shadow-none font-bold"
            >
              Run Career Analysis
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate('/jobs')}
              leftIcon={<Briefcase className="w-4 h-4" />}
              className="bg-white/10 border-white/20 text-white hover:bg-white/20"
            >
              Explore Jobs ({jobs.length})
            </Button>
          </div>
        </div>
      </div>

      {/* Candidate Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card padding="md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Active Applications</span>
            <div className="w-9 h-9 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <Layers className="w-5 h-5" />
            </div>
          </div>
          <p className="text-2xl font-black text-gray-900 mt-2">{applications.length}</p>
          <p className="text-xs text-gray-400 mt-1">Submitted applications</p>
        </Card>

        <Card padding="md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Uploaded Resumes</span>
            <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <FileText className="w-5 h-5" />
            </div>
          </div>
          <p className="text-2xl font-black text-gray-900 mt-2">{resumes.length}</p>
          <p className="text-xs text-gray-400 mt-1">Stored versions</p>
        </Card>

        <Card padding="md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">ATS Readiness</span>
            <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>
          <p className="text-2xl font-black text-gray-900 mt-2">
            {currentResume?.ats_score ? `${Math.round(currentResume.ats_score * 100)}%` : 'Ready'}
          </p>
          <p className="text-xs text-gray-400 mt-1">Based on current resume</p>
        </Card>

        <Card padding="md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Predicted Role</span>
            <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <Sparkles className="w-5 h-5" />
            </div>
          </div>
          <p className="text-base font-bold text-gray-900 mt-2 truncate">
            {currentResume?.predicted_role || 'General Tech'}
          </p>
          <p className="text-xs text-gray-400 mt-1">Occupational Taxonomy</p>
        </Card>
      </div>

      {/* Recommended Jobs & Applications Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recommended Jobs Feed */}
        <Card padding="lg">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-bold text-gray-900">Recommended Jobs</h3>
            <Button variant="ghost" size="sm" onClick={() => navigate('/jobs')} rightIcon={<ArrowRight className="w-4 h-4" />}>
              View All
            </Button>
          </div>
          <div className="space-y-3">
            {jobs.slice(0, 3).map((job) => (
              <div key={job.id} className="p-4 rounded-xl border border-gray-100 bg-gray-50/50 hover:bg-gray-50 transition-colors">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="text-sm font-bold text-gray-900">{job.title}</h4>
                    <p className="text-xs text-gray-500 flex items-center gap-1.5 mt-0.5">
                      <Building className="w-3.5 h-3.5" /> {job.company_name} • <MapPin className="w-3.5 h-3.5" /> {job.location}
                    </p>
                  </div>
                  <Badge variant="primary">{job.job_type}</Badge>
                </div>
                <div className="mt-3 flex justify-between items-center">
                  <span className="text-xs font-semibold text-gray-700">{job.salary || 'Competitive'}</span>
                  <Button size="sm" variant="emerald" onClick={() => navigate('/jobs')}>
                    View & Apply
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* My Applications Status */}
        <Card padding="lg">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-bold text-gray-900">Recent Applications</h3>
            <Button variant="ghost" size="sm" onClick={() => navigate('/applications')} rightIcon={<ArrowRight className="w-4 h-4" />}>
              All Applications
            </Button>
          </div>
          <div className="space-y-3">
            {applications.length === 0 ? (
              <p className="text-sm text-gray-400 py-8 text-center">No applications submitted yet. Browse jobs to apply.</p>
            ) : (
              applications.slice(0, 3).map((app) => (
                <div key={app.id} className="p-4 rounded-xl border border-gray-100 flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-bold text-gray-900">{app.job_title || 'Position Application'}</h4>
                    <p className="text-xs text-gray-500 mt-0.5">{app.company_name || 'TalentFlow Partner'}</p>
                  </div>
                  <Badge
                    variant={
                      app.stage === 'hired'
                        ? 'success'
                        : app.stage === 'shortlisted'
                        ? 'primary'
                        : app.stage === 'rejected'
                        ? 'danger'
                        : 'secondary'
                    }
                  >
                    {app.stage.toUpperCase()}
                  </Badge>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};

