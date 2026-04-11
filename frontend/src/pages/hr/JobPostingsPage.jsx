import { useState, useEffect } from 'react';
import { Spinner, Modal, Btn, Badge, useToast } from '../../components/shared/index.jsx';
import { DndProvider, useDrag, useDrop } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { Users, Star, Clock, XCircle, CheckCircle } from 'lucide-react';
import { hrGetJobs, hrUpdateJob, updateSubmissionStatus, hrGetJobResults } from '../../api/index.js';

// --- STYLES & HELPERS ---
const DEGREES = ['Unknown', 'High School', 'Associate', 'Bachelor', 'Master', 'PhD'];
const inputStyle = { width: '100%', padding: '11px 14px', background: 'var(--gray-100)', border: '2px solid transparent', borderRadius: 12, fontSize: 13.5, outline: 'none', fontFamily: 'var(--sans)', color: 'var(--gray-900)' };
const labelStyle = { display: 'block', fontSize: 12, fontWeight: 700, color: 'var(--gray-700)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '.06em' };

// --- KANBAN COMPONENTS ---
const DraggableCandidate = ({ candidate }) => {
  const [{ isDragging }, drag] = useDrag(() => ({
    type: 'CANDIDATE',
    item: { id: candidate.id },
    collect: (monitor) => ({ isDragging: !!monitor.isDragging() }),
  }));

  return (
    <div ref={drag} style={{ 
      opacity: isDragging ? 0.5 : 1, padding: 12, background: 'white', borderRadius: 8, 
      border: '1px solid #EAECF0', marginBottom: 8, cursor: 'grab', boxShadow: '0 2px 4px rgba(0,0,0,0.04)' 
    }}>
      <div style={{ fontWeight: 700, fontSize: 13 }}>{candidate.candidate_name || "New Applicant"}</div>
      <div style={{ fontSize: 11, color: '#6B7280' }}>
        ATS Score: {candidate.ats_score ? candidate.ats_score.toFixed(1) : 'N/A'}%
      </div>
    </div>
  );
};

const KanbanColumn = ({ title, status, icon, bgColor, candidates, onDrop }) => {
  const [{ isOver }, drop] = useDrop(() => ({
    accept: 'CANDIDATE',
    drop: (item) => onDrop(item.id, status),
    collect: (monitor) => ({ isOver: !!monitor.isOver() }),
  }));

  return (
    <div ref={drop} style={{ 
      background: bgColor, borderRadius: 12, padding: 12, minHeight: 400, 
      border: isOver ? '2px dashed #6366F1' : '2px solid transparent',
      transition: 'all 0.2s ease'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, fontWeight: 700, fontSize: 12, color: 'var(--gray-700)' }}>
        {icon} {title} ({candidates.length})
      </div>
      {candidates.map(c => <DraggableCandidate key={c.id} candidate={c} />)}
    </div>
  );
};

// --- FORM COMPONENTS ---
const WeightInput = ({ label, fieldKey, field }) => (
  <div>
    <label style={labelStyle}>{label}</label>
    <input type="number" step="0.05" min="0" max="1" style={inputStyle} {...field(fieldKey)} />
  </div>
);

const FormFields = ({ form, field }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
    <div>
      <label style={labelStyle}>Job Title *</label>
      <input style={inputStyle} placeholder="e.g. Senior Backend Engineer" {...field('title')} />
    </div>
    <div>
      <label style={labelStyle}>Job Description *</label>
      <textarea style={{ ...inputStyle, minHeight: 120, resize: 'vertical' }} placeholder="Full description..." {...field('description')} />
    </div>
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
      <div>
        <label style={labelStyle}>Min. Exp</label>
        <input type="number" style={inputStyle} {...field('min_experience_years')} />
      </div>
      <div>
        <label style={labelStyle}>Degree</label>
        <select style={inputStyle} {...field('required_degree')}>
          {DEGREES.map(d => <option key={d} value={d}>{d}</option>)}
        </select>
      </div>
    </div>
    <div>
      <label style={labelStyle}>Weights (Total: 1.0)</label>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
        <WeightInput label="Skills" fieldKey="weight_skills" field={field} />
        <WeightInput label="Exp" fieldKey="weight_experience" field={field} />
        <WeightInput label="Edu" fieldKey="weight_education" field={field} />
        <WeightInput label="Sem" fieldKey="weight_semantic" field={field} />
      </div>
    </div>
  </div>
);

// --- MAIN PAGE ---
export function HRJobPostingsPage() {
  const toast = useToast();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [showEdit, setShowEdit] = useState(false);
  const [showPipeline, setShowPipeline] = useState(false);
  const [candidates, setCandidates] = useState([]);
  const [saving, setSaving] = useState(false);

  const empty = { title: '', description: '', min_experience_years: 0, required_degree: 'Bachelor', weight_skills: 0.40, weight_experience: 0.30, weight_education: 0.10, weight_semantic: 0.20 };
  const [form, setForm] = useState(empty);

  const load = async () => {
    setLoading(true);
    try {
      const data = await hrGetJobs();
      setJobs(Array.isArray(data) ? data : []);
    } catch { toast('Failed to load jobs', 'error'); }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const handleOpenPipeline = async (job) => {
    setSelected(job);
    setShowPipeline(true);
    try {
      const data = await hrGetJobResults(job.id); 
      setCandidates(Array.isArray(data) ? data : []);
    } catch (err) {
      toast('Failed to load pipeline', 'error');
    }
  };

  const handleCandidateMove = async (candidateId, newStatus) => {
  // 1. Optimistic Update (makes it stay in place)
  const previousCandidates = [...candidates];
  setCandidates(prev => prev.map(c => 
    c.id === candidateId ? { ...c, status: newStatus } : c
  ));

  try {
    // 2. The PATCH call
    await updateSubmissionStatus(candidateId, newStatus);
    toast('Moved to ' + newStatus, 'success');
  } catch (err) {
    // 3. If it fails (like a 400 error from Django), snap it back
    console.error("Move failed:", err.response?.data || err.message);
    setCandidates(previousCandidates);
    toast('Failed to save: ' + (err.response?.data?.status || 'Server Error'), 'error');
  }
};

  const weightsValid = () => {
    const total = +form.weight_skills + +form.weight_experience + +form.weight_education + +form.weight_semantic;
    return Math.abs(total - 1.0) < 0.001;
  };

  const field = (key) => ({ 
    value: form[key], 
    onChange: e => setForm(f => ({ ...f, [key]: e.target.value })) 
  });

  const handleUpdate = async () => {
    setSaving(true);
    try {
      await hrUpdateJob(selected.id, form);
      toast('Job updated');
      setShowEdit(false);
      load();
    } catch { toast('Failed to update', 'error'); }
    setSaving(false);
  };

  if (loading) return <Spinner />;

  return (
    <DndProvider backend={HTML5Backend}>
      <div style={{ maxWidth: 1280, margin: '0 auto', padding: '40px 32px' }}>
        <div style={{ background: 'white', borderRadius: 24, border: '1px solid #EAECF0', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: 'var(--gray-50)' }}>
                {['Title', 'Applicants', 'Status', 'Actions'].map(h => (
                  <th key={h} style={{ padding: '14px 20px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: 'var(--gray-500)', textTransform: 'uppercase' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                  <div 
                    key={job.id} 
                    style={{ 
                      background: 'white', 
                      padding: '24px', 
                      borderRadius: 20, 
                      border: '1px solid #EAECF0',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                  >
                    <div>
                      <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>{job.title}</h3>
                      <p style={{ color: '#667085', fontSize: 14 }}>{job.company_name || 'Empower HR'}</p>
                    </div>

                    {/* --- UPDATED BUTTON LOGIC --- */}
                    <Btn
                      variant={job.has_applied ? "ghost" : "primary"} // Changes look if applied
                      disabled={job.has_applied} // Actually prevents the click
                      onClick={() => handleApply(job.id)}
                      style={{ 
                        minWidth: 140,
                        // Optional: Change cursor to show it's blocked
                        cursor: job.has_applied ? 'not-allowed' : 'pointer',
                        opacity: job.has_applied ? 0.7 : 1
                      }}
                    >
                      {job.has_applied ? (
                        <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <CheckCircle size={16} /> Applied
                        </span>
                      ) : (
                        "Apply Now"
                      )}
                    </Btn>
                  </div>
                ))}
            </tbody>
          </table>
        </div>

        <Modal open={showPipeline} onClose={() => setShowPipeline(false)} title={`Pipeline: ${selected?.title}`} maxWidth={1200}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 16, marginTop: 20 }}>
            <KanbanColumn title="Pending" status="pending" icon={<Users size={16}/>} bgColor="#F9FAFB" candidates={candidates.filter(c => c.status === 'pending')} onDrop={handleCandidateMove} />
            <KanbanColumn title="Shortlisted" status="shortlisted" icon={<Star size={16} className="text-blue-500"/>} bgColor="#EFF6FF" candidates={candidates.filter(c => c.status === 'shortlisted')} onDrop={handleCandidateMove} />
            <KanbanColumn title="In-Progress" status="in-progress" icon={<Clock size={16} className="text-purple-500"/>} bgColor="#F5F3FF" candidates={candidates.filter(c => c.status === 'in-progress')} onDrop={handleCandidateMove} />
            <KanbanColumn title="Rejected" status="rejected" icon={<XCircle size={16} className="text-red-500"/>} bgColor="#FEF2F2" candidates={candidates.filter(c => c.status === 'rejected')} onDrop={handleCandidateMove} />
            <KanbanColumn title="Approved" status="approved" icon={<CheckCircle size={16} className="text-emerald-500"/>} bgColor="#ECFDF5" candidates={candidates.filter(c => c.status === 'approved')} onDrop={handleCandidateMove} />
          </div>
        </Modal>

        <Modal open={showEdit} onClose={() => setShowEdit(false)} title="Edit Job Posting">
           <FormFields form={form} field={field} />
           <Btn onClick={handleUpdate} disabled={saving || !weightsValid()} style={{ marginTop: 20, width: '100%' }}>{saving ? 'Saving...' : 'Save Changes'}</Btn>
        </Modal>
      </div>
    </DndProvider>
  );
}