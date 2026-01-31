import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Dashboard } from './pages/Dashboard';
import { Inventory } from './pages/Inventory';
import { Analytics } from './pages/Analytics';
import { Sensitivity } from './pages/Sensitivity';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/inventory" element={<Inventory />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/sensitivity" element={<Sensitivity />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
