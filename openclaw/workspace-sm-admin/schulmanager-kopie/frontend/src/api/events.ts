/**
 * Gemeinsame Server-Sent-Events-Verbindung zu /api/v1/events mit automatischem Reconnect.
 * Ereignisse: `change` {version,scope,dates}, `job` {id,status,progress,message}, `ping`.
 */
import { API_BASE } from './client';
import type { LiveChangeEvent, LiveJobEvent } from './types';
import { backoffDelay } from '../lib/live';

export type LiveStatus = 'idle' | 'connecting' | 'open' | 'error';

export interface LiveListener {
  onChange?: (ev: LiveChangeEvent) => void;
  onJob?: (ev: LiveJobEvent) => void;
  /** nach Wiederverbindung: verpasste Ereignisse → neu laden */
  onReconnect?: () => void;
}

const WATCHDOG_MS = 75_000;

class LiveConnection {
  private es: EventSource | null = null;
  private listeners = new Set<LiveListener>();
  private statusListeners = new Set<(s: LiveStatus) => void>();
  private status: LiveStatus = 'idle';
  private attempt = 0;
  private retryTimer: number | null = null;
  private watchdog: number | null = null;
  private stopTimer: number | null = null;
  private everOpened = false;
  private lostSinceOpen = false;
  private enabled = true;

  constructor() {
    if (typeof document !== 'undefined') {
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible' && this.listeners.size && this.status !== 'open') {
          this.attempt = 0;
          this.connect();
        }
      });
      window.addEventListener('online', () => {
        if (this.listeners.size && this.status !== 'open') {
          this.attempt = 0;
          this.connect();
        }
      });
    }
  }

  getStatus(): LiveStatus {
    return this.status;
  }

  /** Bei Abmeldung trennen, nach Anmeldung wieder erlauben. */
  setEnabled(on: boolean): void {
    this.enabled = on;
    if (!on) this.disconnect();
    else if (this.listeners.size) this.connect();
  }

  subscribe(l: LiveListener): () => void {
    this.listeners.add(l);
    if (this.stopTimer !== null) {
      window.clearTimeout(this.stopTimer);
      this.stopTimer = null;
    }
    if (!this.es && this.enabled) this.connect();
    return () => {
      this.listeners.delete(l);
      if (!this.listeners.size && this.stopTimer === null) {
        // kurze Verzögerung, damit Seitenwechsel die Verbindung nicht neu aufbauen
        this.stopTimer = window.setTimeout(() => {
          this.stopTimer = null;
          if (!this.listeners.size) this.disconnect();
        }, 5000);
      }
    };
  }

  onStatus(fn: (s: LiveStatus) => void): () => void {
    this.statusListeners.add(fn);
    fn(this.status);
    return () => this.statusListeners.delete(fn);
  }

  private setStatus(s: LiveStatus): void {
    if (this.status === s) return;
    this.status = s;
    this.statusListeners.forEach((fn) => fn(s));
  }

  private resetWatchdog(): void {
    if (this.watchdog !== null) window.clearTimeout(this.watchdog);
    this.watchdog = window.setTimeout(() => {
      // keine Nachricht (auch kein ping) seit langem → neu verbinden
      this.reconnectLater();
    }, WATCHDOG_MS);
  }

  private connect(): void {
    if (typeof EventSource === 'undefined' || !this.enabled) return;
    this.closeSource();
    if (this.retryTimer !== null) {
      window.clearTimeout(this.retryTimer);
      this.retryTimer = null;
    }
    this.setStatus('connecting');
    const es = new EventSource(`${API_BASE}/events`, { withCredentials: true });
    this.es = es;

    es.onopen = () => {
      this.attempt = 0;
      this.setStatus('open');
      this.resetWatchdog();
      if (this.everOpened && this.lostSinceOpen) {
        this.listeners.forEach((l) => l.onReconnect?.());
      }
      this.everOpened = true;
      this.lostSinceOpen = false;
    };
    es.onerror = () => {
      this.lostSinceOpen = true;
      this.reconnectLater();
    };
    es.addEventListener('change', (ev) => {
      this.resetWatchdog();
      const data = parse<LiveChangeEvent>((ev as MessageEvent).data);
      if (data) this.listeners.forEach((l) => l.onChange?.(data));
    });
    es.addEventListener('job', (ev) => {
      this.resetWatchdog();
      const data = parse<LiveJobEvent>((ev as MessageEvent).data);
      if (data) this.listeners.forEach((l) => l.onJob?.(data));
    });
    es.addEventListener('ping', () => this.resetWatchdog());
    es.onmessage = () => this.resetWatchdog();
  }

  private reconnectLater(): void {
    this.closeSource();
    this.setStatus('error');
    if (!this.listeners.size || !this.enabled) return;
    const delay = backoffDelay(this.attempt++);
    if (this.retryTimer !== null) window.clearTimeout(this.retryTimer);
    this.retryTimer = window.setTimeout(() => {
      this.retryTimer = null;
      this.connect();
    }, delay);
  }

  private closeSource(): void {
    if (this.es) {
      this.es.onopen = null;
      this.es.onerror = null;
      this.es.close();
      this.es = null;
    }
    if (this.watchdog !== null) {
      window.clearTimeout(this.watchdog);
      this.watchdog = null;
    }
  }

  private disconnect(): void {
    this.closeSource();
    if (this.retryTimer !== null) {
      window.clearTimeout(this.retryTimer);
      this.retryTimer = null;
    }
    this.everOpened = false;
    this.lostSinceOpen = false;
    this.setStatus('idle');
  }
}

function parse<T>(raw: unknown): T | null {
  if (typeof raw !== 'string' || !raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export const live = new LiveConnection();
