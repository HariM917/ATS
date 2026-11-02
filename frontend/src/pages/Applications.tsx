import React, { useState, useEffect } from 'react';
import {
  Layers,
  Clock,
  CheckCircle2,
  XCircle,
  ChevronRight,
  Filter,
  User,
  GraduationCap,
  Sparkles,
} from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { applicationsApi } from '../api/applications';
import { Application, isRecruiter } from '../types';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import { Alert } from '../components/ui/Alert';
import { Spinner } from '../components/ui/Spinner';

const STAGES = ['applied', 'screening', 'shortlisted', 'interview', 'offer', 'hired', 'rejected'];

export const Applications: React.FC = () => {
  const { user } = useAuthStore();
  const isHR = isRecruiter(user);

  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedStage, setSelectedStage] = useState('all');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Manage stage modal (for HR)
  const [selectedApp, setSelectedApp] = useState<Application | null>(null);
  const [newStage, setNewStage] = useState('');
  const [notes, setNotes] = useState('');
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    loadApplications();
  }, []);

  const loadApplications = async () => {
    setLoading(true);
    try {
      const data = await applicationsApi.getApplications();
      setApplications(data);
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to load applications.' });
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStage = async () => {
    if (!selectedApp || !newStage) return;
    setUpdating(true);
    try {
      const updated = await applicationsApi.updateStage(selectedApp.id, {
        stage: newStage,
        notes,
      });
      setApplications((prev) => prev.map((a) => (a.id === selectedApp.id ? { ...a, ...updated } : a)));
      setMessage({ type: 'success', text: `Application moved to ${newStage.toUpperCase()}!` });
      setSelectedApp(null);
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to update stage.' });
    } finally {
      setUpdating(false);
    }
  };

  const filtered = applications.filter((app) =>
    selectedStage === 'all' ? true : (app.stage || app.status) === selectedStage
  );

  const getStageBadge = (stage: string) => {
    const s = stage?.toLowerCase();
    switch (s) {
      case 'hired':
      case 'offer':
        return <Badge variant="success">{stage.toUpperCase()}</Badge>;
      case 'interview':
      case 'shortlisted':
        return <Badge variant="primary">{stage.toUpperCase()}</Badge>;
      case 'rejected':
        return <Badge variant="danger">{stage.toUpperCase()}</Badge>;
      case 'screening':
        return <Badge variant="warning">{stage.toUpperCase()}</Badge>;
      default:
        return <Badge variant="secondary">{stage ? stage.toUpperCase() : 'APPLIED'}</Badge>;
    }
  };

  if (loading) {
    return <Spinner label="Loading applications..." className="h-96" />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-gray-900">
            {isHR ? 'Candidate Recruitment Pipeline' : 'My Job Applications'}
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {isHR
              ? 'Review candidate profiles, evaluate match scores, and progress applications through pipeline stages.'
              : 'Track the status and progress of all your submitted job applications.'}
          </p>
        </div>
      </div>

      {message && <Alert type={message.type}>{message.text}</Alert>}

      {/* Stage Filter Pills */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        <button
          onClick={() => setSelectedStage('all')}
          className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
            selectedStage === 'all'
              ? isHR
                ? 'bg-indigo-600 text-white'
                : 'bg-emerald-600 text-white'
              : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
          }`}
        >
          All Applications ({applications.length})
        </button>
        {STAGES.map((st) => {
          const count = applications.filter((a) => (a.stage || a.status) === st).length;
          return (
            <button
              key={st}
              onClick={() => setSelectedStage(st)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap capitalize transition-all cursor-pointer ${
                selectedStage === st
                  ? isHR
                    ? 'bg-indigo-600 text-white'
                    : 'bg-emerald-600 text-white'
                  : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              {st} ({count})
            </button>
          );
        })}
      </div>

      {/* Applications List */}
      <div className="space-y-4">
        {filtered.length === 0 ? (
          <Card padding="lg" className="text-center py-16">
            <Layers className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <h3 className="text-base font-bold text-gray-900">No applications found</h3>
            <p className="text-sm text-gray-500 mt-1">
              {selectedStage === 'all'
                ? 'No applications submitted yet.'
                : `No applications currently in '${selectedStage}' stage.`}
            </p>
          </Card>
        ) : (
          filtered.map((app) => (
            <Card key={app.id} padding="lg">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1.5">
                  <div className="flex items-center gap-3">
                    <h3 className="text-base font-bold text-gray-900">
                      {isHR ? app.candidate_name || 'Candidate' : app.job_title || 'Position Application'}
                    </h3>
                    {getStageBadge(app.stage || app.status)}
                  </div>

                  <p className="text-xs text-gray-500 flex items-center gap-2">
                    {isHR ? (
                      <>
                        <span>Applied for: <strong className="text-gray-800">{app.job_title}</strong></span>
                        {app.email && <span>• {app.email}</span>}
                        {app.branch && <span>• {app.branch}</span>}
                      </>
                    ) : (
                      <>
                        <span>{app.company_name || 'TalentFlow Partner'}</span>
                        {app.location && <span>• {app.location}</span>}
                      </>
                    )}
                    {app.created_at && (
                      <span>• Applied {new Date(app.created_at).toLocaleDateString()}</span>
                    )}
                  </p>

                  {app.notes && (
                    <p className="text-xs text-gray-600 italic bg-gray-50 p-2 rounded-lg max-w-xl">
                      Recruiter Note: {app.notes}
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-3 self-end sm:self-center">
                  {app.score !== undefined && (
                    <div className="text-right">
                      <span className="text-[10px] uppercase font-bold text-gray-400 block">Match Score</span>
                      <span className="text-sm font-black text-emerald-600">
                        {Math.round(app.score <= 1 ? app.score * 100 : app.score)}%
                      </span>
                    </div>
                  )}

                  {isHR && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSelectedApp(app);
                        setNewStage(app.stage || 'applied');
                        setNotes(app.notes || '');
                      }}
                    >
                      Update Stage
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          ))
        )}
      </div>

      {/* Recruiter Stage Update Modal */}
      {selectedApp && (
        <Modal
          isOpen={!!selectedApp}
          onClose={() => setSelectedApp(null)}
          title={`Update Pipeline: ${selectedApp.candidate_name || 'Candidate'}`}
        >
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1.5">
                Pipeline Stage
              </label>
              <select
                value={newStage}
                onChange={(e) => setNewStage(e.target.value)}
                className="block w-full rounded-xl border border-gray-200 p-2.5 text-sm text-gray-900 capitalize focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {STAGES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1.5">
                Recruiter Notes & Feedback
              </label>
              <textarea
                rows={3}
                placeholder="Interview notes, technical review feedback..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="block w-full rounded-xl border border-gray-200 p-3 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <Button variant="outline" onClick={() => setSelectedApp(null)}>
                Cancel
              </Button>
              <Button variant="primary" isLoading={updating} onClick={handleUpdateStage}>
                Save Status
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

