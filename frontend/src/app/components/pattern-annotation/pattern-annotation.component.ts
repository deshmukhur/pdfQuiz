import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-pattern-annotation',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="pattern-annotation" *ngIf="patterns.length > 0">
      <div class="pattern-item" *ngFor="let p of patterns" [ngClass]="getDirectionClass(p)">
        <span class="pattern-icon">{{ getIcon(p) }}</span>
        <span class="pattern-name">{{ p.name || p }}</span>
        <span class="pattern-confidence" *ngIf="p.confidence">({{ p.confidence }})</span>
      </div>
    </div>
  `,
  styles: [`
    .pattern-annotation {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .pattern-item {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 11px;
      background: var(--bg-hover);
      border: 1px solid var(--border-color);
      font-weight: 500;
      transition: border-color 0.2s ease;
    }
    .pattern-item.bullish {
      border-color: rgba(14, 163, 113, 0.25);
      color: var(--accent-green);
      background: rgba(14, 163, 113, 0.05);
    }
    .pattern-item.bearish {
      border-color: rgba(229, 53, 75, 0.25);
      color: var(--accent-red);
      background: rgba(229, 53, 75, 0.05);
    }
    .pattern-icon { font-size: 12px; }
    .pattern-confidence {
      color: var(--text-muted);
      font-size: 10px;
      font-weight: 600;
    }
  `],
})
export class PatternAnnotationComponent {
  @Input() patterns: PatternInfo[] = [];

  getDirectionClass(p: PatternInfo): string {
    if (typeof p === 'string') return '';
    return p.direction === 'bullish' ? 'bullish' : p.direction === 'bearish' ? 'bearish' : '';
  }

  getIcon(p: PatternInfo): string {
    if (typeof p === 'string') return '';
    return p.direction === 'bullish' ? '\u25B2' : p.direction === 'bearish' ? '\u25BC' : '\u25C6';
  }
}

interface PatternInfo {
  name?: string;
  direction?: string;
  confidence?: string;
  [key: string]: unknown;
}
