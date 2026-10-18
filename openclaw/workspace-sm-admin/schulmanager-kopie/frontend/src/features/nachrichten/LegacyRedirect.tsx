/** Leitet alte Adressen (`/postfach…`, `/chats…`) auf `/nachrichten…` um (siehe `legacy.ts`). */
import { Navigate, useLocation } from 'react-router-dom';
import { legacyTarget } from './legacy';

export default function LegacyRedirect() {
  const { pathname, search } = useLocation();
  return <Navigate to={legacyTarget(pathname, search) ?? '/nachrichten'} replace />;
}
