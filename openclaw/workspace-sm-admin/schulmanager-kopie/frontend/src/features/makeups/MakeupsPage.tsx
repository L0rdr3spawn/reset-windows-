import { useTitle } from '../../hooks/misc';
import { MakeupPanel } from './MakeupPanel';

/** `/nachschreiben` – Nachschreibtermine für Lehrkräfte (Klausur), Klassenleitung, Sekretariat und Leitung. */
export default function MakeupsPage() {
  useTitle('Nachschreibtermine');
  return (
    <div className="page">
      <div className="page-head">
        <h1>Nachschreibtermine</h1>
      </div>
      <MakeupPanel heading="Verpasste Klausuren und Tests" />
    </div>
  );
}
