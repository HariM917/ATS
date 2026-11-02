import React, { useState, useEffect } from 'react';
import {
  User,
  Mail,
  GraduationCap,
  MapPin,
  Phone,
  Linkedin,
  Github,
  Globe,
  Briefcase,
  Award,
  Sparkles,
  Plus,
  X,
  CheckCircle2,
  AlertCircle,
  Save,
} from 'lucide-react';
import { candidatesApi } from '../api/candidates';
import { CandidateProfile } from '../types';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { Alert } from '../components/ui/Alert';
import { Spinner } from '../components/ui/Spinner';
import { Badge } from '../components/ui/Badge';

export const Profile: React.FC = () => {
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [error, setError] = useState('');

  // 17 Fields Form State
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [location, setLocation] = useState('');
  const [headline, setHeadline] = useState('');
  const [bio, setBio] = useState('');
  const [skills, setSkills] = useState<string[]>([]);
  const [skillInput, setSkillInput] = useState('');
  const [branch, setBranch] = useState('');
  const [graduationYear, setGraduationYear] = useState('');
  const [education, setEducation] = useState('');
  const [linkedin, setLinkedin] = useState('');
  const [github, setGithub] = useState('');
  const [portfolio, setPortfolio] = useState('');
  const [experience, setExperience] = useState('');
  const [certifications, setCertifications] = useState<string[]>([]);
  const [certInput, setCertInput] = useState('');
  const [preferredRole, setPreferredRole] = useState('');
  const [preferredLocation, setPreferredLocation] = useState('');

  useEffect(() => {
    loadProfile();
  }, []);

  const hydrateStateFromProfile = (data: CandidateProfile) => {
    setProfile(data);
    setName(data.name || '');
    setEmail(data.email || '');
    setPhone(data.phone || '');
    setLocation(data.location || '');
    setHeadline(data.headline || '');
    setBio(data.bio || '');

    // Skills array
    if (Array.isArray(data.skills)) {
      setSkills(data.skills);
    } else if (typeof data.skills === 'string') {
      setSkills((data.skills as string).split(',').map((s) => s.trim()).filter(Boolean));
    } else {
      setSkills([]);
    }

    setBranch(data.branch || '');
    setGraduationYear(data.graduation_year ? String(data.graduation_year) : '');

    // Education
    if (Array.isArray(data.education)) {
      setEducation(data.education.join('\n'));
    } else {
      setEducation(data.education || '');
    }

    setLinkedin(data.linkedin_url || '');
    setGithub(data.github_url || '');
    setPortfolio(data.portfolio_url || '');

    // Experience
    if (Array.isArray(data.experience)) {
      setExperience(data.experience.join('\n'));
    } else {
      setExperience(data.experience || '');
    }

    // Certifications array
    if (Array.isArray(data.certifications)) {
      setCertifications(data.certifications);
    } else if (typeof data.certifications === 'string') {
      setCertifications((data.certifications as string).split(',').map((s) => s.trim()).filter(Boolean));
    } else {
      setCertifications([]);
    }

    setPreferredRole(data.preferred_role || '');
    setPreferredLocation(data.preferred_location || '');
  };

  const loadProfile = async () => {
    setLoading(true);
    try {
      const data = await candidatesApi.getProfile();
      hydrateStateFromProfile(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load profile.');
    } finally {
      setLoading(false);
    }
  };

  // Add Skill Tag
  const handleAddSkill = (e?: React.KeyboardEvent | React.MouseEvent) => {
    if (e && 'key' in e && e.key !== 'Enter') return;
    if (e) e.preventDefault();
    const clean = skillInput.trim();
    if (clean && !skills.includes(clean)) {
      setSkills([...skills, clean]);
      setSkillInput('');
    }
  };

  const handleRemoveSkill = (skillToRemove: string) => {
    setSkills(skills.filter((s) => s !== skillToRemove));
  };

  // Add Certification Tag
  const handleAddCert = (e?: React.KeyboardEvent | React.MouseEvent) => {
    if (e && 'key' in e && e.key !== 'Enter') return;
    if (e) e.preventDefault();
    const clean = certInput.trim();
    if (clean && !certifications.includes(clean)) {
      setCertifications([...certifications, clean]);
      setCertInput('');
    }
  };

  const handleRemoveCert = (certToRemove: string) => {
    setCertifications(certifications.filter((c) => c !== certToRemove));
  };

  // Strict Save Flow: PUT -> Wait -> Refetch GET -> Hydrate -> Notify
  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccessMessage('');

    try {
      // 1. Submit PUT
      await candidatesApi.updateProfile({
        name,
        phone,
        location,
        headline,
        bio,
        skills,
        branch,
        graduation_year: graduationYear ? parseInt(graduationYear, 10) : null,
        education,
        linkedin_url: linkedin,
        github_url: github,
        portfolio_url: portfolio,
        experience,
        certifications,
        preferred_role: preferredRole,
        preferred_location: preferredLocation,
      });

      // 2. Refetch GET from authoritative database
      const refetched = await candidatesApi.getProfile();

      // 3. Hydrate state from server response
      hydrateStateFromProfile(refetched);

      // 4. Notify user of confirmed persistence
      setSuccessMessage('Profile saved successfully! All 17 profile fields synchronized.');
      setTimeout(() => setSuccessMessage(''), 5000);
    } catch (err: any) {
      setError(err.message || 'Failed to update profile.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <Spinner label="Loading profile record..." className="h-96" />;
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 uppercase tracking-wide">
            Candidate Credentials
          </span>
        </div>
        <h1 className="text-3xl font-black tracking-tight text-gray-900">Candidate Profile & Career Portfolio</h1>
        <p className="text-sm text-gray-500 mt-1">
          Complete your professional background, skills catalog, and career preferences for automated ATS job matching.
        </p>
      </div>

      {successMessage && (
        <Alert type="success" title="Persistence Confirmed">
          {successMessage}
        </Alert>
      )}
      {error && <Alert type="error" title="Profile Update Error">{error}</Alert>}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Section 1: Basic Identity & Contact Information */}
        <Card padding="lg">
          <div className="flex items-center gap-2 mb-4 border-b border-gray-100 pb-3">
            <User className="w-5 h-5 text-emerald-600" />
            <h3 className="text-base font-bold text-gray-900">Personal & Contact Information</h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                Full Name *
              </label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                leftIcon={<User className="w-4 h-4" />}
                placeholder="Jane Doe"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                Email Address
              </label>
              <Input
                value={email}
                disabled
                leftIcon={<Mail className="w-4 h-4" />}
                helperText="Primary email cannot be changed directly."
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                Phone Number
              </label>
              <Input
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                leftIcon={<Phone className="w-4 h-4" />}
                placeholder="+1 (555) 000-0000"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                Current Location
              </label>
              <Input
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                leftIcon={<MapPin className="w-4 h-4" />}
                placeholder="San Francisco, CA or Remote"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                Professional Headline
              </label>
              <Input
                value={headline}
                onChange={(e) => setHeadline(e.target.value)}
                placeholder="e.g. Senior Machine Learning Engineer | PyTorch, NLP, MLOps"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1.5">
                Professional Summary / Bio
              </label>
              <textarea
                rows={3}
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Brief summary of your career focus, technical expertise, and accomplishments..."
                className="w-full text-xs rounded-xl border border-gray-200 p-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          </div>
        </Card>

        {/* Section 2: Technical Skills Tag Editor */}
        <Card padding="lg">
          <div className="flex items-center gap-2 mb-4 border-b border-gray-100 pb-3">
            <Sparkles className="w-5 h-5 text-emerald-600" />
            <div>
              <h3 className="text-base font-bold text-gray-900">Technical Skills Catalog</h3>
              <p className="text-xs text-gray-500">Key competencies recognized by our matching classifier.</p>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex gap-2">
              <input
                type="text"
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyDown={handleAddSkill}
                placeholder="Type a skill and press Enter (e.g. PyTorch, Docker, React, FastAPI)..."
                className="flex-1 text-xs rounded-xl border border-gray-200 px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
              <Button
                type="button"
                variant="emerald"
                size="sm"
                onClick={handleAddSkill}
                leftIcon={<Plus className="w-3.5 h-3.5" />}
              >
                Add Skill
              </Button>
            </div>

            {skills.length > 0 ? (
              <div className="flex flex-wrap gap-2 p-3 bg-gray-50 rounded-2xl border border-gray-100">
                {skills.map((s) => (
                  <span
                    key={s}
                    className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold bg-white border border-gray-200 text-gray-800 shadow-sm"
                  >
                    {s}
                    <button
                      type="button"
                      onClick={() => handleRemoveSkill(s)}
                      className="text-gray-400 hover:text-red-500 cursor-pointer"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-xs text-gray-400 italic">No skills added yet. Type a skill above to add tags.</p>
            )}
          </div>
        </Card>

        {/* Section 3: Education & Academic History */}
        <Card padding="lg">
          <div className="flex items-center gap-2 mb-4 border-b border-gray-100 pb-3">
            <GraduationCap className="w-5 h-5 text-emerald-600" />
            <h3 className="text-base font-bold text-gray-900">Education & Academic Background</h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                Branch / Major
              </label>
              <Input
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                placeholder="Computer Science, Information Technology, Electrical..."
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                Graduation Year
              </label>
              <Input
                type="number"
                min="1970"
                max="2035"
                value={graduationYear}
                onChange={(e) => setGraduationYear(e.target.value)}
                placeholder="2025"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1.5">
                Degree & Institution Overview
              </label>
              <textarea
                rows={2}
                value={education}
                onChange={(e) => setEducation(e.target.value)}
                placeholder="e.g. B.Tech in Computer Science, Stanford University (GPA: 3.8/4.0)"
                className="w-full text-xs rounded-xl border border-gray-200 p-2.5 text-gray-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          </div>
        </Card>

        {/* Section 4: Work Experience & Certifications */}
        <Card padding="lg">
          <div className="flex items-center gap-2 mb-4 border-b border-gray-100 pb-3">
            <Briefcase className="w-5 h-5 text-emerald-600" />
            <h3 className="text-base font-bold text-gray-900">Experience & Credentials</h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1.5">
                Work Experience Overview
              </label>
              <textarea
                rows={3}
                value={experience}
                onChange={(e) => setExperience(e.target.value)}
                placeholder="Summary of previous employment, internships, responsibilities, and achievements..."
                className="w-full text-xs rounded-xl border border-gray-200 p-2.5 text-gray-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            {/* Certifications Tag Editor */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1.5">
                Certifications & Licensures
              </label>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={certInput}
                  onChange={(e) => setCertInput(e.target.value)}
                  onKeyDown={handleAddCert}
                  placeholder="e.g. AWS Certified Solutions Architect, Google Professional ML Engineer..."
                  className="flex-1 text-xs rounded-xl border border-gray-200 px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleAddCert}
                  leftIcon={<Plus className="w-3.5 h-3.5" />}
                >
                  Add Cert
                </Button>
              </div>

              {certifications.length > 0 && (
                <div className="flex flex-wrap gap-2 p-2.5 bg-gray-50 rounded-xl border border-gray-100">
                  {certifications.map((c) => (
                    <span
                      key={c}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold bg-white border border-gray-200 text-gray-800"
                    >
                      <Award className="w-3 h-3 text-emerald-600" />
                      {c}
                      <button
                        type="button"
                        onClick={() => handleRemoveCert(c)}
                        className="text-gray-400 hover:text-red-500 cursor-pointer"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </Card>

        {/* Section 5: Target Role & Location Preferences */}
        <Card padding="lg">
          <div className="flex items-center gap-2 mb-4 border-b border-gray-100 pb-3">
            <Award className="w-5 h-5 text-emerald-600" />
            <h3 className="text-base font-bold text-gray-900">Career & Placement Preferences</h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                Preferred Target Role
              </label>
              <Input
                value={preferredRole}
                onChange={(e) => setPreferredRole(e.target.value)}
                placeholder="e.g. Machine Learning Engineer, Backend Developer"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                Preferred Work Location
              </label>
              <Input
                value={preferredLocation}
                onChange={(e) => setPreferredLocation(e.target.value)}
                placeholder="e.g. Remote, San Francisco, New York, Hybrid"
              />
            </div>
          </div>
        </Card>

        {/* Section 6: Professional Portfolio & Social Links */}
        <Card padding="lg">
          <div className="flex items-center gap-2 mb-4 border-b border-gray-100 pb-3">
            <Globe className="w-5 h-5 text-emerald-600" />
            <h3 className="text-base font-bold text-gray-900">Online Profiles & Links</h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                LinkedIn Profile URL
              </label>
              <Input
                value={linkedin}
                onChange={(e) => setLinkedin(e.target.value)}
                leftIcon={<Linkedin className="w-4 h-4 text-blue-600" />}
                placeholder="https://linkedin.com/in/username"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                GitHub Profile URL
              </label>
              <Input
                value={github}
                onChange={(e) => setGithub(e.target.value)}
                leftIcon={<Github className="w-4 h-4 text-gray-800" />}
                placeholder="https://github.com/username"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">
                Portfolio or Personal Website
              </label>
              <Input
                value={portfolio}
                onChange={(e) => setPortfolio(e.target.value)}
                leftIcon={<Globe className="w-4 h-4 text-emerald-600" />}
                placeholder="https://yourportfolio.dev"
              />
            </div>
          </div>
        </Card>

        {/* Submit Actions */}
        <div className="flex justify-end pt-2">
          <Button
            type="submit"
            variant="emerald"
            size="lg"
            isLoading={saving}
            leftIcon={<Save className="w-5 h-5" />}
            className="font-bold px-8 shadow-md shadow-emerald-100"
          >
            Save All Profile Details
          </Button>
        </div>
      </form>
    </div>
  );
};
