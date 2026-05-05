import { useEffect, useState } from "react";

import { api } from "../api/client.js";

function formatTimestamp(value) {
  if (!value) {
    return "Never";
  }
  return new Date(value).toLocaleString();
}

export default function ProjectsPage() {
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadProject() {
      try {
        const res = await api.get("/projects/current");
        setProject(res.data);
      } catch (err) {
        setError(err.response?.data?.detail || "Could not load current project.");
      } finally {
        setLoading(false);
      }
    }

    loadProject();
  }, []);

  if (loading) {
    return <section className="panel projects-panel">Loading current project...</section>;
  }

  return (
    <section className="panel projects-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Dashboard</p>
          <h2>Current Project</h2>
        </div>
      </div>

      {error ? <div className="error-msg">{error}</div> : null}

      {!error && project ? (
        <div className="current-project-card">
          <div className="meta-list">
            <div className="meta-row">
              <span>Name</span>
              <strong>{project.name}</strong>
            </div>
            <div className="meta-row">
              <span>Identifier</span>
              <strong>{project.identifier}</strong>
            </div>
            <div className="meta-row">
              <span>Last synced</span>
              <strong>{formatTimestamp(project.last_synced_at)}</strong>
            </div>
            <div className="meta-row">
              <span>Status</span>
              <strong className={`status-chip ${project.is_active ? "active" : "inactive"}`}>
                {project.is_active ? "Active" : "Inactive"}
              </strong>
            </div>
          </div>

          <div className="project-description">
            <p className="eyebrow">Description</p>
            <p className="muted-copy">{project.description || "No description available."}</p>
          </div>
        </div>
      ) : null}
    </section>
  );
}
