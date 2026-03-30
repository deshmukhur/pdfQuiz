import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatIconModule } from '@angular/material/icon';
import { Subscription, interval } from 'rxjs';
import { InstrumentTableComponent } from '../../components/instrument-table/instrument-table.component';
import { NewsTickerComponent } from '../../components/news-ticker/news-ticker.component';
import { ApiService } from '../../services/api.service';
import { WebSocketService } from '../../services/websocket.service';
import { ScanResult, NewsArticle } from '../../models/instrument.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule, MatCardModule, MatButtonToggleModule,
    MatProgressSpinnerModule, MatIconModule,
    InstrumentTableComponent, NewsTickerComponent,
  ],
  template: `
    <div class="dashboard">
      <!-- News ticker -->
      <app-news-ticker [articles]="newsArticles"></app-news-ticker>

      <!-- Stats row -->
      <div class="stats-row">
        <mat-card class="stat-card">
          <div class="stat-label">Total Scanned</div>
          <div class="stat-value">{{ scanResults.length }}</div>
        </mat-card>
        <mat-card class="stat-card">
          <div class="stat-label">Strong Buy</div>
          <div class="stat-value text-green">{{ countBySignal('STRONG_BUY') }}</div>
        </mat-card>
        <mat-card class="stat-card">
          <div class="stat-label">Buy</div>
          <div class="stat-value text-green">{{ countBySignal('BUY') }}</div>
        </mat-card>
        <mat-card class="stat-card">
          <div class="stat-label">Neutral</div>
          <div class="stat-value">{{ countBySignal('NEUTRAL') }}</div>
        </mat-card>
        <mat-card class="stat-card">
          <div class="stat-label">Sell</div>
          <div class="stat-value text-red">{{ countBySignal('SELL') }}</div>
        </mat-card>
        <mat-card class="stat-card">
          <div class="stat-label">Strong Sell</div>
          <div class="stat-value text-red">{{ countBySignal('STRONG_SELL') }}</div>
        </mat-card>
      </div>

      <!-- Filter bar -->
      <div class="filter-bar">
        <mat-button-toggle-group [(value)]="selectedFilter" (change)="applyFilter()">
          <mat-button-toggle value="all">All</mat-button-toggle>
          <mat-button-toggle value="buy">Buys Only</mat-button-toggle>
          <mat-button-toggle value="sell">Sells Only</mat-button-toggle>
          <mat-button-toggle value="strong">Strong Only</mat-button-toggle>
        </mat-button-toggle-group>
        <span class="last-scan text-muted text-sm" *ngIf="lastScanTime">
          Last scan: {{ lastScanTime | date:'HH:mm:ss' }}
        </span>
      </div>

      <!-- Main scanner table -->
      <div class="table-section">
        <mat-spinner *ngIf="loading" diameter="40"></mat-spinner>
        <app-instrument-table
          *ngIf="!loading"
          [data]="filteredResults"
          (symbolSelected)="onSymbolSelected($event)">
        </app-instrument-table>
        <div class="empty-state" *ngIf="!loading && filteredResults.length === 0">
          <mat-icon>search_off</mat-icon>
          <p>No scan results yet. Scanner runs every 60 seconds during market hours (09:15–15:30 IST).</p>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .dashboard {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .stats-row {
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 12px;
    }
    .stat-card {
      padding: 16px 12px;
      text-align: center;
      border-radius: var(--radius-md) !important;
      border: 1px solid var(--border-color) !important;
      background: var(--bg-card) !important;
      transition: transform 0.2s ease, box-shadow 0.25s ease;
    }
    .stat-card:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-md) !important;
    }
    .stat-label {
      font-size: 10px;
      color: var(--text-muted);
      text-transform: uppercase;
      font-weight: 600;
      letter-spacing: 0.06em;
    }
    .stat-value {
      font-size: 26px;
      font-weight: 800;
      margin-top: 6px;
      letter-spacing: -0.02em;
    }
    .filter-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 0;
    }
    .table-section {
      min-height: 200px;
      display: flex;
      flex-direction: column;
      align-items: center;
      background: var(--bg-card);
      border-radius: var(--radius-md);
      border: 1px solid var(--border-color);
      padding: 4px;
      box-shadow: var(--shadow-card);
    }
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;
      padding: 64px;
      color: var(--text-muted);
    }
    .empty-state mat-icon {
      font-size: 56px;
      width: 56px;
      height: 56px;
      color: var(--border-strong);
    }
    .empty-state p {
      max-width: 360px;
      text-align: center;
      line-height: 1.5;
    }
    @media (max-width: 900px) {
      .stats-row { grid-template-columns: repeat(3, 1fr); }
    }
  `],
})
export class DashboardComponent implements OnInit, OnDestroy {
  scanResults: ScanResult[] = [];
  filteredResults: ScanResult[] = [];
  newsArticles: NewsArticle[] = [];
  selectedFilter = 'all';
  loading = true;
  lastScanTime: Date | null = null;

  private wsSub?: Subscription;
  private pollSub?: Subscription;

  constructor(
    private api: ApiService,
    private wsService: WebSocketService,
    private router: Router,
  ) {}

  ngOnInit(): void {
    // Load initial data via HTTP
    this.api.getDashboardLatest().subscribe({
      next: (res) => {
        this.scanResults = res.instruments;
        this.applyFilter();
        this.loading = false;
        this.lastScanTime = new Date();
      },
      error: () => {
        this.loading = false;
      },
    });

    // Subscribe to WebSocket updates
    this.wsSub = this.wsService.scanResults.subscribe(results => {
      if (results.length > 0) {
        this.scanResults = results;
        this.applyFilter();
        this.lastScanTime = new Date();
        this.loading = false;
      }
    });

    // Fetch news
    this.api.getNews(undefined, 20).subscribe({
      next: (articles) => { this.newsArticles = articles; },
    });

    // Poll dashboard every 30s as fallback
    this.pollSub = interval(30000).subscribe(() => {
      this.api.getDashboardLatest().subscribe({
        next: (res) => {
          if (res.instruments.length > 0) {
            this.scanResults = res.instruments;
            this.applyFilter();
            this.lastScanTime = new Date();
          }
        },
      });
    });
  }

  applyFilter(): void {
    switch (this.selectedFilter) {
      case 'buy':
        this.filteredResults = this.scanResults.filter(r =>
          ['BUY', 'STRONG_BUY', 'WEAK_BUY'].includes(r.signal));
        break;
      case 'sell':
        this.filteredResults = this.scanResults.filter(r =>
          ['SELL', 'STRONG_SELL', 'WEAK_SELL'].includes(r.signal));
        break;
      case 'strong':
        this.filteredResults = this.scanResults.filter(r =>
          ['STRONG_BUY', 'STRONG_SELL'].includes(r.signal));
        break;
      default:
        this.filteredResults = [...this.scanResults];
    }
  }

  countBySignal(signal: string): number {
    return this.scanResults.filter(r => r.signal === signal).length;
  }

  onSymbolSelected(symbol: string): void {
    this.router.navigate(['/chart', symbol]);
  }

  ngOnDestroy(): void {
    this.wsSub?.unsubscribe();
    this.pollSub?.unsubscribe();
  }
}
