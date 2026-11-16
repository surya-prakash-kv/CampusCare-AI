import { useEffect, useMemo, useState } from "react";
import {
  FileText,
  Clock3,
  CheckCircle2,
  AlertCircle,
  Plus,
  Send,
  X,
  Eye,
  ArrowLeft,
} from "lucide-react";
import api from "../services/api";
import { logout } from "../services/authService";
import AppLayout from "../components/layout/AppLayout";

const CATEGORIES = [
  "ACADEMIC",
  "EXAMINATION",
  "FEES_FINANCE",
  "SCHOLARSHIP",
  "HOSTEL",
  "FOOD_CANTEEN",
  "TRANSPORT",
  "LIBRARY",
  "LABORATORY",
  "IT_SUPPORT",
  "FACILITIES_MAINTENANCE",
  "ADMINISTRATION",
  "HEALTH_AND_SAFETY",
  "STUDENT_WELFARE",
  "OTHER",
];

function formatCategory(category) {
  return category
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function getErrorMessage(error, fallback) {
  const detail = error.response?.data?.detail;

  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).join(", ");
  }

  return fallback;
}

function StudentDashboard({ student, onLogout }) {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showComplaintForm, setShowComplaintForm] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [selectedComplaint, setSelectedComplaint] = useState(null);
  const [selectedComplaintId, setSelectedComplaintId] = useState(null);
  const [complaintHistory, setComplaintHistory] = useState([]);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");
  const [complaintHistoryError, setComplaintHistoryError] = useState("");
  const [activeSection, setActiveSection] = useState("overview");

async function openComplaintDetails(complaintId) {
  setSelectedComplaintId(complaintId);
  setSelectedComplaint(null);
  setComplaintHistory([]);
  setDetailError("");
  setComplaintHistoryError("");
  setDetailLoading(true);

  const [complaintResult, historyResult] = await Promise.allSettled([
    api.get(`/api/complaints/${complaintId}`),
    api.get(`/api/complaints/${complaintId}/history`),
  ]);

  try {
    if (complaintResult.status === "rejected") {
      throw complaintResult.reason;
    }

    setSelectedComplaint(complaintResult.value.data);

    if (historyResult.status === "fulfilled") {
      setComplaintHistory(historyResult.value.data);
    } else {
      setComplaintHistoryError(
        getErrorMessage(
          historyResult.reason,
          "Unable to load complaint history."
        )
      );
    }
  } catch (err) {
    setDetailError(
      getErrorMessage(
        err,
        "Unable to load complaint details. Please try again."
      )
    );
  } finally {
    setDetailLoading(false);
  }
}

