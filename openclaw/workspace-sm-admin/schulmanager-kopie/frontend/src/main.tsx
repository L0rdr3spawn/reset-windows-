import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './styles/tokens.css';
import './styles/app.css';
import './styles/timetable.css';
import './styles/monitor.css';
import './styles/print.css';

// gespeichertes Farbschema sofort anwenden (verhindert Aufblitzen)
try {
  const t = window.localStorage.getItem('sm-theme');
  if (t === 'light' || t === 'dark') document.documentElement.setAttribute('data-theme', t);
} catch {
  /* ignorieren */
}

const root = document.getElementById('root');
if (root) {
  createRoot(root).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
}
