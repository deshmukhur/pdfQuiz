import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '@env/environment';
import {
  Instrument, ScanResult, Signal, Candle,
  NewsArticle, FundamentalData, BacktestReport,
} from '../models/instrument.model';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  // Instruments
  getInstruments(segment?: string, exchange?: string): Observable<Instrument[]> {
    let params = new HttpParams();
    if (segment) params = params.set('segment', segment);
    if (exchange) params = params.set('exchange', exchange);
    return this.http.get<Instrument[]>(`${this.baseUrl}/api/instruments`, { params });
  }

  // Dashboard
  getDashboardLatest(filters?: {
    segment?: string;
    exchange?: string;
    min_score?: number;
    min_volume_ratio?: number;
  }): Observable<{ count: number; instruments: ScanResult[] }> {
    let params = new HttpParams();
    if (filters?.segment) params = params.set('segment', filters.segment);
    if (filters?.exchange) params = params.set('exchange', filters.exchange);
    if (filters?.min_score) params = params.set('min_score', filters.min_score.toString());
    if (filters?.min_volume_ratio) params = params.set('min_volume_ratio', filters.min_volume_ratio.toString());
    return this.http.get<{ count: number; instruments: ScanResult[] }>(
      `${this.baseUrl}/api/dashboard/latest`, { params }
    );
  }

  // Candles
  getCandles(symbol: string, timeframe: string = '1m', limit: number = 300): Observable<{
    candles: Candle[];
    symbol: string;
    timeframe: string;
  }> {
    const params = new HttpParams()
      .set('symbol', symbol)
      .set('timeframe', timeframe)
      .set('limit', limit.toString());
    return this.http.get<{ candles: Candle[]; symbol: string; timeframe: string }>(
      `${this.baseUrl}/api/candles`, { params }
    );
  }

  // Signals
  getSignals(filters?: {
    symbol?: string;
    type?: string;
    status?: string;
    from?: string;
    to?: string;
  }): Observable<Signal[]> {
    let params = new HttpParams();
    if (filters?.symbol) params = params.set('symbol', filters.symbol);
    if (filters?.type) params = params.set('type', filters.type);
    if (filters?.status) params = params.set('status', filters.status);
    if (filters?.from) params = params.set('from', filters.from);
    if (filters?.to) params = params.set('to', filters.to);
    return this.http.get<Signal[]>(`${this.baseUrl}/api/signals`, { params });
  }

  closeSignal(signalId: number): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(
      `${this.baseUrl}/api/signals/${signalId}/close`, {}
    );
  }

  // News
  getNews(symbol?: string, limit: number = 50): Observable<NewsArticle[]> {
    let params = new HttpParams().set('limit', limit.toString());
    if (symbol) params = params.set('symbol', symbol);
    return this.http.get<NewsArticle[]>(`${this.baseUrl}/api/news`, { params });
  }

  // Fundamentals
  getFundamentals(symbol?: string): Observable<FundamentalData[]> {
    let params = new HttpParams();
    if (symbol) params = params.set('symbol', symbol);
    return this.http.get<FundamentalData[]>(`${this.baseUrl}/api/fundamental`, { params });
  }

  // Backtest
  getBacktestReport(from?: string, to?: string, signalType?: string): Observable<BacktestReport> {
    let params = new HttpParams();
    if (from) params = params.set('from', from);
    if (to) params = params.set('to', to);
    if (signalType) params = params.set('signal_type', signalType);
    return this.http.get<BacktestReport>(`${this.baseUrl}/api/backtest/report`, { params });
  }

  runBacktest(from?: string, to?: string): Observable<BacktestReport> {
    let params = new HttpParams();
    if (from) params = params.set('from', from);
    if (to) params = params.set('to', to);
    return this.http.post<BacktestReport>(`${this.baseUrl}/api/backtest/run`, null, { params });
  }

  // Auth
  getFyersAuthUrl(): Observable<{ auth_url: string }> {
    return this.http.get<{ auth_url: string }>(`${this.baseUrl}/api/auth/fyers/url`);
  }

  getFyersStatus(): Observable<{ authenticated: boolean; client_id: string }> {
    return this.http.get<{ authenticated: boolean; client_id: string }>(
      `${this.baseUrl}/api/auth/fyers/status`
    );
  }

  // Option Chain
  getOptionChain(symbol: string, expiry?: string): Observable<Record<string, unknown>> {
    let params = new HttpParams().set('symbol', symbol);
    if (expiry) params = params.set('expiry', expiry);
    return this.http.get<Record<string, unknown>>(`${this.baseUrl}/api/optionchain`, { params });
  }
}
