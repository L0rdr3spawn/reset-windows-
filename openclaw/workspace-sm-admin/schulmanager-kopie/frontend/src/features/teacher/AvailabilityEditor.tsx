/**
 * „Verfügbarkeit“ einer Lehrkraft – EINE Bedienung für Arbeitszeiten, Sperrzeiten und Wünsche.
 *
 * Jeder **Block** ist ein Raster (Tage × Stunden) zum Antippen: Feld antippen = markiert, nochmal = frei; mit gedrückter
 * Maus/Finger über mehrere Felder ziehen; Tag bzw. Stunde im Kopf antippen = ganze Spalte/Zeile. Darunter stehen für
 * genau diesen Block: Art (Sperre = nie Unterricht / Wunsch = möglichst frei), Rhythmus (jede Woche, alle 2/3/4 Wochen
 * …, bestimmte Wochen), „gilt ab“ (Datum) und eine Notiz. Alles zusammen ergibt die Regeln `unavailable`/`wishes`
 * (siehe `availability.ts`); eine Schnellauswahl gibt es bewusst nicht.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import type { TimeRule } from '../../api/types';
import { DayPeriodGrid, GridLegend, type GridDay, type GridRow } from '../../components/grid/DayPeriodGrid';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { patternRhythm, WeekChips } from '../../components/WeekPatternInput';
import { WEEKDAYS, WEEKDAYS_SHORT } from '../../lib/dates';
import { MAX_WEEKS, normalizeWeeks, selectionWeeks, weekNumberOf, weekWord, weeksPreview } from '../../lib/weeks';
import {
  applyRhythmChoice,
  blockError,
  blocksFromRules,
  cellKey,
  describeCells,
  emptyBlock,
  fitDims,
  minFreePerWeek,
  RHYTHM_LABELS,
  rhythmChoice,
  rulesFromBlocks,
  todayISO,
  type AvBlock,
  type AvKind,
  type RhythmChoice,
} from './availability';
import type { OutsideConflict } from './types';
import { fmtMinutes, toMinutes } from './windows';
import './teacher.css';

type Cells = Set<string>;

function BlockGrid({
  cells,
  onChange,
  days,
  periods,
  periodTimes,
  periodMinutes,
  conflictAt,
  kind,
  disabled,
  label,
}: {
  cells: Cells;
  onChange: (c: Cells) => void;
  days: number;
  periods: number;
  periodTimes: string[];
  periodMinutes: number;
  conflictAt: Map<string, string>;
  kind: AvKind;
  disabled?: boolean;
  label: string;
}) {
  const dayList = useMemo(() => Array.from({ length: days }, (_, d) => d), [days]);
  const periodList = useMemo(() => Array.from({ length: periods }, (_, p) => p), [periods]);
  const drag = useRef<{ mark: boolean; cells: Cells; last: [number, number] } | null>(null);
  const [, setTick] = useState(0);
  const latest = useRef(onChange);
  latest.current = onChange;
  useEffect(() => {
    const end = () => {
      if (!drag.current) return;
      latest.current(drag.current.cells);
      drag.current = null;
      setTick((t) => t + 1);
    };
    window.addEventListener('pointerup', end);
    window.addEventListener('pointercancel', end);
    return () => {
      window.removeEventListener('pointerup', end);
      window.removeEventListener('pointercancel', end);
    };
  }, []);
  const on = (d: number, p: number) => (drag.current ? drag.current.cells : cells).has(cellKey(d, p));
  const paint = (d: number, p: number) => {
    const cur = drag.current;
    if (!cur) return;
    // schnelles Ziehen überspringt Zellen: Rechteck von der letzten bis zur aktuellen Zelle füllen
    const [d0, p0] = cur.last;
    for (let dd = Math.min(d0, d); dd <= Math.max(d0, d); dd++)
      for (let pp = Math.min(p0, p); pp <= Math.max(p0, p); pp++) {
        if (cur.mark) cur.cells.add(cellKey(dd, pp));
        else cur.cells.delete(cellKey(dd, pp));
      }
    cur.last = [d, p];
    setTick((t) => t + 1);
  };
  const start = (d: number, p: number) => {
    if (disabled) return;
    drag.current = { mark: !cells.has(cellKey(d, p)), cells: new Set(cells), last: [d, p] };
    paint(d, p);
  };
  const apply = (fn: (set: Cells) => void) => {
    const set = new Set(cells);
    fn(set);
    onChange(set);
  };
  const dayOn = (d: number) => periodList.every((p) => cells.has(cellKey(d, p)));
  const rowOn = (p: number) => dayList.every((d) => cells.has(cellKey(d, p)));
  const timeOf = (p: number) => {
    const s = toMinutes(periodTimes[p]);
    return s === null ? (periodTimes[p] ?? '') : `${fmtMinutes(s)}–${fmtMinutes(s + periodMinutes)}`;
  };
  const word = kind === 'hard' ? 'gesperrt' : 'Wunsch frei';
  const gridDays: GridDay[] = dayList.map((d) => ({
    key: d,
    name: WEEKDAYS[d] ?? String(d + 1),
    short: WEEKDAYS_SHORT[d] ?? String(d + 1),
    onHeadClick: () => apply((set) => periodList.forEach((p) => (dayOn(d) ? set.delete(cellKey(d, p)) : set.add(cellKey(d, p))))),
    headPressed: dayOn(d),
    headDisabled: disabled,
    headTitle: dayOn(d) ? `${WEEKDAYS[d]} wieder freigeben` : `${WEEKDAYS[d]} ganz markieren`,
    header: <small className="wg-sub">{dayOn(d) ? word : 'frei'}</small>,
  }));
  const gridRows: GridRow[] = periodList.map((p) => ({
    key: p,
    label: `${p + 1}.`,
    time: timeOf(p),
    onHeadClick: () => apply((set) => dayList.forEach((d) => (rowOn(p) ? set.delete(cellKey(d, p)) : set.add(cellKey(d, p))))),
    headPressed: rowOn(p),
    headDisabled: disabled,
    headTitle: rowOn(p) ? `${p + 1}. Stunde an allen Tagen freigeben` : `${p + 1}. Stunde an allen Tagen markieren`,
  }));
  return (
    <DayPeriodGrid
      days={gridDays}
      rows={gridRows}
      label={label}
      gridClassName="editing"
      minWidth={0}
      cell={(d, p) => {
        const off = on(d, p);
        const conflict = off && kind === 'hard' ? conflictAt.get(`${d}:${p}`) : undefined;
        const text = `${WEEKDAYS[d]}, ${p + 1}. Stunde (${timeOf(p)}): ${off ? word : 'frei'}${conflict ? ` – hier liegt noch Unterricht (${conflict})` : ''}`;
        return {
          tone: conflict ? 'conflict' : off ? (kind === 'wish' ? 'wish' : 'bad') : 'free',
          title: text,
          content: (
            <button
              type="button"
              className="tt-fill"
              aria-pressed={off}
              aria-label={text}
              disabled={disabled}
              onPointerDown={(e) => {
                e.preventDefault();
                (e.target as HTMLElement).releasePointerCapture?.(e.pointerId);
                start(d, p);
              }}
              onPointerEnter={() => paint(d, p)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  apply((set) => (set.has(cellKey(d, p)) ? set.delete(cellKey(d, p)) : set.add(cellKey(d, p))));
                }
              }}
            >
              {conflict ? <strong>!</strong> : off ? <Icon name="x" /> : <span className="wg-free">frei</span>}
            </button>
          ),
        };
      }}
    />
  );
}

/** Rhythmus-Auswahl eines Blocks: jede Woche · alle 2/3/4 Wochen · anderer Abstand · bestimmte Wochen. */
function RhythmFields({ block, onChange, yearWeeks, disabled, idBase }: { block: AvBlock; onChange: (p: Partial<AvBlock>) => void; yearWeeks: number; disabled?: boolean; idBase: string }) {
  const choice = rhythmChoice(block);
  const word = weekWord();
  const r = block.rhythm;
  const [pat, setPat] = useState(() => ({
    every: r?.every ?? 2,
    from: r ? weekNumberOf(r.from_week) : weekNumberOf(1),
    to: r?.to_week ? weekNumberOf(r.to_week) : 0,
  }));
  const num = (v: string) => {
    const n = parseInt(v, 10);
    return Number.isFinite(n) ? n : 0;
  };
  const emit = (next: typeof pat) => {
    setPat(next);
    const { rhythm } = patternRhythm(next);
    if (rhythm) onChange({ weeks: [], rhythm });
  };
  const error = blockError(block);
  const preview = r && !error ? weeksPreview(selectionWeeks({ rhythm: r }, yearWeeks), yearWeeks) : '';
  return (
    <div className="stack-sm">
      <div className="field">
        <label htmlFor={`${idBase}-rh`}>Wie oft?</label>
        <select
          id={`${idBase}-rh`}
          value={choice}
          disabled={disabled}
          onChange={(e) => {
            const next = applyRhythmChoice(block, e.target.value as RhythmChoice);
            if (next.rhythm) setPat({ every: next.rhythm.every, from: weekNumberOf(next.rhythm.from_week), to: next.rhythm.to_week ? weekNumberOf(next.rhythm.to_week) : 0 });
            onChange(next);
          }}
        >
          {(Object.keys(RHYTHM_LABELS) as RhythmChoice[]).map((k) => (
            <option key={k} value={k}>
              {RHYTHM_LABELS[k]}
            </option>
          ))}
        </select>
      </div>
      {choice === 'weeks' && (
        <WeekChips
          n={yearWeeks}
          selected={normalizeWeeks(block.weeks)}
          label={`${word === 'KW' ? 'Kalenderwochen' : 'Wochen'} des Schuljahres`}
          disabled={disabled}
          onToggle={(w) => {
            const cur = normalizeWeeks(block.weeks);
            const next = cur.includes(w) ? cur.filter((x) => x !== w) : [...cur, w];
            if (next.length) onChange({ weeks: normalizeWeeks(next), rhythm: null });
          }}
        />
      )}
      {(choice === 'custom' || choice === 'every2' || choice === 'every3' || choice === 'every4') && (
        <div className="week-rhythm">
          {choice === 'custom' && (
            <div className="field">
              <label htmlFor={`${idBase}-ev`}>Alle … Wochen</label>
              <input id={`${idBase}-ev`} type="number" min={2} max={MAX_WEEKS} value={pat.every || ''} disabled={disabled} onChange={(e) => emit({ ...pat, every: num(e.target.value) })} />
            </div>
          )}
          <div className="field">
            <label htmlFor={`${idBase}-from`}>Erste Woche ({word})</label>
            <input id={`${idBase}-from`} type="number" min={1} max={MAX_WEEKS} value={pat.from || ''} disabled={disabled} onChange={(e) => emit({ ...pat, from: num(e.target.value) })} />
          </div>
          <div className="field">
            <label htmlFor={`${idBase}-to`}>Bis {word} (optional)</label>
            <input id={`${idBase}-to`} type="number" min={0} max={MAX_WEEKS} value={pat.to || ''} disabled={disabled} onChange={(e) => emit({ ...pat, to: num(e.target.value) })} />
          </div>
        </div>
      )}
      {error && (
        <span className="error-text" role="alert">
          {error}
        </span>
      )}
      {preview && <span className="week-preview small muted">{preview}</span>}
    </div>
  );
}

