/**
 * `/monitore` – Vertretungsmonitore einstellen (Recht `monitor.manage`: Admin, Schulleitung, Sekretariat): je Standort
 * bzw. „Alle Standorte“ Anzahl der Tage, eigene Überschrift, Laufband, Hinweise (optional mit Ablaufdatum),
 * Schriftgröße, Scrolltempo, „Nicht im Haus“. Vertretungen selbst kommen automatisch aus dem Plan.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { monitor as monitorApi } from '../api/endpoints';
import type { MonitorConfig, MonitorNotice } from '../api/types';
import { HelpTip } from '../components/HelpTip';
import { Icon } from '../components/Icon';
import { AsyncButton, ErrorBox, Loading } from '../components/ui';
import { useToast } from '../context/ToastContext';
import { useApi } from '../hooks/useApi';
import { useTitle } from '../hooks/misc';

function MonitorCard({ site, siteName, initial }: { site: string; siteName: string; initial: MonitorConfig }) {
  const toast = useToast();
  const [cfg, setCfg] = useState<MonitorConfig>(initial);
  useEffect(() => setCfg(initial), [initial]);
  const set = (patch: Partial<MonitorConfig>) => setCfg((c) => ({ ...c, ...patch }));
  const setNotice = (i: number, patch: Partial<MonitorNotice>) => set({ notices: cfg.notices.map((n, j) => (j === i ? { ...n, ...patch } : n)) });
  const pid = `mon-${site || 'alle'}`;
  return (
    <section className="card stack-sm" aria-labelledby={`${pid}-h`}>
      <div className="row-between">
        <h2 id={`${pid}-h`} style={{ margin: 0 }}>
          {siteName}
        </h2>
        <Link className="btn btn-ghost btn-sm" to={`/monitor/${encodeURIComponent(site || 'alle')}`} target="_blank" rel="noopener">
          <Icon name="monitor" /> Vorschau
        </Link>
      </div>
      <div className="form-grid">
        <div className="field">
          <label htmlFor={`${pid}-title`}>
            Überschrift <HelpTip>Leer lassen für den Schulnamen.</HelpTip>
          </label>
          <input id={`${pid}-title`} value={cfg.title} maxLength={100} onChange={(e) => set({ title: e.target.value })} />
        </div>
        <div className="field">
          <label htmlFor={`${pid}-days`}>
            Tage <HelpTip>Heute und die folgenden Schultage (Ferien und Wochenenden werden übersprungen).</HelpTip>
          </label>
          <select id={`${pid}-days`} value={cfg.days} onChange={(e) => set({ days: Number(e.target.value) })}>
            {[1, 2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor={`${pid}-scroll`}>Scrolltempo</label>
          <select id={`${pid}-scroll`} value={cfg.scroll} onChange={(e) => set({ scroll: e.target.value as MonitorConfig['scroll'] })}>
            <option value="langsam">langsam</option>
            <option value="normal">normal</option>
            <option value="schnell">schnell</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor={`${pid}-font`}>
            Schriftgröße <HelpTip>Für große Räume oder Beamer größer stellen.</HelpTip>
          </label>
          <select id={`${pid}-font`} value={cfg.font_scale} onChange={(e) => set({ font_scale: Number(e.target.value) })}>
            {[0.8, 0.9, 1, 1.15, 1.3, 1.5, 1.8].map((n) => (
              <option key={n} value={n}>
                {Math.round(n * 100)} %
              </option>
            ))}
          </select>
        </div>
      </div>
      <label className="check">
        <input type="checkbox" checked={cfg.show_absent_classes} onChange={(e) => set({ show_absent_classes: e.target.checked })} /> „Nicht im Haus“ anzeigen{' '}
        <HelpTip>Klassen, die an dem Tag nicht in der Schule sind (z. B. Praktikum, Ausflug).</HelpTip>
      </label>
      <div className="field">
        <label htmlFor={`${pid}-ticker`}>
          Laufband <HelpTip>Läuft unten durch, zusätzlich zu Mitteilungen mit dem Haken „auf Monitoren anzeigen“.</HelpTip>
        </label>
        <input id={`${pid}-ticker`} value={cfg.ticker} maxLength={500} onChange={(e) => set({ ticker: e.target.value })} />
      </div>
      <div className="stack-sm">
        <span className="small">
          Hinweise <HelpTip>Stehen groß über dem Plan, z. B. „Heute Hitzefrei ab der 5. Stunde“. Mit Ablaufdatum verschwinden sie von selbst.</HelpTip>
        </span>
        {cfg.notices.map((n, i) => (
          <div key={i} className="row" style={{ flexWrap: 'wrap', gap: 8 }}>
            <input aria-label={`Hinweis ${i + 1}`} style={{ flex: '1 1 260px' }} value={n.text} maxLength={300} onChange={(e) => setNotice(i, { text: e.target.value })} />
            <input type="date" aria-label={`Hinweis ${i + 1} gilt bis`} value={n.until ?? ''} onChange={(e) => setNotice(i, { until: e.target.value || null })} />
            <label className="check small">
              <input type="checkbox" checked={!!n.important} onChange={(e) => setNotice(i, { important: e.target.checked })} /> wichtig (rot)
            </label>
            <button type="button" className="btn btn-ghost btn-sm" aria-label={`Hinweis ${i + 1} entfernen`} onClick={() => set({ notices: cfg.notices.filter((_, j) => j !== i) })}>
              <Icon name="trash" />
            </button>
          </div>
        ))}
        {cfg.notices.length < 10 && (
          <button type="button" className="btn btn-sm" style={{ alignSelf: 'flex-start' }} onClick={() => set({ notices: [...cfg.notices, { text: '', until: null, important: false }] })}>
            <Icon name="plus" /> Hinweis
          </button>
        )}
      </div>
      <div>
        <AsyncButton
          className="btn btn-primary"
          onClick={async () => {
            try {
              const saved = await monitorApi.saveConfig(site, { ...cfg, notices: cfg.notices.filter((n) => n.text.trim()) });
              setCfg(saved);
              toast.success(`Monitor ${siteName} gespeichert`);
            } catch (e) {
              toast.error(e, 'Monitor');
            }
          }}
        >
          <Icon name="check" /> Speichern
        </AsyncButton>
      </div>
    </section>
  );
}

export default function MonitorAdminPage() {
  useTitle('Monitore einstellen');
  const q = useApi((signal) => monitorApi.configs(signal), []);
  return (
    <div className="page page-narrow stack">
      <div className="page-head">
        <h1>
          Monitore einstellen{' '}
          <HelpTip>
            Vertretungen, Entfall und Raumänderungen kommen automatisch aus dem Plan. Hier wird nur eingestellt, wie der Monitor eines Standorts aussieht und was zusätzlich angezeigt wird.
            Monitor-Konten (Benutzer mit Rolle „Monitor“) zeigen immer ihren Standort.
          </HelpTip>
        </h1>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {!q.data && !q.error && <Loading />}
      {q.data?.monitors.map((m) => (
        <MonitorCard key={m.site || 'alle'} site={m.site} siteName={m.site_name} initial={m.config} />
      ))}
    </div>
  );
}
