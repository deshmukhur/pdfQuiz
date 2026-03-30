import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { WebSocketService } from '../../services/websocket.service';

@Component({
  selector: 'app-market-status-bar',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="market-bar">
      <div class="market-item">
        <span class="label">NIFTY</span>
        <span class="value" [class.text-green]="niftyChange >= 0" [class.text-red]="niftyChange < 0">
          {{ niftyLtp | number:'1.2-2' }}
        </span>
        <span class="change" [class.text-green]="niftyChange >= 0" [class.text-red]="niftyChange < 0">
          ({{ niftyChange >= 0 ? '+' : '' }}{{ niftyChange | number:'1.2-2' }}%)
        </span>
      </div>
      <div class="market-item">
        <span class="label">BANKNIFTY</span>
        <span class="value" [class.text-green]="bankNiftyChange >= 0" [class.text-red]="bankNiftyChange < 0">
          {{ bankNiftyLtp | number:'1.2-2' }}
        </span>
        <span class="change" [class.text-green]="bankNiftyChange >= 0" [class.text-red]="bankNiftyChange < 0">
          ({{ bankNiftyChange >= 0 ? '+' : '' }}{{ bankNiftyChange | number:'1.2-2' }}%)
        </span>
      </div>
      <div class="market-item">
        <span class="label">VIX</span>
        <span class="value">{{ indiaVix | number:'1.2-2' }}</span>
      </div>
      <div class="market-item market-clock">
        <span class="label">{{ marketOpen ? 'LIVE' : 'CLOSED' }}</span>
        <span class="live-dot" [class.active]="marketOpen"></span>
      </div>
    </div>
  `,
  styles: [`
    .market-bar {
      display: flex;
      align-items: center;
      gap: 18px;
      font-size: 12px;
    }
    .market-item {
      display: flex;
      align-items: center;
      gap: 5px;
      padding: 4px 10px;
      background: var(--bg-hover);
      border-radius: 6px;
      border: 1px solid var(--border-color);
    }
    .label {
      color: var(--text-muted);
      font-weight: 600;
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .value {
      font-weight: 700;
    }
    .change {
      font-size: 11px;
      font-weight: 600;
    }
    .market-clock {
      border: none;
      background: transparent;
    }
    .live-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--accent-red);
      margin-left: 4px;
      box-shadow: 0 0 0 2px rgba(229,53,75,0.15);
    }
    .live-dot.active {
      background: var(--accent-green);
      box-shadow: 0 0 0 2px rgba(14,163,113,0.15);
      animation: pulse 2s infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.4; }
    }
  `],
})
export class MarketStatusBarComponent implements OnInit, OnDestroy {
  niftyLtp = 0;
  niftyChange = 0;
  bankNiftyLtp = 0;
  bankNiftyChange = 0;
  indiaVix = 0;
  marketOpen = false;

  private sub?: Subscription;

  constructor(private wsService: WebSocketService) {}

  ngOnInit(): void {
    this.checkMarketHours();
    this.sub = this.wsService.marketStatus.subscribe(status => {
      if (status && Object.keys(status).length > 0) {
        this.niftyLtp = (status['nifty_ltp'] as number) || 0;
        this.niftyChange = (status['nifty_change'] as number) || 0;
        this.bankNiftyLtp = (status['banknifty_ltp'] as number) || 0;
        this.bankNiftyChange = (status['banknifty_change'] as number) || 0;
        this.indiaVix = (status['india_vix'] as number) || 0;
      }
    });
  }

  private checkMarketHours(): void {
    const now = new Date();
    const istOffset = 5.5 * 60 * 60 * 1000;
    const ist = new Date(now.getTime() + istOffset);
    const hours = ist.getUTCHours();
    const minutes = ist.getUTCMinutes();
    const totalMin = hours * 60 + minutes;
    const day = ist.getUTCDay();
    this.marketOpen = day >= 1 && day <= 5 && totalMin >= 555 && totalMin <= 930;
  }

  ngOnDestroy(): void {
    this.sub?.unsubscribe();
  }
}
