import { Component, useEffect, useRef, useState, type ErrorInfo, type ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { http } from '../api/client';
import { useUser } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { backgroundComponents, badgeText, navBadge, useBadgeVersion } from '../features/registry';
import { useApi } from '../hooks/useApi';
import { useLiveStatus } from '../hooks/useLive';
import { WeekCalendarOutlet } from './WeekCalendarSync';
import { useSettings } from '../hooks/useCollection';
import { bottomNavItems, bottomNavLabel, shouldRestoreMenuFocus } from '../lib/layout';
import { NAV_GROUP_LABELS, NAV_GROUP_ORDER, ROLE_LABELS, bestNavMatch, pageTitleFor, visibleNav, type NavItem } from '../lib/permissions';
import { setHelpInline } from '../lib/help';
import { useHelpInline } from './Help';
import { AccountSwitcher, AddAccountModal, LogoutConfirm } from './AccountSwitcher';
import { ParentAccessBanner } from '../features/elternzugriff/ParentAccessSection';
import { NotificationBell } from '../features/benachrichtigungen/Bell';
import { Icon } from './Icon';
import { canManageLicense, licenseBanner } from '../lib/license';
import { BrandLogo } from './BrandLogo';
import { APP_NAME } from '../brand';

interface FeatureBoundaryProps {
  children: ReactNode;
  label?: string;
  /** nichts anzeigen (für unsichtbare Hintergrund-Komponenten) */
  silent?: boolean;
  /** ändert sich der Wert (z. B. Pfad), wird ein Fehlerzustand zurückgesetzt */
  resetKey?: string;
}

/**
 * Fehlergrenze für Feature-Bereiche (Seiten, Startseiten-Kacheln, Hintergrund-Komponenten): Ein Fehler in einem
 * Feature legt nicht die ganze Anwendung lahm. `silent` zeigt nichts an (für unsichtbare Hintergrund-Komponenten).
 */
export class FeatureBoundary extends Component<FeatureBoundaryProps, { failed: boolean }> {
  override state = { failed: false };

  static getDerivedStateFromError(): { failed: boolean } {
    return { failed: true };
  }

  override componentDidCatch(error: unknown, info: ErrorInfo): void {
    console.error(`[features] Fehler in ${this.props.label ?? 'Feature'}`, error, info.componentStack);
  }

  override componentDidUpdate(prev: FeatureBoundaryProps): void {
    if (this.state.failed && prev.resetKey !== this.props.resetKey) this.setState({ failed: false });
  }

  override render(): ReactNode {
    if (!this.state.failed) return this.props.children;
    if (this.props.silent) return null;
    return (
      <div className="alert alert-error" role="alert">
        <Icon name="alert" />
        <div className="alert-body">
          <strong>{this.props.label ? `${this.props.label}: ` : ''}Bereich konnte nicht angezeigt werden</strong>
          <div>Bitte die Seite neu laden. Besteht das Problem weiter, informieren Sie bitte die Schulverwaltung.</div>
        </div>
      </div>
    );
  }
}

/** Unsichtbare Hintergrund-Komponenten der Feature-Module (z. B. Badges per Live-Ereignis aktualisieren). */
function FeatureBackgrounds() {
  const list = backgroundComponents();
  if (!list.length) return null;
  // hidden: versehentliche Ausgaben stören das Raster des App-Rahmens nicht
  return (
    <div hidden>
      {list.map(({ id, Component: Bg }) => (
        <FeatureBoundary key={id} label={id} silent>
          <Bg />
        </FeatureBoundary>
      ))}
    </div>
  );
}

function NavBadge({ item, count }: { item: NavItem; count: number }) {
  const text = item.badgeLabel ? item.badgeLabel(count) : `${count} neu`;
  return (
    <span className="badge badge-danger nav-badge">
      <span aria-hidden="true">{badgeText(count)}</span>
      <span className="sr-only">, {text}</span>
    </span>
  );
}

/** Neue oder noch nicht fertig eingerichtete Schule: Admin auf den Einrichtungs-Assistenten hinweisen (außer auf dessen Seite). */
function SetupHint() {
  const location = useLocation();
  const q = useApi((signal) => http.get<{ empty: boolean; banner?: boolean }>('/setup/status', undefined, { signal }).catch(() => null), []);
  if (!q.data?.banner || location.pathname.startsWith('/einrichtung')) return null;
  return (
    <div className="alert alert-info readonly-banner" role="note">
      <Icon name="cog" /> {q.data.empty ? 'Neue Schule ohne Daten' : 'Einrichtung noch nicht abgeschlossen'} –{' '}
      <Link to="/einrichtung">Schule einrichten</Link>
    </div>
  );
}

const LIVE_TEXT = { idle: 'Live aus', connecting: 'Verbinde …', open: 'Live', error: 'Offline – verbinde neu' } as const;

function ThemeButton() {
  const { mode, nextMode } = useTheme();
  const label = mode === 'system' ? 'Farbschema: System' : mode === 'light' ? 'Farbschema: Hell' : 'Farbschema: Dunkel';
  return (
    <button type="button" className="btn btn-ghost btn-icon" onClick={nextMode} aria-label={`${label} – umschalten`} title={label}>
      <Icon name={mode === 'system' ? 'contrast' : mode === 'light' ? 'sun' : 'moon'} />
    </button>
  );
}

/** Initialen ohne Anrede/Klammern: „Frau Ludwig“ → „L“, „Stundenplanung (Demo)“ → „SD“ */
export function initialsOf(name: string): string {
  const words = name
    .replace(/[^\p{L}\s-]/gu, ' ')
    .split(/[\s-]+/)
    .filter((w) => w && !['frau', 'herr', 'familie', 'dr'].includes(w.toLowerCase()));
  return (words.length ? words : [name])
    .map((w) => w[0] ?? '')
    .join('')
    .slice(0, 2)
    .toUpperCase();
}

function UserMenu() {
  const user = useUser();
  const [open, setOpen] = useState(false);
  const inlineHelp = useHelpInline();
  const [adding, setAdding] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return undefined;
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false);
    document.addEventListener('mousedown', onDoc);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDoc);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);
  const initials = initialsOf(user.display_name || user.username);
  return (
    <div className="user-menu" ref={ref}>
      <button type="button" className="btn btn-ghost user-btn" aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
        <span className="avatar" aria-hidden="true">
          {initials}
        </span>
        <span className="hide-mobile">{user.display_name || user.username}</span>
        <Icon name="chevronDown" />
      </button>
      {open && (
        <div className="dropdown" role="menu">
          <div className="small muted dropdown-meta">
            {user.username} · {ROLE_LABELS[user.role] ?? user.role}
          </div>
          <hr />
          <Link role="menuitem" className="item" to="/profil" onClick={() => setOpen(false)}>
            <Icon name="user" /> Profil & Sicherheit
          </Link>
          <button role="menuitemcheckbox" aria-checked={inlineHelp} type="button" className="item" onClick={() => setHelpInline(!inlineHelp)}>
            <Icon name={inlineHelp ? 'check' : 'info'} /> Hilfetexte immer anzeigen
          </button>
          <hr />
          <AccountSwitcher onAction={() => setOpen(false)} onAdd={() => setAdding(true)} onLogout={() => setLoggingOut(true)} />
        </div>
      )}
      {adding && <AddAccountModal onClose={() => setAdding(false)} />}
      {loggingOut && <LogoutConfirm onClose={() => setLoggingOut(false)} />}
    </div>
  );
}

