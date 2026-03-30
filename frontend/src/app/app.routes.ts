import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  {
    path: 'dashboard',
    loadComponent: () =>
      import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent),
  },
  {
    path: 'chart',
    loadComponent: () =>
      import('./pages/chart/chart.component').then(m => m.ChartComponent),
  },
  {
    path: 'chart/:symbol',
    loadComponent: () =>
      import('./pages/chart/chart.component').then(m => m.ChartComponent),
  },
  {
    path: 'backtest',
    loadComponent: () =>
      import('./pages/backtest/backtest.component').then(m => m.BacktestComponent),
  },
  {
    path: 'news',
    loadComponent: () =>
      import('./pages/news/news.component').then(m => m.NewsComponent),
  },
  {
    path: 'fundamentals',
    loadComponent: () =>
      import('./pages/fundamentals/fundamentals.component').then(m => m.FundamentalsComponent),
  },
  {
    path: 'settings',
    loadComponent: () =>
      import('./pages/settings/settings.component').then(m => m.SettingsComponent),
  },
  {
    path: 'auth',
    loadComponent: () =>
      import('./pages/auth/auth.component').then(m => m.AuthComponent),
  },
  { path: '**', redirectTo: 'dashboard' },
];
