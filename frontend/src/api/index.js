
import axios from 'axios';

const BASE = 'http://127.0.0.1:8000/api';

const authHeaders = () => {
  const token = localStorage.getItem('access');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

export const api = {
  get:    (url)       => fetch(`${BASE}${url}`, { headers: authHeaders() }).then(r => r.json()),
  post:   (url, data) => fetch(`${BASE}${url}`, { method: 'POST',   headers: authHeaders(), body: JSON.stringify(data) }).then(r => r.json()),
  put:    (url, data) => fetch(`${BASE}${url}`, { method: 'PUT',    headers: authHeaders(), body: JSON.stringify(data) }).then(r => r.json()),
  delete: (url)       => fetch(`${BASE}${url}`, { method: 'DELETE', headers: authHeaders() }),
  patch:  (url, data) => fetch(`${BASE}${url}`, { method: 'PATCH',  headers: authHeaders(), body: JSON.stringify(data) }).then(r => r.json()),
};

// Auth
export const login  = (email, password) => fetch(`${BASE}/auth/login/`, {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
}).then(r => r.json());

export const logout = (refresh) => api.post('/auth/logout/', { refresh });

// Employee
export const getForms        = (employeeID) => api.get(`/feedback/forms/?employee_id=${employeeID}`);
export const getFormDetail   = (formID, employeeID) => api.get(`/feedback/forms/${formID}/?employee_id=${employeeID}`);
export const submitFeedback  = (formID, data) => api.post(`/feedback/forms/${formID}/submit/`, data);
//cd export const changePassword = (data) => api.post('/auth/change-password/', data);

// HR Manager -- Forms
export const hrGetForms      = ()          => api.get('/feedback/hr/forms/');
export const hrCreateForm    = (data)      => api.post('/feedback/hr/forms/', data);
export const hrUpdateForm    = (id, data)  => api.put(`/feedback/hr/forms/${id}/`, data);
export const hrDeleteForm    = (id)        => api.delete(`/feedback/hr/forms/${id}/`);
export const hrActivateForm  = (id)        => api.post(`/feedback/hr/forms/${id}/activate/`, {});
export const hrDeactivateForm= (id)        => api.post(`/feedback/hr/forms/${id}/deactivate/`, {});


// HR Manager -- Questions
export const hrGetQuestions    = (formID)        => api.get(`/feedback/hr/forms/${formID}/questions/`);
export const hrAddQuestion     = (formID, data)  => api.post(`/feedback/hr/forms/${formID}/questions/`, data);
export const hrUpdateQuestion  = (qID, data)     => api.put(`/feedback/hr/questions/${qID}/`, data);
export const hrDeleteQuestion  = (qID)           => api.delete(`/feedback/hr/questions/${qID}/`);

// HR Manager -- Submissions
export const hrGetSubmissions  = (formID) => api.get(`/feedback/hr/submissions/${formID ? `?form_id=${formID}` : ''}`);


// Attrition
export const runPrediction     = (formID)  => api.post('/attrition/run/', formID ? { form_id: formID } : {});
export const getPredictions    = ()        => api.get('/attrition/predictions/latest/');

// --- HR Manager --Job Postings ---
export const hrGetJobs         = () => api.get('/resume_pipeline/jobs/');
export const hrCreateJob      = (data) => api.post('/resume_pipeline/jobs/', data);
export const hrUpdateJob      = (id, data) => api.put(`/resume_pipeline/jobs/${id}/`, data);
export const hrUpdateWeights  = (id, data) => api.put(`/resume_pipeline/jobs/${id}/weights/`, data);
export const hrGetJobResults  = (id) => api.get(`/resume_pipeline/jobs/${id}/submissions/`);
export const updateSubmissionStatus = (id, status) => 
  api.patch(`/resume_pipeline/submissions/${id}/`, { status })


// --- Candidate -- Resume Submission ---
// Example helper update
// api/index.js
export const getJobPostings = () => 
  api.get('/resume_pipeline/jobs/');

export const submitResume = (formData) => {
  const token = localStorage.getItem('access'); // Matches your authHeaders() logic

  return fetch(`${BASE}/resume_pipeline/submit/`, {
    method: 'POST',
    headers: {
      // We skip 'Content-Type' so the browser handles the boundary
      'Authorization': token ? `Bearer ${token}` : '',
    },
    body: formData, // Send the raw object, NO JSON.stringify
  }).then((r) => r.json());
};


// Auth
export const loginUser           = (data) => api.post('/auth/login/', data);
export const logoutUser          = (refresh) => api.post('/auth/logout/', { refresh });
export const refreshToken        = (refresh) => api.post('/auth/token/refresh/', { refresh });
export const getMe               = () => api.get('/auth/me/');
export const registerCandidate   = (data) => api.post('/auth/candidate/register/', data);
export const changePassword      = (data) => api.post('/auth/change-password/', data);