/** Untere Leiste am Handy (< 600 px): wichtigste Ziele + „Menü“ (öffnet die Seitenleiste). */
function BottomNav({ items, activePath, menuOpen, onMenu, restBadges }: { items: NavItem[]; activePath?: string; menuOpen: boolean; onMenu: (opener: HTMLElement) => void; restBadges: number }) {
  return (
    <nav className="bottom-nav" aria-label="Schnellzugriff">
      <ul>
        {items.map((i) => {
          const count = navBadge(i);
          const active = i.path === activePath;
          return (
            <li key={i.path}>
              <Link to={i.path} className="bottom-nav-item" aria-current={active ? 'page' : undefined}>
                <Icon name={i.icon} />
                <span>{bottomNavLabel(i)}</span>
                {count ? (
                  <>
                    <span className="bottom-nav-dot" aria-hidden="true" />
                    <span className="sr-only">, {i.badgeLabel ? i.badgeLabel(count) : `${count} neu`}</span>
                  </>
                ) : null}
              </Link>
            </li>
          );
        })}
        <li>
          <button type="button" className="bottom-nav-item" aria-expanded={menuOpen} aria-controls="app-sidebar" onClick={(e) => onMenu(e.currentTarget)}>
            <Icon name="menu" />
            <span>Menü</span>
            {restBadges > 0 && (
              <>
                <span className="bottom-nav-dot" aria-hidden="true" />
                <span className="sr-only">, {restBadges} neu</span>
              </>
            )}
          </button>
        </li>
      </ul>
    </nav>
  );
}

