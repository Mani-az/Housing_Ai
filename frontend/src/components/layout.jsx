import { Outlet } from "react-router-dom";
import Sidebar from "./sidebar.jsx";

function Layout() {
  return (
    <div className="app">
      <Sidebar />

      <main className="content">
        <header className="header">
          <h1>AI-Powered Cooperative Housing System</h1>
          <p>Pre-purchase and construction finance management</p>
        </header>

        <Outlet />
      </main>
    </div>
  );
}

export default Layout;