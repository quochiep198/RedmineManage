import { useEffect, useState } from "react";

import { api } from "../api/client.js";

function formatTimestamp(value) {
  if (!value) {
    return "Never";
  }
  return new Date(value).toLocaleString();
}

export default function ProjectSyncPage() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    async function loadStatus() {
      try {
        const res = await api.get("/projects/sync/status");
        setStatus(res.data);
      } catch (err) {
        setError(err.response?.data?.detail || "Could not load project sync status.");
      } finally {
        setLoading(false);
      }
    }

    loadStatus();
  }, []);

  async function handleSync() {
    setSyncing(true);
    setError("");
    setNotice("");

    try {
      const res = await api.post("/projects/sync", {});
      setStatus((current) => ({
        shared_connection_name: current?.shared_connection_name ?? "Shared Redmine Connection",
        connection_id: res.data.connection_id,
        identifier: res.data.identifier,
        last_sync_at: res.data.synced_at,
        last_status: "success",
        last_result: {
          total_synced: res.data.total_synced,
          created: res.data.created,
          updated: res.data.updated,
        },
      }));
      setNotice(`Synced ${res.data.total_synced} project successfully.`);
    } catch (err) {
      const data = err.response?.data;
      setStatus((current) =>
        current
          ? {
              ...current,
              last_sync_at: new Date().toISOString(),
              last_status: "failed",
            }
          : current,
      );
      setError(data?.message || data?.detail || "Project sync failed.");
    } finally {
      setSyncing(false);
    }
  }

  if (loading) {
    return <div className="panel">Loading project sync status...</div>;
  }

  return (
    <section className="connection-layout">
      <div className="panel connection-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Admin Settings</p>
            <h2>Project Sync</h2>
          </div>
          <button className="primary-action" type="button" onClick={handleSync} disabled={syncing}>
            {syncing ? "Syncing..." : "Sync now"}
          </button>
        </div>

        <p className="muted-copy">
          The active project is synced from the shared Redmine connection using the configured project identifier.
        </p>

        {error ? <div className="error-msg">{error}</div> : null}
        {notice ? <div className="success-msg">{notice}</div> : null}

        <div className="meta-list project-sync-metrics">
          <div className="meta-row">
            <span>Shared connection</span>
            <strong>{status?.shared_connection_name ?? "Not configured"}</strong>
          </div>
          <div className="meta-row">
            <span>Project identifier</span>
            <strong>{status?.identifier ?? "Not configured"}</strong>
          </div>
          <div className="meta-row">
            <span>Last sync</span>
            <strong>{formatTimestamp(status?.last_sync_at)}</strong>
          </div>
          <div className="meta-row">
            <span>Last status</span>
            <strong className="status-chip">{status?.last_status ?? "not-run"}</strong>
          </div>
        </div>
      </div>

      <div className="panel connection-side-panel">
        <p className="eyebrow">Last Result</p>
        <h3 className="status-title">
          {status?.last_result ? `${status.last_result.total_synced} synced` : "No sync yet"}
        </h3>
        <div className="meta-list">
          <div className="meta-row">
            <span>Created</span>
            <strong>{status?.last_result?.created ?? 0}</strong>
          </div>
          <div className="meta-row">
            <span>Updated</span>
            <strong>{status?.last_result?.updated ?? 0}</strong>
          </div>
          <div className="meta-row">
            <span>Total</span>
            <strong>{status?.last_result?.total_synced ?? 0}</strong>
          </div>
        </div>
      </div>
    </section>
  );
}