export function AppLayout() {
  const user = useUser();
  const [confirmLogout, setConfirmLogout] = useState(false);
  const licBanner = licenseBanner(user.license, canManageLicense(user));
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const live = useLiveStatus();
  const { data: settings } = useSettings();
  const mainRef = useRef<HTMLElement>(null);
  const first = useRef(true);
  const sidebarRef = useRef<HTMLElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const menuOpener = useRef<HTMLElement | null>(null);
  const wasOpen = useRef(false);
  const toggleMenu = (opener: HTMLElement) => {
    menuOpener.current = opener;
    setMenuOpen((o) => !o);
  };

  useBadgeVersion();
  const items = visibleNav(user);
  const groups = NAV_GROUP_ORDER.map((g) => ({ g, items: items.filter((i) => i.group === g) })).filter((x) => x.items.length);
  const title = pageTitleFor(location.pathname);
  // genau ein Eintrag ist „aktuell“ (längstes Präfix) – z. B. /planung/antraege markiert nicht zusätzlich „Planung“
  const activePath = bestNavMatch(items, location.pathname)?.path;
  const badgeTotal = items.reduce((sum, i) => sum + (navBadge(i) ?? 0), 0);
  const quick = bottomNavItems(items);
  const restBadges = items.filter((i) => !quick.includes(i)).reduce((sum, i) => sum + (navBadge(i) ?? 0), 0);

  useEffect(() => {
    if (!menuOpen) return undefined;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setMenuOpen(false);
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [menuOpen]);

  // Ausgeklapptes Menü: Fokus hinein (sonst bleibt er hinter dem Hintergrund), beim Schließen zurück zum Auslöser
  useEffect(() => {
    if (menuOpen) {
      wasOpen.current = true;
      closeRef.current?.focus();
      return;
    }
    if (!wasOpen.current) return;
    wasOpen.current = false;
    const opener = menuOpener.current;
    if (opener?.isConnected && shouldRestoreMenuFocus<Element>(document.activeElement, sidebarRef.current, document.body)) opener.focus();
  }, [menuOpen]);

  useEffect(() => {
    setMenuOpen(false);
    if (first.current) {
      first.current = false;
      return;
    }
    mainRef.current?.focus({ preventScroll: true });
    window.scrollTo(0, 0);
  }, [location.pathname]);

  return (
    <div className="app-shell">
      <a href="#main" className="skip-link">
        Zum Inhalt springen
      </a>
      <aside id="app-sidebar" ref={sidebarRef} className={`app-sidebar${menuOpen ? ' open' : ''}`} aria-label="Hauptnavigation">
        <Link to="/" className="brand">
          <span className="brand-logo" aria-hidden="true">
            <BrandLogo />
          </span>
          <span>{APP_NAME}</span>
        </Link>
        {menuOpen && (
          <button type="button" ref={closeRef} className="btn btn-ghost btn-icon sidebar-close" aria-label="Menü schließen" onClick={() => setMenuOpen(false)}>
            <Icon name="close" />
          </button>
        )}
        <nav className="nav">
          {groups.map(({ g, items: list }) => (
            <div className="nav-group" key={g}>
              <div className="nav-group-label" id={`nav-${g}`}>
                {NAV_GROUP_LABELS[g]}
              </div>
              <ul aria-labelledby={`nav-${g}`}>
                {list.map((i) => {
                  const count = navBadge(i);
                  const active = i.path === activePath;
                  return (
                    <li key={i.path}>
                      <Link to={i.path} className={active ? 'active' : undefined} aria-current={active ? 'page' : undefined} title={i.label}>
                        <Icon name={i.icon} />
                        <span className="nav-label">{i.label}</span>
                        {count ? <NavBadge item={i} count={count} /> : null}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>
        <div className="sidebar-logout">
          <button type="button" className="nav-logout" onClick={() => setConfirmLogout(true)}>
            <Icon name="logout" />
            <span className="nav-label">Abmelden</span>
          </button>
        </div>
        <div className="sidebar-footer">
          <div>{settings?.school_name ?? ''}</div>
          <div>{ROLE_LABELS[user.role] ?? user.role}</div>
        </div>
      </aside>
      {confirmLogout && <LogoutConfirm onClose={() => setConfirmLogout(false)} />}
      <div className={`sidebar-backdrop${menuOpen ? ' open' : ''}`} onClick={() => setMenuOpen(false)} aria-hidden="true" />
      <header className="app-header">
        <button
          type="button"
          className="btn btn-ghost btn-icon menu-toggle"
          aria-label={`${menuOpen ? 'Menü schließen' : 'Menü öffnen'}${badgeTotal ? ` (${badgeTotal} neu)` : ''}`}
          aria-expanded={menuOpen}
          aria-controls="app-sidebar"
          onClick={(e) => toggleMenu(e.currentTarget)}
        >
          <Icon name={menuOpen ? 'close' : 'menu'} />
          {badgeTotal > 0 && !menuOpen && <span className="menu-dot" aria-hidden="true" />}
        </button>
        <div className="page-title">{title ?? APP_NAME}</div>
        <div className="spacer" />
        <span className={`live-dot ${live}`} role="status" title="Live-Aktualisierung">
          <span className="hide-mobile">{LIVE_TEXT[live]}</span>
          <span className="sr-only show-mobile">{LIVE_TEXT[live]}</span>
        </span>
        <ThemeButton />
        {user.role !== 'monitor' && (
          <FeatureBoundary label="Benachrichtigungen" silent>
            <NotificationBell />
          </FeatureBoundary>
        )}
        <UserMenu />
      </header>
      <main id="main" className="app-main" ref={mainRef} tabIndex={-1}>
        {licBanner && (
          <div className={`alert alert-${licBanner.kind} readonly-banner`} role={licBanner.kind === 'error' ? 'alert' : 'note'}>
            <Icon name={licBanner.kind === 'error' ? 'lock' : 'info'} /> {licBanner.text} {licBanner.link && <Link to="/lizenz">Lizenz</Link>}
          </div>
        )}
        {user.role === 'admin' && <SetupHint />}
        <ParentAccessBanner />
        {user.demo && (
          <div className="alert alert-info readonly-banner" role="note">
            <Icon name="info" /> Demo-Schule mit simulierten Daten – wird jede Nacht neu aufgesetzt.
          </div>
        )}
        {user.role === 'zuschauer' && (
          <div className="alert alert-info readonly-banner" role="note">
            <Icon name="eye" /> Ansichtskonto: Sie sehen alles wie die Schulleitung, können aber nichts ändern.
          </div>
        )}
        <WeekCalendarOutlet />
      </main>
      <BottomNav items={quick} activePath={activePath} menuOpen={menuOpen} onMenu={toggleMenu} restBadges={restBadges} />
      <FeatureBackgrounds />
    </div>
  );
}
