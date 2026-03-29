import { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { changePassword } from "../../api/index";

export function EmployeeProfilePage() {
  const { user, logout } = useAuth();

  const [form, setForm]       = useState({ old_password: "", new_password: "", confirm_password: "" });
  const [error, setError]     = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) =>
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(""); setSuccess("");

    if (form.new_password !== form.confirm_password) {
      setError("New passwords do not match.");
      return;
    }
    if (form.new_password.length < 8) {
      setError("New password must be at least 8 characters.");
      return;
    }

    setLoading(true);
    try {
      await changePassword({
        old_password: form.old_password,
        new_password: form.new_password,
      });
      setSuccess("Password changed successfully.");
      setForm({ old_password: "", new_password: "", confirm_password: "" });
    } catch (err) {
      const data = err?.data ?? err?.response?.data;
      const msg  = data?.old_password?.[0] ?? data?.detail ?? "Failed to change password.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="profile-page">

      {/* Profile header */}
      <div className="profile-header">
        <div className="profile-avatar">
          {user?.full_name?.charAt(0).toUpperCase() ?? "?"}
        </div>
        <div className="profile-info">
          <h2>{user?.full_name}</h2>
          <p>{user?.email}</p>
          <span className="role-badge">{user?.role}</span>
        </div>
      </div>

      {/* Change password card */}
      <div className="profile-card">
        <h3>Change Password</h3>
        <p className="profile-card-subtitle">
          Choose a strong password you don't use elsewhere.
        </p>

        <form onSubmit={handleSubmit} className="login-form">
          {error   && <div className="login-error">{error}</div>}
          {success && <div className="login-success">{success}</div>}

          <div className="form-group">
            <label htmlFor="old_password">Current Password</label>
            <input
              id="old_password"
              type="password"
              name="old_password"
              value={form.old_password}
              onChange={handleChange}
              placeholder="••••••••"
              required
              autoComplete="current-password"
            />
          </div>

          <div className="form-group">
            <label htmlFor="new_password">New Password</label>
            <input
              id="new_password"
              type="password"
              name="new_password"
              value={form.new_password}
              onChange={handleChange}
              placeholder="••••••••"
              required
              minLength={8}
              autoComplete="new-password"
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirm_password">Confirm New Password</label>
            <input
              id="confirm_password"
              type="password"
              name="confirm_password"
              value={form.confirm_password}
              onChange={handleChange}
              placeholder="••••••••"
              required
              autoComplete="new-password"
            />
          </div>

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Updating..." : "Update Password"}
          </button>
        </form>
      </div>

      {/* Sign out */}
      <div className="profile-card">
        <h3>Session</h3>
        <p className="profile-card-subtitle">Sign out of your account on this device.</p>
        <button className="btn-danger" onClick={logout}>
          Sign Out
        </button>
      </div>

    </div>
  );
}
