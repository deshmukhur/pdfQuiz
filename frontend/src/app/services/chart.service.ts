import { Injectable } from '@angular/core';
import { ApiService } from './api.service';
import { Candle } from '../models/instrument.model';
import { Observable, map } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ChartService {
  constructor(private api: ApiService) {}

  loadCandles(symbol: string, timeframe: string, limit: number = 300): Observable<Candle[]> {
    return this.api.getCandles(symbol, timeframe, limit).pipe(
      map(response => response.candles)
    );
  }

  formatCandleForChart(candle: Candle): {
    time: number;
    open: number;
    high: number;
    low: number;
    close: number;
  } {
    return {
      time: new Date(candle.time).getTime() / 1000 as number,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
    };
  }

  formatVolumeForChart(candle: Candle): {
    time: number;
    value: number;
    color: string;
  } {
    return {
      time: new Date(candle.time).getTime() / 1000 as number,
      value: candle.volume,
      color: candle.close >= candle.open ? '#10b981' : '#ef4444',
    };
  }
}
