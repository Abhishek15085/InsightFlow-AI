import React from 'react';
import { NavLink } from 'react-router-dom';
import { UploadCloud, CheckCircle, BarChart2, MessageSquare } from 'lucide-react';
import { useData } from '../DataContext';
import './Header.css';
import logo from '../assets/logo.png';

const Header: React.FC = () => {
  const { dataset } = useData();

  return (
    <header className="top-header glass-panel">
      <div className="header-brand">
        <div className="brand-logo" style={{ background: 'transparent', boxShadow: 'none' }}>
          <img src={logo} alt="InsightFlow AI Logo" style={{ width: '36px', height: '36px', objectFit: 'contain' }} />
        </div>
        <h2>InsightFlow AI</h2>
      </div>

      <nav className="header-nav">
        <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <UploadCloud size={18} />
          <span>Upload Data</span>
        </NavLink>
        
        {dataset && (
          <>
            <NavLink to="/preview" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <CheckCircle size={18} />
              <span>Preview</span>
            </NavLink>
            <NavLink to="/summary" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <CheckCircle size={18} />
              <span>Summary</span>
            </NavLink>
            <NavLink to="/validate" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <CheckCircle size={18} />
              <span>Validate</span>
            </NavLink>
            <NavLink to="/eda" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <BarChart2 size={18} />
              <span>EDA</span>
            </NavLink>
            <NavLink to="/clean" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <CheckCircle size={18} />
              <span>Clean Data</span>
            </NavLink>
            <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <BarChart2 size={18} />
              <span>Dashboard</span>
            </NavLink>
          </>
        )}
      </nav>

      <div className="header-actions">
        {dataset && (
          <div className="dataset-badge">
            <span className="pulse-dot"></span>
            {dataset.filename}
          </div>
        )}
        <NavLink to="/chat" className={({ isActive }) => `chat-btn ${isActive ? 'active' : ''}`}>
          <MessageSquare size={18} />
          <span>AI Assistant</span>
        </NavLink>
      </div>
    </header>
  );
};

export default Header;
