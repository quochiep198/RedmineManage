import { useEffect, useState } from "react";

import { api } from "../api/client.js";

function formatDate(value) {
  if (!value) {
    return "-";
  }
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return value;
  }
  return new Date(value).toLocaleDateString();
}

function buildParams(filters, page, pageSize) {
  const params = { page, page_size: pageSize };
  if (filters.status_id) {
    params.status_id = Number(filters.status_id);
  }
  if (filters.priority_id) {
    params.priority_id = Number(filters.priority_id);
  }
  if (filters.assignee_id) {
    params.assignee_id = Number(filters.assignee_id);
  }
  if (filters.assignee_name.trim()) {
    params.assignee_name = filters.assignee_name.trim();
  }
  if (filters.tracker_name.trim()) {
    params.tracker_name = filters.tracker_name.trim();
  }
  if (filters.subject_group.trim()) {
    params.subject_group = filters.subject_group.trim();
  }
  if (filters.risk_type) {
    params.risk_type = filters.risk_type;
  }
  if (filters.keyword.trim()) {
    params.keyword = filters.keyword.trim();
  }
  if (filters.due_date_from) {
    params.due_date_from = filters.due_date_from;
  }
  if (filters.due_date_to) {
    params.due_date_to = filters.due_date_to;
  }
  return params;
}

const emptyFilters = {
  status_id: "",
  priority_id: "",
  assignee_id: "",
  assignee_name: "",
  tracker_name: "",
  subject_group: "",
  risk_type: "",
  keyword: "",
  due_date_from: "",
  due_date_to: "",
};

function presetToFilters(preset) {
  if (!preset) {
    return emptyFilters;
  }
  return {
    ...emptyFilters,
    ...preset.filters,
  };
}

