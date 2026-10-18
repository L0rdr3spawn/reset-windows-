---
name: keine-eigenen-screenshots-als-test
description: Geofinder testen nie mit Aufnahmen vom Bildschirm des Users oder simulierten Tastendrücken/Mausklicks auf seinem PC
metadata:
  node_type: memory
  type: feedback
  originSessionId: 351b144d-002e-4799-b3ef-362385ffc541
  modified: 2026-10-04T17:22:14.171Z
---

Für Tests am Geofinder ([[geofinder-ort]]) keine Screenshots vom Bildschirm des Users machen und nicht per SendInput Tasten
oder Maus auf seinem PC fernsteuern. Am 2026-10-04 hat das den Kopf seines GeoGuessr-Avatars aufgenommen: als Testbild wertlos,
und er hat den Lauf abgebrochen.

**Why:** Das sind keine gültigen Testdaten, und das Fernsteuern stört ihn bei der Arbeit am PC.
**How to apply:** Teste mit echten Ortsbildern mit bekannter Lage: entweder Screenshots, die der User selbst liefert und deren
Ort er angibt, oder Bilder aus dem Internet mit bekannten Koordinaten (z. B. Wikimedia Commons). Diese per API (`/api/bild`)
oder per `--bild` einspeisen. Overlay- und Tastentests nur nach Absprache.
