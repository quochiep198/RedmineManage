import { useEffect, useState } from "react";

import { api } from "../api/client.js";

const emptyForm = {
  name: "",
  base_url: "",
  identifier: "",
  api_key: "",
};

function formatTimestamp(value) {
  if (!value) {
    return "Never";
  }
  return new Date(value).toLocaleString();
}

export default function RedmineConnectionPage() {
  const [form, setForm] = useState(emptyForm);
  const [connection, setConnection] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    async function loadConnection() {
      try {
        const res = await api.get("/redmine/connections/current");
        setConnection(res.data);
        setForm({
          name: res.data.name ?? "",
          base_url: res.data.base_url ?? "",
          identifier: res.data.identifier ?? "",
          api_key: "",
        });
      } catch (err) {
        if (err.response?.status !== 404) {
          setError("Could not load current Redmine connection.");
        }
      } finally {
        setLoading(false);
      }
    }

    loadConnection();
  }, []);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function handleSave(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setNotice("");

    const payload = {
      name: form.name.trim(),
      base_url: form.base_url.trim(),
      identifier: form.identifier.trim(),
    };

    if (!connection || form.api_key.trim()) {
      payload.api_key = form.api_key.trim();
    }

    try {
      const res = connection
        ? await api.patch(`/redmine/connections/${connection.id}`, payload)
        : await api.post("/redmine/connections", payload);

      setConnection(res.data);
      setForm((current) => ({ ...current, api_key: "" }));
      setNotice(connection ? "Connection updated." : "Connection created.");
    } catch (err) {
      setError(err.response?.data?.message || err.response?.data?.detail || "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  async function handleTest() {
    if (!connection) {
      setError("Save the connection before testing.");
      return;
    }

    setTesting(true);
    setError("");
    setNotice("");

    try {
      const res = await api.post(`/redmine/connections/${connection.id}/test`);
      setConnection((current) =>
        current
          ? {
              ...current,
              status: res.data.status,
              last_tested_at: res.data.last_tested_at,
            }
          : current,
      );
      setNotice(
        `Connection successful. Redmine user: ${res.data.redmine_user.login || "unknown"}`,
      );
    } catch (err) {
      const data = err.response?.data;
      if (data?.code && connection) {
        setConnection((current) =>
          current
            ? {
                ...current,
                status: "failed",
                last_tested_at: new Date().toISOString(),
              }
            : current,
        );
      }
      setError(data?.message || data?.detail || "Connection test failed.");
    } finally {
      setTesting(false);
    }
  }

  if (loading) {
    return <div className="panel">Loading Redmine connection...</div>;
  }

  return (
    <section className="connection-layout">
      <div className="panel connection-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Admin Settings</p>
            <h2>Redmine Connection</h2>
          </div>
          <button className="secondary" type="button" onClick={handleTest} disabled={testing || !connection}>
            {testing ? "Testing..." : "Test connection"}
          </button>
        </div>

        <p className="muted-copy">
          Admin manages one shared Redmine API key. End users never receive this key in the browser.
        </p>

        {error ? <div className="error-msg">{error}</div> : null}
        {notice ? <div className="success-msg">{notice}</div> : null}

        <form className="connection-form" onSubmit={handleSave}>
          <label className="field-label">
            Name
            <input name="name" value={form.name} onChange={handleChange} placeholder="Company Redmine" required />
          </label>

          <label className="field-label">
            Base URL
            <input
              name="base_url"
              value={form.base_url}
              onChange={handleChange}
              placeholder="https://redmine.example.com"
              required
            />
          </label>

          <label className="field-label">
            Project identifier
            <input
              name="identifier"
              value={form.identifier}
              onChange={handleChange}
              placeholder="nishimatsuya"
              required
            />
          </label>

          <label className="field-label">
            API key
            <input
              name="api_key"
              type="password"
              value={form.api_key}
              onChange={handleChange}
              placeholder={connection ? "Leave blank to keep current API key" : "Enter Redmine API key"}
              required={!connection}
            />
          </label>

          <div className="connection-actions">
            <button className="primary-action" type="submit" disabled={saving}>
              {saving ? "Saving..." : connection ? "Update connection" : "Create connection"}
            </button>
          </div>
        </form>
      </div>

      <div className="panel connection-side-panel">
        <p className="eyebrow">Status</p>
        <h3 className="status-title">{connection?.status ?? "not-configured"}</h3>
        <div className="meta-list">
          <div className="meta-row">
            <span>Last tested</span>
            <strong>{formatTimestamp(connection?.last_tested_at)}</strong>
          </div>
          <div className="meta-row">
            <span>Project identifier</span>
            <strong>{connection?.identifier ?? "Not configured"}</strong>
          </div>
          <div className="meta-row">
            <span>Stored API key</span>
            <strong>{connection ? "Encrypted in database" : "Not configured"}</strong>
          </div>
          <div className="meta-row">
            <span>Shared access</span>
            <strong>Backend only</strong>
          </div>
        </div>
      </div>
    </section>
  );
}