async function loadComplaints() {
    try {
      setLoading(true);
      setError("");
      const response = await api.get("/api/complaints/my");
      setComplaints(response.data);
    } catch (err) {
      setError(
        getErrorMessage(
          err,
          "Unable to load your complaints. Please try again."
        )
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadComplaints();
  }, []);

  const summary = useMemo(
  () => [
    {
      label: "Total complaints",
      value: complaints.length,
      icon: FileText,
    },
    {
      label: "Open",
      value: complaints.filter((item) => item.status === "OPEN").length,
      icon: Clock3,
    },
    {
      label: "In progress",
      value: complaints.filter((item) => item.status === "IN_PROGRESS").length,
      icon: AlertCircle,
    },
    {
      label: "Resolved",
      value: complaints.filter((item) => item.status === "RESOLVED").length,
      icon: CheckCircle2,
    },
  ],
  [complaints]
);

  function handleNavigation(section) {
  setActiveSection(section);

  if (section === "submit") {
  openComplaintForm();

  requestAnimationFrame(() => {
    document
      .getElementById("student-complaint-form")
      ?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
  });

  return;
}

  if (section === "overview") {
    window.scrollTo({ top: 0, behavior: "smooth" });
    return;
  }

  if (section === "complaints") {
    document.getElementById("student-complaints")?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }
}

  function handleLogout() {
    logout();
    onLogout();
  }

  function formatDate(value) {
    return new Date(value).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  }

  function openComplaintForm() {
    setFormError("");
    setSuccessMessage("");
    setShowComplaintForm(true);
  }

  function closeComplaintForm() {
    if (submitting) return;
    setShowComplaintForm(false);
    setFormError("");
  }

  async function handleComplaintSubmit(event) {
    event.preventDefault();
    setFormError("");
    setSuccessMessage("");

    const trimmedTitle = title.trim();
    const trimmedDescription = description.trim();

    if (trimmedTitle.length < 5 || trimmedTitle.length > 200) {
      setFormError("Title must contain between 5 and 200 characters.");
      return;
    }

    if (
      trimmedDescription.length < 10 ||
      trimmedDescription.length > 5000
    ) {
      setFormError("Description must contain between 10 and 5000 characters.");
      return;
    }

    try {
      setSubmitting(true);

      await api.post("/api/complaints", {
        title: trimmedTitle,
        description: trimmedDescription,
        category: category || null,
      });

      setTitle("");
      setDescription("");
      setCategory("");
      setShowComplaintForm(false);
      setSuccessMessage(
        "Your complaint was submitted successfully. AI classification may take a little time."
      );

      await loadComplaints();
    } catch (err) {
      setFormError(
        getErrorMessage(
          err,
          "Unable to submit your complaint. Please try again."
        )
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AppLayout
  role="STUDENT"
  activeSection={activeSection}
  onNavigate={handleNavigation}
  userName={student?.full_name}
  onLogout={handleLogout}
>

      <section className="dashboard-content">
        <div className="dashboard-welcome">
          <div>
            <p className="dashboard-eyebrow">STUDENT WORKSPACE</p>
            <h1>
              Welcome back
              {student?.full_name
                ? `, ${student.full_name.split(" ")[0]}`
                : ""}
            </h1>
            <p>
              Keep track of your campus concerns and their progress.
            </p>
          </div>

          <button
            type="button"
            className="complaint-create-button"
            onClick={openComplaintForm}
          >
            <Plus size={18} />
            Submit complaint
          </button>
        </div>

        {successMessage && (
          <div className="complaint-success" role="status">
            <CheckCircle2 size={18} />
            <span>{successMessage}</span>
            <button
              type="button"
              aria-label="Dismiss success message"
              onClick={() => setSuccessMessage("")}
            >
              <X size={17} />
            </button>
          </div>
        )}

        {showComplaintForm && (
  <section
    className="complaint-form-card"
    id="student-complaint-form"
  >
            <div className="complaint-form-heading">
              <div>
                <h2>Submit a complaint</h2>
                <p>
                  Tell us about your concern. Our team will review it.
                </p>
              </div>

              <button
                type="button"
                className="complaint-close-button"
                onClick={closeComplaintForm}
                disabled={submitting}
                aria-label="Close complaint form"
              >
                <X size={20} />
              </button>
            </div>

            <form
              className="complaint-form"
              onSubmit={handleComplaintSubmit}
            >

<div className="complaint-form-fields">
  <div className="complaint-form-field">
    <label htmlFor="complaint-title">Complaint title</label>
    <input
      id="complaint-title"
      type="text"
      value={title}
      onChange={(event) => setTitle(event.target.value)}
      placeholder="Briefly describe your concern"
      minLength={5}
      maxLength={200}
      required
      disabled={submitting}
    />
    <span className="complaint-field-hint" aria-live="polite">
  {title.length}/200 characters
</span>
  </div>

  <div className="complaint-form-field">
    <label htmlFor="complaint-category">Category</label>
    <select
      id="complaint-category"
      value={category}
      onChange={(event) => setCategory(event.target.value)}
      disabled={submitting}
    >
      <option value="">Select a category (optional)</option>
      {CATEGORIES.map((item) => (
        <option key={item} value={item}>
          {formatCategory(item)}
        </option>
      ))}
    </select>
  </div>

  <div className="complaint-form-field complaint-form-field-full">
    <label htmlFor="complaint-description">Description</label>
    <textarea
      id="complaint-description"
      value={description}
      onChange={(event) => setDescription(event.target.value)}
      placeholder="Provide the details of your complaint..."
      minLength={10}
      maxLength={5000}
      rows={6}
      required
      disabled={submitting}
    />
    <span className="complaint-field-hint" aria-live="polite">
  {description.length}/5000 characters
</span>
  </div>
</div>

              {formError && (
                <p className="dashboard-error" role="alert">
                  {formError}
                </p>
              )}

              <div className="complaint-form-actions">
                <button
                  type="button"
                  className="complaint-cancel-button"
                  onClick={closeComplaintForm}
                  disabled={submitting}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="complaint-create-button"
                  disabled={submitting}
                >
                  <Send size={16} />
                  {submitting ? "Submitting..." : "Submit complaint"}
                </button>
              </div>
            </form>
          </section>
        )}

        <section className="dashboard-summary">
          {summary.map(({ label, value, icon: Icon }) => (
            <article className="summary-card" key={label}>
              <div className="summary-card-top">
                <span>{label}</span>
                <Icon size={19} />
              </div>
              <strong>{loading ? "—" : value}</strong>
            </article>
          ))}
        </section>

        <section
  className="complaints-section"
  id="student-complaints"
>
          <div className="section-heading">
            <div>
              <h2>My complaints</h2>
              <p>View the complaints you have submitted.</p>
            </div>
          </div>

          {loading && (
            <p className="dashboard-feedback" role="status" aria-live="polite">
  Loading your complaints...
</p>
          )}

          {error && (
  <div className="dashboard-error" role="alert">
    <p>{error}</p>
    <button
      type="button"
      onClick={loadComplaints}
    >
      Retry
    </button>
  </div>
)}

          {!loading && !error && complaints.length === 0 && (
            <div className="dashboard-empty">
              <FileText size={30} />
              <h3>No complaints yet</h3>
              <p>Your submitted complaints will appear here.</p>
            </div>
          )}

          {detailLoading && (
  <p className="dashboard-feedback" role="status" aria-live="polite">
  Loading complaint details...
</p>
)}

{detailError && (
  <div className="dashboard-error" role="alert">
    <p>{detailError}</p>

    <button
      type="button"
      onClick={() => openComplaintDetails(selectedComplaintId)}
      disabled={!selectedComplaintId || detailLoading}
    >
      Retry
    </button>

    <button
      type="button"
      onClick={() => setDetailError("")}
    >
      Dismiss
    </button>
  </div>
)}

{selectedComplaint && (
  <article className="complaint-detail-card">
    <button
      type="button"
      className="complaint-back-button"
      onClick={() => {
        setSelectedComplaint(null);
        setComplaintHistory([]);
        setDetailError("");
      }}
    >
      <ArrowLeft size={16} />
      Back to complaints
    </button>

    <div className="complaint-detail-heading">
      <div>
        <span className="dashboard-eyebrow">COMPLAINT DETAILS</span>
        <h2>{selectedComplaint.title}</h2>
      </div>

      <span
        className={`status status-${selectedComplaint.status.toLowerCase()}`}
      >
        {selectedComplaint.status.replace("_", " ")}
      </span>
    </div>

    <div className="complaint-detail-meta">
      <div>
        <span>Complaint ID</span>
        <strong>#{selectedComplaint.id}</strong>
      </div>
      <div>
        <span>Category</span>
        <strong>
          {selectedComplaint.category
            ? formatCategory(selectedComplaint.category)
            : "Uncategorized"}
        </strong>
      </div>
      <div>
        <span>Priority</span>
        <strong>{selectedComplaint.priority}</strong>
      </div>
      <div>
        <span>Submitted</span>
        <strong>{formatDate(selectedComplaint.created_at)}</strong>
      </div>
      <div>
        <span>Last updated</span>
        <strong>{formatDate(selectedComplaint.updated_at)}</strong>
      </div>
    </div>

    <div className="complaint-detail-description">
      <h3>Description</h3>
      <p>{selectedComplaint.description}</p>
    </div>

    <div className="student-ai-insight">
  <div className="student-ai-insight-header">
    <h3>AI Classification</h3>

    <span
      className={`ai-status ai-status-${(
        selectedComplaint.ai_classification_status || "NOT_STARTED"
      ).toLowerCase()}`}
    >
      {(selectedComplaint.ai_classification_status || "NOT_STARTED")
        .replaceAll("_", " ")}
    </span>
  </div>

  {selectedComplaint.ai_classification_status === "COMPLETED" ? (
    <div className="student-ai-insight-content">
      <div>
        <span>Suggested category</span>
        <strong>
          {selectedComplaint.ai_suggested_category
            ? formatCategory(selectedComplaint.ai_suggested_category)
            : "Not available"}
        </strong>
      </div>

      <div>
        <span>Suggested priority</span>
        <strong>
          {selectedComplaint.ai_suggested_priority || "Not available"}
        </strong>
      </div>

      {typeof selectedComplaint.ai_confidence === "number" && (
        <div>
          <span>Confidence</span>
          <strong>
            {(selectedComplaint.ai_confidence * 100).toFixed(1)}%
          </strong>
        </div>
      )}

      {selectedComplaint.ai_reason && (
        <div className="student-ai-reason">
          <span>AI explanation</span>
          <p>{selectedComplaint.ai_reason}</p>
        </div>
      )}
    </div>
  ) : (
    <p className="student-ai-insight-message">
      {selectedComplaint.ai_classification_status === "PENDING"
        ? "AI classification is being processed."
        : selectedComplaint.ai_classification_status === "FAILED"
          ? "AI classification could not be completed."
          : selectedComplaint.ai_classification_status === "SKIPPED"
            ? "AI classification was skipped for this complaint."
            : "AI classification has not started yet."}
    </p>
  )}
</div>

    <div className="complaint-history">
      <h3>Complaint history</h3>

      {complaintHistoryError ? (
  <div className="dashboard-error" role="alert">
    <p>{complaintHistoryError}</p>

    <button
      type="button"
      onClick={() => openComplaintDetails(selectedComplaint.id)}
    >
      Retry
    </button>
  </div>
) : complaintHistory.length === 0 ? (
  <p className="complaint-history-empty">
    No status changes have been recorded yet.
  </p>
) : (
  <div className="complaint-history-list">
    {complaintHistory.map((entry) => (
      <article className="complaint-history-item" key={entry.id}>
        <div className="complaint-history-marker" />

        <div>
          <strong>
            {entry.old_status
              ? entry.old_status.replace("_", " ")
              : "Created"}
            {" → "}
            {entry.new_status.replace("_", " ")}
          </strong>

          {entry.remarks && <p>{entry.remarks}</p>}

          <span>{formatDate(entry.created_at)}</span>
        </div>
      </article>
    ))}
  </div>
)}
    </div>
  </article>
)}

{!detailLoading &&
  !selectedComplaint &&
  !loading &&
  !error &&
  complaints.length > 0 && (
    <div className="complaints-list">
      {complaints.map((complaint) => (
        <article className="complaint-card" key={complaint.id}>
          <div className="complaint-main">
            <h3>{complaint.title}</h3>
            <p>{complaint.description}</p>
            <span>
              {complaint.category
                ? formatCategory(complaint.category)
                : "Uncategorized"}
              {" · "}
              {formatDate(complaint.created_at)}
            </span>
          </div>

          <div className="complaint-meta">
            <span
              className={`status status-${complaint.status.toLowerCase()}`}
            >
              {complaint.status.replace("_", " ")}
            </span>

            <span
  className={`ai-status ai-status-${(
    complaint.ai_classification_status || "NOT_STARTED"
  ).toLowerCase()}`}
>
  AI: {(complaint.ai_classification_status || "NOT_STARTED")
    .replaceAll("_", " ")}
</span>

            <span
              className={`priority priority-${complaint.priority.toLowerCase()}`}
            >
              {complaint.priority}
            </span>

            <button
              type="button"
              className="complaint-view-button"
              onClick={() => openComplaintDetails(complaint.id)}
            >
              <Eye size={15} />
              View details
            </button>
          </div>
        </article>
      ))}
    </div>
  )}
                </section>
      </section>
    </AppLayout>
  );
}

export default StudentDashboard;
