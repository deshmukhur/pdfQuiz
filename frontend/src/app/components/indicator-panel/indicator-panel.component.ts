import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { ScanResult, ScoreBreakdown } from '../../models/instrument.model';

@Component({
  selector: 'app-indicator-panel',
  standalone: true,
  imports: [CommonModule, MatCardModule],
  template: `
    <div class="indicator-panel" *ngIf="data">
      <!-- Score breakdown -->
      <mat-card class="panel-card">
        <div class="card-title">Score Breakdown</div>
        <div class="breakdown-row" *ngFor="let cat of categories">
          <span class="cat-label">{{ cat.name }}</span>
          <div class="score-bar-container">
            <div class="score-bar"
                 [style.width.%]="getBarWidth(cat.score)"
                 [class.positive]="cat.score >= 0"
                 [class.negative]="cat.score < 0">
            </div>
          </div>
          <span class="cat-score" [class.text-green]="cat.score >= 0" [class.text-red]="cat.score < 0">
            {{ cat.score | number:'1.1-1' }}
          </span>
        </div>
      </mat-card>

      <!-- Key Indicators -->
      <mat-card class="panel-card">
        <div class="card-title">Key Indicators</div>
        <div class="indicator-grid">
          <div class="indicator-item" *ngFor="let ind of keyIndicators">
            <span class="ind-label">{{ ind.label }}</span>
            <span class="ind-value" [ngClass]="ind.colorClass">{{ ind.value }}</span>
          </div>
        </div>
      </mat-card>

      <!-- Targets -->
      <mat-card class="panel-card" *ngIf="data.stop_loss || data.target_1">
        <div class="card-title">Entry / Targets</div>
        <div class="target-grid">
          <div class="target-item">
            <span class="target-label">Entry</span>
            <span class="target-value">{{ data.entry_price | number:'1.2-2' }}</span>
          </div>
          <div class="target-item text-red">
            <span class="target-label">Stop Loss</span>
            <span class="target-value">{{ data.stop_loss | number:'1.2-2' }}</span>
          </div>
          <div class="target-item text-green" *ngIf="data.target_1">
            <span class="target-label">Target 1</span>
            <span class="target-value">{{ data.target_1 | number:'1.2-2' }}</span>
          </div>
          <div class="target-item text-green" *ngIf="data.target_2">
            <span class="target-label">Target 2</span>
            <span class="target-value">{{ data.target_2 | number:'1.2-2' }}</span>
          </div>
          <div class="target-item text-green" *ngIf="data.target_3">
            <span class="target-label">Target 3</span>
            <span class="target-value">{{ data.target_3 | number:'1.2-2' }}</span>
          </div>
        </div>
      </mat-card>

      <!-- Patterns -->
      <mat-card class="panel-card" *ngIf="data.patterns_detected?.length">
        <div class="card-title">Detected Patterns</div>
        <div class="pattern-list">
          <span class="pattern-tag" *ngFor="let p of data.patterns_detected">{{ p }}</span>
        </div>
      </mat-card>
    </div>
  `,
  styles: [`
    .indicator-panel {
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    .panel-card {
      padding: 16px;
      border-radius: var(--radius-md) !important;
    }
    .card-title {
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--text-muted);
      margin-bottom: 12px;
      letter-spacing: 0.06em;
    }
    .breakdown-row {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
    }
    .cat-label {
      width: 100px;
      font-size: 12px;
      color: var(--text-secondary);
      font-weight: 500;
    }
    .score-bar-container {
      flex: 1;
      height: 6px;
      background: var(--bg-hover);
      border-radius: 3px;
      overflow: hidden;
    }
    .score-bar {
      height: 100%;
      border-radius: 3px;
      transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .score-bar.positive { background: linear-gradient(90deg, #0ea371, #34d399); }
    .score-bar.negative { background: linear-gradient(90deg, #e5354b, #fca5a5); }
    .cat-score {
      width: 40px;
      text-align: right;
      font-weight: 700;
      font-size: 12px;
    }
    .indicator-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px;
    }
    .indicator-item {
      display: flex;
      justify-content: space-between;
      padding: 6px 0;
      border-bottom: 1px solid var(--border-color);
    }
    .ind-label {
      font-size: 12px;
      color: var(--text-muted);
      font-weight: 500;
    }
    .ind-value {
      font-size: 12px;
      font-weight: 700;
    }
    .target-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .target-item {
      padding: 8px 10px;
      background: var(--bg-hover);
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-color);
    }
    .target-label {
      display: block;
      font-size: 10px;
      color: var(--text-muted);
      font-weight: 600;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    .target-value {
      font-size: 15px;
      font-weight: 800;
      letter-spacing: -0.02em;
    }
    .pattern-list {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .pattern-tag {
      display: inline-block;
      padding: 4px 10px;
      font-size: 11px;
      background: var(--bg-hover);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      color: var(--text-secondary);
      font-weight: 500;
    }
  `],
})
export class IndicatorPanelComponent {
  @Input() data: ScanResult | null = null;

  get categories(): { name: string; score: number }[] {
    if (!this.data?.score_breakdown) return [];
    const b = this.data.score_breakdown;
    return [
      { name: 'Trend', score: b.trend?.score ?? 0 },
      { name: 'Momentum', score: b.momentum?.score ?? 0 },
      { name: 'Volume', score: b.volume?.score ?? 0 },
      { name: 'Patterns', score: b.patterns?.score ?? 0 },
      { name: 'S/R Levels', score: b.support_resistance?.score ?? 0 },
    ];
  }

  get keyIndicators(): { label: string; value: string; colorClass: string }[] {
    if (!this.data) return [];
    const ind = this.data.indicators || {};
    const items: { label: string; value: string; colorClass: string }[] = [];

    if (this.data.rsi != null) {
      items.push({
        label: 'RSI(14)',
        value: this.data.rsi.toFixed(1),
        colorClass: this.data.rsi > 70 ? 'text-red' : this.data.rsi < 30 ? 'text-green' : '',
      });
    }

    const addInd = (key: string, label: string) => {
      const val = ind[key];
      if (val != null) {
        items.push({ label, value: Number(val).toFixed(2), colorClass: '' });
      }
    };

    addInd('ema_9', 'EMA(9)');
    addInd('ema_20', 'EMA(20)');
    addInd('ema_50', 'EMA(50)');
    addInd('atr', 'ATR(14)');
    addInd('adx', 'ADX');
    addInd('vwap', 'VWAP');
    addInd('mfi', 'MFI');

    return items;
  }

  getBarWidth(score: number): number {
    return Math.min(Math.abs(score), 100);
  }
}
