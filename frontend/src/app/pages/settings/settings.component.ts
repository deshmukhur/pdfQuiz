import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [
    CommonModule, FormsModule,
    MatCardModule, MatFormFieldModule, MatInputModule,
    MatSlideToggleModule, MatButtonModule, MatIconModule,
    MatDividerModule,
  ],
  template: `
    <div class="settings-page">
      <h2>Settings</h2>

      <!-- Connection Status -->
      <mat-card class="settings-card">
        <div class="card-title">
          <mat-icon>cloud</mat-icon>
          Connection Status
        </div>
        <div class="status-row">
          <span>Fyers API</span>
          <span class="status-badge" [class.connected]="fyersConnected" [class.disconnected]="!fyersConnected">
            {{ fyersConnected ? 'Connected' : 'Not Connected' }}
          </span>
        </div>
        <div class="status-row">
          <span>WebSocket</span>
          <span class="status-badge" [class.connected]="wsConnected">
            {{ wsConnected ? 'Connected' : 'Disconnected' }}
          </span>
        </div>
      </mat-card>

      <!-- Scanner Settings -->
      <mat-card class="settings-card">
        <div class="card-title">
          <mat-icon>radar</mat-icon>
          Scanner Settings
        </div>
        <div class="settings-grid">
          <mat-form-field appearance="outline">
            <mat-label>Scan Interval (seconds)</mat-label>
            <input matInput type="number" [(ngModel)]="scanInterval" min="30" max="300">
          </mat-form-field>
          <mat-form-field appearance="outline">
            <mat-label>Min Score Filter</mat-label>
            <input matInput type="number" [(ngModel)]="minScore" min="-100" max="100">
          </mat-form-field>
          <mat-form-field appearance="outline">
            <mat-label>Min Volume Ratio</mat-label>
            <input matInput type="number" [(ngModel)]="minVolumeRatio" min="0" step="0.1">
          </mat-form-field>
        </div>
      </mat-card>

      <!-- Notification Settings -->
      <mat-card class="settings-card">
        <div class="card-title">
          <mat-icon>notifications</mat-icon>
          Notifications
        </div>
        <div class="toggle-row">
          <mat-slide-toggle [(ngModel)]="enableSoundAlerts">Sound Alerts for Strong Signals</mat-slide-toggle>
        </div>
        <div class="toggle-row">
          <mat-slide-toggle [(ngModel)]="enableBrowserNotifs">Browser Notifications</mat-slide-toggle>
        </div>
      </mat-card>

      <!-- Display Settings -->
      <mat-card class="settings-card">
        <div class="card-title">
          <mat-icon>palette</mat-icon>
          Display
        </div>
        <div class="toggle-row">
          <mat-slide-toggle [(ngModel)]="showVolume">Show Volume on Chart</mat-slide-toggle>
        </div>
        <div class="toggle-row">
          <mat-slide-toggle [(ngModel)]="showPatterns">Show Pattern Annotations</mat-slide-toggle>
        </div>
        <div class="toggle-row">
          <mat-slide-toggle [(ngModel)]="showNewsTicker">Show News Ticker</mat-slide-toggle>
        </div>
      </mat-card>

      <div class="actions">
        <button mat-raised-button color="primary" (click)="saveSettings()">
          <mat-icon>save</mat-icon> Save Settings
        </button>
      </div>
    </div>
  `,
  styles: [`
    .settings-page { display: flex; flex-direction: column; gap: 20px; max-width: 700px; }
    h2 { margin: 0; color: var(--text-primary); font-weight: 700; letter-spacing: -0.02em; }
    .settings-card {
      padding: 20px;
      border-radius: var(--radius-md) !important;
    }
    .card-title {
      display: flex; align-items: center; gap: 10px;
      font-size: 14px; font-weight: 700; color: var(--text-primary);
      margin-bottom: 16px;
      letter-spacing: -0.01em;
    }
    .card-title mat-icon {
      color: var(--accent-blue);
      font-size: 20px;
      width: 20px;
      height: 20px;
    }
    .status-row {
      display: flex; justify-content: space-between; align-items: center;
      padding: 10px 0; border-bottom: 1px solid var(--border-color);
      font-weight: 500;
    }
    .status-badge {
      padding: 3px 10px; border-radius: 6px; font-size: 10px; font-weight: 700;
      letter-spacing: 0.04em; text-transform: uppercase;
    }
    .status-badge.connected { background: rgba(14,163,113,0.10); color: var(--accent-green); border: 1px solid rgba(14,163,113,0.12); }
    .status-badge.disconnected { background: rgba(229,53,75,0.08); color: var(--accent-red); border: 1px solid rgba(229,53,75,0.10); }
    .settings-grid {
      display: grid; grid-template-columns: 1fr 1fr; gap: 14px;
    }
    .settings-grid ::ng-deep .mat-mdc-form-field-subscript-wrapper { display: none; }
    .toggle-row { padding: 10px 0; }
    .actions { padding: 12px 0; }
  `],
})
export class SettingsComponent implements OnInit {
  fyersConnected = false;
  wsConnected = false;
  scanInterval = 60;
  minScore = 0;
  minVolumeRatio = 0;
  enableSoundAlerts = true;
  enableBrowserNotifs = false;
  showVolume = true;
  showPatterns = true;
  showNewsTicker = true;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.getFyersStatus().subscribe({
      next: (status) => { this.fyersConnected = status.authenticated; },
      error: () => { this.fyersConnected = false; },
    });

    // Load saved settings from localStorage
    const saved = localStorage.getItem('scanner_settings');
    if (saved) {
      const s = JSON.parse(saved);
      this.scanInterval = s.scanInterval ?? 60;
      this.minScore = s.minScore ?? 0;
      this.minVolumeRatio = s.minVolumeRatio ?? 0;
      this.enableSoundAlerts = s.enableSoundAlerts ?? true;
      this.enableBrowserNotifs = s.enableBrowserNotifs ?? false;
      this.showVolume = s.showVolume ?? true;
      this.showPatterns = s.showPatterns ?? true;
      this.showNewsTicker = s.showNewsTicker ?? true;
    }
  }

  saveSettings(): void {
    const settings = {
      scanInterval: this.scanInterval,
      minScore: this.minScore,
      minVolumeRatio: this.minVolumeRatio,
      enableSoundAlerts: this.enableSoundAlerts,
      enableBrowserNotifs: this.enableBrowserNotifs,
      showVolume: this.showVolume,
      showPatterns: this.showPatterns,
      showNewsTicker: this.showNewsTicker,
    };
    localStorage.setItem('scanner_settings', JSON.stringify(settings));
  }
}
