import { useEffect, useState } from "react";
import axios from "axios";
import { API_BASE_URL } from "../api.js";

export default function MembershipRequests({ currentAccount }) {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/membership-requests/?owner_user_id=${currentAccount?.user_id}`);
      setRequests(Array.isArray(response.data) ? response.data : []);
    }
    catch (err) { setError(err.response?.data?.detail || "Could not load membership requests."); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);

  async function review(requestId, status) {
    try { await axios.put(`${API_BASE_URL}/membership-requests/${requestId}/review`, { status, reviewed_by: currentAccount?.user_id || null, rejection_reason: status === "REJECTED" ? "Rejected by project owner during review" : null }); await load(); }
    catch (err) { setError(err.response?.data?.detail || "Could not review this request."); }
  }

  return <div className="membership-review-page"><div className="presentation-card"><p className="control-eyebrow">Owner workflow</p><h1>Membership Requests</h1><p className="muted">Review applications for your projects before a member is added. Risk is a transparent snapshot of prior payment history.</p></div>{error && <div className="member-notice error">{error}</div>}{loading ? <div className="presentation-card member-empty">Loading requests…</div> : requests.length === 0 ? <div className="presentation-card member-empty">No membership requests for your projects yet.</div> : <div className="membership-request-grid">{requests.map((request) => { const risk = request.risk_level || request.risk_snapshot || "NEW"; const reasons = Array.isArray(request.reasons) ? request.reasons : []; return <article className="presentation-card membership-request-card" key={request.id}><div className="membership-request-header"><div><h2>{request.member_name || `Member #${request.member_id}`}</h2><p>{request.member_email || ""}</p><strong>{request.project_name || `Project #${request.project_id}`}</strong></div><span className={`risk-pill ${String(risk).toLowerCase()}`}>{risk}</span></div><div className="risk-grid"><div><span>Previous Projects</span><b>{request.has_history ? request.previous_projects ?? 0 : "No history"}</b></div><div><span>Late Payments</span><b>{request.has_history ? request.late_payments ?? 0 : "—"}</b></div><div><span>Overdue Payments</span><b>{request.has_history ? request.overdue_payments ?? 0 : "—"}</b></div><div><span>Risk Score</span><b>{request.has_history ? `${request.risk_score ?? 0}/100` : "—"}</b></div></div><p className="risk-reasons">{request.has_history ? `Reasons: ${reasons.join(", ") || "On-time history"}` : "No previous history available"}</p><div className="membership-request-footer"><span className={`request-status ${String(request.status).toLowerCase()}`}>{request.status}</span>{request.status === "PENDING" && <div><button className="approve-button" onClick={() => review(request.id, "APPROVED")}>Accept</button><button className="reject-button" onClick={() => review(request.id, "REJECTED")}>Reject</button></div>}</div></article>; })}</div>}</div>;
}
