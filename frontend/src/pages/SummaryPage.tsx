import React from 'react';
import { useData } from '../DataContext';
import { motion } from 'framer-motion';
import { AlertCircle, FileText, Settings2, BarChart } from 'lucide-react';

const SummaryPage: React.FC = () => {
  const { dataset } = useData();

  if (!dataset) {
    return (
      <div className="page-container center-empty">
        <AlertCircle size={48} className="empty-icon warning" />
        <h2>No Dataset Uploaded</h2>
      </div>
    );
  }

  const numericStats = dataset.summary.numeric_stats;

  return (
    <motion.div className="page-container" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="page-header">
        <h1>Dataset Summary</h1>
        <p>High-level overview & metadata</p>
      </div>

      <div className="dashboard-grid">
        {/* Quick KPI Stats */}
        <div className="kpi-card glass-panel">
          <FileText className="kpi-icon primary" />
          <div className="kpi-info">
            <h3>{dataset.memory_mb} MB</h3>
            <p>Memory Usage</p>
          </div>
        </div>
        <div className="kpi-card glass-panel">
          <Settings2 className="kpi-icon secondary" />
          <div className="kpi-info">
            <h3>{Object.keys(dataset.dtypes).length}</h3>
            <p>Features</p>
          </div>
        </div>
        <div className="kpi-card glass-panel">
          <BarChart className="kpi-icon warning" />
          <div className="kpi-info">
            <h3>{Object.keys(numericStats).length}</h3>
            <p>Numeric Columns</p>
          </div>
        </div>

        {/* Data Types Summary */}
        <div className="full-width-card glass-panel">
          <div className="card-header">
            <h2>Data Types Dictionary</h2>
          </div>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Column</th>
                  <th>Data Type</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(dataset.dtypes).map(([col, dtype]) => (
                  <tr key={col}>
                    <td><strong>{col}</strong></td>
                    <td>
                      <span className={`badge ${dtype.includes('float') || dtype.includes('int') ? 'success' : 'primary'}`}>
                        {dtype}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Numeric Snapshot */}
        {Object.keys(numericStats).length > 0 && (
          <div className="full-width-card glass-panel">
            <div className="card-header">
              <h2>Numeric Column Snapshot</h2>
            </div>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Column</th>
                    <th>Mean</th>
                    <th>Std Dev</th>
                    <th>Min</th>
                    <th>Max</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(numericStats).map(([col, stats]) => (
                    <tr key={col}>
                      <td><strong>{col}</strong></td>
                      <td>{stats.mean?.toFixed(2) ?? 'N/A'}</td>
                      <td>{stats.std?.toFixed(2) ?? 'N/A'}</td>
                      <td>{stats.min?.toFixed(2) ?? 'N/A'}</td>
                      <td>{stats.max?.toFixed(2) ?? 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default SummaryPage;
