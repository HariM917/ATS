import React, { useState, useEffect } from 'react';
import {
  Users,
  Search,
  Filter,
  FileText,
  Sparkles,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Award,
  ChevronRight,
  GraduationCap,
  Briefcase,
  Mail,
  MapPin,
  ExternalLink,
} from 'lucide-react';
import { candidatesApi } from '../api/candidates';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';
import { Spinner } from '../components/ui/Spinner';

interface CandidateRecord {
  id: string;
  name: string;
  email: string;
  branch?: string;
  graduation_year?: number;
  headline?: string;
  location?: string;
  resume_id?: string;
  resume_filename?: string;
  extracted_skills?: string[];
  predicted_role?: string;
  ats_score?: number;
  applications_count?: number;
}

export const HRCandidates: React.FC = () => {
  const [candidates, setCandidates] = useState<CandidateRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [skillFilter, setSkillFilter] = useState('');
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateRecord | null>(null);

  const fetchCandidates = async () => {
    setLoading(true);
    try {
      const data = await candidatesApi.listCandidates({
        search: search.trim() || undefined,
        skill: skillFilter.trim() || undefined,
      });
      setCandidates(data);
    } catch (err) {
      console.error('Failed to load candidates:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
  }, [search, skillFilter]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-gray-900 flex items-center gap-2">
            <Users className="w-6 h-6 text-indigo-600" />
            Candidate Talent Pool
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Browse, search, and inspect candidates with AI-extracted skills and ATS readiness scores.
          </p>
        </div>
        <div className="text-xs font-semibold px-3 py-1.5 rounded-xl bg-indigo-50 text-indigo-700 border border-indigo-100 flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5" />
          {candidates.length} Candidate{candidates.length !== 1 ? 's' : ''} in Database
        </div>
      </div>

      {/* Filters Bar */}
      <Card className="p-4 bg-white shadow-sm border border-gray-100">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1">
            <Input
              placeholder="Search by candidate name, email, or predicted role..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              leftIcon={<Search className="w-4 h-4 text-gray-400" />}
            />
          </div>
          <div className="sm:w-64">
            <Input
              placeholder="Filter by skill (e.g. Python, React)..."
              value={skillFilter}
              onChange={(e) => setSkillFilter(e.target.value)}
              leftIcon={<Filter className="w-4 h-4 text-gray-400" />}
            />
          </div>
        </div>
      </Card>

      {/* Candidate List */}
      {loading ? (
        <Spinner label="Loading talent pool..." className="h-64" />
      ) : candidates.length === 0 ? (
        <Card className="p-12 text-center bg-white border border-gray-100">
          <Users className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-gray-900">No candidates match your criteria</h3>
          <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
            Try adjusting your search query or skill filter to view candidates.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {candidates.map((cand) => {
            const atsScore = Math.round((cand.ats_score || 0) * (cand.ats_score && cand.ats_score <= 1 ? 100 : 1));
            const hasReviewWarning = atsScore < 60;

            return (
              <Card
                key={cand.id}
                className="p-5 bg-white border border-gray-100 hover:border-indigo-200 hover:shadow-md transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
                        {cand.name}
                      </h3>
                      <p className="text-xs text-gray-500 flex items-center gap-1.5 mt-0.5">
                        <Mail className="w-3.5 h-3.5 text-gray-400" />
                        {cand.email || 'No email provided'}
                      </p>
                    </div>
                    {cand.ats_score ? (
                      <Badge
                        variant={atsScore >= 75 ? 'emerald' : atsScore >= 60 ? 'primary' : 'warning'}
                        size="sm"
                      >
                        {atsScore}% ATS
                      </Badge>
                    ) : (
                      <Badge variant="neutral" size="sm">No ATS</Badge>
                    )}
                  </div>

                  {/* Predicted Role */}
                  <div className="mt-4 pt-3 border-t border-gray-100">
                    <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block mb-1">
                      Predicted Occupational Role
                    </span>
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700 text-xs font-semibold">
                      <Briefcase className="w-3.5 h-3.5" />
                      {cand.predicted_role || 'General Tech / Unclassified'}
                    </span>
                  </div>

                  {/* Skills preview */}
                  <div className="mt-3">
                    <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block mb-1.5">
                      Extracted Skills ({cand.extracted_skills?.length || 0})
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {cand.extracted_skills && cand.extracted_skills.length > 0 ? (
                        cand.extracted_skills.slice(0, 4).map((skill, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 rounded-md bg-gray-50 border border-gray-200 text-[11px] text-gray-600 font-medium"
                          >
                            {skill}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-gray-400 italic">No skills extracted</span>
                      )}
                      {cand.extracted_skills && cand.extracted_skills.length > 4 && (
                        <span className="px-1.5 py-0.5 text-[10px] font-bold text-gray-400">
                          +{cand.extracted_skills.length - 4} more
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Card Action */}
                <div className="mt-5 pt-3 border-t border-gray-100 flex items-center justify-between">
                  <span className="text-xs text-gray-500">
                    {cand.applications_count || 0} application{cand.applications_count !== 1 ? 's' : ''}
                  </span>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setSelectedCandidate(cand)}
                    rightIcon={<ChevronRight className="w-3.5 h-3.5" />}
                  >
                    Inspect Profile
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Candidate Inspector Modal */}
      {selectedCandidate && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedCandidate(null)}
          title={`Candidate Profile: ${selectedCandidate.name}`}
          size="lg"
        >
          <div className="space-y-5">
            {/* Header Info */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-gray-50 border border-gray-100">
              <div>
                <h4 className="text-lg font-bold text-gray-900">{selectedCandidate.name}</h4>
                <p className="text-xs text-gray-600 mt-0.5">{selectedCandidate.email}</p>
                {selectedCandidate.branch && (
                  <p className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                    <GraduationCap className="w-3.5 h-3.5" />
                    {selectedCandidate.branch} (Class of {selectedCandidate.graduation_year || 'N/A'})
                  </p>
                )}
              </div>
              <div className="text-right">
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block">ATS Readiness</span>
                <span className="text-2xl font-black text-indigo-600">
                  {Math.round((selectedCandidate.ats_score || 0) * (selectedCandidate.ats_score && selectedCandidate.ats_score <= 1 ? 100 : 1))}%
                </span>
              </div>
            </div>

            {/* AI Occupational Classifier Gate */}
            <div className="p-4 rounded-xl border border-indigo-100 bg-indigo-50/40 space-y-2">
              <div className="flex items-center gap-2 text-indigo-900 font-bold text-xs">
                <Sparkles className="w-4 h-4 text-indigo-600" />
                V21/V23 Occupational Classification Contract
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600">Predicted Primary Role:</span>
                <span className="font-bold text-gray-900">{selectedCandidate.predicted_role || 'General Tech'}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600">Review Gate Status:</span>
                {(selectedCandidate.ats_score || 0) >= 0.7 ? (
                  <span className="inline-flex items-center gap-1 font-semibold text-emerald-700">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Clear to Advance
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 font-semibold text-amber-700">
                    <AlertTriangle className="w-3.5 h-3.5" /> Human Recruiter Review Required
                  </span>
                )}
              </div>
            </div>

            {/* Extracted Skills Matrix */}
            <div>
              <h5 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">
                All Extracted Skills ({selectedCandidate.extracted_skills?.length || 0})
              </h5>
              <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto p-3 bg-gray-50 rounded-xl border border-gray-100">
                {selectedCandidate.extracted_skills && selectedCandidate.extracted_skills.length > 0 ? (
                  selectedCandidate.extracted_skills.map((s, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-1 rounded-lg bg-white border border-gray-200 text-xs font-medium text-gray-800 shadow-2xs"
                    >
                      {s}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-gray-400">No skills identified in current resume.</span>
                )}
              </div>
            </div>

            {/* Resume Info */}
            <div className="flex items-center justify-between p-3.5 rounded-xl border border-gray-200 bg-white">
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5 text-gray-500" />
                <div>
                  <p className="text-xs font-bold text-gray-900">
                    {selectedCandidate.resume_filename || 'Candidate Resume'}
                  </p>
                  <p className="text-[11px] text-gray-500">
                    Verified through TalentFlow Resume Extraction Pipeline
                  </p>
                </div>
              </div>
              <Button size="sm" variant="outline" onClick={() => setSelectedCandidate(null)}>
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

