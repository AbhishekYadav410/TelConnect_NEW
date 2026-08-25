import React from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { user } from './api.js';
import { ThemeProvider } from './ThemeContext.jsx';
import ThemeToggle from './ThemeToggle.jsx';
import WakingBanner from './components/WakingBanner.jsx';
import Landing from './pages/Landing.jsx';
import Login from './pages/Login.jsx';
import AdminLayout from './pages/AdminLayout.jsx';
import Overview from './pages/Overview.jsx';
import AdminAssistant from './pages/AdminAssistant.jsx';
import UploadWizard from './pages/UploadWizard.jsx';
import Queue from './pages/Queue.jsx';
import Heatmap from './pages/Heatmap.jsx';
import Incidents from './pages/Incidents.jsx';
import Alerts from './pages/Alerts.jsx';
import NotifyQueue from './pages/NotifyQueue.jsx';
import Chat from './pages/Chat.jsx';
import Audit from './pages/Audit.jsx';

function Guard({ role, children }) {
  const u = user();
  if (!u) return <Navigate to="/login" replace />;
  if (u.role !== role) return <Navigate to={u.role === 'admin' ? '/admin' : '/chat'} replace />;
  return children;
}

export default function App() {
  return (
    <ThemeProvider>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/chat" element={<Guard role="customer"><Chat /></Guard>} />
        <Route path="/admin" element={<Guard role="admin"><AdminLayout /></Guard>}>
          <Route index element={<Overview />} />
          <Route path="assistant" element={<AdminAssistant />} />
          <Route path="upload" element={<UploadWizard />} />
          <Route path="queue" element={<Queue />} />
          <Route path="heatmap" element={<Heatmap />} />
          <Route path="incidents" element={<Incidents />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="notifications" element={<NotifyQueue />} />
          <Route path="audit" element={<Audit />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <WakingBanner />
      <ThemeToggle />
    </ThemeProvider>
  );
}

