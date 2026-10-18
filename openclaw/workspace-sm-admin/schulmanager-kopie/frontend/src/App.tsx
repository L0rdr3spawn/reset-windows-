import { lazy, Suspense, type ReactNode } from 'react';
import { BrowserRouter, Link, Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom';
import { AppLayout, FeatureBoundary } from './components/Layout';
import { Icon } from './components/Icon';
import { Alert, Empty, Loading } from './components/ui';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { ToastProvider } from './context/ToastContext';
import { ConfirmHost } from './components/ConfirmHost';
import { canManageLicense } from './lib/license';
import { featureRoutes, routeAllowed, type FeatureRoute } from './features/registry';
import { useTitle } from './hooks/misc';
import { APP_NAME } from './brand';
import { canAccessPath, homePath } from './lib/permissions';
import LoginPage from './pages/LoginPage';
import SignedOutPage from './pages/SignedOutPage';

/** Seiten der Feature-Module (src/features/<feature>/module.tsx), siehe features/registry.ts */
const FEATURE_ROUTES = featureRoutes();

const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const TimetablePage = lazy(() => import('./pages/TimetablePage'));
const SubstitutionsPage = lazy(() => import('./pages/SubstitutionsPage'));
const PlanningPage = lazy(() => import('./pages/PlanningPage'));
const MasterDataPage = lazy(() => import('./pages/MasterDataPage'));
const ExamsPage = lazy(() => import('./pages/ExamsPage'));
const DutiesPage = lazy(() => import('./pages/DutiesPage'));
const AnnouncementsPage = lazy(() => import('./pages/AnnouncementsPage'));
const StudentAbsencesPage = lazy(() => import('./pages/StudentAbsencesPage'));
const UsersPage = lazy(() => import('./pages/UsersPage'));
const ImportExportPage = lazy(() => import('./pages/ImportExportPage'));
const HistoryPage = lazy(() => import('./pages/HistoryPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const AdminPage = lazy(() => import('./pages/AdminPage'));
const MonitorPage = lazy(() => import('./pages/MonitorPage'));
const MonitorAdminPage = lazy(() => import('./pages/MonitorAdminPage'));
const LicensePage = lazy(() => import('./pages/LicensePage'));
const LicenseLockedPage = lazy(() => import('./pages/LicenseLockedPage'));
const RightsPage = lazy(() => import('./pages/RightsPage'));
const SetupPage = lazy(() => import('./pages/SetupPage'));
const ChangePasswordPage = lazy(() => import('./pages/ChangePasswordPage'));
const TwoFactorSetupPage = lazy(() => import('./pages/TwoFactorSetupPage'));
const PrintSubstitutionsPage = lazy(() => import('./pages/PrintSubstitutionsPage'));
const AccessLettersPage = lazy(() => import('./pages/AccessLettersPage'));
// Erweiterung 4 (§11): öffentliche Konto-Seiten und Pflicht-Verknüpfungen
const ForgotPasswordPage = lazy(() => import('./features/konto/ForgotPasswordPage'));
const ResetPasswordPage = lazy(() => import('./features/konto/ResetPasswordPage'));
const DevOutboxPage = lazy(() => import('./features/konto/DevOutboxPage'));
const LinkSetupPage = lazy(() => import('./features/anmelderichtlinien/LinkSetupPage'));

function BootScreen() {
  const { bootError, refresh } = useAuth();
  if (bootError) {
    return (
      <div className="login-wrap">
        <div className="card login-card">
          <Alert
            kind="error"
            title="Server nicht erreichbar"
            action={
              <button type="button" className="btn btn-sm" onClick={() => void refresh()}>
                <Icon name="refresh" /> Erneut
              </button>
            }
          >
            {bootError}
          </Alert>
        </div>
      </div>
    );
  }
  return <Loading label={`${APP_NAME} wird geladen …`} />;
}

/**
 * Schützt Routen: Anmeldung, Passwortwechsel-Zwang, Pflicht-Verknüpfungen (§11.5), Rechte. `inFrame`: die Rechte
 * prüft {@link AccessGate} innerhalb des App-Rahmens (Menü bleibt bei „Kein Zugriff“ erhalten, U-38).
 */
function Guard({
  children,
  allowPasswordChange,
  allowLinkSetup,
  inFrame,
}: {
  children: ReactNode;
  allowPasswordChange?: boolean;
  allowLinkSetup?: boolean;
  inFrame?: boolean;
}) {
  const { user, loading, bootError } = useAuth();
  const location = useLocation();
  if (loading || (bootError && !user)) return <BootScreen />;
  if (!user) {
    const next = location.pathname + location.search;
    return <Navigate to={`/login${next && next !== '/' ? `?next=${encodeURIComponent(next)}` : ''}`} replace />;
  }
  if (user.must_change_password && !allowPasswordChange) return <Navigate to="/passwort" replace />;
  if (user.totp_setup_required && !user.totp_enabled && !allowPasswordChange) return <Navigate to="/zwei-faktor" replace />;
  if (user.login_setup?.missing_links?.length && !allowPasswordChange && !allowLinkSetup) return <Navigate to="/konten-verbinden" replace />;
  // Lizenz gesperrt (oder frische Instanz ohne Lizenz): nichts außer der Sperrseite; Konten mit `license.manage`
  // landen auf /lizenz (dort gibt es die neue Lizenz ein). Passwortwechsel bleibt möglich (Einmal-Passwort).
  if (user.license?.locked && !allowPasswordChange) {
    if (canManageLicense(user) && location.pathname !== '/lizenz') return <Navigate to="/lizenz" replace />;
    return (
      <S>
        <LicenseLockedPage />
      </S>
    );
  }
  if (allowLinkSetup || inFrame) return <>{children}</>;
  if (!canAccessPath(user, location.pathname)) {
    if (user.role === 'monitor') return <Navigate to={homePath(user)} replace />;
    return <Forbidden />;
  }
  return <>{children}</>;
}

/** Rechteprüfung der Seiten im App-Rahmen: „Kein Zugriff“ mit Menü und Rückweg statt leerer Seite (U-38). */
function AccessGate() {
  const { user } = useAuth();
  const location = useLocation();
  if (!canAccessPath(user, location.pathname)) {
    if (user?.role === 'monitor') return <Navigate to={homePath(user)} replace />;
    return <Forbidden />;
  }
  return <Outlet />;
}

function Forbidden() {
  useTitle('Kein Zugriff');
  return (
    <div className="page-narrow">
      <h1>Kein Zugriff</h1>
      <Empty
        icon="lock"
        title="Für diese Seite fehlt Ihrem Konto die Berechtigung."
        action={
          <Link className="btn btn-primary" to="/">
            Zur Startseite
          </Link>
        }
      />
    </div>
  );
}

function NotFound() {
  useTitle('Seite nicht gefunden');
  return (
    <div className="notfound">
      <h1>Seite nicht gefunden</h1>
      <p className="muted">Die aufgerufene Adresse gibt es nicht.</p>
      <Link className="btn btn-primary" to="/">
        Zur Startseite
      </Link>
    </div>
  );
}

function HomeRoute() {
  const { user } = useAuth();
  if (user?.role === 'monitor') return <Navigate to={homePath(user)} replace />;
  return <DashboardPage />;
}

function S({ children }: { children: ReactNode }) {
  return <Suspense fallback={<Loading />}>{children}</Suspense>;
}

/**
 * Rechteprüfung einer Feature-Route (zusätzlich zum Guard, der über `canAccessPath` auch die Routenregeln kennt)
 * + Fehlergrenze (setzt sich beim Seitenwechsel zurück) + Lazy-Loading.
 */
function FeatureRouteElement({ route }: { route: FeatureRoute }) {
  const { user } = useAuth();
  const location = useLocation();
  if (!routeAllowed(user, route)) {
    if (user?.role === 'monitor') return <Navigate to={homePath(user)} replace />;
    return <Forbidden />;
  }
  return (
    <FeatureBoundary key={route.path} resetKey={location.pathname}>
      <S>{route.element}</S>
    </FeatureBoundary>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <ConfirmHost />
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/abgemeldet" element={<SignedOutPage />} />
              <Route path="/passwort-vergessen" element={<S><ForgotPasswordPage /></S>} />
              <Route path="/passwort-zuruecksetzen" element={<S><ResetPasswordPage /></S>} />
              <Route path="/test-postausgang" element={<S><DevOutboxPage /></S>} />
              <Route
                path="/konten-verbinden"
                element={
                  <Guard allowLinkSetup>
                    <S>
                      <LinkSetupPage />
                    </S>
                  </Guard>
                }
              />
              <Route
                path="/passwort"
                element={
                  <Guard allowPasswordChange>
                    <S>
                      <ChangePasswordPage />
                    </S>
                  </Guard>
                }
              />
              <Route
                path="/zwei-faktor"
                element={
                  <Guard allowPasswordChange>
                    <S>
                      <TwoFactorSetupPage />
                    </S>
                  </Guard>
                }
              />
              <Route
                path="/monitor/:site?"
                element={
                  <Guard>
                    <S>
                      <MonitorPage />
                    </S>
                  </Guard>
                }
              />
              <Route
                path="/druck/vertretung"
                element={
                  <Guard>
                    <S>
                      <PrintSubstitutionsPage />
                    </S>
                  </Guard>
                }
              />
              <Route
                path="/druck/zugangsbriefe"
                element={
                  <Guard>
                    <S>
                      <AccessLettersPage />
                    </S>
                  </Guard>
                }
              />
              {FEATURE_ROUTES.filter((r) => r.layout === false).map((r) => (
                <Route
                  key={r.path}
                  path={r.path}
                  element={
                    <Guard>
                      <FeatureRouteElement route={r} />
                    </Guard>
                  }
                />
              ))}
              <Route
                element={
                  <Guard inFrame>
                    <AppLayout />
                  </Guard>
                }
              >
                <Route element={<AccessGate />}>
                  <Route index element={<S><HomeRoute /></S>} />
                  <Route path="stundenplan" element={<S><TimetablePage /></S>} />
                  <Route path="stundenplan/:kind" element={<S><TimetablePage /></S>} />
                  <Route path="stundenplan/:kind/:ref" element={<S><TimetablePage /></S>} />
                  <Route path="vertretung" element={<S><SubstitutionsPage /></S>} />
                  <Route path="planung" element={<S><PlanningPage /></S>} />
                  <Route path="planung/:tab" element={<S><PlanningPage /></S>} />
                  <Route path="stammdaten" element={<S><MasterDataPage /></S>} />
                  <Route path="stammdaten/:tab" element={<S><MasterDataPage /></S>} />
                  <Route path="klausuren" element={<S><ExamsPage /></S>} />
                  <Route path="aufsichten" element={<S><DutiesPage /></S>} />
                  <Route path="mitteilungen" element={<S><AnnouncementsPage /></S>} />
                  <Route path="krankmeldungen" element={<S><StudentAbsencesPage /></S>} />
                  <Route path="benutzer" element={<S><UsersPage /></S>} />
                  <Route path="monitore" element={<S><MonitorAdminPage /></S>} />
                  <Route path="lizenz" element={<S><LicensePage /></S>} />
                  <Route path="rechte" element={<S><RightsPage /></S>} />
                  <Route path="einrichtung" element={<S><SetupPage /></S>} />
                  <Route path="daten" element={<S><ImportExportPage /></S>} />
                  <Route path="verlauf" element={<S><HistoryPage /></S>} />
                  <Route path="profil" element={<S><ProfilePage /></S>} />
                  <Route path="system" element={<S><AdminPage /></S>} />
                  {FEATURE_ROUTES.filter((r) => r.layout !== false).map((r) => (
                    <Route key={r.path} path={r.path.slice(1)} element={<FeatureRouteElement route={r} />} />
                  ))}
                  <Route path="*" element={<NotFound />} />
                </Route>
              </Route>
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ToastProvider>
    </ThemeProvider>
  );
}
