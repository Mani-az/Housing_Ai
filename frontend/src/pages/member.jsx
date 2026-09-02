import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  Building2,
  CalendarDays,
  Clock3,
  CreditCard,
  MapPin,
  UserRound,
  Users,
  X,
} from "lucide-react";
import { API_BASE_URL } from "../api.js";

// Backend amounts use the same project unit shown across the rest of the UI;
// Member-facing labels are تومان (no financial conversion is performed here).
const money = (value) => `${new Intl.NumberFormat("en-US").format(Math.round(Number(value || 0)))} تومان`;
const statusLabel = { paid: "Paid", paid_late: "Paid late", overdue: "Overdue", unpaid: "Unpaid", pending: "Pending" };

export default function Member({ currentAccount }) {
  const memberId = currentAccount?.user_id;
  const nameParts = String(currentAccount?.displayName || "").trim().split(/\s+/).filter(Boolean);
  const [projects, setProjects] = useState([]);
  const [participants, setParticipants] = useState([]);
  const [payments, setPayments] = useState([]);
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [selectedProject, setSelectedProject] = useState(null);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [projectRes, participantRes, paymentRes, requestRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/projects/`),
        axios.get(`${API_BASE_URL}/participants/user/${memberId}`),
        axios.get(`${API_BASE_URL}/payments/user/${memberId}`),
        axios.get(`${API_BASE_URL}/membership-requests/?member_id=${memberId}`),
      ]);
      setProjects(Array.isArray(projectRes.data) ? projectRes.data : []);
      setParticipants(Array.isArray(participantRes.data) ? participantRes.data : []);
      setPayments(Array.isArray(paymentRes.data) ? paymentRes.data : []);
      setRequests(Array.isArray(requestRes.data) ? requestRes.data : []);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not load the member workspace.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (memberId) load();
  }, [memberId]);

  const joinedProjectIds = useMemo(
    () => new Set(participants.map((p) => String(p.project_id))),
    [participants],
  );
  const requestByProject = useMemo(
    () => new Map(requests.map((r) => [String(r.project_id), r])),
    [requests],
  );
  const joinedProjects = projects.filter((p) => joinedProjectIds.has(String(p.id)));
  const availableProjects = projects.filter((p) => !joinedProjectIds.has(String(p.id)));
  const paymentGroups = useMemo(() => {
    const groups = new Map();
    payments.forEach((payment) => {
      const key = `${payment.project_id || ""}-${payment.due_date || payment.id}`;
      const group = groups.get(key) || { ...payment, base: 0, extra: 0, penalty: 0 };
      if (payment.payment_type === "cost_share") group.extra += Number(payment.amount || 0);
      else if (payment.payment_type === "penalty") group.penalty += Number(payment.amount || 0);
      else group.base += Number(payment.amount || 0);
      group.penalty += Number(payment.accrued_penalty_amount || 0);
      groups.set(key, group);
    });
    return Array.from(groups.values());
  }, [payments]);

  async function apply(projectId) {
    setMessage("");
    setError("");
    try {
      await axios.post(`${API_BASE_URL}/membership-requests/`, {
        project_id: Number(projectId),
        member_id: Number(memberId),
      });
      setMessage("Application submitted. It is waiting for the project owner review.");
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not submit the application.");
    }
  }

  function projectProgress(project) {
    return Number(project.payment_progress ?? project.progress ?? 0);
  }

  function requestState(projectId) {
    const request = requestByProject.get(String(projectId));
    const status = String(request?.status || "").toUpperCase();
    return { request, hasActiveRequest: ["PENDING", "APPROVED"].includes(status) };
  }

  return (
    <div className="member-workspace">
      <div className="member-hero presentation-card">
        <div>
          <p className="control-eyebrow">Member dashboard</p>
          <h1>Find your next home</h1>
          <p>Browse available cooperative projects, apply once, then follow your approval and payment status.</p>
        </div>
        <div className="member-profile-chip"><UserRound size={20} /><span>{currentAccount?.displayName || "Member"}</span></div>
      </div>
      {message && <div className="member-notice success">{message}</div>}
      {error && <div className="member-notice error">{error}</div>}

      <section className="presentation-card member-profile">
        <div className="member-section-heading"><div><p className="control-eyebrow">Profile</p><h2>My information</h2></div><UserRound size={28} /></div>
        <div className="member-profile-grid">
          <div><span>First name</span><strong>{nameParts[0] || "—"}</strong></div>
          <div><span>Last name</span><strong>{nameParts.slice(1).join(" ") || "—"}</strong></div>
          <div><span>Phone number</span><strong>{currentAccount?.phone_number || "—"}</strong></div>
          <div><span>Email</span><strong>{currentAccount?.email || "—"}</strong></div>
          <div><span>Account role</span><strong>MEMBER</strong></div>
        </div>
      </section>

      <section>
        <div className="member-section-heading">
          <div><p className="control-eyebrow">Marketplace</p><h2>Available projects</h2><p>Choose a project and send a request; membership starts only after the project owner reviews it.</p></div>
          <Building2 size={30} />
        </div>
        {loading ? <div className="presentation-card member-empty">Loading projects…</div> : (
          <div className="project-market-grid">
            {availableProjects.map((project) => {
              const { request, hasActiveRequest } = requestState(project.id);
              const progress = projectProgress(project);
              const available = project.available_units == null ? Number(project.total_units || 0) : Number(project.available_units);
              return (
                <article className="project-market-card" key={project.id}>
                  <div className="project-market-image"><Building2 size={42} /><span>{project.status || "planning"}</span></div>
                  <div className="project-market-body">
                    <h3>{project.name}</h3>
                    <p className="project-location"><MapPin size={15} /> {project.location || "Tehran"} {project.neighborhood_english ? `• ${project.neighborhood_english}` : ""}</p>
                    <div className="project-progress"><span>Payment progress <b>{Math.round(progress)}%</b></span><div><i style={{ width: `${Math.min(100, Math.max(0, progress))}%` }} /></div></div>
                    <div className="project-market-stats">
                      <span><Users size={15} /><b>{project.total_units || 0}</b> total units</span>
                      <span><Users size={15} /><b>{available}</b> available</span>
                      <span><CreditCard size={15} /><b>{project.payment_plan || "Owner-defined"}</b></span>
                    </div>
                    <div className="project-market-cost">Estimated cost <strong>{money(project.estimated_total_cost)}</strong></div>
                    <div className="project-market-actions">
                      <button className="member-details-button" type="button" onClick={() => setSelectedProject(project)}>View details</button>
                      <button className="member-apply-button" disabled={hasActiveRequest} onClick={() => apply(project.id)}>{request ? (request.status === "PENDING" ? "Pending review" : request.status) : "Apply"}</button>
                    </div>
                  </div>
                </article>
              );
            })}
            {availableProjects.length === 0 && <div className="presentation-card member-empty">No projects are currently available to apply for.</div>}
          </div>
        )}
      </section>

      {joinedProjects.length > 0 && <section className="presentation-card member-my-projects">
        <div className="member-section-heading"><div><p className="control-eyebrow">My projects</p><h2>Approved projects</h2><p>Projects where your membership has been approved by the owner.</p></div><Building2 size={30} /></div>
        <div className="member-joined-project-list">{joinedProjects.map((project) => <div className="member-joined-project" key={project.id}><div><strong>{project.name}</strong><span><MapPin size={14} /> {project.location || "Tehran"}</span></div><div><span>Payment progress</span><b>{Math.round(projectProgress(project))}%</b></div><button className="member-details-button" type="button" onClick={() => setSelectedProject(project)}>View details</button></div>)}</div>
      </section>}

      <section className="presentation-card member-payments">
        <div className="member-section-heading"><div><p className="control-eyebrow">My payments</p><h2>Payment schedule</h2></div><CreditCard size={30} /></div>
        {paymentGroups.length === 0 ? <p className="muted">Payment rows appear after the project owner approves a request and generates a round.</p> : (
          <div className="member-payment-list">{paymentGroups.map((payment) => (
            <div className="member-payment-row" key={`${payment.project_id}-${payment.due_date}`}>
              <div><strong>{payment.description || "Installment"}</strong><span><CalendarDays size={14} /> Due {payment.due_date || "—"}</span></div>
              <div><span>Base Installment</span><strong>{money(payment.base)}</strong><span>Extra Cost Share: {money(payment.extra)}</span></div>
              <div className={`member-status ${payment.status}`}><Clock3 size={14} /> {statusLabel[payment.status] || payment.status}</div>
              <div><span>Penalty: {money(payment.penalty)}</span><strong>Final Amount {money(payment.base + payment.extra + payment.penalty)}</strong></div>
            </div>
          ))}</div>
        )}
      </section>

      {selectedProject && (() => {
        const { request, hasActiveRequest } = requestState(selectedProject.id);
        return <div className="member-details-overlay" role="dialog" aria-modal="true" aria-label={`${selectedProject.name} details`} onClick={() => setSelectedProject(null)}>
          <div className="member-details-modal" onClick={(event) => event.stopPropagation()}>
            <button className="member-details-close" type="button" onClick={() => setSelectedProject(null)} aria-label="Close details"><X size={20} /></button>
            <div className="member-details-modal-icon"><Building2 size={42} /></div>
            <p className="control-eyebrow">Project details</p><h2>{selectedProject.name}</h2>
            <p className="project-location"><MapPin size={15} /> {selectedProject.location || "Tehran"} {selectedProject.neighborhood_english ? `• ${selectedProject.neighborhood_english}` : ""}</p>
            <div className="member-details-grid">
              <div><span>Payment progress</span><strong>{Math.round(projectProgress(selectedProject))}%</strong></div>
              <div><span>Total units</span><strong>{selectedProject.total_units || 0}</strong></div>
              <div><span>Available units</span><strong>{selectedProject.available_units ?? "—"}</strong></div>
              <div><span>Estimated cost</span><strong>{money(selectedProject.estimated_total_cost)}</strong></div>
              <div><span>Status</span><strong>{selectedProject.status || "planning"}</strong></div>
              <div><span>Payment plan</span><strong>{selectedProject.payment_plan || "Owner-defined"}</strong></div>
              <div><span>Start date</span><strong>{selectedProject.start_date || "—"}</strong></div>
              <div><span>Expected end</span><strong>{selectedProject.expected_end_date || "—"}</strong></div>
            </div>
            <button className="member-apply-button member-details-apply" disabled={hasActiveRequest} onClick={() => { apply(selectedProject.id); setSelectedProject(null); }}>{request?.status === "PENDING" ? "Pending review" : request?.status === "APPROVED" ? "Approved" : "Apply to this project"}</button>
          </div>
        </div>;
      })()}
    </div>
  );
}
