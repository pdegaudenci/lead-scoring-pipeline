import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Charts from './pages/Charts';
import Table from './pages/Table';
import Scoring from './pages/Scoring';
import Upload from './pages/Upload';

function App() {
  return (
    <Router>
      <div style={{ display: 'flex' }}>
        <Sidebar />
        <main style={{ flexGrow: 1, padding: '24px' }}>
          <Routes>
            <Route path="/charts" element={<Charts />} />
            <Route path="/table" element={<Table />} />
            <Route path="/scoring" element={<Scoring />} />
            <Route path="/upload" element={<Upload />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
