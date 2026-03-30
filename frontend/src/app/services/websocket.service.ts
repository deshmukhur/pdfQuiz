import { Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject, Observable, Subject } from 'rxjs';
import { environment } from '@env/environment';
import { ScanResult } from '../models/instrument.model';

@Injectable({ providedIn: 'root' })
export class WebSocketService implements OnDestroy {
  private ws: WebSocket | null = null;
  private chartWs: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 2000;

  private scanResults$ = new BehaviorSubject<ScanResult[]>([]);
  private marketStatus$ = new BehaviorSubject<Record<string, unknown>>({});
  private tickData$ = new Subject<{ symbol: string; data: Record<string, unknown> }>();
  private connected$ = new BehaviorSubject<boolean>(false);

  get scanResults(): Observable<ScanResult[]> {
    return this.scanResults$.asObservable();
  }

  get marketStatus(): Observable<Record<string, unknown>> {
    return this.marketStatus$.asObservable();
  }

  get tickData(): Observable<{ symbol: string; data: Record<string, unknown> }> {
    return this.tickData$.asObservable();
  }

  get isConnected(): Observable<boolean> {
    return this.connected$.asObservable();
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    try {
      this.ws = new WebSocket(`${environment.wsUrl}/ws`);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.connected$.next(true);
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'scan_update') {
            this.scanResults$.next(msg.data);
          } else if (msg.type === 'market_status') {
            this.marketStatus$.next(msg.data);
          }
        } catch (e) {
          console.error('WebSocket message parse error:', e);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.connected$.next(false);
        this.tryReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (e) {
      console.error('WebSocket connection error:', e);
      this.tryReconnect();
    }
  }

  private tryReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1);
      setTimeout(() => this.connect(), delay);
    }
  }

  connectChart(symbol: string): void {
    this.disconnectChart();

    try {
      this.chartWs = new WebSocket(`${environment.wsUrl}/ws/chart?symbol=${encodeURIComponent(symbol)}`);

      this.chartWs.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'tick') {
            this.tickData$.next({ symbol: msg.symbol, data: msg.data });
          }
        } catch (e) {
          console.error('Chart WS parse error:', e);
        }
      };
    } catch (e) {
      console.error('Chart WebSocket error:', e);
    }
  }

  disconnectChart(): void {
    if (this.chartWs) {
      this.chartWs.close();
      this.chartWs = null;
    }
  }

  disconnect(): void {
    this.ws?.close();
    this.ws = null;
    this.disconnectChart();
  }

  ngOnDestroy(): void {
    this.disconnect();
  }
}
