import { useEffect, useState } from "react";

import { api } from "../api/client.js";
import DashboardSummaryPage from "./DashboardSummaryPage.jsx";
import IssuesPage from "./IssuesPage.jsx";
import IssueSyncPage from "./IssueSyncPage.jsx";
import ProjectsPage from "./ProjectsPage.jsx";
import ProjectSyncPage from "./ProjectSyncPage.jsx";
import RedmineConnectionPage from "./RedmineConnectionPage.jsx";

export default function DashboardPage({ user, onLogout }) {
  const [dbStatus, setDbStatus] = useState("checking...");
  const [view, setView] = useState("dashboard");
  const [settingsTab, setSettingsTab] = useState("connection");

  useEffect(() => {
    api
      .get("/health/db")
      .then((res) => setDbStatus(res.data.database))
      .catch(() => setDbStatus("error"));
  }, []);

  async function handleLogout() {
    try {
      await api.post("/auth/logout");
    } catch {
      // Ignore logout transport errors.
    }
    onLogout();
  }

  const showSettings = user.is_admin && view === "settings";
  const showProjects = view === "projects";
  const showIssues = view === "issues";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h2>Redmine</h2>
        <nav>
          <button
            className={`nav-link ${view === "dashboard" ? "active" : ""}`}
            type="button"
            onClick={() => setView("dashboard")}
          >
            Dashboard
          </button>
          <button
            className={`nav-link ${view === "projects" ? "active" : ""}`}
            type="button"
            onClick={() => setView("projects")}
          >
            Current Project
          </button>
          <button
            className={`nav-link ${view === "issues" ? "active" : ""}`}
            type="button"
            onClick={() => setView("issues")}
          >
            Issues
          </button>
          <button className="nav-link" type="button">
            Members
          </button>
          {user.is_admin ? (
            <button
              className={`nav-link ${view === "settings" ? "active" : ""}`}
              type="button"
              onClick={() => setView("settings")}
            >
              Settings
            </button>
          ) : null}
        </nav>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <h1>
              {showSettings
                ? "Settings"
                : showProjects
                  ? "Current Project"
                  : showIssues
                    ? "Issues"
                    : "Dashboard"}
            </h1>
            <p>
              Xin chao, {user.username}
              {user.is_admin ? " (admin)" : ""}
            </p>
          </div>
          <button className="secondary" onClick={handleLogout}>
            Logout
          </button>
        </header>

        {showSettings ? (
          <section className="settings-stack">
            <div className="settings-tabs">
              <button
                className={`nav-link ${settingsTab === "connection" ? "active" : ""}`}
                type="button"
                onClick={() => setSettingsTab("connection")}
              >
                Redmine Connection
              </button>
              <button
                className={`nav-link ${settingsTab === "project-sync" ? "active" : ""}`}
                type="button"
                onClick={() => setSettingsTab("project-sync")}
              >
                Project Sync
              </button>
              <button
                className={`nav-link ${settingsTab === "issue-sync" ? "active" : ""}`}
                type="button"
                onClick={() => setSettingsTab("issue-sync")}
              >
                Issue Sync
              </button>
            </div>
            {settingsTab === "connection" ? (
              <RedmineConnectionPage />
            ) : settingsTab === "project-sync" ? (
              <ProjectSyncPage />
            ) : (
              <IssueSyncPage />
            )}
          </section>
        ) : showProjects ? (
          <ProjectsPage />
        ) : showIssues ? (
          <IssuesPage />
        ) : (
          <DashboardSummaryPage dbStatus={dbStatus} />
        )}
      </main>
    </div>
  );
}
