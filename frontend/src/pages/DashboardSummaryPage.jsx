import { useEffect, useState } from "react";

import { api, LONG_RUNNING_REQUEST_TIMEOUT_MS } from "../api/client.js";

const emptyFilters = {
  from_date: "",
  to_date: "",
  group_by: "day",
};

function maxCount(items) {
  return items.reduce((max, item) => Math.max(max, item.count), 0) || 1;
}

function barWidth(count, max) {
  return `${Math.max(8, Math.round((count / max) * 100))}%`;
}

function formatGroupLabel(value) {
  return value === "week" ? "Week" : "Day";
}

function buildParams(filters) {
  const params = { group_by: filters.group_by };
  if (filters.from_date) {
    params.from_date = filters.from_date;
  }
  if (filters.to_date) {
    params.to_date = filters.to_date;
  }
  return params;
}

function MetricCard({ label, value }) {
  return (
    <div className="stat-card">
      <p>{label}</p>
      <h3>{value}</h3>
    </div>
  );
}

function formatWarningType(value) {
  switch (value) {
    case "high_priority_not_in_progress":
      return "High priority not in progress";
    case "high_priority_late":
      return "High priority overdue";
    case "overdue":
      return "Overdue";
    default:
      return value;
  }
}

function HealthBadge({ value }) {
  return <span className={`health-badge ${value}`}>{value}</span>;
}

