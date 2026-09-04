import { useEffect, useState } from "react";
import api from "../api/axios";

function Dashboard() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    async function loadProjects() {
      try {
        const response = await api.get("/projects/");

        if (Array.isArray(response.data)) {
          setProjects(response.data);
        } else {
          setErrorMessage("Projects API did not return a list.");
        }
      } catch (error) {
        console.error("Dashboard loading error:", error);
        setErrorMessage("Could not load projects.");
      } finally {
        setLoading(false);
      }
    }

    loadProjects();
  }, []);

  return (
    <>
      <section className="cards">
        <div className="card">
          <p>Total Projects</p>
          <h3>{projects.length}</h3>
        </div>

        <div className="card">
          <p>Status</p>
          <h3>{errorMessage ? "Error" : "Active"}</h3>
        </div>

        <div className="card">
          <p>Backend</p>
          <h3>{errorMessage ? "Check" : "Connected"}</h3>
        </div>
      </section>

      <section className="panel">
        <h2>Recent Projects</h2>

        {loading && <p>Loading projects...</p>}

        {!loading && errorMessage && (
          <div className="error-box">
            <strong>Error:</strong> {errorMessage}
          </div>
        )}

        {!loading && !errorMessage && projects.length === 0 && (
          <p>No projects found.</p>
        )}

        {!loading && projects.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Project Name</th>
                <th>Location</th>
                <th>Units</th>
                <th>Status</th>
                <th>Estimated Cost</th>
              </tr>
            </thead>

            <tbody>
              {projects.slice(0, 5).map((project) => (
                <tr key={project.id}>
                  <td>{project.id}</td>
                  <td>{project.name || "-"}</td>
                  <td>{project.location || "-"}</td>
                  <td>{project.total_units || "-"}</td>
                  <td>
                    <span className="badge">{project.status || "unknown"}</span>
                  </td>
                  <td>
                    {Number(project.estimated_total_cost || 0).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </>
  );
}

export default Dashboard;