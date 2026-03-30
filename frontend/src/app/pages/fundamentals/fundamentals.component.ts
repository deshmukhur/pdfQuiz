import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatSortModule, Sort } from '@angular/material/sort';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { ApiService } from '../../services/api.service';
import { FundamentalData } from '../../models/instrument.model';

@Component({
  selector: 'app-fundamentals',
  standalone: true,
  imports: [
    CommonModule, FormsModule,
    MatCardModule, MatTableModule, MatSortModule,
    MatFormFieldModule, MatInputModule, MatIconModule,
    MatProgressSpinnerModule,
  ],
  template: `
    <div class="fundamentals-page">
      <h2>Fundamental Data</h2>
      <p class="text-muted text-sm">Data sourced from Screener.in — updated weekly</p>

      <div class="search-bar">
        <mat-form-field appearance="outline" class="search-field">
          <mat-label>Search Symbol</mat-label>
          <input matInput [(ngModel)]="searchQuery" placeholder="e.g. TCS">
          <mat-icon matSuffix>search</mat-icon>
        </mat-form-field>
      </div>

      <mat-spinner *ngIf="loading" diameter="40"></mat-spinner>

      <div class="table-container" *ngIf="!loading">
        <table mat-table [dataSource]="filteredData" matSort (matSortChange)="onSort($event)">
          <ng-container matColumnDef="symbol">
            <th mat-header-cell *matHeaderCellDef mat-sort-header>Symbol</th>
            <td mat-cell *matCellDef="let row" class="font-bold">{{ row.symbol }}</td>
          </ng-container>
          <ng-container matColumnDef="pe_ratio">
            <th mat-header-cell *matHeaderCellDef mat-sort-header>P/E</th>
            <td mat-cell *matCellDef="let row" class="text-right">{{ row.pe_ratio | number:'1.1-1' }}</td>
          </ng-container>
          <ng-container matColumnDef="pb_ratio">
            <th mat-header-cell *matHeaderCellDef mat-sort-header>P/B</th>
            <td mat-cell *matCellDef="let row" class="text-right">{{ row.pb_ratio | number:'1.2-2' }}</td>
          </ng-container>
          <ng-container matColumnDef="eps">
            <th mat-header-cell *matHeaderCellDef mat-sort-header>EPS</th>
            <td mat-cell *matCellDef="let row" class="text-right">{{ row.eps | number:'1.2-2' }}</td>
          </ng-container>
          <ng-container matColumnDef="roe">
            <th mat-header-cell *matHeaderCellDef mat-sort-header>ROE%</th>
            <td mat-cell *matCellDef="let row" class="text-right"
                [class.text-green]="row.roe && row.roe >= 15"
                [class.text-red]="row.roe && row.roe < 10">
              {{ row.roe | number:'1.1-1' }}
            </td>
          </ng-container>
          <ng-container matColumnDef="debt_to_equity">
            <th mat-header-cell *matHeaderCellDef mat-sort-header>D/E</th>
            <td mat-cell *matCellDef="let row" class="text-right"
                [class.text-green]="row.debt_to_equity != null && row.debt_to_equity < 0.5"
                [class.text-red]="row.debt_to_equity != null && row.debt_to_equity > 1">
              {{ row.debt_to_equity | number:'1.2-2' }}
            </td>
          </ng-container>
          <ng-container matColumnDef="market_cap">
            <th mat-header-cell *matHeaderCellDef mat-sort-header>Mkt Cap</th>
            <td mat-cell *matCellDef="let row" class="text-right">{{ formatCr(row.market_cap) }}</td>
          </ng-container>
          <ng-container matColumnDef="promoter_holding">
            <th mat-header-cell *matHeaderCellDef mat-sort-header>Promoter%</th>
            <td mat-cell *matCellDef="let row" class="text-right">
              {{ row.promoter_holding | number:'1.1-1' }}
            </td>
          </ng-container>
          <ng-container matColumnDef="updated_at">
            <th mat-header-cell *matHeaderCellDef>Updated</th>
            <td mat-cell *matCellDef="let row" class="text-muted text-sm">
              {{ row.updated_at | date:'mediumDate' }}
            </td>
          </ng-container>

          <tr mat-header-row *matHeaderRowDef="displayedCols"></tr>
          <tr mat-row *matRowDef="let row; columns: displayedCols;"></tr>
        </table>
      </div>
    </div>
  `,
  styles: [`
    .fundamentals-page { display: flex; flex-direction: column; gap: 16px; }
    h2 { margin: 0; color: var(--text-primary); font-weight: 700; letter-spacing: -0.02em; }
    .search-bar { display: flex; gap: 12px; }
    .search-field { width: 320px; }
    .search-field ::ng-deep .mat-mdc-form-field-subscript-wrapper { display: none; }
    .table-container {
      overflow-x: auto;
      background: var(--bg-card);
      border-radius: var(--radius-md);
      border: 1px solid var(--border-color);
      box-shadow: var(--shadow-card);
    }
  `],
})
export class FundamentalsComponent implements OnInit {
  data: FundamentalData[] = [];
  filteredData: FundamentalData[] = [];
  searchQuery = '';
  loading = true;
  displayedCols = ['symbol', 'pe_ratio', 'pb_ratio', 'eps', 'roe', 'debt_to_equity', 'market_cap', 'promoter_holding', 'updated_at'];

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.getFundamentals().subscribe({
      next: (data) => {
        this.data = data;
        this.filteredData = data;
        this.loading = false;
      },
      error: () => { this.loading = false; },
    });
  }

  ngDoCheck(): void {
    if (!this.searchQuery.trim()) {
      this.filteredData = this.data;
    } else {
      const q = this.searchQuery.toUpperCase().trim();
      this.filteredData = this.data.filter(d => d.symbol.includes(q));
    }
  }

  onSort(sort: Sort): void {
    if (!sort.active || sort.direction === '') {
      this.filteredData = [...this.data];
      return;
    }
    this.filteredData = [...this.filteredData].sort((a, b) => {
      const isAsc = sort.direction === 'asc';
      const aVal = (a as unknown as Record<string, unknown>)[sort.active] as number;
      const bVal = (b as unknown as Record<string, unknown>)[sort.active] as number;
      return ((aVal ?? 0) - (bVal ?? 0)) * (isAsc ? 1 : -1);
    });
  }

  formatCr(val: number | null): string {
    if (val == null) return '-';
    if (val >= 10000000) return (val / 10000000).toFixed(0) + ' Cr';
    if (val >= 100000) return (val / 100000).toFixed(0) + ' L';
    return val.toFixed(0);
  }
}
