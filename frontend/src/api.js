import { mockData } from "./mockData.js";

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

async function request(path, options = {}) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), options.timeout ?? 1800);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`Request failed with ${response.status}`);
    }

    return await response.json();
  } finally {
    window.clearTimeout(timeout);
  }
}

function asArray(value) {
  if (Array.isArray(value)) return value;
  if (Array.isArray(value?.data)) return value.data;
  return [];
}

function normalizeAccount(account) {
  return {
    ...account,
    id: String(account.id),
    displayName: account.displayName || account.full_name || "Project owner",
    roleLabel: account.roleLabel || (account.role === "admin" ? "System administrator" : "Project owner"),
    accessLabel: account.accessLabel || "Assigned project access",
    projectIds: Array.isArray(account.projectIds) ? account.projectIds.map(Number) : account.projectIds,
  };
}

function paymentStatus(payment) {
  if (payment.status) return payment.status;
  if (payment.paid_date && Number(payment.delay_days || 0) > 0) return "paid_late";
  if (payment.paid_date) return "paid";
  // Match the backend's date-only rule: a payment due today is still unpaid,
  // not overdue. Comparing ISO date strings also avoids timezone drift.
  const today = new Date();
  const todayKey = [today.getFullYear(), today.getMonth() + 1, today.getDate()]
    .map((part) => String(part).padStart(2, "0"))
    .join("-");
  return String(payment.due_date || "").slice(0, 10) < todayKey ? "overdue" : "unpaid";
}

function isPenaltyPayment(payment) {
  return String(payment.payment_type || payment.paymentType || "").toLowerCase() === "penalty";
}

function enrichProjects(rawProjects, rawPayments, rawParticipants) {
  return rawProjects.map((project) => {
    const projectPayments = rawPayments.filter((payment) => String(payment.project_id) === String(project.id));
    const collected = projectPayments
      .filter((payment) => !isPenaltyPayment(payment) && ["paid", "paid_late"].includes(paymentStatus(payment)))
      .reduce((sum, payment) => sum + Number(payment.amount || 0), 0);
    const due = projectPayments
      .filter((payment) => !isPenaltyPayment(payment) && paymentStatus(payment) === "overdue")
      .reduce(
        (sum, payment) => sum + Number(payment.amount || 0) + Number(payment.accrued_penalty_amount || 0),
        0,
      );
    const feeCollected = projectPayments
      .filter((payment) => isPenaltyPayment(payment) && ["paid", "paid_late"].includes(paymentStatus(payment)))
      .reduce((sum, payment) => sum + Number(payment.amount || 0), 0);
    const start = project.start_date ? new Date(project.start_date).getTime() : null;
    const end = project.expected_end_date ? new Date(project.expected_end_date).getTime() : null;
    const scheduleProgress = start && end && end > start
      ? Math.min(100, Math.max(0, ((Date.now() - start) / (end - start)) * 100))
      : 0;

    return {
      ...project,
      code: project.code || `PR-${String(project.id).padStart(2, "0")}`,
      collected_amount: project.collected_amount ?? collected,
      due_amount: project.due_amount ?? due,
      fee_collected_amount: project.fee_collected_amount ?? feeCollected,
      payment_progress: project.payment_progress ?? (project.estimated_total_cost
        ? Math.min(100, (collected / Number(project.estimated_total_cost)) * 100)
        : 0),
      build_progress: project.build_progress ?? scheduleProgress,
      members_count: rawParticipants.filter((item) => String(item.project_id) === String(project.id)).length,
      next_milestone: project.next_milestone || "Next construction milestone",
      milestone_date: project.milestone_date || project.expected_end_date,
      roundInfo: project.roundInfo || null,
    };
  });
}

export async function loadWorkspace() {
  const endpoints = [
    ["projects", "/projects/"],
    ["users", "/users/"],
    ["participants", "/participants/"],
    ["payments", "/payments/"],
    ["accounts", "/project-owners/demo-accounts"],
  ];

  const results = await Promise.allSettled(endpoints.map(([, path]) => request(path)));
  const unavailable = [];
  const resolved = {};

  endpoints.forEach(([key], index) => {
    if (results[index].status === "fulfilled") {
      resolved[key] = asArray(results[index].value);
    } else {
      unavailable.push(key);
      resolved[key] = mockData[key];
    }
  });

  const normalizedPayments = resolved.payments.map((payment) => ({
    ...payment,
    status: paymentStatus(payment),
  }));

  const normalizedAccounts = resolved.accounts.map(normalizeAccount);
  const hasAdmin = normalizedAccounts.some((account) => account.role === "admin");

  return {
    projects: enrichProjects(resolved.projects, normalizedPayments, resolved.participants),
    users: resolved.users,
    participants: resolved.participants,
    payments: normalizedPayments,
    accounts: hasAdmin ? normalizedAccounts : [mockData.accounts[0], ...normalizedAccounts],
    owners: unavailable.includes("accounts")
      ? mockData.owners
      : normalizedAccounts
          .filter((account) => account.role === "project_owner")
          .map((account) => ({
            id: account.user_id || account.id,
            full_name: account.displayName,
            email: account.email,
            projectIds: account.projectIds || [],
            status: "active",
            last_seen: "Active account",
          })),
    predictions: mockData.predictions,
    source: unavailable.length === 0 ? "live" : unavailable.length === endpoints.length ? "demo" : "mixed",
    unavailable,
  };
}

export async function markPaymentPaid(paymentId, paidDate) {
  return request(`/payments/${paymentId}/mark-paid`, {
    method: "PATCH",
    body: JSON.stringify({ paid_date: paidDate || null }),
    timeout: 4000,
  });
}

export async function createPayment(payload) {
  return request("/payments/", {
    method: "POST",
    body: JSON.stringify(payload),
    timeout: 4000,
  });
}

export async function createUser(payload) {
  return request("/users/", {
    method: "POST",
    body: JSON.stringify(payload),
    timeout: 4000,
  });
}

export async function assignParticipant(payload) {
  return request("/participants/", {
    method: "POST",
    body: JSON.stringify(payload),
    timeout: 4000,
  });
}

export async function runProjectInsights({ projectId, userIds, months, onProgress }) {
  const jobs = [
    ["economic", `/ml/forecast/economic-indicators?months=${months}`],
    ["delay", `/project-delay/project/${projectId}`],
    ...userIds.map((userId) => [
      `member-${userId}`,
      `/member-risk/project/${projectId}/user/${userId}`,
    ]),
  ];

  const output = { economic: null, delay: null, members: [] };

  for (let index = 0; index < jobs.length; index += 1) {
    const [key, path] = jobs[index];
    onProgress?.({
      progress: Math.round((index / jobs.length) * 100),
      label: key.startsWith("member-") ? "Reviewing member payment readiness" : key === "delay" ? "Reviewing delivery outlook" : "Updating economic outlook",
    });

    const result = await request(path, { timeout: 20_000 });
    if (key === "economic") output.economic = result;
    else if (key === "delay") output.delay = result;
    else output.members.push(result);
  }

  onProgress?.({ progress: 100, label: "Outlook updated" });
  return output;
}
