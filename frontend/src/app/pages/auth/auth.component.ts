import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-auth',
  standalone: true,
  imports: [
    CommonModule, FormsModule,
    MatCardModule, MatButtonModule, MatFormFieldModule,
    MatInputModule, MatIconModule, MatProgressSpinnerModule,
  ],
  template: `
    <div class="auth-page">
      <mat-card class="auth-card">
        <div class="auth-header">
          <mat-icon class="auth-icon">vpn_key</mat-icon>
          <h2>Fyers API Authentication</h2>
          <p class="text-muted">Connect your Fyers trading account to receive real-time market data</p>
        </div>

        <!-- Status -->
        <div class="status-section">
          <div class="status-indicator" [class.connected]="isAuthenticated">
            <mat-icon>{{ isAuthenticated ? 'check_circle' : 'cancel' }}</mat-icon>
            <span>{{ isAuthenticated ? 'Connected' : 'Not Connected' }}</span>
          </div>
          <p class="client-id text-muted" *ngIf="clientId">Client ID: {{ clientId }}</p>
        </div>

        <mat-spinner *ngIf="loading" diameter="30"></mat-spinner>

        <!-- OAuth Login -->
        <div class="auth-actions" *ngIf="!isAuthenticated && !loading">
          <p class="text-sm text-muted">Click below to authenticate via Fyers OAuth2:</p>
          <button mat-raised-button color="primary" (click)="startOAuth()" class="oauth-btn">
            <mat-icon>login</mat-icon>
            Login with Fyers
          </button>

          <div class="divider">
            <span>OR</span>
          </div>

          <p class="text-sm text-muted">Paste an existing access token:</p>
          <mat-form-field appearance="outline" class="token-field">
            <mat-label>Access Token</mat-label>
            <input matInput [(ngModel)]="manualToken" placeholder="Paste Fyers access token">
          </mat-form-field>
          <button mat-raised-button color="accent" (click)="setManualToken()" [disabled]="!manualToken.trim()">
            <mat-icon>key</mat-icon>
            Set Token
          </button>
        </div>

        <!-- Connected state -->
        <div class="connected-info" *ngIf="isAuthenticated">
          <p class="text-green">Your Fyers account is connected. Real-time market data is streaming.</p>
          <button mat-stroked-button color="warn" (click)="checkStatus()">
            <mat-icon>refresh</mat-icon> Refresh Status
          </button>
        </div>

        <!-- Message -->
        <p class="message" *ngIf="message" [class.error]="isError" [class.success]="!isError">
          {{ message }}
        </p>
      </mat-card>
    </div>
  `,
  styles: [`
    .auth-page {
      display: flex; justify-content: center; align-items: flex-start; padding: 40px;
    }
    .auth-card {
      max-width: 480px; width: 100%; padding: 36px;
      border-radius: var(--radius-lg) !important;
      box-shadow: var(--shadow-lg) !important;
    }
    .auth-header {
      text-align: center; margin-bottom: 28px;
    }
    .auth-icon {
      font-size: 48px; width: 48px; height: 48px;
      background: var(--gradient-accent);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: 14px;
    }
    h2 { margin: 0 0 8px; color: var(--text-primary); font-weight: 700; letter-spacing: -0.02em; }
    .status-section {
      text-align: center; margin-bottom: 24px;
      padding: 18px; background: var(--bg-hover); border-radius: var(--radius-md);
      border: 1px solid var(--border-color);
    }
    .status-indicator {
      display: flex; align-items: center; justify-content: center; gap: 8px;
      font-size: 16px; font-weight: 700;
    }
    .status-indicator.connected { color: var(--accent-green); }
    .status-indicator:not(.connected) { color: var(--accent-red); }
    .client-id { margin-top: 6px; font-size: 12px; font-weight: 500; }
    .auth-actions {
      display: flex; flex-direction: column; align-items: center; gap: 14px;
    }
    .oauth-btn { width: 100%; max-width: 300px; border-radius: var(--radius-sm) !important; }
    .divider {
      width: 100%; text-align: center; position: relative;
      margin: 16px 0; color: var(--text-muted); font-size: 12px; font-weight: 600;
    }
    .divider::before, .divider::after {
      content: ''; position: absolute; top: 50%; width: 40%;
      height: 1px; background: var(--border-strong);
    }
    .divider::before { left: 0; }
    .divider::after { right: 0; }
    .token-field { width: 100%; }
    .token-field ::ng-deep .mat-mdc-form-field-subscript-wrapper { display: none; }
    .connected-info { text-align: center; }
    .message {
      text-align: center; margin-top: 18px; padding: 10px 14px;
      border-radius: var(--radius-sm); font-size: 13px; font-weight: 500;
    }
    .message.error { background: rgba(229,53,75,0.08); color: var(--accent-red); border: 1px solid rgba(229,53,75,0.12); }
    .message.success { background: rgba(14,163,113,0.08); color: var(--accent-green); border: 1px solid rgba(14,163,113,0.12); }
  `],
})
export class AuthComponent implements OnInit {
  isAuthenticated = false;
  clientId = '';
  manualToken = '';
  loading = true;
  message = '';
  isError = false;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.checkStatus();
  }

  checkStatus(): void {
    this.loading = true;
    this.api.getFyersStatus().subscribe({
      next: (status) => {
        this.isAuthenticated = status.authenticated;
        this.clientId = status.client_id;
        this.loading = false;
      },
      error: () => {
        this.isAuthenticated = false;
        this.loading = false;
      },
    });
  }

  startOAuth(): void {
    this.api.getFyersAuthUrl().subscribe({
      next: (res) => {
        window.open(res.auth_url, '_blank');
        this.message = 'Complete login in the opened window. Refresh status after login.';
        this.isError = false;
      },
      error: (err) => {
        this.message = 'Failed to get auth URL: ' + (err.error?.detail || err.message);
        this.isError = true;
      },
    });
  }

  setManualToken(): void {
    // POST to /api/auth/fyers/token
    const url = 'http://localhost:8000/api/auth/fyers/token';
    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ access_token: this.manualToken.trim() }),
    })
    .then(r => r.json())
    .then(() => {
      this.message = 'Token set successfully!';
      this.isError = false;
      this.checkStatus();
    })
    .catch(err => {
      this.message = 'Failed to set token: ' + err.message;
      this.isError = true;
    });
  }
}
