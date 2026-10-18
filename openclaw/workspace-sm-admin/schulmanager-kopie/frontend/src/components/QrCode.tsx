import { useMemo } from 'react';
import qrcode from 'qrcode-generator';

/** QR-Code als SVG (für 2FA-Einrichtung). */
export function QrCode({ text, size = 200, label }: { text: string; size?: number; label: string }) {
  const svg = useMemo(() => {
    const qr = qrcode(0, 'M');
    qr.addData(text);
    qr.make();
    const n = qr.getModuleCount();
    const rects: string[] = [];
    for (let r = 0; r < n; r++) {
      for (let c = 0; c < n; c++) {
        if (qr.isDark(r, c)) rects.push(`M${c} ${r}h1v1h-1z`);
      }
    }
    return { n, d: rects.join('') };
  }, [text]);
  return (
    <div className="qr">
      <svg width={size} height={size} viewBox={`0 0 ${svg.n} ${svg.n}`} role="img" aria-label={label} shapeRendering="crispEdges">
        <rect width={svg.n} height={svg.n} fill="#fff" />
        <path d={svg.d} fill="#000" />
      </svg>
    </div>
  );
}
