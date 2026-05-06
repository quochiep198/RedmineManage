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

function HealthBadge({ value }) {
  return <span className={`health-badge ${String(value || "").toLowerCase()}`}>{value}</span>;
}

function KpiStatusTag({ value }) {
  return <span className={`warning-tag ${String(value || "").toLowerCase()}`}>{value}</span>;
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

function formatDateTime(value) {
  if (!value) {
    return "N/A";
  }
  return new Date(value).toLocaleString();
}

function trendBarClass(status) {
  return `trend-bar ${String(status || "").toLowerCase()}`;
}

function TrendChart({ items }) {
  if (!items?.length) {
    return <p className="muted-copy">No trend data yet.</p>;
  }

  return (
    <div className="trend-chart-wrap">
      <div className="trend-bar-chart" role="img" aria-label="Health trend bar chart">
        {items.map((item) => {
          const score = Number(item.score || 0);
          const barHeight = Math.max(10, Math.min(100, (score / 6) * 100));
          return (
            <div className="trend-bar-col" key={`${item.label}-${item.snapshot_at}`}>
              <div className="trend-bar-track">
                <div className="trend-bar-hitbox">
                  <div
                    className={trendBarClass(item.status)}
                    style={{ height: `${barHeight}%` }}
                  />
                  <div className="trend-bar-tooltip">
                    <strong>{item.label}</strong>
                    <span>Score: {score} / 6</span>
                    <span>Status: {item.status}</span>
                  </div>
                </div>
              </div>
              <span className="trend-bar-label">{item.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function DashboardSummaryPage({ onOpenIssues }) {
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
        `Synced ${res.data.total_synced} issues (${res.data.created} created, ${res.data.updated} updated, ${res.data.deleted} deleted).`,
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
          <button className="primary-action" type="button" onClick={syncIssues} disabled={syncing}>
            {syncing ? "Syncing..." : "Sync"}
          </button>
          <button className="secondary" type="button" onClick={applyFilters}>
            Apply
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
            <div className="stat-card">
              <p>Total Issues</p>
              <h3>{data?.total_issues ?? 0}</h3>
            </div>
            <div className="stat-card">
              <p>Open Issues</p>
              <h3>{data?.open_issues ?? 0}</h3>
            </div>
            <div className="stat-card">
              <p>Closed Issues</p>
              <h3>{data?.closed_issues ?? 0}</h3>
            </div>
            <div className="stat-card">
              <p>Last Updated</p>
              <h3 className="stat-card-datetime">{formatDateTime(data?.last_updated)}</h3>
            </div>
          </section>

          <section className="panel dashboard-health-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Project Health Analyzer</p>
                <h2>KPI Dashboard</h2>
              </div>
              <HealthBadge value={data?.health_summary?.status ?? "Red"} />
            </div>

            {/* <div className="dashboard-health-grid health-summary-grid">
              <div className="dashboard-health-stat">
                <span>Project Health</span>
                <strong>{data?.health_summary?.status ?? "Red"}</strong>
              </div>
              <div className="dashboard-health-stat">
                <span>Reference Score</span>
                <strong>{data?.health_summary?.score_label || "N/A"}</strong>
              </div>
            </div> */}

            <div className="dashboard-warning-list">
              <h3>Trend</h3>
              <TrendChart items={data?.health_trend || []} />
            </div>

            <div className="metric-breakdown">
              <div className="section-heading compact">
                <div>
                  <p className="eyebrow">KPI Insights</p>
                  <h3>Core Indicators</h3>
                </div>
              </div>
              <div className="metric-list">
                {(data?.kpi_cards || []).map((item) => (
                  <div className="metric-row" key={item.code}>
                    <div>
                      <strong>{item.label}</strong>
                      <p>{item.summary}</p>
                    </div>
                    <div className="metric-actions">
                      <KpiStatusTag value={item.status} />
                      {item.drilldown_risk_type ? (
                        <button
                          className="link-button"
                          type="button"
                          onClick={() =>
                            onOpenIssues({
                              title: item.label,
                              filters: { risk_type: item.drilldown_risk_type },
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
              <h3>Data Quality Warnings</h3>
              {data?.data_quality_warnings?.length ? (
                data.data_quality_warnings.map((item) => (
                  <div className="dashboard-warning-item" key={item.code}>
                    <div>
                      <strong>{item.message}</strong>
                      <p>{item.code}</p>
                    </div>
                    <KpiStatusTag value={item.level} />
                  </div>
                ))
              ) : (
                <p className="muted-copy">No active warnings.</p>
              )}
            </div>
          </section>
        </>
      )}
    </section>
  );
}
