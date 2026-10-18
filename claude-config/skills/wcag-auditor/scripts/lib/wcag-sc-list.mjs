/**
 * wcag-sc-list.mjs - canonical list of all 86 WCAG 2.2 success criteria.
 *
 * Keep in sync with references/wcag-2.2-criteria.md.
 */

export const WCAG_SCS = [
  { sc: '1.1.1', level: 'A',   title: 'Non-text Content', newIn22: false },
  { sc: '1.2.1', level: 'A',   title: 'Audio-only and Video-only (Prerecorded)', newIn22: false },
  { sc: '1.2.2', level: 'A',   title: 'Captions (Prerecorded)', newIn22: false },
  { sc: '1.2.3', level: 'A',   title: 'Audio Description or Media Alternative (Prerecorded)', newIn22: false },
  { sc: '1.2.4', level: 'AA',  title: 'Captions (Live)', newIn22: false },
  { sc: '1.2.5', level: 'AA',  title: 'Audio Description (Prerecorded)', newIn22: false },
  { sc: '1.2.6', level: 'AAA', title: 'Sign Language (Prerecorded)', newIn22: false },
  { sc: '1.2.7', level: 'AAA', title: 'Extended Audio Description (Prerecorded)', newIn22: false },
  { sc: '1.2.8', level: 'AAA', title: 'Media Alternative (Prerecorded)', newIn22: false },
  { sc: '1.2.9', level: 'AAA', title: 'Audio-only (Live)', newIn22: false },
  { sc: '1.3.1', level: 'A',   title: 'Info and Relationships', newIn22: false },
  { sc: '1.3.2', level: 'A',   title: 'Meaningful Sequence', newIn22: false },
  { sc: '1.3.3', level: 'A',   title: 'Sensory Characteristics', newIn22: false },
  { sc: '1.3.4', level: 'AA',  title: 'Orientation', newIn22: false },
  { sc: '1.3.5', level: 'AA',  title: 'Identify Input Purpose', newIn22: false },
  { sc: '1.3.6', level: 'AAA', title: 'Identify Purpose', newIn22: false },
  { sc: '1.4.1', level: 'A',   title: 'Use of Color', newIn22: false },
  { sc: '1.4.2', level: 'A',   title: 'Audio Control', newIn22: false },
  { sc: '1.4.3', level: 'AA',  title: 'Contrast (Minimum)', newIn22: false },
  { sc: '1.4.4', level: 'AA',  title: 'Resize Text', newIn22: false },
  { sc: '1.4.5', level: 'AA',  title: 'Images of Text', newIn22: false },
  { sc: '1.4.6', level: 'AAA', title: 'Contrast (Enhanced)', newIn22: false },
  { sc: '1.4.7', level: 'AAA', title: 'Low or No Background Audio', newIn22: false },
  { sc: '1.4.8', level: 'AAA', title: 'Visual Presentation', newIn22: false },
  { sc: '1.4.9', level: 'AAA', title: 'Images of Text (No Exception)', newIn22: false },
  { sc: '1.4.10', level: 'AA',  title: 'Reflow', newIn22: false },
  { sc: '1.4.11', level: 'AA',  title: 'Non-text Contrast', newIn22: false },
  { sc: '1.4.12', level: 'AA',  title: 'Text Spacing', newIn22: false },
  { sc: '1.4.13', level: 'AA',  title: 'Content on Hover or Focus', newIn22: false },
  { sc: '2.1.1', level: 'A',   title: 'Keyboard', newIn22: false },
  { sc: '2.1.2', level: 'A',   title: 'No Keyboard Trap', newIn22: false },
  { sc: '2.1.3', level: 'AAA', title: 'Keyboard (No Exception)', newIn22: false },
  { sc: '2.1.4', level: 'A',   title: 'Character Key Shortcuts', newIn22: false },
  { sc: '2.2.1', level: 'A',   title: 'Timing Adjustable', newIn22: false },
  { sc: '2.2.2', level: 'A',   title: 'Pause, Stop, Hide', newIn22: false },
  { sc: '2.2.3', level: 'AAA', title: 'No Timing', newIn22: false },
  { sc: '2.2.4', level: 'AAA', title: 'Interruptions', newIn22: false },
  { sc: '2.2.5', level: 'AAA', title: 'Re-authenticating', newIn22: false },
  { sc: '2.2.6', level: 'AAA', title: 'Timeouts', newIn22: false },
  { sc: '2.3.1', level: 'A',   title: 'Three Flashes or Below Threshold', newIn22: false },
  { sc: '2.3.2', level: 'AAA', title: 'Three Flashes', newIn22: false },
  { sc: '2.3.3', level: 'AAA', title: 'Animation from Interactions', newIn22: false },
  { sc: '2.4.1', level: 'A',   title: 'Bypass Blocks', newIn22: false },
  { sc: '2.4.2', level: 'A',   title: 'Page Titled', newIn22: false },
  { sc: '2.4.3', level: 'A',   title: 'Focus Order', newIn22: false },
  { sc: '2.4.4', level: 'A',   title: 'Link Purpose (In Context)', newIn22: false },
  { sc: '2.4.5', level: 'AA',  title: 'Multiple Ways', newIn22: false },
  { sc: '2.4.6', level: 'AA',  title: 'Headings and Labels', newIn22: false },
  { sc: '2.4.7', level: 'AA',  title: 'Focus Visible', newIn22: false },
  { sc: '2.4.8', level: 'AAA', title: 'Location', newIn22: false },
  { sc: '2.4.9', level: 'AAA', title: 'Link Purpose (Link Only)', newIn22: false },
  { sc: '2.4.10', level: 'AAA', title: 'Section Headings', newIn22: false },
  { sc: '2.4.11', level: 'AA',  title: 'Focus Not Obscured (Minimum)', newIn22: true },
  { sc: '2.4.12', level: 'AAA', title: 'Focus Not Obscured (Enhanced)', newIn22: true },
  { sc: '2.4.13', level: 'AAA', title: 'Focus Appearance', newIn22: true },
  { sc: '2.5.1', level: 'A',   title: 'Pointer Gestures', newIn22: false },
  { sc: '2.5.2', level: 'A',   title: 'Pointer Cancellation', newIn22: false },
  { sc: '2.5.3', level: 'A',   title: 'Label in Name', newIn22: false },
  { sc: '2.5.4', level: 'A',   title: 'Motion Actuation', newIn22: false },
  { sc: '2.5.5', level: 'AAA', title: 'Target Size (Enhanced)', newIn22: false },
  { sc: '2.5.6', level: 'AAA', title: 'Concurrent Input Mechanisms', newIn22: false },
  { sc: '2.5.7', level: 'AA',  title: 'Dragging Movements', newIn22: true },
  { sc: '2.5.8', level: 'AA',  title: 'Target Size (Minimum)', newIn22: true },
  { sc: '3.1.1', level: 'A',   title: 'Language of Page', newIn22: false },
  { sc: '3.1.2', level: 'AA',  title: 'Language of Parts', newIn22: false },
  { sc: '3.1.3', level: 'AAA', title: 'Unusual Words', newIn22: false },
  { sc: '3.1.4', level: 'AAA', title: 'Abbreviations', newIn22: false },
  { sc: '3.1.5', level: 'AAA', title: 'Reading Level', newIn22: false },
  { sc: '3.1.6', level: 'AAA', title: 'Pronunciation', newIn22: false },
  { sc: '3.2.1', level: 'A',   title: 'On Focus', newIn22: false },
  { sc: '3.2.2', level: 'A',   title: 'On Input', newIn22: false },
  { sc: '3.2.3', level: 'AA',  title: 'Consistent Navigation', newIn22: false },
  { sc: '3.2.4', level: 'AA',  title: 'Consistent Identification', newIn22: false },
  { sc: '3.2.5', level: 'AAA', title: 'Change on Request', newIn22: false },
  { sc: '3.2.6', level: 'A',   title: 'Consistent Help', newIn22: true },
  { sc: '3.3.1', level: 'A',   title: 'Error Identification', newIn22: false },
  { sc: '3.3.2', level: 'A',   title: 'Labels or Instructions', newIn22: false },
  { sc: '3.3.3', level: 'AA',  title: 'Error Suggestion', newIn22: false },
  { sc: '3.3.4', level: 'AA',  title: 'Error Prevention (Legal, Financial, Data)', newIn22: false },
  { sc: '3.3.5', level: 'AAA', title: 'Help', newIn22: false },
  { sc: '3.3.6', level: 'AAA', title: 'Error Prevention (All)', newIn22: false },
  { sc: '3.3.7', level: 'A',   title: 'Redundant Entry', newIn22: true },
  { sc: '3.3.8', level: 'AA',  title: 'Accessible Authentication (Minimum)', newIn22: true },
  { sc: '3.3.9', level: 'AAA', title: 'Accessible Authentication (Enhanced)', newIn22: true },
  { sc: '4.1.2', level: 'A',   title: 'Name, Role, Value', newIn22: false },
  { sc: '4.1.3', level: 'AA',  title: 'Status Messages', newIn22: false },
];

export function filterByLevel(scs, targetLevel) {
  if (targetLevel === 'AAA') return scs;
  // AA (default) includes A + AA
  return scs.filter((s) => s.level === 'A' || s.level === 'AA');
}

export function scTagFromAxe(axeTag) {
  // axe tag 'wcag143' -> '1.4.3'
  const m = axeTag.match(/^wcag(\d)(\d)(\d+)$/);
  if (!m) return null;
  return `${m[1]}.${m[2]}.${m[3]}`;
}
