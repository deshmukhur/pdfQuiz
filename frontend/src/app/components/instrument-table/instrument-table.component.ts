import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTableModule } from '@angular/material/table';
import { MatSortModule, Sort } from '@angular/material/sort';
import { MatChipsModule } from '@angular/material/chips';
import { SignalBadgeComponent } from '../signal-badge/signal-badge.component';
import { ScanResult } from '../../models/instrument.model';

@Component({
  selector: 'app-instrument-table',
  standalone: true,
  imports: [CommonModule, MatTableModule, MatSortModule, MatChipsModule, SignalBadgeComponent],
  template: `
    <div class="table-container">
      <table mat-table [dataSource]="sortedData" matSort (matSortChange)="onSort($event)" class="instrument-table">
        <!-- Symbol -->
        <ng-container matColumnDef="symbol">
          <th mat-header-cell *matHeaderCellDef mat-sort-header>Symbol</th>
          <td mat-cell *matCellDef="let row">
            <span class="symbol-name" (click)="onSymbolClick(row)">{{ row.symbol }}</span>
          </td>
        </ng-container>

        <!-- LTP -->
        <ng-container matColumnDef="ltp">
          <th mat-header-cell *matHeaderCellDef mat-sort-header>LTP</th>
          <td mat-cell *matCellDef="let row" class="text-right">{{ row.ltp | number:'1.2-2' }}</td>
        </ng-container>

        <!-- Change % -->
        <ng-container matColumnDef="change_pct">
          <th mat-header-cell *matHeaderCellDef mat-sort-header>Chg%</th>
          <td mat-cell *matCellDef="let row" class="text-right"
              [class.text-green]="row.change_pct >= 0" [class.text-red]="row.change_pct < 0">
            {{ row.change_pct >= 0 ? '+' : '' }}{{ row.change_pct | number:'1.2-2' }}%
          </td>
        </ng-container>

        <!-- Volume -->
        <ng-container matColumnDef="volume">
          <th mat-header-cell *matHeaderCellDef mat-sort-header>Volume</th>
          <td mat-cell *matCellDef="let row" class="text-right">{{ formatVolume(row.volume) }}</td>
        </ng-container>

        <!-- RSI -->
        <ng-container matColumnDef="rsi">
          <th mat-header-cell *matHeaderCellDef mat-sort-header>RSI</th>
          <td mat-cell *matCellDef="let row" class="text-right"
              [class.text-green]="row.rsi && row.rsi < 30"
              [class.text-red]="row.rsi && row.rsi > 70">
            {{ row.rsi ? (row.rsi | number:'1.1-1') : '-' }}
          </td>
        </ng-container>

        <!-- Score -->
        <ng-container matColumnDef="score">
          <th mat-header-cell *matHeaderCellDef mat-sort-header>Score</th>
          <td mat-cell *matCellDef="let row" class="text-right">
            <span class="score-value"
                  [class.text-green]="row.score > 0"
                  [class.text-red]="row.score < 0">
              {{ row.score | number:'1.1-1' }}
            </span>
          </td>
        </ng-container>

        <!-- Signal -->
        <ng-container matColumnDef="signal">
          <th mat-header-cell *matHeaderCellDef mat-sort-header>Signal</th>
          <td mat-cell *matCellDef="let row">
            <app-signal-badge [signal]="row.signal" [score]="row.score"></app-signal-badge>
          </td>
        </ng-container>

        <!-- Patterns -->
        <ng-container matColumnDef="patterns">
          <th mat-header-cell *matHeaderCellDef>Patterns</th>
          <td mat-cell *matCellDef="let row">
            <span class="pattern-chip" *ngFor="let p of row.patterns_detected?.slice(0, 2)">{{ p }}</span>
          </td>
        </ng-container>

        <!-- Key Reason -->
        <ng-container matColumnDef="key_reason">
          <th mat-header-cell *matHeaderCellDef>Key Reason</th>
          <td mat-cell *matCellDef="let row" class="text-sm text-muted">
            {{ row.key_reason || '-' }}
          </td>
        </ng-container>

        <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
        <tr mat-row *matRowDef="let row; columns: displayedColumns;"
            (click)="onSymbolClick(row)"></tr>
      </table>
    </div>
  `,
  styles: [`
    .table-container {
      overflow-x: auto;
      max-height: calc(100vh - 200px);
      overflow-y: auto;
    }
    .instrument-table {
      width: 100%;
    }
    .symbol-name {
      font-weight: 700;
      color: var(--accent-blue);
      cursor: pointer;
      transition: color 0.2s ease;
      letter-spacing: -0.01em;
    }
    .symbol-name:hover {
      color: #2952cc;
      text-decoration: none;
    }
    .score-value {
      font-weight: 800;
    }
    .pattern-chip {
      display: inline-block;
      font-size: 10px;
      padding: 2px 8px;
      margin: 1px 2px;
      border-radius: 5px;
      background: var(--bg-hover);
      color: var(--text-secondary);
      font-weight: 500;
      border: 1px solid var(--border-color);
    }
    th {
      font-size: 10px !important;
      text-transform: uppercase;
      color: var(--text-muted) !important;
      font-weight: 600 !important;
      letter-spacing: 0.06em;
    }
  `],
})
export class InstrumentTableComponent {
  @Input() data: ScanResult[] = [];
  @Output() symbolSelected = new EventEmitter<string>();

  displayedColumns = ['symbol', 'ltp', 'change_pct', 'volume', 'rsi', 'score', 'signal', 'patterns', 'key_reason'];

  sortedData: ScanResult[] = [];

  ngOnChanges(): void {
    this.sortedData = [...this.data];
  }

  onSort(sort: Sort): void {
    if (!sort.active || sort.direction === '') {
      this.sortedData = [...this.data];
      return;
    }
    this.sortedData = [...this.data].sort((a, b) => {
      const isAsc = sort.direction === 'asc';
      const aVal = (a as unknown as Record<string, unknown>)[sort.active];
      const bVal = (b as unknown as Record<string, unknown>)[sort.active];
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return (aVal - bVal) * (isAsc ? 1 : -1);
      }
      return String(aVal ?? '').localeCompare(String(bVal ?? '')) * (isAsc ? 1 : -1);
    });
  }

  onSymbolClick(row: ScanResult): void {
    this.symbolSelected.emit(row.symbol);
  }

  formatVolume(vol: number): string {
    if (!vol) return '-';
    if (vol >= 10000000) return (vol / 10000000).toFixed(1) + 'Cr';
    if (vol >= 100000) return (vol / 100000).toFixed(1) + 'L';
    if (vol >= 1000) return (vol / 1000).toFixed(1) + 'K';
    return vol.toString();
  }
}
