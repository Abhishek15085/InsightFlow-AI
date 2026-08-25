import React from 'react';
import { useData } from '../DataContext';
import { motion } from 'framer-motion';
import { AlertCircle, Table } from 'lucide-react';

const PreviewPage: React.FC = () => {
  const { dataset } = useData();

  if (!dataset || !dataset.preview) {
    return (
      <div className="page-container center-empty">
        <AlertCircle size={48} className="empty-icon warning" />
        <h2>No Dataset Uploaded</h2>
      </div>
    );
  }

  const columns = Object.keys(dataset.preview[0] || {});

  return (
    <motion.div className="page-container" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="page-header">
        <h1>Dataset Preview</h1>
        <p>Raw data inspection for {dataset.filename}</p>
      </div>

      <div className="dashboard-grid" style={{ gridTemplateColumns: '1fr' }}>
        <div className="full-width-card glass-panel" style={{ overflowX: 'auto' }}>
          <div className="card-header" style={{ marginBottom: '1rem' }}>
            <Table className="kpi-icon primary" style={{ width: '24px', height: '24px' }} />
            <h2 style={{ marginLeft: '12px', display: 'inline-block' }}>First 10 Rows (Preview)</h2>
          </div>
          
          <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: 'rgba(255,255,255,0.05)' }}>
                {columns.map(col => (
                  <th key={col} style={{ padding: '0.75rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {dataset.preview.map((row: any, idx: number) => (
                <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  {columns.map(col => (
                    <td key={col} style={{ padding: '0.75rem' }}>
                      {typeof row[col] === 'number' ? row[col].toFixed(4).replace(/\.0000$/, '') : String(row[col])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </motion.div>
  );
};

export default PreviewPage;
