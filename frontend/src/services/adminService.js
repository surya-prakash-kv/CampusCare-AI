
import api from "./api";

export async function getAdminComplaints() {
  const response = await api.get("/api/complaints/admin/all");
  return response.data;
}

export async function getAIOperationsMetrics() {
  const response = await api.get("/api/admin/ai-operations/metrics");
  return response.data;
}

export async function getPendingAIReviews() {
  const response = await api.get("/api/complaints/admin/ai-review/pending");
  return response.data;
}

export async function updateComplaintStatus(complaintId, status, remarks = null) {
  const response = await api.patch(
    `/api/complaints/admin/${complaintId}/status`,
    { status, remarks }
  );
  return response.data;
}

export async function submitAIReview(complaintId, reviewData) {
  const response = await api.post(
    `/api/complaints/admin/${complaintId}/ai-review`,
    reviewData
  );
  return response.data;
}

export async function getAIReviewHistory(complaintId) {
  const response = await api.get(
    `/api/complaints/admin/${complaintId}/ai-review/history`
  );
  return response.data;
}

export async function getComplaintDetails(complaintId) {
  const response = await api.get(`/api/complaints/${complaintId}`);
  return response.data;
}

export async function getComplaintHistory(complaintId) {
  const response = await api.get(`/api/complaints/${complaintId}/history`);
  return response.data;
}