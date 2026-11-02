import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Upload, Trash2, Sparkles, Brain, CheckCircle2, AlertCircle } from 'lucide-react';
import { resumesApi } from '../api/resumes';
import { Resume } from '../types';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';
import { Spinner } from '../components/ui/Spinner';

export const MyResumes: React.FC = () => {
  const navigate = useNavigate();
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadResumes();
  }, []);

  const loadResumes = async () => {
    setLoading(true);
    try {
      const data = await resumesApi.getMyResumes();
      setResumes(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load resumes.');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError(null);
    try {
      await resumesApi.upload(file);
      await loadResumes();
    } catch (err: any) {
      setError(err.message || 'Failed to upload resume.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this resume?')) return;
    try {
      await resumesApi.deleteResume(id);
      setResumes((prev) => prev.filter((r) => r.id !== id));
    } catch (err: any) {
      setError(err.message || 'Failed to delete resume.');
    }
  };

  if (loading) {
    return <Spinner label="Loading resumes..." className="h-96" />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-gray-900">My Resumes</h1>
          <p className="text-sm text-gray-500 mt-1">
            Store and manage versioned resumes used for job applications and ATS screening.
          </p>
        </div>

        <label className="inline-block">
          <Button
            variant="emerald"
            size="md"
            isLoading={uploading}
            leftIcon={<Upload className="w-4 h-4" />}
            onClick={() => document.getElementById('resume-file-input-page')?.click()}
          >
            Upload Resume
          </Button>
          <input
            id="resume-file-input-page"
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={handleFileUpload}
            className="hidden"
          />
        </label>
      </div>

      {error && <Alert type="error">{error}</Alert>}

      {resumes.length === 0 ? (
        <Card padding="lg" className="text-center py-16">
          <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-base font-bold text-gray-900">No resumes uploaded</h3>
          <p className="text-sm text-gray-500 mt-1 mb-6">
            Upload your resume in PDF or DOCX format to get started with ATS analysis.
          </p>
          <Button
            variant="emerald"
            leftIcon={<Upload className="w-4 h-4" />}
            onClick={() => document.getElementById('resume-file-input-page')?.click()}
          >
            Upload First Resume
          </Button>
        </Card>
      ) : (
        <div className="space-y-4">
          {resumes.map((resume) => (
            <Card key={resume.id} padding="lg">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2.5">
                      <h4 className="text-base font-bold text-gray-900">{resume.original_filename}</h4>
                      {resume.is_current && <Badge variant="success">Current Version</Badge>}
                      <Badge variant="secondary">v{resume.version}</Badge>
                    </div>

                    <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500 mt-1.5">
                      {resume.predicted_role && (
                        <span className="flex items-center gap-1 font-semibold text-indigo-600">
                          <Brain className="w-3.5 h-3.5" />
                          {resume.predicted_role}
                        </span>
                      )}
                      <span>{resume.extracted_skills?.length || 0} skills detected</span>
                      {resume.created_at && (
                        <span>Uploaded {new Date(resume.created_at).toLocaleDateString()}</span>
                      )}
                    </div>

                    {/* Skill tags */}
                    <div className="flex flex-wrap gap-1.5 mt-3">
                      {resume.extracted_skills?.slice(0, 10).map((skill, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded-md font-medium"
                        >
                          {skill}
                        </span>
                      ))}
                      {(resume.extracted_skills?.length || 0) > 10 && (
                        <span className="text-xs text-gray-400 self-center">
                          +{resume.extracted_skills.length - 10} more
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-center">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigate('/career-analysis')}
                    leftIcon={<Sparkles className="w-4 h-4" />}
                  >
                    Analyze
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(resume.id)}
                    className="text-red-600 hover:bg-red-50 hover:text-red-700"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

