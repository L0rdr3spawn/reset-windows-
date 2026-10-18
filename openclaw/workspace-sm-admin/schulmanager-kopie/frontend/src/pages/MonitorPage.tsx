import { Fragment, useEffect, useRef, useState, type ReactNode } from 'react';
import { Link, useParams } from 'react-router-dom';
import { monitor as monitorApi } from '../api/endpoints';
import type { DayPlan, Entry } from '../api/types';
import { Icon } from '../components/Icon';
import { ErrorBox, KindBadge, Loading } from '../components/ui';
import { useAuth } from '../context/AuthContext';
import { useApi } from '../hooks/useApi';
import { useCollection } from '../hooks/useCollection';
import { useLiveStatus } from '../hooks/useLive';
import { useMediaQuery, useNow, useTitle } from '../hooks/misc';
import { formatClock, formatLong, relativeDayLabel, todayISO } from '../lib/dates';
import { NO_PLAN_SHORT, planMissing } from '../lib/planPeriods';
import { groupByClass } from '../lib/substitution';

/** Scrollt Inhalt automatisch langsam durch (mit Pausen oben/unten); bei reduzierter Bewegung seitenweise. */
function AutoScroll({ children, speed = 28 }: { children: ReactNode; speed?: number }) {
  const outer = useRef<HTMLDivElement>(null);
  const inner = useRef<HTMLDivElement>(null);
  const reduced = useMediaQuery('(prefers-reduced-motion: reduce)');
  useEffect(() => {
    let raf = 0;
    let pos = 0;
    let phase: 'top' | 'down' | 'bottom' = 'top';
    let phaseStart = performance.now();
    let last = performance.now();
    const step = (t: number) => {
      const o = outer.current;
      const i = inner.current;
      if (!o || !i) return;
      const max = Math.max(0, i.scrollHeight - o.clientHeight);
      const dt = (t - last) / 1000;
      last = t;
      if (max <= 2) {
        pos = 0;
      } else if (phase === 'top') {
        if (t - phaseStart > 5000) {
          phase = 'down';
          phaseStart = t;
        }
      } else if (phase === 'down') {
        if (reduced) {
          if (t - phaseStart > 10000) {
            pos = Math.min(max, pos + o.clientHeight * 0.9);
            phaseStart = t;
          }
        } else pos = Math.min(max, pos + speed * dt);
        if (pos >= max) {
          phase = 'bottom';
          phaseStart = t;
        }
      } else if (t - phaseStart > 5000) {
        pos = 0;
        phase = 'top';
        phaseStart = t;
      }
      i.style.transform = `translateY(${-pos}px)`;
      raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [speed, reduced]);
  return (
    <div className="monitor-scroll" ref={outer}>
      <div className="monitor-scroll-inner" ref={inner}>
        {children}
      </div>
    </div>
  );
}

function teacherText(e: Entry): ReactNode {
  if (e.substitute && e.substitute !== e.teacher) {
    return (
      <>
        <strong>{e.substitute}</strong> {e.teacher && <span className="strike faint">{e.teacher}</span>}
      </>
    );
  }
  return e.teacher ?? '';
}

const SCROLL_SPEED = { langsam: 16, normal: 28, schnell: 48 } as const;

function DayColumn({ plan, speed, showAbsent }: { plan: DayPlan; speed: number; showAbsent: boolean }) {
  const groups = groupByClass(plan.entries.filter((e) => e.kind !== 'aufsicht'));
  return (
    <section className="monitor-col" aria-label={`Vertretungen ${formatLong(plan.date)}`}>
      <h2>
        <span>
          {relativeDayLabel(plan.date)} · {formatLong(plan.date)}
        </span>
        {plan.week_no ? <span>Woche {plan.week_no}</span> : null}
      </h2>
      {showAbsent && plan.absent_classes?.length > 0 && <div className="monitor-absent">Nicht im Haus: {plan.absent_classes.join(', ')}</div>}
      {plan.holiday ? (
        <div className="monitor-empty">{plan.holiday}</div>
      ) : planMissing(plan.week_info?.plan) ? (
        <div className="monitor-empty">{NO_PLAN_SHORT}</div>
      ) : groups.length === 0 ? (
        <div className="monitor-empty">Keine Vertretungen</div>
      ) : (
        <AutoScroll speed={speed}>
          <table>
            <thead>
              <tr>
                <th scope="col">Std.</th>
                <th scope="col">Fach</th>
                <th scope="col">Lehrkraft</th>
                <th scope="col">Raum</th>
                <th scope="col">Art</th>
                <th scope="col">Hinweis</th>
              </tr>
            </thead>
            <tbody>
              {groups.map(([cls, list]) => (
                <Fragment key={cls}>
                  <tr className="class-head">
                    <td colSpan={6}>{cls}</td>
                  </tr>
                  {list.map((e) => (
                    <tr key={e.id}>
                      <td>
                        <strong>{e.period_label || `${e.period + 1}.`}</strong>
                      </td>
                      <td className={e.kind === 'entfall' ? 'strike' : undefined}>{e.subject}</td>
                      <td className="nowrap">{teacherText(e)}</td>
                      <td className="nowrap">{e.new_room && e.new_room !== e.room ? <strong>{e.new_room}</strong> : e.room}</td>
                      <td>
                        <KindBadge kind={e.kind} />
                      </td>
                      <td>{e.note}</td>
                    </tr>
                  ))}
                </Fragment>
              ))}
            </tbody>
          </table>
        </AutoScroll>
      )}
    </section>
  );
}

function SitePicker() {
  const sites = useCollection('sites');
  return (
    <div className="page-narrow" style={{ padding: 24 }}>
      <h1>Monitor-Ansicht</h1>
      <p className="muted">Standort für die Vollbildanzeige wählen:</p>
      <div className="stack-sm">
        <Link className="btn w-100" to="/monitor/alle">
          Alle Standorte
        </Link>
        {(sites.data ?? []).map((s) => (
          <Link key={s.id} className="btn w-100" to={`/monitor/${encodeURIComponent(s.id)}`}>
            {s.name}
          </Link>
        ))}
      </div>
      <p style={{ marginTop: 24 }}>
        <Link to="/">Zurück zur Startseite</Link>
      </p>
    </div>
  );
}

export default function MonitorPage() {
  const { site: siteParam } = useParams<{ site: string }>();
  const { user } = useAuth();
  const now = useNow(1000);
  const [today, setToday] = useState(todayISO());
  const live = useLiveStatus();
  const site = siteParam && siteParam !== 'alle' ? siteParam : undefined;

  // Datumswechsel um Mitternacht
  useEffect(() => {
    const t = todayISO(now);
    if (t !== today) setToday(t);
  }, [now, today]);

  const q = useApi(() => monitorApi.get(site, today), [site, today], {
    enabled: !!siteParam,
    live: ['substitutions', 'absences', 'overrides', 'timetable', 'announcements', 'holidays', 'exams'],
  });
  // zusätzlich minütlich aktualisieren (falls Live-Verbindung gestört)
  useEffect(() => {
    if (!siteParam) return undefined;
    const t = window.setInterval(() => q.reload(), 120_000);
    return () => window.clearInterval(t);
  }, [siteParam, q.reload]); // eslint-disable-line react-hooks/exhaustive-deps

  const data = q.data;
  useTitle(data?.site_name ? `Monitor ${data.site_name}` : 'Monitor');

  if (!siteParam) return <SitePicker />;

  const anns = data?.announcements ?? [];
  const cfg = data?.config;
  const notices = cfg?.notices ?? [];
  const speed = SCROLL_SPEED[cfg?.scroll ?? 'normal'] ?? SCROLL_SPEED.normal;
  return (
    <div className="monitor" style={cfg?.font_scale && cfg.font_scale !== 1 ? { fontSize: `${cfg.font_scale * 100}%` } : undefined}>
      <header className="monitor-head">
        <div>
          <h1>{cfg?.title || data?.school_name || 'Vertretungsplan'}</h1>
          <div>{data?.site_name || (site ? site : 'alle Standorte')}</div>
        </div>
        <div className="grow" />
        <div className="monitor-date">
          <div>{formatLong(today)}</div>
          <div className="xsmall" aria-live="off">
            {live === 'open' ? '● live' : '○ verbinde …'}
          </div>
        </div>
        <div className="monitor-clock" aria-label="Uhrzeit">
          {formatClock(now)}
        </div>
        {user?.role !== 'monitor' && (
          <button
            type="button"
            className="btn btn-ghost btn-icon"
            style={{ color: 'inherit' }}
            aria-label="Vollbild"
            onClick={() => {
              void document.documentElement.requestFullscreen?.().catch(() => undefined);
            }}
          >
            <Icon name="fullscreen" />
          </button>
        )}
      </header>
      {q.error && !data ? (
        <div style={{ padding: 16 }}>
          <ErrorBox error={q.error} onRetry={q.reload} />
        </div>
      ) : !data ? (
        <Loading />
      ) : (
        <>
          {notices.length > 0 && (
            <div className="monitor-notices" role="note">
              {notices.map((n, i) => (
                <div key={i} className={`monitor-notice${n.important ? ' important' : ''}`}>
                  {n.text}
                </div>
              ))}
            </div>
          )}
          <div className="monitor-body">
            {data.days.length === 0 && <div className="monitor-empty">Keine Daten</div>}
            {data.days.map((d) => (
              <DayColumn key={d.date} plan={d} speed={speed} showAbsent={cfg?.show_absent_classes ?? true} />
            ))}
          </div>
        </>
      )}
      {(anns.length > 0 || !!cfg?.ticker) && (
        <footer className="monitor-foot" aria-label="Mitteilungen">
          <div className="monitor-ticker">
            {cfg?.ticker && <span style={{ marginRight: '4em' }}>{cfg.ticker}</span>}
            {anns.map((a) => (
              <span key={a.id} style={{ marginRight: '4em' }}>
                <strong>{a.title}</strong>
                {a.body ? ` – ${a.body.replace(/\s+/g, ' ').slice(0, 300)}` : ''}
              </span>
            ))}
          </div>
        </footer>
      )}
    </div>
  );
}
