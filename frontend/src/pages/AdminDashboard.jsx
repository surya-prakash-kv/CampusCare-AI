
import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  ClipboardList,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Eye,
  ArrowLeft,
  History,
} from "lucide-react";

import {
  getAdminComplaints,
  getAIOperationsMetrics,
  getPendingAIReviews,
  updateComplaintStatus,
  submitAIReview,
  getComplaintDetails,
  getComplaintHistory,
  getAIReviewHistory,
} from "../services/adminService";
import AppLayout from "../components/layout/AppLayout";

const STATUSES = ["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"];

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

const PRIORITIES = ["LOW", "MEDIUM", "HIGH", "URGENT"];

function formatLabel(value) {
  return value
    ? value.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase())
    : "—";
}

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "—";

  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function getErrorMessage(error) {
  const detail = error.response?.data?.detail;

  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).join(", ");
  }

  return error.response?.status === 403
    ? "You do not have permission to perform this action."
    : "Something went wrong. Please try again.";
}

function MetricCard({ label, value, icon: Icon }) {
  return (
    <article className="admin-metric-card">
      <div className="admin-metric-icon">
        <Icon size={20} />
      </div>
      <p>{label}</p>
      <strong>{value ?? "—"}</strong>
    </article>
  );
}

function AdminDashboard({ onLogout }) {
  const [complaints, setComplaints] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [pendingReviews, setPendingReviews] = useState([]);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [actionError, setActionError] = useState("");
  const [processingId, setProcessingId] = useState(null);

  const [statusDrafts, setStatusDrafts] = useState({});
  const [reviewDrafts, setReviewDrafts] = useState({});

  // Complaint details and history
  const [selectedComplaint, setSelectedComplaint] = useState(null);
  const [complaintHistory, setComplaintHistory] = useState([]);
  const [complaintHistoryError, setComplaintHistoryError] = useState("");
  const [aiReviewHistory, setAIReviewHistory] = useState([]);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");
  const [activeSection, setActiveSection] = useState("overview");

  function handleNavigation(section) {
  setActiveSection(section);

  const sectionIds = {
    complaints: "admin-complaints",
    "ai-reviews": "admin-ai-reviews",
    "ai-operations": "admin-ai-operations",
  };

  if (section === "overview") {
    window.scrollTo({ top: 0, behavior: "smooth" });
    return;
  }

  const targetId = sectionIds[section];

  if (targetId) {
    document.getElementById(targetId)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }
}
  const [aiHistoryError, setAIHistoryError] = useState("");

  const loadDashboard = useCallback(async (showRefresh = false) => {
  if (showRefresh) setRefreshing(true);
  else setLoading(true);

  setError("");

  try {
    const results = await Promise.allSettled([
      getAdminComplaints(),
      getAIOperationsMetrics(),
      getPendingAIReviews(),
    ]);

    const [complaintResult, metricsResult, reviewResult] = results;

    if (complaintResult.status === "fulfilled") {
      setComplaints(complaintResult.value);
    }

    if (metricsResult.status === "fulfilled") {
      setMetrics(metricsResult.value);
    }

    if (reviewResult.status === "fulfilled") {
      setPendingReviews(reviewResult.value);
    }

    const failedResult = results.find(
      (result) => result.status === "rejected"
    );

    if (failedResult) {
      setError(getErrorMessage(failedResult.reason));
      return false;
    }

    return true;
  } catch (err) {
    setError(getErrorMessage(err));
    return false;
  } finally {
    setLoading(false);
    setRefreshing(false);
  }
}, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  async function handleStatusUpdate(complaintId) {
    const newStatus = statusDrafts[complaintId];
    if (!newStatus) return;

    setProcessingId(complaintId);
    setActionMessage("");
    setActionError("");

    try {
      await updateComplaintStatus(complaintId, newStatus);
setActionMessage(`Complaint #${complaintId} status updated.`);

const refreshed = await loadDashboard(true);

if (!refreshed) {
  setActionError(
    "Status was updated successfully, but dashboard refresh failed. Please refresh the dashboard."
  );
  return;
}

// Refresh the currently opened complaint details if applicable.
if (selectedComplaint?.id === complaintId) {
  await openComplaintDetails(complaintId);
}
    } catch (err) {
      setActionError(getErrorMessage(err));
    } finally {
      setProcessingId(null);
    }
  }

  async function handleAIReview(complaintId, decision) {
    const draft = reviewDrafts[complaintId] ?? {
      final_category: "",
      final_priority: "",
      remarks: "",
    };

    if (
      decision === "MODIFIED" &&
      (!draft.final_category || !draft.final_priority)
    ) {
      setActionError("Select both a final category and priority.");
      return;
    }

    setProcessingId(complaintId);
    setActionMessage("");
    setActionError("");

    const payload = {
      decision,
      remarks: draft.remarks.trim() || null,
    };

    if (decision === "MODIFIED") {
      payload.final_category = draft.final_category;
      payload.final_priority = draft.final_priority;
    }

    try {
      await submitAIReview(complaintId, payload);
setActionMessage(`AI review for complaint #${complaintId} submitted.`);

const refreshed = await loadDashboard(true);

if (!refreshed) {
  setActionError(
    "AI review was submitted successfully, but dashboard refresh failed. Please refresh the dashboard."
  );
  return;
}

if (selectedComplaint?.id === complaintId) {
  await openComplaintDetails(complaintId);
}
    } catch (err) {
      setActionError(getErrorMessage(err));
    } finally {
      setProcessingId(null);
    }
  }

  function updateReviewDraft(complaintId, field, value) {
    setReviewDrafts((current) => ({
      ...current,
      [complaintId]: {
        final_category: "",
        final_priority: "",
        remarks: "",
        ...current[complaintId],
        [field]: value,
      },
    }));
  }


async function openComplaintDetails(complaintId) {
  setSelectedComplaint(null);
  setComplaintHistory([]);
  setComplaintHistoryError("");
  setAIReviewHistory([]);
  setDetailError("");
  setAIHistoryError("");
  setDetailLoading(true);

  try {
    const [complaintResult, historyResult] = await Promise.allSettled([
      getComplaintDetails(complaintId),
      getComplaintHistory(complaintId),
    ]);

    if (complaintResult.status === "rejected") {
      throw complaintResult.reason;
    }

    setSelectedComplaint(complaintResult.value);

    if (historyResult.status === "fulfilled") {
      setComplaintHistory(historyResult.value);
    } else {
      setComplaintHistoryError(getErrorMessage(historyResult.reason));
    }

    try {
      const reviews = await getAIReviewHistory(complaintId);
      setAIReviewHistory(reviews);
    } catch (err) {
      setAIHistoryError(getErrorMessage(err));
    }
  } catch (err) {
    setDetailError(getErrorMessage(err));
  } finally {
    setDetailLoading(false);

    requestAnimationFrame(() => {
      document.getElementById("admin-complaint-details")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  }
}

  function closeComplaintDetails() {
    setSelectedComplaint(null);
    setComplaintHistory([]);
    setAIReviewHistory([]);
    setDetailError("");
    setAIHistoryError("");
    setComplaintHistoryError("");
  }

  if (loading) {
  return (
    <AppLayout
      role="ADMIN"
      activeSection={activeSection}
      onNavigate={handleNavigation}
      onLogout={onLogout}
      onRefresh={() => loadDashboard(true)}
      refreshing={refreshing}
    >
      <div className="dashboard-feedback" role="status" aria-live="polite">
        <RefreshCw className="admin-loading-icon" size={22} />
        <p>Loading admin workspace...</p>
      </div>
    </AppLayout>
  );
}

  return (
    <AppLayout
  role="ADMIN"
  activeSection={activeSection}
  onNavigate={handleNavigation}
  onLogout={onLogout}
  onRefresh={() => loadDashboard(true)}
  refreshing={refreshing}
>

      <div className="admin-content">
        <section className="admin-welcome">
          <div>
            <span className="admin-eyebrow">ADMIN WORKSPACE</span>
            <h1>Overview</h1>
            <p>Monitor complaints and manage AI classification reviews.</p>
          </div>

          <div className="admin-welcome-icon">
            <Activity size={28} />
          </div>
        </section>

        {error && (
          <div className="admin-alert admin-alert-error" role="alert">
            <AlertCircle size={18} />
            {error}
            <button type="button" onClick={() => loadDashboard(true)}>
              Retry
            </button>
          </div>
        )}

        {actionMessage && (
          <div className="admin-alert admin-alert-success" role="status">
            <CheckCircle2 size={18} />
            {actionMessage}
          </div>
        )}

        {actionError && (
          <div className="admin-alert admin-alert-error" role="alert">
            <AlertCircle size={18} />
            {actionError}
            <button type="button" onClick={() => setActionError("")}>
              Dismiss
            </button>
          </div>
        )}

        {/* Complaint details and history */}
        {detailLoading && (
          <section className="admin-section">
            <div className="admin-empty-state" role="status" aria-live="polite">
              <RefreshCw className="admin-loading-icon" size={22} />
              <strong>Loading complaint details...</strong>
            </div>
          </section>
        )}

        {detailError && (
          <div className="admin-alert admin-alert-error" role="alert">
            <AlertCircle size={18} />
            {detailError}
            <button type="button" onClick={() => setDetailError("")}>
              Dismiss
            </button>
          </div>
        )}

        {selectedComplaint && !detailLoading && (
          <section
  className="admin-section admin-detail-section"
  id="admin-complaint-details"
>
            <div className="admin-section-heading">
              <div>
                <span className="admin-eyebrow">COMPLAINT DETAILS</span>
                <h2>Complaint #{selectedComplaint.id}</h2>
                <p>Complete complaint information and review history.</p>
              </div>

              <button
                type="button"
                className="admin-detail-back-button"
                onClick={closeComplaintDetails}
              >
                <ArrowLeft size={16} />
                Back to overview
              </button>
            </div>

            <article className="admin-detail-card">
              <div className="admin-detail-header">
                <div>
                  <span className="admin-record-id">
                    COMPLAINT #{selectedComplaint.id}
                  </span>
                  <h3>{selectedComplaint.title}</h3>
                </div>
                <span className={`admin-health admin-health-${selectedComplaint.status.toLowerCase()}`}>
                  {formatLabel(selectedComplaint.status)}
                </span>
              </div>

              <div className="admin-detail-meta">
                <div>
                  <span>Category</span>
                  <strong>{formatLabel(selectedComplaint.category)}</strong>
                </div>
                <div>
                  <span>Priority</span>
                  <strong>{formatLabel(selectedComplaint.priority)}</strong>
                </div>
                <div>
                  <span>Created</span>
                  <strong>{formatDate(selectedComplaint.created_at)}</strong>
                </div>
                <div>
                  <span>Last updated</span>
                  <strong>{formatDate(selectedComplaint.updated_at)}</strong>
                </div>
                <div>
                  <span>Student ID</span>
                  <strong>{selectedComplaint.student_id}</strong>
                </div>
                {selectedComplaint.assigned_admin_id != null && (
                  <div>
                    <span>Assigned admin ID</span>
                    <strong>{selectedComplaint.assigned_admin_id}</strong>
                  </div>
                )}
              </div>

              <div className="admin-detail-description">
                <h4>Description</h4>
                <p>{selectedComplaint.description}</p>
              </div>

              <div className="admin-detail-ai">
  <div className="admin-detail-ai-header">
    <div>
      <h4>AI Classification</h4>
      <p>Automated complaint assessment</p>
    </div>

    <span
      className={`ai-status ai-status-${(
        selectedComplaint.ai_classification_status || "NOT_STARTED"
      ).toLowerCase()}`}
    >
      {formatLabel(
        selectedComplaint.ai_classification_status || "NOT_STARTED"
      )}
    </span>
  </div>

  {selectedComplaint.ai_classification_status === "COMPLETED" ? (
    <div className="admin-detail-ai-content">
      <div>
        <span>Suggested category</span>
        <strong>
          {formatLabel(selectedComplaint.ai_suggested_category)}
        </strong>
      </div>

      <div>
        <span>Suggested priority</span>
        <strong>
          {formatLabel(selectedComplaint.ai_suggested_priority)}
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

      {selectedComplaint.ai_model && (
        <div>
          <span>AI model</span>
          <strong>{selectedComplaint.ai_model}</strong>
        </div>
      )}

      {selectedComplaint.ai_reason && (
        <div className="admin-detail-ai-reason">
          <span>AI explanation</span>
          <p>{selectedComplaint.ai_reason}</p>
        </div>
      )}
    </div>
  ) : (
    <p className="admin-detail-ai-message">
      {selectedComplaint.ai_classification_status === "PENDING"
        ? "AI classification is being processed."
        : selectedComplaint.ai_classification_status === "FAILED"
          ? "AI classification failed. Check AI operations for details."
          : selectedComplaint.ai_classification_status === "SKIPPED"
            ? "AI classification was skipped."
            : "AI classification has not started yet."}
    </p>
  )}
</div>
            </article>

            <article className="admin-detail-card">
              <div className="admin-detail-section-title">
                <History size={19} />
                <div>
                  <h3>Status history</h3>
                  <p>Recorded workflow status changes.</p>
                </div>
              </div>


{complaintHistoryError ? (
  <div className="admin-alert admin-alert-error" role="alert">
    <AlertCircle size={18} />
    {complaintHistoryError}
    <button
      type="button"
      onClick={() => openComplaintDetails(selectedComplaint.id)}
    >
      Retry
    </button>
  </div>
) : complaintHistory.length === 0 ? (
  <div className="admin-empty-state">

                  <p>No status history is available for this complaint.</p>
                </div>
              ) : (
                <div className="admin-history-list">
                  {complaintHistory.map((item) => (
                    <div className="admin-history-item" key={item.id}>
                      <div className="admin-history-marker" />
                      <div className="admin-history-content">
                        <strong>
                          {formatLabel(item.old_status)}{" "}
                          <span aria-hidden="true">→</span>{" "}
                          {formatLabel(item.new_status)}
                        </strong>
                        {item.remarks && <p>{item.remarks}</p>}
                        <span>{formatDate(item.created_at)}</span>
                        <small>Changed by: {item.changed_by}</small>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </article>

            <article className="admin-detail-card">
              <div className="admin-detail-section-title">
                <Sparkles size={19} />
                <div>
                  <h3>AI review history</h3>
                  <p>Recorded administrator decisions on AI classifications.</p>
                </div>
              </div>

              {aiHistoryError && (
                <div className="admin-alert admin-alert-error" role="alert">
                  <AlertCircle size={18} />
                  {aiHistoryError}
                  <button
  type="button"
  onClick={() => openComplaintDetails(selectedComplaint.id)}
>
  Retry
</button>
                </div>
              )}



{!aiHistoryError && aiReviewHistory.length === 0 ? (
  <div className="admin-empty-state">
    <p>No AI review records are available for this complaint.</p>
  </div>
) : !aiHistoryError && aiReviewHistory.length > 0 ? (
  <div className="admin-ai-history-list">
    {aiReviewHistory.map((review) => (
      <div className="admin-ai-history-item" key={review.id}>
        <div className="admin-ai-history-header">
          <strong>{formatLabel(review.decision)}</strong>
          <span>{formatDate(review.reviewed_at)}</span>
        </div>

        <div className="admin-detail-meta">
          <div>
            <span>AI suggested category</span>
            <strong>{formatLabel(review.ai_suggested_category)}</strong>
          </div>
          <div>
            <span>AI suggested priority</span>
            <strong>{formatLabel(review.ai_suggested_priority)}</strong>
          </div>
          <div>
            <span>AI confidence</span>
            <strong>
              {review.ai_confidence == null
                ? "—"
                : `${Math.round(review.ai_confidence * 100)}%`}
            </strong>
          </div>
          <div>
            <span>AI model</span>
            <strong>{review.ai_model || "—"}</strong>
          </div>
          <div>
            <span>Final category</span>
            <strong>{formatLabel(review.final_category)}</strong>
          </div>
          <div>
            <span>Final priority</span>
            <strong>{formatLabel(review.final_priority)}</strong>
          </div>
        </div>

        {review.remarks && (
          <div className="admin-detail-description">
            <h4>Review remarks</h4>
            <p>{review.remarks}</p>
          </div>
        )}
      </div>
    ))}
  </div>
) : null}


            </article>
          </section>
        )}

        <section className="admin-section" id="admin-ai-operations">
          <div className="admin-section-heading">
            <div>
              <h2>AI operations</h2>
              <p>Live classification metrics from the backend</p>
            </div>

            {metrics && (
              <span className={`admin-health admin-health-${metrics.processing_status.toLowerCase()}`}>
                {formatLabel(metrics.processing_status)}
              </span>
            )}
          </div>

          {metrics ? (
            <>
              <div className="admin-metrics-grid">
                <MetricCard label="Total complaints" value={metrics.total_complaints} icon={ClipboardList} />
                <MetricCard label="Not started" value={metrics.not_started} icon={Activity} />
                <MetricCard label="Pending" value={metrics.pending} icon={RefreshCw} />
                <MetricCard label="Completed" value={metrics.completed} icon={CheckCircle2} />
                <MetricCard label="Failed" value={metrics.failed} icon={AlertCircle} />
                <MetricCard label="Skipped" value={metrics.skipped} icon={ShieldCheck} />
              </div>

              <div className="admin-operations-detail">
                <div>
                  <span>Oldest pending age</span>
                  <strong>
                    {metrics.oldest_pending_age_seconds == null
                      ? "No pending attempts"
                      : `${Math.round(metrics.oldest_pending_age_seconds)} seconds`}
                  </strong>
                </div>

                <div>
                  <span>Attempt distribution</span>
                  <div className="admin-attempt-list">
                    {metrics.attempt_distribution.map((item) => (
                      <span key={item.attempt_count}>
                        {item.attempt_count} attempts: <strong>{item.total}</strong>
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </>
          ) : (
            <p className="admin-empty-state">AI metrics are currently unavailable.</p>
          )}
        </section>

        <section className="admin-section" id="admin-ai-reviews">
          <div className="admin-section-heading">
            <div>
              <h2>Pending AI reviews</h2>
              <p>Review AI suggestions before they are accepted or modified.</p>
            </div>
            <span className="admin-count">{pendingReviews.length} pending</span>
          </div>

          {pendingReviews.length === 0 ? (
            <div className="admin-empty-state">
              <Sparkles size={22} />
              <strong>No pending AI reviews</strong>
              <p>There are no completed classifications awaiting review.</p>
            </div>
          ) : (
            <div className="admin-review-list">
              {pendingReviews.map((review) => {
                const draft = reviewDrafts[review.id] ?? {
                  final_category: "",
                  final_priority: "",
                  remarks: "",
                };

                return (
                  <article className="admin-review-card" key={review.id}>
                    <div className="admin-review-header">
                      <div>
                        <span className="admin-record-id">COMPLAINT #{review.id}</span>
                        <h3>{review.title}</h3>
                      </div>
                      <span className="admin-priority">
                        {formatLabel(review.ai_suggested_priority)}
                      </span>
                    </div>

                    <p className="admin-review-description">{review.description}</p>

                    <div className="admin-ai-suggestion">
                      <span>AI suggestion</span>
                      <strong>{formatLabel(review.ai_suggested_category)}</strong>
                      <span>Priority: {formatLabel(review.ai_suggested_priority)}</span>
                      <span>
                        Confidence: {Math.round(review.ai_confidence * 100)}%
                      </span>
                      {review.ai_model && <span>Model: {review.ai_model}</span>}
                    </div>

                    {review.ai_reason && (
                      <p className="admin-ai-reason">{review.ai_reason}</p>
                    )}

                    <div className="admin-review-form">
                      <label>
                        Final category (for modification)
                        <select
                          value={draft.final_category}
                          onChange={(event) =>
                            updateReviewDraft(review.id, "final_category", event.target.value)
                          }
                        >
                          <option value="">Select category</option>
                          {CATEGORIES.map((category) => (
                            <option key={category} value={category}>
                              {formatLabel(category)}
                            </option>
                          ))}
                        </select>
                      </label>

                      <label>
                        Final priority (for modification)
                        <select
                          value={draft.final_priority}
                          onChange={(event) =>
                            updateReviewDraft(review.id, "final_priority", event.target.value)
                          }
                        >
                          <option value="">Select priority</option>
                          {PRIORITIES.map((priority) => (
                            <option key={priority} value={priority}>
                              {formatLabel(priority)}
                            </option>
                          ))}
                        </select>
                      </label>

                      <label className="admin-review-remarks">
                        Review remarks
                        <textarea
                          maxLength={1000}
                          value={draft.remarks}
                          onChange={(event) =>
                            updateReviewDraft(review.id, "remarks", event.target.value)
                          }
                          placeholder="Add optional review remarks..."
                        />
                      </label>
                    </div>

                    <div className="admin-review-actions">
                      <button
                        type="button"
                        className="admin-action-accept"
                        disabled={processingId === review.id}
                        onClick={() => handleAIReview(review.id, "ACCEPTED")}
                      >
                        Accept
                      </button>

                      <button
                        type="button"
                        className="admin-action-modify"
                        disabled={processingId === review.id}
                        onClick={() => handleAIReview(review.id, "MODIFIED")}
                      >
                        Modify
                      </button>

                      <button
                        type="button"
                        className="admin-action-reject"
                        disabled={processingId === review.id}
                        onClick={() => handleAIReview(review.id, "REJECTED")}
                      >
                        Reject
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>

        <section className="admin-section" id="admin-complaints">
          <div className="admin-section-heading">
            <div>
              <h2>All complaints</h2>
              <p>Monitor complaints and update their workflow status.</p>
            </div>
            <span className="admin-count">{complaints.length} records</span>
          </div>

          {complaints.length === 0 ? (
            <div className="admin-empty-state">
              <ClipboardList size={22} />
              <strong>No complaints found</strong>
              <p>Submitted complaints will appear here.</p>
            </div>
          ) : (
            <div className="admin-complaint-list">
              {complaints.map((complaint) => (
                <article className="admin-complaint-card" key={complaint.id}>
                  <div className="admin-complaint-main">
                    <span className="admin-record-id">COMPLAINT #{complaint.id}</span>
                    <h3>{complaint.title}</h3>
                    <p>{complaint.description}</p>

                    <div className="admin-complaint-meta">
  <span>{formatLabel(complaint.category)}</span>
  <span>{formatLabel(complaint.priority)} priority</span>
  <span>{formatDate(complaint.created_at)}</span>
  <span>{formatLabel(complaint.status)}</span>

  <span
    className={`ai-status ai-status-${(
      complaint.ai_classification_status || "NOT_STARTED"
    ).toLowerCase()}`}
  >
    AI: {formatLabel(complaint.ai_classification_status || "NOT_STARTED")}
  </span>
</div>
                  </div>

                  <div className="admin-status-control">
                    <label htmlFor={`status-${complaint.id}`}>Update status</label>

                    <select
                      id={`status-${complaint.id}`}
                      value={statusDrafts[complaint.id] ?? complaint.status}
                      onChange={(event) =>
                        setStatusDrafts((current) => ({
                          ...current,
                          [complaint.id]: event.target.value,
                        }))
                      }
                    >
                      {STATUSES.map((status) => (
                        <option key={status} value={status}>
                          {formatLabel(status)}
                        </option>
                      ))}
                    </select>

                    <button
  type="button"
  aria-label={`Save status for complaint #${complaint.id}`}
  disabled={
    processingId === complaint.id ||
    (statusDrafts[complaint.id] ?? complaint.status) === complaint.status
  }
  onClick={() => handleStatusUpdate(complaint.id)}
>
  Save status
</button>

                    <button
                      type="button"
                      className="admin-view-details-button"
                      aria-label={`View details for complaint #${complaint.id}`}
                      onClick={() => openComplaintDetails(complaint.id)}
                      disabled={detailLoading}
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
            </div>
    </AppLayout>
  );
}

export default AdminDashboard;
