import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Briefcase,
  Search,
  MapPin,
  Building,
  Plus,
  Trash2,
  Edit2,
  CheckCircle2,
  Clock,
  Send,
  Sparkles,
  Globe,
  Filter,
  Check,
  FileText,
  AlertCircle,
  Eye,
} from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { jobsApi, CreateJobPayload } from '../api/jobs';
import { resumesApi } from '../api/resumes';
import { rolesApi, RoleItem } from '../api/roles';
import { applicationsApi } from '../api/applications';
import { Job, Resume, isRecruiter } from '../types';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';
import { Alert } from '../components/ui/Alert';
import { Spinner } from '../components/ui/Spinner';

export const Jobs: React.FC = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const isHR = isRecruiter(user);

  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState('All');
  const [selectedStatus, setSelectedStatus] = useState('All');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Candidate Apply Modal State
  const [applyingJob, setApplyingJob] = useState<Job | null>(null);
  const [candidateResumes, setCandidateResumes] = useState<Resume[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<string>('');
  const [isApplying, setIsApplying] = useState(false);

  // HR Create & Edit State
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingJobId, setEditingJobId] = useState<string | null>(null);
  const [isSubmittingJob, setIsSubmittingJob] = useState(false);
  const [roleCatalog, setRoleCatalog] = useState<RoleItem[]>([]);
  const [jobForm, setJobForm] = useState<CreateJobPayload>({
    title: '',
    company_name: '',
    department: 'Engineering',
    location: 'Remote',
    job_type: 'Full-time',
    experience_required: 2,
    required_skills: '',
    salary: '$100,000 - $130,000',
    description: '',
    status: 'draft',
    occupational_class: 'INFORMATION-TECHNOLOGY',
    specific_role: '',
  });

  useEffect(() => {
    loadJobs();
    if (isHR) {
      loadRoleCatalog();
    }
  }, [isHR]);

  const loadJobs = async () => {
    setLoading(true);
    try {
      const data = await jobsApi.getJobs(isHR ? { hr_only: true } : undefined);
      setJobs(data);
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to load jobs.' });
    } finally {
      setLoading(false);
    }
  };

  const loadRoleCatalog = async () => {
    try {
      const roles = await rolesApi.getRoles();
      setRoleCatalog(roles);
    } catch (e) {
      console.error('Failed to load role catalog:', e);
    }
  };

  // Open Candidate Apply Modal
  const handleOpenApplyModal = async (job: Job) => {
    setApplyingJob(job);
    try {
      const resumes = await resumesApi.getMyResumes();
      setCandidateResumes(resumes);
      if (resumes.length > 0) {
        const current = resumes.find((r) => r.is_current) || resumes[0];
        setSelectedResumeId(current.id);
      }
    } catch (e) {
      console.error('Failed to load resumes:', e);
    }
  };

  const handleApply = async () => {
    if (!applyingJob) return;
    setIsApplying(true);
    setMessage(null);
    try {
      await applicationsApi.apply(applyingJob.id, selectedResumeId || undefined);
      setMessage({ type: 'success', text: `Application submitted successfully for ${applyingJob.title}!` });
      setApplyingJob(null);
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Application submission failed.' });
    } finally {
      setIsApplying(false);
    }
  };

  // Direct to Career Analysis with Job Preselected
  const handleAnalyzeMatch = (job: Job) => {
    navigate('/career-analysis', { state: { preselectedJobId: job.id } });
  };

  // HR: Handle Role selection in Job Creation
  const handleRoleSelection = (roleName: string) => {
    const selected = roleCatalog.find((r) => r.name === roleName);
    if (selected) {
      setJobForm((prev) => ({
        ...prev,
        specific_role: selected.name,
        occupational_class: selected.occupational_class,
        title: prev.title || selected.name,
        required_skills: prev.required_skills || selected.required_skills_default.join(', '),
        description: prev.description || selected.description || '',
      }));
    } else {
      setJobForm((prev) => ({ ...prev, specific_role: roleName }));
    }
  };

  // HR: Open Create Modal
  const handleOpenCreateModal = () => {
    setEditingJobId(null);
    setJobForm({
      title: '',
      company_name: user?.name ? `${user.name}'s Org` : 'Acme Corporation',
      department: 'Engineering',
      location: 'Remote',
      job_type: 'Full-time',
      experience_required: 2,
      required_skills: '',
      salary: '$100,000 - $130,000',
      description: '',
      status: 'draft',
      occupational_class: 'INFORMATION-TECHNOLOGY',
      specific_role: '',
    });
    setIsCreateModalOpen(true);
  };

  // HR: Open Edit Modal
  const handleOpenEditModal = (job: Job) => {
    setEditingJobId(job.id);
    setJobForm({
      title: job.title,
      company_name: job.company_name,
      department: job.department || 'Engineering',
      location: job.location,
      job_type: job.job_type,
      experience_required: job.experience_required,
      required_skills: job.required_skills || '',
      salary: job.salary || '',
      description: job.description,
      status: job.status || 'draft',
      occupational_class: job.occupational_class || 'INFORMATION-TECHNOLOGY',
      specific_role: job.specific_role || '',
    });
    setIsCreateModalOpen(true);
  };

  // HR: Save Job (Create or Edit)
  const handleSaveJob = async (e: React.FormEvent, publishImmediately = false) => {
    e.preventDefault();
    if (!jobForm.title || !jobForm.description) return;

    setIsSubmittingJob(true);
    setMessage(null);
    try {
      const payload: CreateJobPayload = {
        ...jobForm,
        status: publishImmediately ? 'published' : jobForm.status,
      };

      if (editingJobId) {
        const updated = await jobsApi.updateJob(editingJobId, payload);
        setJobs((prev) => prev.map((j) => (j.id === editingJobId ? updated : j)));
        setMessage({ type: 'success', text: 'Job updated successfully!' });
      } else {
        const created = await jobsApi.createJob(payload);
        if (publishImmediately) {
          try {
            await jobsApi.publishJob(created.id);
            created.status = 'published';
          } catch (e) {
            console.error('Auto-publish note:', e);
          }
        }
        setJobs((prev) => [created, ...prev]);
        setMessage({
          type: 'success',
          text: publishImmediately
            ? 'Job published live to candidate feed!'
            : 'Job saved as draft. Publish when ready.',
        });
      }
      setIsCreateModalOpen(false);
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to save job.' });
    } finally {
      setIsSubmittingJob(false);
    }
  };

  // HR: Publish Job
  const handlePublishJob = async (id: string) => {
    try {
      const published = await jobsApi.publishJob(id);
      setJobs((prev) => prev.map((j) => (j.id === id ? { ...j, status: 'published' } : j)));
      setMessage({ type: 'success', text: 'Job is now published and visible to candidates!' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to publish job.' });
    }
  };

  // HR: Close Job
  const handleCloseJob = async (id: string) => {
    try {
      await jobsApi.updateJob(id, { status: 'closed' });
      setJobs((prev) => prev.map((j) => (j.id === id ? { ...j, status: 'closed' } : j)));
      setMessage({ type: 'success', text: 'Job posting closed.' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to close job.' });
    }
  };

  // HR: Delete Job
  const handleDeleteJob = async (id: string) => {
    if (!window.confirm('Are you sure you want to permanently delete this job posting?')) return;
    try {
      await jobsApi.deleteJob(id);
      setJobs((prev) => prev.filter((j) => j.id !== id));
      setMessage({ type: 'success', text: 'Job deleted successfully.' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to delete job.' });
    }
  };

  // Filter Jobs
  const filteredJobs = jobs.filter((job) => {
    const matchesSearch =
      job.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      job.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      job.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      job.location?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      job.specific_role?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = selectedType === 'All' || job.job_type === selectedType;
    const matchesStatus =
      !isHR || selectedStatus === 'All' || (job.status || 'published').toLowerCase() === selectedStatus.toLowerCase();
    return matchesSearch && matchesType && matchesStatus;
  });

  const distinctDomains = Array.from(new Set(roleCatalog.map((r) => r.occupational_class))).sort();
  const availableRolesForClass = roleCatalog.filter(
    (r) => !jobForm.occupational_class || r.occupational_class === jobForm.occupational_class
  );

  if (loading) {
    return <Spinner label="Loading positions..." className="h-96" />;
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wide ${
                isHR ? 'bg-indigo-100 text-indigo-800' : 'bg-emerald-100 text-emerald-800'
              }`}
            >
              {isHR ? 'Recruiter Job Operations' : 'Verified Career Opportunities'}
            </span>
          </div>
          <h1 className="text-3xl font-black tracking-tight text-gray-900">
            {isHR ? 'Recruitment Openings & Postings' : 'Explore Open Positions'}
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {isHR
              ? 'Author draft jobs with controlled taxonomy classification, publish live, and manage application pipelines.'
              : 'Browse verified company openings, evaluate ATS compatibility, and apply with your active resume.'}
          </p>
        </div>

        {isHR && (
          <Button
            variant="primary"
            onClick={handleOpenCreateModal}
            leftIcon={<Plus className="w-4 h-4" />}
            className="font-bold shadow-md shadow-indigo-100"
          >
            Post New Job
          </Button>
        )}
      </div>

      {message && (
        <Alert type={message.type} className="mb-4">
          {message.text}
        </Alert>
      )}

      {/* Filter and Search Bar */}
      <Card padding="md">
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="w-full md:max-w-md">
            <Input
              placeholder="Search by role, company, location, or keyword..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              leftIcon={<Search className="w-4 h-4" />}
            />
          </div>

          <div className="flex flex-wrap gap-2 w-full md:w-auto items-center">
            {isHR && (
              <div className="flex items-center gap-1 mr-2 bg-gray-50 p-1 rounded-xl border border-gray-200">
                {['All', 'published', 'draft', 'closed'].map((status) => (
                  <button
                    key={status}
                    onClick={() => setSelectedStatus(status)}
                    className={`px-3 py-1 rounded-lg text-xs font-bold capitalize transition-all cursor-pointer ${
                      selectedStatus.toLowerCase() === status.toLowerCase()
                        ? 'bg-indigo-600 text-white shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    {status}
                  </button>
                ))}
              </div>
            )}

            <div className="flex gap-1.5 overflow-x-auto pb-1 sm:pb-0">
              {['All', 'Full-time', 'Part-time', 'Contract', 'Internship'].map((type) => (
                <button
                  key={type}
                  onClick={() => setSelectedType(type)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                    selectedType === type
                      ? isHR
                        ? 'bg-indigo-600 text-white'
                        : 'bg-emerald-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* Job Cards Feed */}
      <div className="space-y-4">
        {filteredJobs.length === 0 ? (
          <Card padding="lg" className="text-center py-12">
            <Briefcase className="w-10 h-10 text-gray-300 mx-auto mb-3" />
            <p className="text-base font-bold text-gray-700">No positions found</p>
            <p className="text-xs text-gray-400 mt-1">
              {isHR
                ? 'You have not created any job postings yet, or none match the active filters.'
                : 'No published job postings are currently active. Please check back shortly.'}
            </p>
          </Card>
        ) : (
          filteredJobs.map((job) => {
            const status = (job.status || 'published').toLowerCase();
            return (
              <Card key={job.id} padding="lg" hover className="transition-all duration-150">
                <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6">
                  <div className="space-y-2.5 flex-1">
                    <div className="flex flex-wrap items-center gap-2.5">
                      <h3 className="text-lg font-black text-gray-900">{job.title}</h3>
                      <Badge variant={job.job_type === 'Full-time' ? 'success' : 'secondary'}>
                        {job.job_type}
                      </Badge>

                      {isHR && (
                        <Badge
                          variant={
                            status === 'published' ? 'success' : status === 'draft' ? 'warning' : 'secondary'
                          }
                        >
                          {status.toUpperCase()}
                        </Badge>
                      )}

                      {job.specific_role && (
                        <span className="text-xs font-bold px-2.5 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-100">
                          {job.specific_role}
                        </span>
                      )}

                      {job.location && (
                        <span className="text-xs text-gray-500 flex items-center gap-1 font-medium">
                          <MapPin className="w-3.5 h-3.5 text-gray-400" />
                          {job.location}
                        </span>
                      )}
                    </div>

                    <p className="text-xs font-bold text-gray-700 flex items-center gap-1.5">
                      <Building className="w-3.5 h-3.5 text-gray-400" />
                      {job.company_name || 'Verified Organization'} • {job.department || 'Engineering'}
                      {job.occupational_class && (
                        <span className="text-gray-400 font-normal">
                          • Domain: {job.occupational_class.replace(/-/g, ' ')}
                        </span>
                      )}
                    </p>

                    <p className="text-sm text-gray-600 line-clamp-3 leading-relaxed">
                      {job.description}
                    </p>

                    {job.required_skills && (
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {job.required_skills.split(',').map((s, i) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded-md font-medium"
                          >
                            {s.trim()}
                          </span>
                        ))}
                      </div>
                    )}

                    <div className="flex items-center gap-4 text-xs text-gray-500 pt-1 font-semibold">
                      {job.salary && <span className="text-gray-900 font-bold">{job.salary}</span>}
                      <span>Min {job.experience_required} yrs experience required</span>
                      {job.created_at && (
                        <span className="text-gray-400 font-normal">
                          Posted: {new Date(job.created_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex sm:flex-row lg:flex-col gap-2 self-start lg:self-center w-full lg:w-auto">
                    {isHR ? (
                      <div className="flex flex-wrap lg:flex-col gap-2 w-full">
                        {status === 'draft' && (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => handlePublishJob(job.id)}
                            leftIcon={<Globe className="w-3.5 h-3.5" />}
                            className="font-bold"
                          >
                            Publish Live
                          </Button>
                        )}
                        {status === 'published' && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleCloseJob(job.id)}
                            className="text-gray-600 hover:bg-gray-100"
                          >
                            Close Posting
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleOpenEditModal(job)}
                          leftIcon={<Edit2 className="w-3.5 h-3.5" />}
                        >
                          Edit
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDeleteJob(job.id)}
                          className="text-red-600 hover:bg-red-50 hover:border-red-200"
                          leftIcon={<Trash2 className="w-3.5 h-3.5" />}
                        >
                          Delete
                        </Button>
                      </div>
                    ) : (
                      <div className="flex sm:flex-row gap-2 w-full lg:w-auto">
                        <Button
                          variant="outline"
                          size="md"
                          onClick={() => handleAnalyzeMatch(job)}
                          leftIcon={<Sparkles className="w-4 h-4 text-emerald-600" />}
                          className="font-bold border-emerald-200 text-emerald-800 hover:bg-emerald-50"
                        >
                          Analyze Match
                        </Button>
                        <Button
                          variant="emerald"
                          size="md"
                          onClick={() => handleOpenApplyModal(job)}
                          leftIcon={<Send className="w-4 h-4" />}
                          className="font-bold whitespace-nowrap shadow-md shadow-emerald-100"
                        >
                          Apply Now
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            );
          })
        )}
      </div>

      {/* Candidate Apply Modal with Resume Selector */}
      {applyingJob && (
        <Modal
          isOpen={!!applyingJob}
          onClose={() => setApplyingJob(null)}
          title={`Apply for ${applyingJob.title}`}
        >
          <div className="space-y-5">
            <div>
              <p className="text-sm text-gray-600">
                Submit your credentials to <strong className="text-gray-900">{applyingJob.company_name}</strong> for the position of <strong className="text-gray-900">{applyingJob.title}</strong>.
              </p>
            </div>

            {/* Resume Selection */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-2">
                Choose Resume Version to Submit
              </label>

              {candidateResumes.length === 0 ? (
                <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-xs text-amber-900 flex items-start gap-2.5">
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-amber-600" />
                  <div>
                    <p className="font-bold">No resumes found in your profile</p>
                    <p className="mt-0.5">Please upload a resume in the Career Analysis or My Resumes page first.</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {candidateResumes.map((r) => (
                    <div
                      key={r.id}
                      onClick={() => setSelectedResumeId(r.id)}
                      className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                        selectedResumeId === r.id
                          ? 'border-emerald-500 bg-emerald-50/50 ring-2 ring-emerald-100'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <FileText className={`w-4 h-4 ${selectedResumeId === r.id ? 'text-emerald-600' : 'text-gray-400'}`} />
                        <div className="truncate">
                          <p className="text-xs font-bold text-gray-900 truncate">{r.original_filename}</p>
                          <p className="text-[11px] text-gray-500">Version {r.version}</p>
                        </div>
                      </div>
                      <Badge variant={selectedResumeId === r.id ? 'success' : 'secondary'}>
                        {selectedResumeId === r.id ? 'Selected' : `v${r.version}`}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="p-3 bg-gray-50 rounded-xl text-xs text-gray-500 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <span>Your profile information and selected resume will be securely transmitted.</span>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <Button variant="outline" onClick={() => setApplyingJob(null)}>
                Cancel
              </Button>
              <Button
                variant="emerald"
                isLoading={isApplying}
                onClick={handleApply}
                disabled={candidateResumes.length === 0}
                className="font-bold"
              >
                Submit Application
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* HR Create / Edit Job Modal */}
      {isHR && isCreateModalOpen && (
        <Modal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          title={editingJobId ? 'Edit Job Posting' : 'Author New Job Posting'}
        >
          <form className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                Job Title *
              </label>
              <Input
                required
                value={jobForm.title}
                onChange={(e) => setJobForm({ ...jobForm, title: e.target.value })}
                placeholder="e.g. Senior Machine Learning Engineer"
              />
            </div>

            {/* Controlled Role Catalog Selection */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                  Occupational Domain (22-Class)
                </label>
                <select
                  value={jobForm.occupational_class}
                  onChange={(e) => setJobForm({ ...jobForm, occupational_class: e.target.value })}
                  className="w-full text-xs font-semibold bg-white border border-gray-200 rounded-xl px-3 py-2 text-gray-800 focus:ring-2 focus:ring-indigo-500"
                >
                  {distinctDomains.map((dom) => (
                    <option key={dom} value={dom}>
                      {dom.replace(/-/g, ' ')}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                  Specific Standard Role
                </label>
                <select
                  value={jobForm.specific_role || ''}
                  onChange={(e) => handleRoleSelection(e.target.value)}
                  className="w-full text-xs font-semibold bg-white border border-gray-200 rounded-xl px-3 py-2 text-gray-800 focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">-- Choose Role from Catalog --</option>
                  {availableRolesForClass.map((r) => (
                    <option key={r.id} value={r.name}>
                      {r.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                  Company Name
                </label>
                <Input
                  value={jobForm.company_name}
                  onChange={(e) => setJobForm({ ...jobForm, company_name: e.target.value })}
                  placeholder="Acme Corp"
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                  Department
                </label>
                <Input
                  value={jobForm.department}
                  onChange={(e) => setJobForm({ ...jobForm, department: e.target.value })}
                  placeholder="Engineering"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                  Location
                </label>
                <Input
                  value={jobForm.location}
                  onChange={(e) => setJobForm({ ...jobForm, location: e.target.value })}
                  placeholder="Remote / New York, NY"
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                  Job Type
                </label>
                <select
                  value={jobForm.job_type}
                  onChange={(e) => setJobForm({ ...jobForm, job_type: e.target.value })}
                  className="w-full text-xs font-semibold bg-white border border-gray-200 rounded-xl px-3 py-2 text-gray-800 focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="Full-time">Full-time</option>
                  <option value="Part-time">Part-time</option>
                  <option value="Contract">Contract</option>
                  <option value="Internship">Internship</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                  Exp Required (Yrs)
                </label>
                <Input
                  type="number"
                  min="0"
                  max="30"
                  value={jobForm.experience_required}
                  onChange={(e) =>
                    setJobForm({ ...jobForm, experience_required: parseInt(e.target.value, 10) || 0 })
                  }
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                Salary Range
              </label>
              <Input
                value={jobForm.salary}
                onChange={(e) => setJobForm({ ...jobForm, salary: e.target.value })}
                placeholder="$120,000 - $160,000"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                Required Skills (Comma separated)
              </label>
              <Input
                value={jobForm.required_skills}
                onChange={(e) => setJobForm({ ...jobForm, required_skills: e.target.value })}
                placeholder="Python, PyTorch, SQL, Docker, AWS"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                Job Description *
              </label>
              <textarea
                rows={4}
                required
                value={jobForm.description}
                onChange={(e) => setJobForm({ ...jobForm, description: e.target.value })}
                placeholder="Detailed position overview, responsibilities, and requirements..."
                className="w-full text-xs rounded-xl border border-gray-200 p-2.5 text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="flex flex-col sm:flex-row justify-end gap-2 pt-3 border-t border-gray-100">
              <Button variant="outline" onClick={() => setIsCreateModalOpen(false)}>
                Cancel
              </Button>
              <Button
                variant="outline"
                isLoading={isSubmittingJob}
                onClick={(e) => handleSaveJob(e, false)}
                className="font-semibold"
              >
                Save as Draft
              </Button>
              <Button
                variant="primary"
                isLoading={isSubmittingJob}
                onClick={(e) => handleSaveJob(e, true)}
                className="font-bold shadow-md shadow-indigo-100"
              >
                Publish Live
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
