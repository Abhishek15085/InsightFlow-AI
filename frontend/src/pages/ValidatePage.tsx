import React, { useEffect, useState } from 'react';
import { useData } from '../DataContext';
import { getValidationStats } from '../api';
import { motion } from 'framer-motion';
import { AlertCircle, FileCheck2, Database, CheckCircle } from 'lucide-react';
import './ValidatePage.css';

const ValidatePage: React.FC = () => {
  const { dataset } = useData();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (dataset) {
      fetchStats();
    }
  }, [dataset]);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const data = await getValidationStats(dataset!.filename);
      setStats(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (!dataset) {
    return (
      <div className="page-container center-empty">
        <AlertCircle size={48} className="empty-icon warning" />
        <h2>No Dataset Uploaded</h2>
        <p>Please go to the Upload tab and select a CSV file first.</p>
      </div>
    );
  }

  return (
    <motion.div 
      className="page-container"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
    >
      <div className="page-header">
        <h1>Data Validation & Quality</h1>
        <p>Overview of {dataset.filename}</p>
      </div>

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Analyzing dataset schema and quality metrics...</p>
        </div>
      ) : stats ? (
        <div className="dashboard-grid">
          {/* Top KPI Cards */}
          <div className="kpi-card glass-panel">
            <Database className="kpi-icon primary" />
            <div className="kpi-info">
              <h3>{dataset.rows.toLocaleString()}</h3>
              <p>Total Rows</p>
            </div>
          </div>
          <div className="kpi-card glass-panel">
            <FileCheck2 className="kpi-icon secondary" />
            <div className="kpi-info">
              <h3>{dataset.columns}</h3>
              <p>Total Columns</p>
            </div>
          </div>
          <div className="kpi-card glass-panel">
            <AlertCircle className="kpi-icon error" />
            <div className="kpi-info">
              <h3>{stats.duplicates.duplicate_rows.toLocaleString()}</h3>
              <p>Duplicate Rows</p>
            </div>
          </div>

          {/* Missing Values Table */}
          <div className="full-width-card glass-panel">
            <div className="card-header">
              <h2>Missing Values Summary</h2>
              <p>Columns that require cleaning before ML training.</p>
            </div>
            
            {stats.missing.total_missing_cells > 0 ? (
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Column Name</th>
                      <th>Missing Count</th>
                      <th>Missing %</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.missing.report.map((item: any) => {
                        const isHigh = item.missing_pct > 20;
                        return (
                          <tr key={item.column}>
                            <td><strong>{item.column}</strong></td>
                            <td>{item.missing_count.toLocaleString()}</td>
                            <td>{item.missing_pct.toFixed(2)}%</td>
                            <td>
                              <span className={`badge ${isHigh ? 'error' : 'warning'}`}>
                                {isHigh ? 'Critical' : 'Review'}
                              </span>
                            </td>
                          </tr>
                        );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="all-good">
                <CheckCircle size={48} className="success-icon" />
                <p>No missing values detected. Dataset is clean!</p>
              </div>
            )}
          </div>
        </div>
      ) : null}
    </motion.div>
  );
};

export default ValidatePage;
