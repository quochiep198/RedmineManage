import { useState } from "react";
import { api } from "../api/client.js";

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await api.post("/auth/login", { username, password });
      onLogin(response.data.user);
    } catch (err) {
      if (err.response?.status === 401) {
        setError("Username hoặc password không đúng.");
      } else {
        setError("Đã xảy ra lỗi. Vui lòng thử lại.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-layout">
      {/* ── Left Panel — Branding (desktop only) ── */}
      <aside className="login-brand">
        <div className="brand-inner">
          <div className="brand-logo-row">
            <div className="brand-logo">R</div>
            <span className="brand-logo-name">Redmine</span>
          </div>

          <div className="brand-copy">
            <h2 className="brand-headline">
              Quản lý dự án — theo cách của bạn
            </h2>
            <p className="brand-description">
              Truy cập workspace tập trung, theo dõi tiến độ và cộng tác hiệu
              quả cùng team trên mọi nền tảng.
            </p>
          </div>

          <div className="brand-foot">
            <span className="brand-version">Version 0.0.1 Enterprise</span>
            <span className="brand-status">
              <span className="status-dot" />
              Systems Online
            </span>
          </div>
        </div>
      </aside>

      {/* ── Right Panel — Login Form ── */}
      <main className="login-form-panel">
        <div className="login-form-card">
          {/* Mobile logo (visible only on small screens) */}
          <div className="mobile-logo-row">
            <div className="mobile-logo">R</div>
            <span className="mobile-logo-name">Redmine</span>
          </div>

          <div className="form-header">
            <h1>Sign In</h1>
            <p> Truy cập workspace của bạn</p>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            <label className="field-label">
              Login or Email
              <div className="input-icon-wrap">
                <span className="input-icon">👤</span>
                <input
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="admin"
                  autoComplete="username"
                  required
                />
              </div>
            </label>

            <label className="field-label">
              <span className="label-row">
                Password{" "}
                <a href="#" className="forgot-link">
                  Forgot?
                </a>
              </span>
              <div className="input-icon-wrap">
                <span className="input-icon">🔒</span>
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  className="icon-btn toggle-pw"
                  onClick={() => setShowPassword((v) => !v)}
                  tabIndex={-1}
                  aria-label="Toggle password visibility"
                >
                  {showPassword ? "🙈" : "👁"}
                </button>
              </div>
            </label>

            {error && <div className="error-msg">{error}</div>}

            <button type="submit" className="btn-login" disabled={loading}>
              {loading ? "Đang đăng nhập..." : "Log In to Workspace"}
            </button>
          </form>

          <p className="form-footer">
            Don&apos;t have account?{" "}
            <a href="mailto:admin@example.com">Contact admin</a>
          </p>
        </div>
      </main>
    </div>
  );
}