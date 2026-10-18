/**
 * Generator › Zeitraum (Planzeiträume, `lib/planPeriods.ts`): für welchen Zeitraum der Entwurf gerechnet wird, optional
 * mit dem Plan eines anderen Zeitraums als fixiertem Start. Als eigener Baustein, damit `GeneratorPanel` nur einen
 * Aufruf (`usePlanPeriod`) und den Block `node` einbindet. Ohne eingerichtete Zeiträume erscheint nichts, und der
 * Generator rechnet wie bisher den Plan für das ganze Schuljahr.
 */
import { useEffect, useState, type ReactNode } from 'react';
import { useSearchParams } from 'react-router-dom';
import { calendar } from '../../api/endpoints';
import type { PlanPeriod } from '../../api/types';
import { Alert, Field } from '../../components/ui';
import { useApi } from '../../hooks/useApi';
import { periodSpan } from '../../lib/planPeriods';

export interface PlanPeriodChoice {
  /** Zeiträume sind eingerichtet */
  active: boolean;
  periods: PlanPeriod[];
  period: string;
  /** Angaben für den Generate-Aufruf (`period`, `copy_from`) */
  params: { period?: string; copy_from?: string };
  /** darf gestartet werden (Zeiträume eingerichtet → Zeitraum gewählt) */
  ready: boolean;
  /** Formularfelder für das Raster des Generators */
  node: ReactNode;
}

export function usePlanPeriod(disabled: boolean): PlanPeriodChoice {
  const q = useApi((signal) => calendar.planPeriods(signal), [], { live: ['settings', 'timetable'] });
  const [sp] = useSearchParams();
  const [period, setPeriod] = useState('');
  const [copyFrom, setCopyFrom] = useState('');
  const data = q.data;
  const active = !!data?.active;
  const periods = data?.periods ?? [];
  useEffect(() => {
    if (!data?.active) return;
    if (period && periods.some((p) => p.id === period)) return;
    const wanted = sp.get('zeitraum');
    setPeriod((wanted && periods.some((p) => p.id === wanted) ? wanted : data.target) ?? periods[0]?.id ?? '');
  }, [data]); // eslint-disable-line react-hooks/exhaustive-deps
  const current = periods.find((p) => p.id === period);
  const sources = periods.filter((p) => p.id !== period && p.lessons > 0);
  const from = sources.some((p) => p.id === copyFrom) ? copyFrom : '';
  const node = active ? (
    <>
      <Field
        label="Zeitraum"
        htmlFor="gen-period"
        help="Der Entwurf gilt nach dem Übernehmen nur für diesen Zeitraum. Der Stundenplan der übrigen Zeiträume bleibt unverändert. Zeiträume legen Sie unter Planung › Zeitraster & Schuljahr fest."
      >
        <select id="gen-period" value={period} disabled={disabled} onChange={(e) => setPeriod(e.target.value)}>
          {periods.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name} ({periodSpan(p)}){p.lessons > 0 ? '' : ' – noch kein Plan'}
            </option>
          ))}
        </select>
      </Field>
      <Field
        label="Start"
        htmlFor="gen-copy"
        help="Neu rechnen: der Generator plant alle Kurse des Zeitraums. Mit dem Plan eines anderen Zeitraums als Start werden dessen Stunden übernommen und fixiert; der Generator ergänzt nur, was fehlt. Das eignet sich für Halbjahre mit wenigen Änderungen."
      >
        <select id="gen-copy" value={from} disabled={disabled || sources.length === 0} onChange={(e) => setCopyFrom(e.target.value)}>
          <option value="">Neu rechnen</option>
          {sources.map((p) => (
            <option key={p.id} value={p.id}>
              Plan aus {p.name} als Start
            </option>
          ))}
        </select>
      </Field>
    </>
  ) : null;
  return {
    active,
    periods,
    period,
    params: active ? { period, ...(from ? { copy_from: from } : {}) } : {},
    ready: !active || !!current,
    node,
  };
}

/** Hinweis über dem Ergebnis: der Entwurf gilt nur für den gewählten Zeitraum */
export function PeriodJobNote({ params, periods }: { params?: { period?: string; copy_from?: string } | null; periods: PlanPeriod[] }) {
  const p = periods.find((x) => x.id === params?.period);
  if (!params?.period) return null;
  const src = periods.find((x) => x.id === params.copy_from);
  return (
    <Alert kind="info" title={`Entwurf für ${p?.name ?? 'einen Zeitraum'}`}>
      Beim Übernehmen wird nur der Stundenplan dieses Zeitraums ersetzt.{src ? ` Start war der Plan aus ${src.name}.` : ''}
    </Alert>
  );
}