export interface AvailabilityValue {
  unavailable: TimeRule[];
  wishes: TimeRule[];
}

export function AvailabilityEditor({
  unavailable,
  wishes,
  onChange,
  days,
  periods,
  periodTimes,
  periodMinutes = 45,
  conflicts = [],
  hours,
  disabled,
  who = 'Sie',
  yearWeeks = 52,
  defaultValidFrom = '',
}: {
  unavailable: TimeRule[];
  wishes: TimeRule[];
  onChange: (v: AvailabilityValue) => void;
  days: number;
  periods: number;
  periodTimes: string[];
  periodMinutes?: number;
  /** Unterricht, der in gesperrten Stunden läge (vom Server) */
  conflicts?: OutsideConflict[];
  /** Deputat (Wochenstunden) für den Hinweis „zu wenig frei“ */
  hours?: number;
  disabled?: boolean;
  /** Anrede in Hinweisen: „Sie“ (eigenes Profil) oder „die Lehrkraft“ (Stammdaten) */
  who?: string;
  yearWeeks?: number;
  /** Vorgabe für „gilt ab“ bei neuen Blöcken (mitten im Jahr: heute) */
  defaultValidFrom?: string;
}) {
  const dims = fitDims([...unavailable, ...wishes], days, periods);
  const D = dims.days;
  const P = dims.periods;
  const [blocks, setBlocks] = useState<AvBlock[]>(() => blocksFromRules(unavailable, wishes, D, P));
  const emitted = useRef<string>(JSON.stringify(rulesFromBlocks(blocks, P)));
  const incoming = JSON.stringify({ unavailable, wishes });

  // Von außen geänderte Regeln (Laden, Zurücksetzen) übernehmen – eigene Änderungen nicht überschreiben
  useEffect(() => {
    if (incoming === emitted.current) return;
    setBlocks(blocksFromRules(unavailable, wishes, D, P));
    emitted.current = incoming;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [incoming]);

  const commit = (next: AvBlock[]) => {
    setBlocks(next);
    const out = rulesFromBlocks(next, P);
    emitted.current = JSON.stringify(out);
    onChange(out);
  };
  const patch = (id: string, p: Partial<AvBlock>) => commit(blocks.map((b) => (b.id === id ? { ...b, ...p } : b)));

  const conflictAt = useMemo(() => {
    const m = new Map<string, string>();
    for (const c of conflicts) for (const p of c.periods) m.set(`${c.day}:${p}`, c.label);
    return m;
  }, [conflicts]);
  const hardRules = useMemo(() => rulesFromBlocks(blocks, P).unavailable, [blocks, P]);
  const free = minFreePerWeek(hardRules, D, P, yearWeeks);
  const conflictCount = [...conflictAt.keys()].filter((k) => blocks.some((b) => b.kind === 'hard' && b.cells.has(k))).length;
  const add = (kind: AvKind) => commit([...blocks, emptyBlock(kind, defaultValidFrom)]);

  return (
    <fieldset className="stack wg" disabled={disabled}>
      <legend>
        Verfügbarkeit{' '}
        <HelpTip label="Anleitung: Verfügbarkeit">
          <strong>So geht&apos;s</strong>
          <ol>
            <li>
              <strong>Block hinzufügen</strong>: „Sperrzeit“ = in diesen Stunden wird nie Unterricht geplant. „Wunsch“ = möglichst keinen Unterricht, wenn der Plan es zulässt.
            </li>
            <li>
              <strong>Felder antippen</strong> (oder mit gedrückter Maus/Finger darüberziehen). Tag oben bzw. Stunde links antippen markiert die ganze Spalte/Zeile.
            </li>
            <li>
              <strong>Wie oft?</strong> Jede Woche, alle 2/3/4 Wochen oder nur bestimmte Wochen. Beispiel: jeden 2. Mittwoch weg = Mittwoch markieren, „Alle 2 Wochen“.
            </li>
            <li>
              <strong>Gilt ab</strong>: Die festen Sperrzeiten gelten normalerweise für das ganze Schuljahr (Feld leer). Soll sich mitten im Jahr etwas ändern, hier das Datum eintragen –
              die Planung bekommt dann einen Hinweis auf betroffenen Unterricht.
            </li>
          </ol>
        </HelpTip>
      </legend>

      {blocks.length === 0 && <p className="small muted">Keine Einschränkung – {who === 'Sie' ? 'Sie sind' : 'die Lehrkraft ist'} zu allen Zeiten verfügbar.</p>}

      {blocks.map((b, i) => {
        const idBase = `av-${b.id}`;
        return (
          <section key={b.id} className={`card stack wg-block ${b.kind}`} aria-label={`Block ${i + 1}`}>
            <div className="row-between">
              <strong className="small">
                {b.kind === 'hard' ? 'Sperrzeit' : 'Wunsch'} · {describeCells(b.cells, P)}
              </strong>
              <button type="button" className="btn btn-sm btn-ghost" onClick={() => commit(blocks.filter((x) => x.id !== b.id))} aria-label={`Block ${i + 1} entfernen`}>
                <Icon name="trash" /> Entfernen
              </button>
            </div>
            <div className="field">
              <label htmlFor={`${idBase}-kind`}>Art</label>
              <select id={`${idBase}-kind`} value={b.kind} onChange={(e) => patch(b.id, { kind: e.target.value as AvKind })}>
                <option value="hard">Sperrzeit – nie Unterricht</option>
                <option value="wish">Wunsch – möglichst kein Unterricht</option>
              </select>
            </div>
            <BlockGrid
              cells={b.cells}
              onChange={(cells) => patch(b.id, { cells })}
              days={D}
              periods={P}
              periodTimes={periodTimes}
              periodMinutes={periodMinutes}
              conflictAt={conflictAt}
              kind={b.kind}
              label={`Block ${i + 1}: ${b.kind === 'hard' ? 'Sperrzeit' : 'Wunsch'}`}
            />
            <RhythmFields block={b} onChange={(p) => patch(b.id, p)} yearWeeks={yearWeeks} idBase={idBase} />
            <div className="row" style={{ alignItems: 'flex-end', flexWrap: 'wrap' }}>
              <div className="field">
                <label htmlFor={`${idBase}-from-date`}>Gilt ab</label>
                <input id={`${idBase}-from-date`} type="date" value={b.valid_from} onChange={(e) => patch(b.id, { valid_from: e.target.value })} />
              </div>
              <button type="button" className="btn btn-sm" onClick={() => patch(b.id, { valid_from: todayISO() })}>
                ab heute
              </button>
              {b.valid_from && (
                <button type="button" className="btn btn-sm btn-ghost" onClick={() => patch(b.id, { valid_from: '' })}>
                  von Schuljahresbeginn an
                </button>
              )}
            </div>
            <p className="small muted" style={{ margin: 0 }}>
              {b.valid_from ? 'Gilt erst ab diesem Tag – davor bleibt alles wie bisher.' : 'Gilt für das ganze Schuljahr.'}
            </p>
            <div className="field">
              <label htmlFor={`${idBase}-note`}>Notiz</label>
              <input id={`${idBase}-note`} type="text" value={b.note} maxLength={200} placeholder="z. B. Praxistag, Teilzeit" onChange={(e) => patch(b.id, { note: e.target.value })} />
            </div>
          </section>
        );
      })}

      <div className="row">
        <button type="button" className="btn btn-sm" onClick={() => add('hard')}>
          <Icon name="plus" /> Sperrzeit hinzufügen
        </button>
        <button type="button" className="btn btn-sm" onClick={() => add('wish')}>
          <Icon name="plus" /> Wunsch hinzufügen
        </button>
      </div>

      <GridLegend
        items={[
          { tone: 'free', label: 'frei – Unterricht möglich' },
          { tone: 'bad', label: 'gesperrt' },
          { tone: 'wish', label: 'Wunsch frei' },
          { tone: 'conflict', label: 'gesperrt, aber noch Unterricht im Plan' },
        ]}
      />

      <ul className="wg-hints">
        {typeof hours === 'number' && hours > 0 && free < hours && (
          <li className="warn">
            <Icon name="alert" /> Nur {free} freie Stunden in der engsten Woche, aber {hours} Wochenstunden Deputat – so lässt sich der Unterricht nicht vollständig planen.
          </li>
        )}
        {conflictCount > 0 && (
          <li className="warn">
            <Icon name="alert" /> {conflictCount} gesperrte Stunde{conflictCount === 1 ? '' : 'n'} mit Unterricht im aktuellen Plan – die Stundenplanung bekommt dazu einen Hinweis mit Lösungsvorschlägen.
          </li>
        )}
      </ul>
    </fieldset>
  );
}
