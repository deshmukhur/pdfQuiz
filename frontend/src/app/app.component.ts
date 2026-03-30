import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatBadgeModule } from '@angular/material/badge';
import { WebSocketService } from './services/websocket.service';
import { MarketStatusBarComponent } from './components/market-status-bar/market-status-bar.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatToolbarModule,
    MatSidenavModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatBadgeModule,
    MarketStatusBarComponent,
  ],
  template: `
    <div class="app-container">
      <!-- Top toolbar -->
      <mat-toolbar class="app-toolbar">
        <button mat-icon-button (click)="sidenavOpen = !sidenavOpen">
          <mat-icon>menu</mat-icon>
        </button>
        <span class="brand">StockScanner</span>
        <span class="subtitle">Indian Market Analysis</span>
        <span class="spacer"></span>
        <app-market-status-bar></app-market-status-bar>
        <span class="connection-dot" [class.connected]="wsConnected" [title]="wsConnected ? 'WebSocket Connected' : 'Disconnected'"></span>
      </mat-toolbar>

      <!-- Layout -->
      <mat-sidenav-container class="sidenav-container">
        <mat-sidenav #sidenav [mode]="'side'" [opened]="sidenavOpen" class="sidenav">
          <mat-nav-list>
            <a mat-list-item routerLink="/dashboard" routerLinkActive="active-link">
              <mat-icon matListItemIcon>dashboard</mat-icon>
              <span matListItemTitle>Dashboard</span>
            </a>
            <a mat-list-item routerLink="/chart" routerLinkActive="active-link">
              <mat-icon matListItemIcon>candlestick_chart</mat-icon>
              <span matListItemTitle>Chart</span>
            </a>
            <a mat-list-item routerLink="/backtest" routerLinkActive="active-link">
              <mat-icon matListItemIcon>science</mat-icon>
              <span matListItemTitle>Backtest</span>
            </a>
            <a mat-list-item routerLink="/news" routerLinkActive="active-link">
              <mat-icon matListItemIcon>newspaper</mat-icon>
              <span matListItemTitle>News</span>
            </a>
            <a mat-list-item routerLink="/fundamentals" routerLinkActive="active-link">
              <mat-icon matListItemIcon>analytics</mat-icon>
              <span matListItemTitle>Fundamentals</span>
            </a>
            <a mat-list-item routerLink="/settings" routerLinkActive="active-link">
              <mat-icon matListItemIcon>settings</mat-icon>
              <span matListItemTitle>Settings</span>
            </a>
            <a mat-list-item routerLink="/auth" routerLinkActive="active-link">
              <mat-icon matListItemIcon>vpn_key</mat-icon>
              <span matListItemTitle>Auth</span>
            </a>
          </mat-nav-list>
        </mat-sidenav>

        <mat-sidenav-content class="main-content">
          <router-outlet></router-outlet>
        </mat-sidenav-content>
      </mat-sidenav-container>
    </div>
  `,
  styles: [`
    .app-container {
      display: flex;
      flex-direction: column;
      height: 100vh;
      background: var(--bg-primary);
    }
    .app-toolbar {
      position: sticky;
      top: 0;
      z-index: 100;
      border-bottom: 1px solid var(--border-color);
      height: 56px;
      padding: 0 16px;
      font-size: 14px;
      background: var(--bg-glass-strong) !important;
      backdrop-filter: blur(20px) saturate(180%);
      -webkit-backdrop-filter: blur(20px) saturate(180%);
    }
    .brand {
      font-weight: 800;
      font-size: 18px;
      margin-left: 12px;
      background: var(--gradient-accent);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      letter-spacing: -0.02em;
    }
    .subtitle {
      font-size: 11px;
      color: var(--text-muted);
      margin-left: 8px;
      font-weight: 500;
      letter-spacing: 0.02em;
    }
    .spacer { flex: 1; }
    .connection-dot {
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: var(--accent-red);
      margin-left: 12px;
      display: inline-block;
      box-shadow: 0 0 0 3px rgba(229, 53, 75, 0.15);
      transition: all 0.3s ease;
    }
    .connection-dot.connected {
      background: var(--accent-green);
      box-shadow: 0 0 0 3px rgba(14, 163, 113, 0.15);
    }
    .sidenav-container {
      flex: 1;
      background: var(--bg-primary);
    }
    .sidenav {
      width: 220px;
      background: var(--bg-secondary) !important;
      border-right: 1px solid var(--border-color) !important;
      padding-top: 8px;
    }
    .sidenav mat-icon {
      color: var(--text-muted);
      margin-right: 10px;
      font-size: 20px;
      width: 20px;
      height: 20px;
    }
    .active-link {
      background: rgba(51, 102, 255, 0.06) !important;
      border-right: 3px solid var(--accent-blue) !important;
    }
    .active-link mat-icon {
      color: var(--accent-blue) !important;
    }
    .active-link span[matListItemTitle] {
      color: var(--accent-blue) !important;
      font-weight: 600;
    }
    .main-content {
      background: var(--bg-primary);
      padding: 24px;
    }
  `],
})
export class AppComponent implements OnInit, OnDestroy {
  sidenavOpen = true;
  wsConnected = false;

  constructor(
    private wsService: WebSocketService,
    private router: Router,
  ) {}

  ngOnInit(): void {
    this.wsService.connect();
    this.wsService.isConnected.subscribe(connected => {
      this.wsConnected = connected;
    });
  }

  ngOnDestroy(): void {
    this.wsService.disconnect();
  }
}
