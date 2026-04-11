import { useState, useEffect } from 'react';
import { Spinner, Modal, Btn, useToast } from '../../components/shared/index.jsx';
import { useAuth } from '../../context/AuthContext';
import { getJobPostings, submitResume } from '../../api/index.js';
// ... (imports remain the same)

export function EmployeeCareersPage() {
  const { user } = useAuth();
  const name  = user?.full_name ?? '';
  const email = user?.email ?? '';
  const toast = useToast();

  const [jobs, setJobs]           = useState([]);
  const [loading, setLoading]     = useState(true);
  const [selected, setSelected]   = useState(null);
  const [search, setSearch]       = useState('');
  const [showApply, setShowApply] = useState(false);
  const [file, setFile]           = useState(null);
  const [submitting, setSubmitting] = useState(false);
  
  // Track applied jobs locally to update the UI instantly
  const [submittedJobs, setSubmittedJobs] = useState([]);

  useEffect(() => {
    getJobPostings()
      .then(data => { 
        const activeJobs = Array.isArray(data) ? data.filter(j => j.is_active !== false) : [];
        setJobs(activeJobs); 
      })
      .catch(() => toast('Could not reach API', 'error'))
      .finally(() => setLoading(false));
  }, []);

  const handleApplyClick = (job) => {
    if (!user) {
      toast('Please sign in as a candidate to apply', 'info');
      return;
    }
    // Prevent opening modal if already applied
    if (submittedJobs.includes(job.id)) return;

    setSelected(job);
    setShowApply(true);
  };

  const handleCloseModal = () => {
    setShowApply(false);
    setFile(null);
  };

  const handleApply = async () => {
    if (!file) { toast('Please upload your resume', 'error'); return; }
    
    setSubmitting(true);
    
    const fd = new FormData();
    fd.append('job', selected.id);
    fd.append('resume_file', file);
    fd.append('candidate_name', name);
    fd.append('candidate_email', email);

    try {
      await submitResume(fd);
      
      // Success: mark as applied locally and close modal
      setSubmittedJobs([...submittedJobs, selected.id]);
      toast('Application submitted successfully!', 'success');
      handleCloseModal(); 
    } catch (e) { 
      toast('Submission Error: ' + e.message, 'error'); 
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ background: 'var(--gray-25)', minHeight: '100vh' }}>
      {/* ... Hero Section remains the same ... */}

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '48px 32px', display: 'grid', gridTemplateColumns: '1fr 360px', gap: 32, alignItems: 'start' }}>
        
        {/* Job List */}
        <div>
          <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 20 }}>Available Positions ({jobs.length})</h3>
          {loading ? (
            <div style={{ padding: 60, textAlign: 'center' }}><Spinner /></div>
          ) : (
            <div style={{ display: 'grid', gap: 16 }}>
              {jobs.filter(j => j.title.toLowerCase().includes(search.toLowerCase())).map(j => {
                const isApplied = submittedJobs.includes(j.id);
                return (
                  <div 
                    key={j.id} 
                    onClick={() => setSelected(j)}
                    style={{
                      background: 'var(--white)', padding: 24, borderRadius: 20, cursor: 'pointer',
                      border: `2px solid ${selected?.id === j.id ? 'var(--red)' : 'transparent'}`,
                      boxShadow: '0 2px 8px rgba(0,0,0,0.04)', transition: '0.2s',
                      opacity: isApplied ? 0.7 : 1
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <h4 style={{ fontWeight: 700, fontSize: 18 }}>{j.title}</h4>
                      {isApplied && <span style={{ color: '#22C55E', fontWeight: 700, fontSize: 13 }}>✓ Applied</span>}
                    </div>
                    <p style={{ fontSize: 14, color: 'var(--gray-500)', marginTop: 8 }}>{j.description}</p>
                    <div style={{ marginTop: 16, display: 'flex', justifyContent: 'flex-end' }}>
                      <Btn 
                        size="sm" 
                        variant={isApplied ? "ghost" : "primary"}
                        disabled={isApplied}
                        onClick={(e) => { e.stopPropagation(); handleApplyClick(j); }}
                      >
                        {isApplied ? "Applied" : "Apply Now"}
                      </Btn>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Sidebar */}
        <aside style={{ position: 'sticky', top: 32 }}>
          {selected && (
            <div style={{ background: 'var(--white)', padding: 28, borderRadius: 24, border: '1px solid #EAECF0' }}>
              <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 12 }}>{selected.title}</h2>
              <Btn 
                onClick={() => handleApplyClick(selected)} 
                disabled={submittedJobs.includes(selected.id)}
                style={{ width: '100%' }}
              >
                {submittedJobs.includes(selected.id) ? "Already Applied" : "Submit Application"}
              </Btn>
            </div>
          )}
        </aside>
      </div>

      {/* Simplified Modal - No results displayed */}
      <Modal open={showApply} onClose={handleCloseModal} title={`Apply for ${selected?.title}`} maxWidth={400}>
        <div 
          onClick={() => document.getElementById('resume-upload').click()}
          style={{ padding: '40px 20px', border: '2px dashed #EAECF0', borderRadius: 16, textAlign: 'center', cursor: 'pointer', background: 'var(--gray-50)', marginBottom: 20 }}
        >
          <input type="file" id="resume-upload" hidden accept=".pdf" onChange={(e) => setFile(e.target.files[0])} />
          <div style={{ fontSize: 14, fontWeight: 600 }}>{file ? file.name : "Upload PDF Resume"}</div>
        </div>
        <Btn onClick={handleApply} disabled={submitting} style={{ width: '100%' }}>
          {submitting ? "Submitting..." : "Send Application"}
        </Btn>
      </Modal>
    </div>
  );
}