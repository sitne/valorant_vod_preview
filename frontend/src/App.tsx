import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Videos } from './pages/Videos';
import { Rounds } from './pages/Rounds';
import { Analysis } from './pages/Analysis';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Videos />} />
        <Route path="/rounds" element={<Rounds />} />
        <Route path="/analysis" element={<Analysis />} />
        <Route path="/config" element={<div style={{ padding: '2rem' }}>Config Placeholder</div>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
