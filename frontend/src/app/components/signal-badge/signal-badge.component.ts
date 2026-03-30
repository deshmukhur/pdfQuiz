import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-signal-badge',
  standalone: true,
  imports: [CommonModule],
  template: `
    <span class="signal-badge" [ngClass]="badgeClass">
      {{ label }}
    </span>
  `,
  styles: [`
    .signal-badge {
      display: inline-block;
      padding: 3px 10px;
      border-radius: 6px;
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
  `],
})
export class SignalBadgeComponent {
  @Input() signal = '';
  @Input() score: number | null = null;

  get label(): string {
    return this.signal.replace(/_/g, ' ');
  }

  get badgeClass(): string {
    const s = this.signal.toUpperCase();
    if (s === 'STRONG_BUY') return 'signal-strong-buy';
    if (s === 'BUY') return 'signal-buy';
    if (s === 'WEAK_BUY') return 'signal-weak-buy';
    if (s === 'NEUTRAL') return 'signal-neutral';
    if (s === 'WEAK_SELL') return 'signal-weak-sell';
    if (s === 'SELL') return 'signal-sell';
    if (s === 'STRONG_SELL') return 'signal-strong-sell';
    return 'signal-neutral';
  }
}
