/** `/lernstand` – Schüler/innen (selbst einschätzen) und Eltern (je Kind, nur ansehen). */
import './kompetenzen.css';
import { PageHelp } from '../../components/Help';
import { useUser } from '../../context/AuthContext';
import { useTitle } from '../../hooks/misc';
import { ChildSelect, useFamilyChild } from '../students/useChild';
import { StudentPanel } from './StudentPanel';

export default function PupilPage() {
  useTitle('Mein Lernstand');
  const user = useUser();
  const { parent, child, setChild, kids } = useFamilyChild();
  const sid = parent ? child : (user.student_id ?? user.student_ids?.[0]);
  return (
    <div className="page stack">
      <div className="page-head">
        <h1>{parent ? 'Lernstand' : 'Mein Lernstand'}</h1>
        <PageHelp label="Hilfe zum Lernstand">
          {parent
            ? 'Hier sehen Sie, was Ihr Kind schon kann, den Wochenplan und die Abzeichen. Bei volljährigen Kindern ist die Ansicht nur mit deren Freigabe sichtbar.'
            : 'Hier sehen Sie, was Sie schon können. Schätzen Sie sich selbst ein – Ihre Lehrkraft schaut es sich an und bestätigt es.'}
        </PageHelp>
      </div>
      {parent && <ChildSelect kids={kids} value={child} onChange={setChild} id="cp-child" />}
      {sid ? <StudentPanel studentId={sid} /> : <p className="muted">Es ist kein Kind verknüpft.</p>}
    </div>
  );
}
