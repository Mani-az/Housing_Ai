import { useEffect, useState } from "react";
import api from "../api/axios";

function Projects() {
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
        console.error("Projects loading error:", error);
        setErrorMessage("Could not load projects.");
      } finally {
        setLoading(false);
      }
    }

    loadProjects();
  }, []);

  return (
    <section className="panel">
      <h2>Projects</h2>
      <p className="section-subtitle">
        List of all pre-purchase housing projects.
      </p>

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
              <th>Neighborhood</th>
              <th>Units</th>
              <th>Avg Area</th>
              <th>Status</th>
              <th>Estimated Cost</th>
            </tr>
          </thead>

          <tbody>
            {projects.map((project) => (
              <tr key={project.id}>
                <td>{project.id}</td>
                <td>{project.name || "-"}</td>
                <td>{project.neighborhood_english || "-"}</td>
                <td>{project.total_units || "-"}</td>
                <td>{project.average_unit_area || "-"}</td>
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
  );
}

export default Projects;