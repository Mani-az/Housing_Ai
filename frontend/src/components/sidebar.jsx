import { NavLink } from "react-router-dom";

/** Small reusable sidebar for legacy Layout consumers. The main presentation
 * shell uses the role-aware sidebar defined in AppUpdated.jsx. */
export default function Sidebar({ links = [] }) {
  return <aside className="sidebar"><h2>Housing AI</h2><nav>{links.map((link) => <NavLink className="nav-link" key={link.to} to={link.to}>{link.label}</NavLink>)}</nav></aside>;
}
