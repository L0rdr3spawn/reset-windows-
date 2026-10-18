import { MakeupPanel } from './MakeupPanel';

/** Startseiten-Kachel: erscheint nur, wenn Nachschreibtermine anstehen. */
export default function MakeupWidget() {
  return <MakeupPanel heading="Nachschreibtermine" hideWhenEmpty />;
}
