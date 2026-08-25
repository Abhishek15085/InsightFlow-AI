import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { DataProvider } from './DataContext';
import Layout from './components/Layout';

import UploadPage from './pages/UploadPage';
import PreviewPage from './pages/PreviewPage';
import SummaryPage from './pages/SummaryPage';
import ValidatePage from './pages/ValidatePage';
import ChatPage from './pages/ChatPage';
import EDAPage from './pages/EDAPage';
import CleanPage from './pages/CleanPage';
import DashboardPage from './pages/DashboardPage';

const App: React.FC = () => {
  return (
    <DataProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<UploadPage />} />
            <Route path="preview" element={<PreviewPage />} />
            <Route path="summary" element={<SummaryPage />} />
            <Route path="validate" element={<ValidatePage />} />
            <Route path="eda" element={<EDAPage />} />
            <Route path="clean" element={<CleanPage />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="chat" element={<ChatPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </DataProvider>
  );
};

export default App;
