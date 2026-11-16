
import { useState } from "react";
import {
  login,
  registerStudent,
  getCurrentStudent,
  getSessionRole,
} from "../services/authService";

function AuthPage({ onAuthenticated }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  function updateField(event) {
    setForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  }

  function switchMode(nextMode) {
    setMode(nextMode);
    setError("");
    setSuccess("");
    setForm({ full_name: "", email: "", password: "" });
  }

  function getErrorMessage(err) {
    const detail = err.response?.data?.detail;

    if (Array.isArray(detail)) {
      return detail.map((item) => item.msg).join(", ");
    }

    return detail || "Something went wrong. Please try again.";
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      if (mode === "register") {
        const result = await registerStudent(form);

        setSuccess(
          result.message || "Registration successful. You can now sign in."
        );
        setMode("login");
        setForm({
          full_name: "",
          email: form.email,
          password: "",
        });
        return;
      }

      await login(form.email, form.password);

      const role = getSessionRole();

      if (role === "STUDENT") {
        const student = await getCurrentStudent();
        onAuthenticated?.({ role, student });
      } else if (role === "ADMIN") {
        onAuthenticated?.({ role, student: null });
      } else {
        throw new Error("Your account has an unsupported role.");
      }
    } catch (err) {
      setError(
        err.response
          ? getErrorMessage(err)
          : err.message || "Unable to connect to the server."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-panel">
        <div className="auth-brand">
          <div className="auth-brand-mark">C</div>
          <span>CampusCare AI</span>
        </div>

        <div className="auth-content">
          <p className="auth-eyebrow">STUDENT SUPPORT PLATFORM</p>

          <h1>
            {mode === "login"
              ? "Welcome back"
              : "Create your account"}
          </h1>

          <p className="auth-description">
            {mode === "login"
              ? "Sign in to manage your campus concerns and track their progress."
              : "Join CampusCare to submit concerns and stay updated on their progress."}
          </p>

          <div className="auth-tabs">
            <button
              type="button"
              className={mode === "login" ? "active" : ""}
              aria-pressed={mode === "login"}
              onClick={() => switchMode("login")}
            >
              Sign in
            </button>

            <button
              type="button"
              className={mode === "register" ? "active" : ""}
              aria-pressed={mode === "register"}
              onClick={() => switchMode("register")}
            >
              Create account
            </button>
          </div>

          {error && (
            <div className="auth-message auth-error" role="alert">
              {error}
            </div>
          )}

          {success && (
            <div className="auth-message auth-success" role="status">
              {success}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {mode === "register" && (
              <div className="auth-field">
                <label htmlFor="full_name">Full name</label>
                <input
                  id="full_name"
                  name="full_name"
                  type="text"
                  placeholder="Enter your full name"
                  value={form.full_name}
                  onChange={updateField}
                  minLength={2}
                  maxLength={100}
                  autoComplete="name"
                  required
                />
              </div>
            )}

            <div className="auth-field">
              <label htmlFor="email">Email address</label>
              <input
                id="email"
                name="email"
                type="email"
                placeholder="you@example.com"
                value={form.email}
                onChange={updateField}
                autoComplete="email"
                required
              />
            </div>

            <div className="auth-field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                name="password"
                type="password"
                placeholder="Enter your password"
                value={form.password}
                onChange={updateField}
                minLength={8}
                maxLength={128}
                autoComplete={
                  mode === "login" ? "current-password" : "new-password"
                }
                required
              />
              {mode === "register" && (
                <span className="auth-hint">
                  Use at least 8 characters.
                </span>
              )}
            </div>

            <button
              className="auth-submit"
              type="submit"
              disabled={loading}
            >
              {loading
                ? "Please wait..."
                : mode === "login"
                  ? "Sign in"
                  : "Create account"}
            </button>
          </form>

          <p className="auth-footer">
            By continuing, you agree to use CampusCare responsibly.
          </p>
        </div>
      </section>

      <aside className="auth-visual">
        <div className="auth-visual-content">
          <span className="auth-visual-tag">YOUR CAMPUS. YOUR VOICE.</span>
          <h2>
            Better campus experiences start with being heard.
          </h2>
          <p>
            Raise concerns, follow updates, and stay connected with
            your campus support team — all in one place.
          </p>
        </div>
        <div className="auth-visual-footer">
          CampusCare AI · Student Complaint Management
        </div>
      </aside>
    </main>
  );
}

export default AuthPage;
