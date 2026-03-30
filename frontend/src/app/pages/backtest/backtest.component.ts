import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatTableModule } from '@angular/material/table';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatIconModule } from '@angular/material/icon';
import { ApiService } from '../../services/api.service';
import { BacktestReport, BacktestResult } from '../../models/instrument.model';

@Component({
  selector: 'app-backtest',
  standalone: true,
  imports: [
    CommonModule, FormsModule,
    MatCardModule, MatButtonModule, MatFormFieldModule,
    MatInputModule, MatTableModule, MatSelectModule,
    MatProgressSpinnerModule, MatIconModule,
  ],
  template: `
    <div class="backtest-page">
      <h2>Backtest Results</h2>

      <!-- Controls -->
      <div class="controls">
        <mat-form-field appearance="outline">
          <mat-label>From Date</mat-label>
          <input matInput type="date" [(ngModel)]="fromDate">
        </mat-form-field>
        <mat-form-field appearance="outline">
          <mat-label>To Date</mat-label>
          <input matInput type="date" [(ngModel)]="toDate">
        </mat-form-field>
        <mat-form-field appearance="outline">
          <mat-label>Signal Type</mat-label>
          <mat-select [(ngModel)]="signalType">
            <mat-option value="">All</mat-option>
            <mat-option value="BUY">Buy</mat-option>
            <mat-option value="SELL">Sell</mat-option>
            <mat-option value="STRONG_BUY">Strong Buy</mat-option>
            <mat-option value="STRONG_SELL">Strong Sell</mat-option>
          </mat-select>
        </mat-form-field>
        <button mat-raised-button color="primary" (click)="loadReport()">
          <mat-icon>analytics</mat-icon> Load Report
        </button>
        <button mat-raised-button color="accent" (click)="runBacktest()">
          <mat-icon>play_arrow</mat-icon> Run Backtest
        </button>
      </div>

      <mat-spinner *ngIf="loading" diameter="40"></mat-spinner>

      <!-- Summary cards -->
      <div class="summary-row" *ngIf="report">
        <mat-card class="summary-card">
          <div class="summary-label">Total Signals</div>
          <div class="summary-value">{{ report.total_signals }}</div>
        </mat-card>
        <mat-card class="summary-card">
          <div class="summary-label">Win Rate</div>
          <div class="summary-value" [class.text-green]="report.win_rate >= 50"
               [class.text-red]="report.win_rate < 50">
            {{ report.win_rate | number:'1.1-1' }}%
          </div>
        </mat-card>
        <mat-card class="summary-card">
          <div class="summary-label">Wins / Losses</div>
          <div class="summary-value">
            <span class="text-green">{{ report.wins }}</span> / <span class="text-red">{{ report.losses }}</span>
          </div>
        </mat-card>
        <mat-card class="summary-card">
          <div class="summary-label">Profit Factor</div>
          <div class="summary-value" [class.text-green]="report.profit_factor >= 1"
               [class.text-red]="report.profit_factor < 1">
            {{ report.profit_factor | number:'1.2-2' }}
          </div>
        </mat-card>
        <mat-card class="summary-card">
          <div class="summary-label">Expectancy</div>
          <div class="summary-value" [class.text-green]="report.expectancy >= 0"
               [class.text-red]="report.expectancy < 0">
            {{ report.expectancy | number:'1.2-2' }}%
          </div>
        </mat-card>
        <mat-card class="summary-card">
          <div class="summary-label">Total P&L</div>
          <div class="summary-value" [class.text-green]="report.total_profit_pct + report.total_loss_pct >= 0"
               [class.text-red]="report.total_profit_pct + report.total_loss_pct < 0">
            {{ (report.total_profit_pct + report.total_loss_pct) | number:'1.2-2' }}%
          </div>
        </mat-card>
      </div>

      <!-- Results table -->
      <div class="results-table" *ngIf="report && report.results.length > 0">
        <table mat-table [dataSource]="report.results">
          <ng-container matColumnDef="symbol">
            <th mat-header-cell *matHeaderCellDef>Symbol</th>
            <td mat-cell *matCellDef="let row">{{ row.symbol }}</td>
          </ng-container>
          <ng-container matColumnDef="signal_type">
            <th mat-header-cell *matHeaderCellDef>Type</th>
            <td mat-cell *matCellDef="let row">{{ row.signal_type }}</td>
          </ng-container>
          <ng-container matColumnDef="entry_price">
            <th mat-header-cell *matHeaderCellDef>Entry</th>
            <td mat-cell *matCellDef="let row">{{ row.entry_price | number:'1.2-2' }}</td>
          </ng-container>
          <ng-container matColumnDef="exit_price">
            <th mat-header-cell *matHeaderCellDef>Exit</th>
            <td mat-cell *matCellDef="let row">{{ row.exit_price | number:'1.2-2' }}</td>
          </ng-container>
          <ng-container matColumnDef="result">
            <th mat-header-cell *matHeaderCellDef>Result</th>
            <td mat-cell *matCellDef="let row"
                [class.text-green]="row.result === 'WIN'"
                [class.text-red]="row.result === 'LOSS'">
              {{ row.result }}
            </td>
          </ng-container>
          <ng-container matColumnDef="pnl_percent">
            <th mat-header-cell *matHeaderCellDef>P&L %</th>
            <td mat-cell *matCellDef="let row"
                [class.text-green]="row.pnl_percent >= 0"
                [class.text-red]="row.pnl_percent < 0">
              {{ row.pnl_percent | number:'1.2-2' }}%
            </td>
          </ng-container>
          <ng-container matColumnDef="holding_minutes">
            <th mat-header-cell *matHeaderCellDef>Hold (min)</th>
            <td mat-cell *matCellDef="let row">{{ row.holding_minutes }}</td>
          </ng-container>
          <tr mat-header-row *matHeaderRowDef="displayedCols"></tr>
          <tr mat-row *matRowDef="let row; columns: displayedCols;"></tr>
        </table>
      </div>
    </div>
  `,
  styles: [`
    .backtest-page { display: flex; flex-direction: column; gap: 20px; }
    h2 { color: var(--text-primary); margin: 0; font-weight: 700; letter-spacing: -0.02em; }
    .controls {
      display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
      background: var(--bg-card);
      padding: 16px;
      border-radius: var(--radius-md);
      border: 1px solid var(--border-color);
      box-shadow: var(--shadow-sm);
    }
    .controls mat-form-field {
      width: 160px;
    }
    .controls mat-form-field ::ng-deep .mat-mdc-form-field-subscript-wrapper { display: none; }
    .summary-row {
      display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px;
    }
    .summary-card {
      padding: 16px 12px; text-align: center;
      border-radius: var(--radius-md) !important;
      transition: transform 0.2s ease, box-shadow 0.25s ease;
    }
    .summary-card:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-md) !important;
    }
    .summary-label {
      font-size: 10px; color: var(--text-muted); text-transform: uppercase;
      font-weight: 600; letter-spacing: 0.06em;
    }
    .summary-value {
      font-size: 24px; font-weight: 800; margin-top: 6px;
      letter-spacing: -0.02em;
    }
    .results-table {
      overflow-x: auto;
      background: var(--bg-card);
      border-radius: var(--radius-md);
      border: 1px solid var(--border-color);
      box-shadow: var(--shadow-card);
    }
    @media (max-width: 900px) {
      .summary-row { grid-template-columns: repeat(3, 1fr); }
    }
  `],
})
export class BacktestComponent implements OnInit {
  fromDate = '';
  toDate = '';
  signalType = '';
  report: BacktestReport | null = null;
  loading = false;
  displayedCols = ['symbol', 'signal_type', 'entry_price', 'exit_price', 'result', 'pnl_percent', 'holding_minutes'];

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    const now = new Date();
    this.toDate = now.toISOString().split('T')[0];
    const weekAgo = new Date(now.getTime() - 7 * 86400000);
    this.fromDate = weekAgo.toISOString().split('T')[0];
    this.loadReport();
  }

  loadReport(): void {
    this.loading = true;
    this.api.getBacktestReport(this.fromDate, this.toDate, this.signalType).subscribe({
      next: (report) => { this.report = report; this.loading = false; },
      error: () => { this.loading = false; },
    });
  }

  runBacktest(): void {
    this.loading = true;
    this.api.runBacktest(this.fromDate, this.toDate).subscribe({
      next: (report) => { this.report = report; this.loading = false; },
      error: () => { this.loading = false; },
    });
  }
}