function DistributionCard({ title, items, labelKey }) {
  const max = maxCount(items);
  return (
    <section className="panel dashboard-chart-panel">
      <h2>{title}</h2>
      {items.length ? (
        <div className="distribution-list">
          {items.map((item) => (
            <div className="distribution-row" key={`${labelKey}-${item[labelKey]}-${item.count}`}>
              <div className="distribution-head">
                <span>{item[labelKey]}</span>
                <strong>{item.count}</strong>
              </div>
              <div className="distribution-track">
                <div className="distribution-bar" style={{ width: barWidth(item.count, max) }} />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="muted-copy">No data available.</p>
      )}
    </section>
  );
}

export default function DashboardSummaryPage({ dbStatus }) {
  const [filters, setFilters] = useState(emptyFilters);
  const [draftFilters, setDraftFilters] = useState(emptyFilters);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    async function loadSummary() {
      setLoading(true);
      setError("");
      try {
        const res = await api.get("/dashboard/summary", {
          params: buildParams(filters),
        });
        setData(res.data);
      } catch (err) {
        setError(err.response?.data?.detail || "Could not load dashboard summary.");
      } finally {
        setLoading(false);
      }
    }

    loadSummary();
  }, [filters, refreshKey]);

  function handleChange(event) {
    const { name, value } = event.target;
    setDraftFilters((current) => ({ ...current, [name]: value }));
  }

  function applyFilters() {
    setSuccess("");
    setFilters(draftFilters);
  }

  async function syncIssues() {
    setSyncing(true);
    setError("");
    setSuccess("");
    try {
      const res = await api.post("/dashboard/sync-issues", {}, {
        timeout: LONG_RUNNING_REQUEST_TIMEOUT_MS,
      });
      setSuccess(
        `Synced ${res.data.total_synced} issues (${res.data.created} created, ${res.data.updated} updated).`,
      );
      setRefreshKey((current) => current + 1);
    } catch (err) {
      if (err.code === "ECONNABORTED") {
        setError("Sync request timed out in the browser. The backend may still be processing.");
      } else {
        setError(err.response?.data?.message || err.response?.data?.detail || "Could not sync issues.");
      }
    } finally {
      setSyncing(false);
    }
  }

  const trendMax =
    data?.trend?.reduce((max, item) => Math.max(max, item.total_issues), 0) || 1;

  return (
    <section className="dashboard-summary">
      <section className="panel dashboard-filter-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Current Project</p>
            <h2>{data?.project?.name ?? "Not synced yet"}</h2>
          </div>
        </div>

        <div className="dashboard-filter-grid">
          <label className="field-label">
            From date
            <input name="from_date" type="date" value={draftFilters.from_date} onChange={handleChange} />
          </label>
          <label className="field-label">
            To date
            <input name="to_date" type="date" value={draftFilters.to_date} onChange={handleChange} />
          </label>
          <label className="field-label">
            Trend group
            <select name="group_by" value={draftFilters.group_by} onChange={handleChange}>
              <option value="day">Day</option>
              <option value="week">Week</option>
            </select>
          </label>
        </div>

        <div className="connection-actions">
          <button className="primary-action" type="button" onClick={applyFilters}>
            Apply
          </button>
          <button className="secondary" type="button" onClick={syncIssues} disabled={syncing}>
            {syncing ? "Syncing..." : "Sync Issues"}
          </button>
        </div>

        <p className="muted-copy">
          Dashboard reads only from local synced data and filters by
          {" "}
          <strong>{data?.date_range?.field ?? "redmine_updated_on"}</strong>.
        </p>
      </section>

      {error ? <div className="error-msg">{error}</div> : null}
      {success ? <div className="success-msg">{success}</div> : null}

      {loading ? (
        <section className="panel">
          <p className="muted-copy">Loading dashboard summary...</p>
        </section>
      ) : (
        <>
          <section className="grid">
            <MetricCard label="Total Issues" value={data?.total_issues ?? 0} />
            <MetricCard label="Open Issues" value={data?.open_issues ?? 0} />
            <MetricCard label="Closed Issues" value={data?.closed_issues ?? 0} />
            <MetricCard label="Overdue Issues" value={data?.overdue_issues ?? 0} />
          </section>

          <section className="panel dashboard-health-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Project Health</p>
                <h2>Current Health</h2>
              </div>
              <HealthBadge value={data?.project_health?.health_status ?? "healthy"} />
            </div>

            <div className="dashboard-health-grid">
              <div className="dashboard-health-stat">
                <span>Completed Early</span>
                <strong>{data?.project_health?.completed_early_count ?? 0}</strong>
              </div>
              <div className="dashboard-health-stat">
                <span>At Risk Tasks</span>
                <strong>{data?.project_health?.at_risk_task_count ?? 0}</strong>
              </div>
              <div className="dashboard-health-stat">
                <span>High Priority Alerts</span>
                <strong>{data?.project_health?.high_priority_alert_count ?? 0}</strong>
              </div>
            </div>

            <div className="dashboard-warning-list">
              <h3>Warning List</h3>
              {data?.project_health?.health_warnings?.length ? (
                data.project_health.health_warnings.map((warning) => (
                  <div className="dashboard-warning-item" key={`${warning.redmine_issue_id}-${warning.warning_type}`}>
                    <div>
                      <strong>#{warning.redmine_issue_id} {warning.subject}</strong>
                      <p>
                        {warning.priority_name || "No priority"} / {warning.status_name || "Unknown status"}
                        {warning.due_date ? ` / due ${warning.due_date}` : ""}
                      </p>
                    </div>
                    <span className="warning-tag">{formatWarningType(warning.warning_type)}</span>
                  </div>
                ))
              ) : (
                <p className="muted-copy">No active warnings.</p>
              )}
            </div>
          </section>

          <section className="dashboard-chart-grid">
            <DistributionCard title="Issues by Status" items={data?.by_status ?? []} labelKey="status_name" />
            <DistributionCard
              title="Issues by Priority"
              items={data?.by_priority ?? []}
              labelKey="priority_name"
            />
            <DistributionCard
              title="Issues by Assignee"
              items={data?.by_assignee ?? []}
              labelKey="assignee_name"
            />
          </section>

          <section className="panel dashboard-chart-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Trend</p>
                <h2>Issue Trend by {formatGroupLabel(filters.group_by)}</h2>
              </div>
            </div>
            {data?.trend?.length ? (
              <div className="trend-list">
                {data.trend.map((item) => (
                  <div className="trend-row" key={item.bucket}>
                    <div className="trend-meta">
                      <strong>{item.label}</strong>
                      <span>
                        {item.total_issues} total / {item.open_issues} open / {item.closed_issues} closed
                      </span>
                    </div>
                    <div className="distribution-track">
                      <div className="distribution-bar" style={{ width: barWidth(item.total_issues, trendMax) }} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="muted-copy">No trend data available.</p>
            )}
          </section>
        </>
      )}
    </section>
  );
}
