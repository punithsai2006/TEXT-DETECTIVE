import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { CaseProvider } from './context/CaseContext';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';

import { DashboardPage } from './pages/DashboardPage';
import { CasesPage } from './pages/CasesPage';
import { NewInvestigationPage } from './pages/NewInvestigationPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { TimelinePage } from './pages/TimelinePage';
import { EvidencePage } from './pages/EvidencePage';
import { ContradictionsPage } from './pages/ContradictionsPage';
import { HypothesesPage } from './pages/HypothesesPage';
import { CaseGraphPage } from './pages/CaseGraphPage';
import { ReportPage } from './pages/ReportPage';
import { AskQuestionPage } from './pages/AskQuestionPage';
import { SettingsPage } from './pages/SettingsPage';

export const App: React.FC = () => {
  return (
    <CaseProvider>
      <BrowserRouter>
        <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 antialiased">
          <Navbar />
          <div className="flex-1 flex overflow-hidden">
            <Sidebar />
            <main className="flex-1 p-6 lg:p-8 overflow-y-auto bg-slate-50">
              <div className="max-w-7xl mx-auto">
                <Routes>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/cases" element={<CasesPage />} />
                  <Route path="/new" element={<NewInvestigationPage />} />
                  <Route path="/documents" element={<DocumentsPage />} />
                  <Route path="/timeline" element={<TimelinePage />} />
                  <Route path="/evidence" element={<EvidencePage />} />
                  <Route path="/contradictions" element={<ContradictionsPage />} />
                  <Route path="/hypotheses" element={<HypothesesPage />} />
                  <Route path="/graph" element={<CaseGraphPage />} />
                  <Route path="/report" element={<ReportPage />} />
                  <Route path="/ask" element={<AskQuestionPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                </Routes>
              </div>
            </main>
          </div>
        </div>
      </BrowserRouter>
    </CaseProvider>
  );
};

export default App;
