import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { Subscription } from 'rxjs';
import { TradingChartComponent } from '../../components/trading-chart/trading-chart.component';
import { IndicatorPanelComponent } from '../../components/indicator-panel/indicator-panel.component';
import { SignalBadgeComponent } from '../../components/signal-badge/signal-badge.component';
import { ApiService } from '../../services/api.service';
import { WebSocketService } from '../../services/websocket.service';
import { StateService } from '../../services/state.service';
import { ScanResult, Instrument } from '../../models/instrument.model';

@Component({
  selector: 'app-chart-page',
  standalone: true,
  imports: [
    CommonModule, FormsModule,
    MatCardModule, MatSelectModule, MatButtonToggleModule,
    MatFormFieldModule, MatInputModule, MatAutocompleteModule,
    TradingChartComponent, IndicatorPanelComponent, SignalBadgeComponent,
  ],
  template: `
    <div class="chart-page">
      <!-- Toolbar -->
      <div class="chart-toolbar">
        <mat-form-field appearance="outline" class="symbol-input">
          <mat-label>Symbol</mat-label>
          <input matInput [(ngModel)]="symbolSearch" (ngModelChange)="filterSymbols()"
                 [matAutocomplete]="auto" placeholder="Search symbol...">
          <mat-autocomplete #auto="matAutocomplete" (optionSelected)="selectSymbol($event.option.value)">
            <mat-option *ngFor="let s of filteredSymbols" [value]="s.symbol">
              {{ s.symbol }} <span class="text-muted text-sm">{{ s.name }}</span>
            </mat-option>
          </mat-autocomplete>
        </mat-form-field>

        <mat-button-toggle-group [(value)]="selectedTimeframe" (change)="onTimeframeChange()">
          <mat-button-toggle value="1m">1m</mat-button-toggle>
          <mat-button-toggle value="5m">5m</mat-button-toggle>
          <mat-button-toggle value="15m">15m</mat-button-toggle>
          <mat-button-toggle value="1h">1H</mat-button-toggle>
          <mat-button-toggle value="1D">1D</mat-button-toggle>
        </mat-button-toggle-group>

        <div class="symbol-info" *ngIf="selectedData">
          <span class="ltp" [class.text-green]="selectedData.change_pct >= 0"
                [class.text-red]="selectedData.change_pct < 0">
            {{ selectedData.ltp | number:'1.2-2' }}
          </span>
          <span class="change" [class.text-green]="selectedData.change_pct >= 0"
                [class.text-red]="selectedData.change_pct < 0">
            {{ selectedData.change_pct >= 0 ? '+' : '' }}{{ selectedData.change_pct | number:'1.2-2' }}%
          </span>
          <app-signal-badge [signal]="selectedData.signal" [score]="selectedData.score"></app-signal-badge>
        </div>
      </div>

      <!-- Main layout -->
      <div class="chart-layout">
        <div class="chart-area">
          <app-trading-chart
            [symbol]="currentSymbol"
            [timeframe]="selectedTimeframe">
          </app-trading-chart>
        </div>
        <div class="panel-area">
          <app-indicator-panel [data]="selectedData"></app-indicator-panel>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .chart-page {
      display: flex;
      flex-direction: column;
      height: calc(100vh - 80px);
    }
    .chart-toolbar {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 0;
      flex-wrap: wrap;
      background: var(--bg-card);
      border-radius: var(--radius-md);
      padding: 12px 16px;
      border: 1px solid var(--border-color);
      box-shadow: var(--shadow-sm);
      margin-bottom: 4px;
    }
    .symbol-input {
      width: 240px;
    }
    .symbol-input ::ng-deep .mat-mdc-form-field-subscript-wrapper {
      display: none;
    }
    .symbol-info {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-left: auto;
      padding: 4px 12px;
      background: var(--bg-hover);
      border-radius: var(--radius-sm);
    }
    .ltp {
      font-size: 22px;
      font-weight: 800;
      letter-spacing: -0.02em;
    }
    .change {
      font-size: 13px;
      font-weight: 600;
    }
    .chart-layout {
      display: flex;
      flex: 1;
      gap: 16px;
      overflow: hidden;
    }
    .chart-area {
      flex: 1;
      min-width: 0;
    }
    .panel-area {
      width: 320px;
      overflow-y: auto;
      flex-shrink: 0;
    }
    @media (max-width: 1024px) {
      .chart-layout { flex-direction: column; }
      .panel-area { width: 100%; max-height: 300px; }
    }
  `],
})
export class ChartComponent implements OnInit, OnDestroy {
  currentSymbol = '';
  selectedTimeframe = '1m';
  symbolSearch = '';
  instruments: Instrument[] = [];
  filteredSymbols: Instrument[] = [];
  selectedData: ScanResult | null = null;

  private routeSub?: Subscription;
  private scanSub?: Subscription;

  constructor(
    private route: ActivatedRoute,
    private api: ApiService,
    private wsService: WebSocketService,
    private state: StateService,
  ) {}

  ngOnInit(): void {
    // Load instruments
    this.api.getInstruments().subscribe({
      next: (instruments) => {
        this.instruments = instruments;
        this.filteredSymbols = instruments.slice(0, 20);
      },
    });

    // Check route param
    this.routeSub = this.route.paramMap.subscribe(params => {
      const sym = params.get('symbol');
      if (sym) {
        this.currentSymbol = sym;
        this.symbolSearch = sym;
        this.loadSymbolData();
      }
    });

    // Listen for scan updates
    this.scanSub = this.wsService.scanResults.subscribe(results => {
      if (this.currentSymbol) {
        const found = results.find(r => r.symbol === this.currentSymbol);
        if (found) {
          this.selectedData = found;
        }
      }
    });
  }

  filterSymbols(): void {
    const q = this.symbolSearch.toLowerCase();
    this.filteredSymbols = this.instruments
      .filter(i => i.symbol.toLowerCase().includes(q) || (i.name && i.name.toLowerCase().includes(q)))
      .slice(0, 20);
  }

  selectSymbol(symbol: string): void {
    this.currentSymbol = symbol;
    this.symbolSearch = symbol;
    this.state.setSelectedSymbol(symbol);
    this.loadSymbolData();
  }

  onTimeframeChange(): void {
    this.state.setSelectedTimeframe(this.selectedTimeframe);
  }

  private loadSymbolData(): void {
    this.api.getDashboardLatest().subscribe({
      next: (res) => {
        const found = res.instruments.find(i => i.symbol === this.currentSymbol);
        if (found) {
          this.selectedData = found;
        }
      },
    });
  }

  ngOnDestroy(): void {
    this.routeSub?.unsubscribe();
    this.scanSub?.unsubscribe();
  }
}
