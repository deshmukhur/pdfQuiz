import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NewsArticle } from '../../models/instrument.model';

@Component({
  selector: 'app-news-ticker',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="news-ticker" *ngIf="articles.length > 0">
      <div class="news-ticker-content">
        <span *ngFor="let article of articles; let i = index" class="ticker-item">
          <span class="sentiment-dot"
                [class.positive]="article.sentiment_score > 0.05"
                [class.negative]="article.sentiment_score < -0.05"></span>
          <a [href]="article.url" target="_blank" rel="noopener">{{ article.headline }}</a>
          <span class="source">— {{ article.source }}</span>
          <span class="separator" *ngIf="i < articles.length - 1">&nbsp;&nbsp;|&nbsp;&nbsp;</span>
        </span>
      </div>
    </div>
  `,
  styles: [`
    .ticker-item {
      white-space: nowrap;
    }
    .ticker-item a {
      color: var(--text-primary);
      font-size: 12px;
      font-weight: 500;
      transition: color 0.2s ease;
    }
    .ticker-item a:hover {
      color: var(--accent-blue);
      text-decoration: none;
    }
    .source {
      color: var(--text-muted);
      font-size: 11px;
      font-weight: 500;
    }
    .separator {
      color: var(--border-strong);
    }
    .sentiment-dot {
      display: inline-block;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--neutral);
      margin-right: 5px;
      vertical-align: middle;
    }
    .sentiment-dot.positive { background: var(--accent-green); box-shadow: 0 0 0 2px rgba(14,163,113,0.15); }
    .sentiment-dot.negative { background: var(--accent-red); box-shadow: 0 0 0 2px rgba(229,53,75,0.15); }
  `],
})
export class NewsTickerComponent {
  @Input() articles: NewsArticle[] = [];
}
