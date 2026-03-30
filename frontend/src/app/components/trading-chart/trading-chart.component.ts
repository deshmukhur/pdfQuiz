import {
  Component, Input, OnChanges, OnDestroy, SimpleChanges,
  ElementRef, ViewChild, AfterViewInit,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { createChart, IChartApi, ISeriesApi, CandlestickData, HistogramData, Time } from 'lightweight-charts';
import { ChartService } from '../../services/chart.service';
import { WebSocketService } from '../../services/websocket.service';
import { Candle } from '../../models/instrument.model';

@Component({
  selector: 'app-trading-chart',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="chart-wrapper">
      <div #chartContainer class="chart-container"></div>
    </div>
  `,
  styles: [`
    .chart-wrapper {
      width: 100%;
      height: 100%;
      min-height: 500px;
      background: #ffffff;
      border-radius: var(--radius-md);
      border: 1px solid var(--border-color);
      box-shadow: var(--shadow-card);
      overflow: hidden;
    }
    .chart-container {
      width: 100%;
      height: 100%;
    }
  `],
})
export class TradingChartComponent implements AfterViewInit, OnChanges, OnDestroy {
  @Input() symbol = '';
  @Input() timeframe = '1m';
  @ViewChild('chartContainer') chartContainer!: ElementRef;

  private chart: IChartApi | null = null;
  private candleSeries: ISeriesApi<'Candlestick'> | null = null;
  private volumeSeries: ISeriesApi<'Histogram'> | null = null;
  private tickSub?: Subscription;

  constructor(
    private chartService: ChartService,
    private wsService: WebSocketService,
  ) {}

  ngAfterViewInit(): void {
    this.initChart();
    if (this.symbol) {
      this.loadData();
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if ((changes['symbol'] || changes['timeframe']) && this.chart) {
      this.loadData();
    }
  }

  private initChart(): void {
    if (!this.chartContainer?.nativeElement) return;

    this.chart = createChart(this.chartContainer.nativeElement, {
      width: this.chartContainer.nativeElement.clientWidth,
      height: 500,
      layout: {
        background: { color: '#ffffff' },
        textColor: '#4a5068',
        fontFamily: 'Inter, -apple-system, sans-serif',
      },
      grid: {
        vertLines: { color: 'rgba(0, 0, 0, 0.04)' },
        horzLines: { color: 'rgba(0, 0, 0, 0.04)' },
      },
      crosshair: {
        mode: 0,
      },
      rightPriceScale: {
        borderColor: 'rgba(0, 0, 0, 0.08)',
      },
      timeScale: {
        borderColor: 'rgba(0, 0, 0, 0.08)',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    this.candleSeries = this.chart.addCandlestickSeries({
      upColor: '#0ea371',
      downColor: '#e5354b',
      borderUpColor: '#0ea371',
      borderDownColor: '#e5354b',
      wickUpColor: '#0ea371',
      wickDownColor: '#e5354b',
    });

    this.volumeSeries = this.chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: '',
    });

    this.volumeSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.85, bottom: 0 },
    });

    // Handle resize
    const observer = new ResizeObserver(() => {
      if (this.chart && this.chartContainer?.nativeElement) {
        this.chart.applyOptions({
          width: this.chartContainer.nativeElement.clientWidth,
        });
      }
    });
    observer.observe(this.chartContainer.nativeElement);
  }

  private loadData(): void {
    if (!this.symbol || !this.chart) return;

    // Unsubscribe from previous tick stream
    this.tickSub?.unsubscribe();

    this.chartService.loadCandles(this.symbol, this.timeframe, 300).subscribe({
      next: (candles) => {
        if (!this.candleSeries || !this.volumeSeries) return;

        const candleData: CandlestickData[] = candles.map(c => ({
          time: (new Date(c.time).getTime() / 1000) as Time,
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        }));

        const volumeData: HistogramData[] = candles.map(c => ({
          time: (new Date(c.time).getTime() / 1000) as Time,
          value: c.volume,
          color: c.close >= c.open ? 'rgba(14,163,113,0.25)' : 'rgba(229,53,75,0.25)',
        }));

        this.candleSeries.setData(candleData);
        this.volumeSeries.setData(volumeData);
        this.chart?.timeScale().fitContent();

        // Subscribe to real-time updates
        this.wsService.connectChart(this.symbol);
        this.tickSub = this.wsService.tickData.subscribe(tick => {
          if (tick.symbol === this.symbol && tick.data) {
            const d = tick.data;
            const time = (new Date(d['time'] as string).getTime() / 1000) as Time;
            this.candleSeries?.update({
              time,
              open: d['open'] as number,
              high: d['high'] as number,
              low: d['low'] as number,
              close: d['close'] as number,
            });
            this.volumeSeries?.update({
              time,
              value: d['volume'] as number,
              color: (d['close'] as number) >= (d['open'] as number)
                ? 'rgba(14,163,113,0.25)' : 'rgba(229,53,75,0.25)',
            });
          }
        });
      },
      error: (err) => console.error('Failed to load candles:', err),
    });
  }

  ngOnDestroy(): void {
    this.tickSub?.unsubscribe();
    this.wsService.disconnectChart();
    this.chart?.remove();
  }
}
