import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import './Layout.css';

const Layout: React.FC = () => {
  return (
    <div className="layout">
      <Header />
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
