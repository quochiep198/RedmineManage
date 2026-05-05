import { useEffect, useState } from "react";

import { api, LONG_RUNNING_REQUEST_TIMEOUT_MS } from "../api/client.js";

const emptyFilters = {
  from_date: "",
  to_date: "",
  group_by: "week",
};

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

function HealthBadge({ value }) {
  return <span className={`health-badge ${String(value || "").toLowerCase()}`}>{value}</span>;
}

function trendLabel(direction, value) {
  if (value == null) {
    return "No previous snapshot";
  }
  const prefix = value > 0 ? "+" : "";
  if (direction === "up") {
    return `${prefix}${value} up`;
  }
  if (direction === "down") {
    return `${value} down`;
  }
  return `${value} flat`;
}

function warningTag(level) {
  return <span className={`warning-tag ${String(level || "").toLowerCase()}`}>{level}</span>;
}

function DrilldownButton({ item, onOpenIssues }) {
  if (!item?.drilldown_risk_type) {
    return null;
  }
  return (
    <button
      className="link-button"
      type="button"
      onClick={() =>
        onOpenIssues({
          title: item.label || item.message || "Risk drill-down",
          filters: {
            risk_type: item.drilldown_risk_type || "",
            assignee_name: item.drilldown_dimension === "assignee" ? item.drilldown_value || "" : "",
            tracker_name: item.drilldown_dimension === "tracker" ? item.drilldown_value || "" : "",
            subject_group: item.drilldown_dimension === "subject_group" ? item.drilldown_value || "" : "",
          },
        })
      }
    >
      View issues
    </button>
  );
}

export default function DashboardSummaryPage({ dbStatus, onOpenIssues }) {
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

  return (
    <section className="dashboard-summary">
      <section className="panel dashboard-filter-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Current Project</p>
            <h2>{data?.project?.name ?? "Not synced yet"}</h2>
          </div>
          <span className="dashboard-db-status">DB: {dbStatus}</span>
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
              <HealthBadge value={data?.health_summary?.status ?? "Red"} />
            </div>

            <div className="dashboard-health-grid health-summary-grid">
              <div className="dashboard-health-stat">
                <span>Score</span>
                <strong>
                  {data?.health_summary?.score ?? 0} / {data?.health_summary?.max_score ?? 12}
                </strong>
              </div>
              <div className="dashboard-health-stat">
                <span>Trend</span>
                <strong>
                  {trendLabel(data?.health_summary?.trend_direction, data?.health_summary?.trend_value)}
                </strong>
              </div>
              <div className="dashboard-health-stat">
                <span>Last Updated</span>
                <strong>{data?.last_updated ? new Date(data.last_updated).toLocaleString() : "N/A"}</strong>
              </div>
            </div>

            <div className="metric-breakdown">
              <div className="section-heading compact">
                <div>
                  <p className="eyebrow">Metrics</p>
                  <h3>Score Breakdown</h3>
                </div>
              </div>
              <div className="metric-list">
                {(data?.metrics || []).map((metric) => (
                  <div className="metric-row" key={metric.code}>
                    <div>
                      <strong>{metric.label}</strong>
                      <p>{metric.value_display}</p>
                    </div>
                    <div className="metric-actions">
                      <span className="metric-score">
                        {metric.score}/{metric.max_score}
                      </span>
                      {metric.drilldown_risk_type ? (
                        <button
                          className="link-button"
                          type="button"
                          onClick={() =>
                            onOpenIssues({
                              title: metric.label,
                              filters: { risk_type: metric.drilldown_risk_type },
                            })
                          }
                        >
                          View issues
                        </button>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="dashboard-two-col">
              <div className="dashboard-warning-list">
                <h3>Main Risk Drivers</h3>
                {data?.main_risk_drivers?.length ? (
                  data.main_risk_drivers.map((item, index) => (
                    <div className="dashboard-warning-item" key={`${item.risk_type}-${index}`}>
                      <div>
                        <strong>{index + 1}. {item.label}</strong>
                        <p>{item.issue_count} issues</p>
                      </div>
                      <DrilldownButton item={item} onOpenIssues={onOpenIssues} />
                    </div>
                  ))
                ) : (
                  <p className="muted-copy">No main risk drivers.</p>
                )}
              </div>

              <div className="dashboard-warning-list">
                <h3>Suggested Actions</h3>
                {data?.suggested_actions?.length ? (
                  data.suggested_actions.map((item, index) => (
                    <div className="dashboard-warning-item" key={`${item.risk_type}-${index}`}>
                      <div>
                        <strong>{index + 1}. {item.message}</strong>
                      </div>
                      <DrilldownButton item={item} onOpenIssues={onOpenIssues} />
                    </div>
                  ))
                ) : (
                  <p className="muted-copy">No suggested actions.</p>
                )}
              </div>
            </div>

            <div className="dashboard-warning-list">
              <h3>Early Warnings</h3>
              {data?.early_warnings?.length ? (
                data.early_warnings.map((item) => (
                  <div className="dashboard-warning-item" key={item.code}>
                    <div>
                      <strong>{item.message}</strong>
                      <p>{item.code}</p>
                    </div>
                    <div className="metric-actions">
                      {warningTag(item.level)}
                      {item.drilldown_risk_type ? (
                        <button
                          className="link-button"
                          type="button"
                          onClick={() =>
                            onOpenIssues({
                              title: item.message,
                              filters: { risk_type: item.drilldown_risk_type },
                            })
                          }
                        >
                          View issues
                        </button>
                      ) : null}
                    </div>
                  </div>
                ))
              ) : (
                <p className="muted-copy">No active warnings.</p>
              )}
            </div>
          </section>

          <section className="panel dashboard-chart-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Health Trend</p>
                <h2>Score History</h2>
              </div>
            </div>
            {data?.health_trend?.length ? (
              <div className="trend-list">
                {data.health_trend.map((item) => (
                  <div className="trend-row" key={`${item.label}-${item.snapshot_at}`}>
                    <div className="trend-meta">
                      <strong>{item.label}</strong>
                      <span>
                        {item.score}/12 • {item.status} • {trendLabel(item.trend_direction, item.trend_value)}
                      </span>
                    </div>
                    <div className="distribution-track">
                      <div
                        className="distribution-bar"
                        style={{ width: `${Math.max(8, Math.round((item.score / 12) * 100))}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="muted-copy">No previous snapshot.</p>
            )}
          </section>
        </>
      )}
    </section>
  );
}
