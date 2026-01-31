import { Link, useLocation } from 'react-router-dom';
import { DataRefreshIndicator } from '../common/DataRefreshIndicator';

export function Header() {
  const location = useLocation();

  return (
    <header className="header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
        <h1>HarryTix</h1>
        <nav className="nav">
          <Link to="/" className={location.pathname === '/' ? 'active' : ''}>
            Dashboard
          </Link>
          <Link to="/inventory" className={location.pathname === '/inventory' ? 'active' : ''}>
            Inventory
          </Link>
          <Link to="/analytics" className={location.pathname === '/analytics' ? 'active' : ''}>
            Analytics
          </Link>
          <Link to="/sensitivity" className={location.pathname === '/sensitivity' ? 'active' : ''}>
            Sensitivity
          </Link>
        </nav>
      </div>
      <DataRefreshIndicator />
    </header>
  );
}
