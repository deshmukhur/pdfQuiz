import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { ScanResult } from '../models/instrument.model';

@Injectable({ providedIn: 'root' })
export class StateService {
  private selectedSymbol$ = new BehaviorSubject<string>('');
  private selectedTimeframe$ = new BehaviorSubject<string>('1m');
  private dashboardFilters$ = new BehaviorSubject<DashboardFilters>({});

  get selectedSymbol(): Observable<string> {
    return this.selectedSymbol$.asObservable();
  }

  get selectedTimeframe(): Observable<string> {
    return this.selectedTimeframe$.asObservable();
  }

  get dashboardFilters(): Observable<DashboardFilters> {
    return this.dashboardFilters$.asObservable();
  }

  setSelectedSymbol(symbol: string): void {
    this.selectedSymbol$.next(symbol);
  }

  setSelectedTimeframe(tf: string): void {
    this.selectedTimeframe$.next(tf);
  }

  setDashboardFilters(filters: DashboardFilters): void {
    this.dashboardFilters$.next(filters);
  }

  getCurrentSymbol(): string {
    return this.selectedSymbol$.value;
  }

  getCurrentTimeframe(): string {
    return this.selectedTimeframe$.value;
  }
}

export interface DashboardFilters {
  segment?: string;
  exchange?: string;
  minScore?: number;
  minVolumeRatio?: number;
}