export default function IssuesPage({ initialPreset, onClearPreset }) {
  const [filters, setFilters] = useState(emptyFilters);
  const [options, setOptions] = useState({ statuses: [], priorities: [] });
  const [result, setResult] = useState({ items: [], page: 1, page_size: 20, total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activePresetTitle, setActivePresetTitle] = useState("");

  useEffect(() => {
    async function loadOptions() {
      try {
        const res = await api.get("/issues/filters");
        setOptions(res.data);
      } catch {
        setOptions({ statuses: [], priorities: [] });
      }
    }

    loadOptions();
  }, []);

  useEffect(() => {
    if (!initialPreset) {
      return;
    }
    setFilters(presetToFilters(initialPreset));
    setResult((current) => ({ ...current, page: 1 }));
    setActivePresetTitle(initialPreset.title || "Risk drill-down");
  }, [initialPreset]);

  useEffect(() => {
    async function loadIssues() {
      setLoading(true);
      setError("");
      try {
        const res = await api.get("/issues", {
          params: buildParams(filters, result.page, result.page_size),
        });
        setResult(res.data);
      } catch (err) {
        setError(err.response?.data?.detail || "Could not load issues.");
      } finally {
        setLoading(false);
      }
    }

    loadIssues();
  }, [filters, result.page, result.page_size]);

  function handleFilterChange(event) {
    const { name, value } = event.target;
    setFilters((current) => ({ ...current, [name]: value }));
    setResult((current) => ({ ...current, page: 1 }));
  }

  function resetFilters() {
    setFilters(emptyFilters);
    setActivePresetTitle("");
    setResult((current) => ({ ...current, page: 1 }));
    onClearPreset?.();
  }

  const totalPages = Math.max(1, Math.ceil(result.total / result.page_size));

  return (
    <section className="panel issues-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Dashboard</p>
          <h2>Issues</h2>
        </div>
      </div>

      {activePresetTitle ? (
        <div className="dashboard-note">
          <strong>Drill-down:</strong> {activePresetTitle}
        </div>
      ) : null}

      <div className="issues-filter-grid">
        <label className="field-label">
          Keyword
          <input
            name="keyword"
            value={filters.keyword}
            onChange={handleFilterChange}
            placeholder="Search subject or description"
          />
        </label>
        <label className="field-label">
          Risk type
          <select name="risk_type" value={filters.risk_type} onChange={handleFilterChange}>
            <option value="">All risks</option>
            <option value="overdue">Overdue</option>
            <option value="bug">Bug</option>
            <option value="effort">Effort</option>
            <option value="stale">Stale</option>
            <option value="progress">Progress</option>
          </select>
        </label>
        <label className="field-label">
          Status
          <select name="status_id" value={filters.status_id} onChange={handleFilterChange}>
            <option value="">All statuses</option>
            {options.statuses.map((status) => (
              <option key={status.id} value={status.id}>
                {status.name}
              </option>
            ))}
          </select>
        </label>
        <label className="field-label">
          Priority
          <select name="priority_id" value={filters.priority_id} onChange={handleFilterChange}>
            <option value="">All priorities</option>
            {options.priorities.map((priority) => (
              <option key={priority.id} value={priority.id}>
                {priority.name}
              </option>
            ))}
          </select>
        </label>
        <label className="field-label">
          Assignee ID
          <input
            name="assignee_id"
            value={filters.assignee_id}
            onChange={handleFilterChange}
            placeholder="12"
          />
        </label>
        <label className="field-label">
          Assignee name
          <input
            name="assignee_name"
            value={filters.assignee_name}
            onChange={handleFilterChange}
            placeholder="A"
          />
        </label>
        <label className="field-label">
          Tracker name
          <input
            name="tracker_name"
            value={filters.tracker_name}
            onChange={handleFilterChange}
            placeholder="Bug"
          />
        </label>
        <label className="field-label">
          Subject group
          <input
            name="subject_group"
            value={filters.subject_group}
            onChange={handleFilterChange}
            placeholder="Payment"
          />
        </label>
        <label className="field-label">
          Due date from
          <input name="due_date_from" type="date" value={filters.due_date_from} onChange={handleFilterChange} />
        </label>
        <label className="field-label">
          Due date to
          <input name="due_date_to" type="date" value={filters.due_date_to} onChange={handleFilterChange} />
        </label>
      </div>

      <div className="issues-toolbar">
        <p className="muted-copy">
          Showing issues synced from the current Redmine project only.
        </p>
        <button className="secondary" type="button" onClick={resetFilters}>
          Reset filters
        </button>
      </div>

      {error ? <div className="error-msg">{error}</div> : null}

      {loading ? (
        <p className="muted-copy">Loading issues...</p>
      ) : result.items.length ? (
        <>
          <div className="issues-table-wrap">
            <table className="issues-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Subject</th>
                  <th>Status</th>
                  <th>Priority</th>
                  <th>Assignee</th>
                  <th>Tracker</th>
                  <th>Due Date</th>
                  <th>Done</th>
                  <th>Redmine</th>
                </tr>
              </thead>
              <tbody>
                {result.items.map((issue) => (
                  <tr key={issue.id}>
                    <td>{issue.redmine_issue_id}</td>
                    <td>
                      <div className="issue-subject-cell">
                        <strong>{issue.subject}</strong>
                        <span>{issue.description || "No description"}</span>
                      </div>
                    </td>
                    <td>{issue.status_name || "-"}</td>
                    <td>{issue.priority_name || "-"}</td>
                    <td>{issue.assignee_name || "-"}</td>
                    <td>{issue.tracker_name || "-"}</td>
                    <td>{formatDate(issue.due_date)}</td>
                    <td>{issue.done_ratio ?? 0}%</td>
                    <td>
                      <a href={issue.redmine_url} target="_blank" rel="noreferrer">
                        Open
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="issues-pagination">
            <button
              className="secondary"
              type="button"
              disabled={result.page <= 1}
              onClick={() => setResult((current) => ({ ...current, page: current.page - 1 }))}
            >
              Previous
            </button>
            <span>
              Page {result.page} / {totalPages} ({result.total} issues)
            </span>
            <button
              className="secondary"
              type="button"
              disabled={result.page >= totalPages}
              onClick={() => setResult((current) => ({ ...current, page: current.page + 1 }))}
            >
              Next
            </button>
          </div>
        </>
      ) : (
        <div className="empty-state">
          <h3>No issues found</h3>
          <p>Try resetting filters or sync the current project issues first.</p>
        </div>
      )}
    </section>
  );
}
