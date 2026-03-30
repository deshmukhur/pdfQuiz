import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { ApiService } from '../../services/api.service';
import { NewsArticle } from '../../models/instrument.model';

@Component({
  selector: 'app-news',
  standalone: true,
  imports: [
    CommonModule, FormsModule,
    MatCardModule, MatFormFieldModule, MatInputModule,
    MatChipsModule, MatIconModule, MatProgressSpinnerModule,
  ],
  template: `
    <div class="news-page">
      <h2>Market News & Sentiment</h2>

      <div class="search-bar">
        <mat-form-field appearance="outline" class="search-field">
          <mat-label>Filter by symbol</mat-label>
          <input matInput [(ngModel)]="symbolFilter" placeholder="e.g. RELIANCE">
          <mat-icon matSuffix>search</mat-icon>
        </mat-form-field>
      </div>

      <mat-spinner *ngIf="loading" diameter="40"></mat-spinner>

      <div class="news-grid" *ngIf="!loading">
        <mat-card *ngFor="let article of filteredArticles" class="news-card">
          <div class="news-header">
            <span class="sentiment-indicator"
                  [class.positive]="article.sentiment_score > 0.05"
                  [class.negative]="article.sentiment_score < -0.05"
                  [class.neutral-sent]="article.sentiment_score >= -0.05 && article.sentiment_score <= 0.05">
              {{ getSentimentLabel(article.sentiment_score) }}
            </span>
            <span class="sentiment-score">{{ article.sentiment_score | number:'1.3-3' }}</span>
          </div>
          <a [href]="article.url" target="_blank" rel="noopener" class="news-headline">
            {{ article.headline }}
          </a>
          <div class="news-meta">
            <span class="source">{{ article.source }}</span>
            <span class="time">{{ article.published_at | date:'short' }}</span>
          </div>
          <div class="related-symbols" *ngIf="article.related_symbols?.length">
            <mat-chip-set>
              <mat-chip *ngFor="let sym of article.related_symbols" class="symbol-chip">{{ sym }}</mat-chip>
            </mat-chip-set>
          </div>
        </mat-card>
      </div>

      <div class="empty-state" *ngIf="!loading && filteredArticles.length === 0">
        <mat-icon>newspaper</mat-icon>
        <p>No news articles found.</p>
      </div>
    </div>
  `,
  styles: [`
    .news-page { display: flex; flex-direction: column; gap: 20px; }
    h2 { color: var(--text-primary); margin: 0; font-weight: 700; letter-spacing: -0.02em; }
    .search-bar { display: flex; gap: 12px; }
    .search-field { width: 320px; }
    .search-field ::ng-deep .mat-mdc-form-field-subscript-wrapper { display: none; }
    .news-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
      gap: 16px;
    }
    .news-card {
      padding: 20px;
      border-radius: var(--radius-md) !important;
      transition: transform 0.2s ease, box-shadow 0.25s ease;
    }
    .news-card:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-md) !important;
    }
    .news-header {
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 10px;
    }
    .sentiment-indicator {
      padding: 3px 10px; border-radius: 6px; font-size: 10px;
      font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em;
    }
    .sentiment-indicator.positive { background: rgba(14,163,113,0.10); color: var(--accent-green); border: 1px solid rgba(14,163,113,0.12); }
    .sentiment-indicator.negative { background: rgba(229,53,75,0.08); color: var(--accent-red); border: 1px solid rgba(229,53,75,0.10); }
    .sentiment-indicator.neutral-sent { background: rgba(136,146,168,0.10); color: var(--text-secondary); border: 1px solid rgba(136,146,168,0.10); }
    .sentiment-score { font-size: 12px; color: var(--text-muted); font-weight: 500; }
    .news-headline {
      font-size: 14px; font-weight: 600; color: var(--text-primary);
      display: block; margin-bottom: 10px; line-height: 1.5;
      transition: color 0.2s ease;
    }
    .news-headline:hover { color: var(--accent-blue); text-decoration: none; }
    .news-meta {
      display: flex; justify-content: space-between;
      font-size: 11px; color: var(--text-muted); margin-bottom: 10px;
      font-weight: 500;
    }
    .symbol-chip { font-size: 11px !important; }
    .empty-state {
      display: flex; flex-direction: column; align-items: center;
      gap: 16px; padding: 64px; color: var(--text-muted);
    }
    .empty-state mat-icon { font-size: 56px; width: 56px; height: 56px; color: var(--border-strong); }
  `],
})
export class NewsComponent implements OnInit {
  articles: NewsArticle[] = [];
  filteredArticles: NewsArticle[] = [];
  symbolFilter = '';
  loading = true;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.getNews(undefined, 100).subscribe({
      next: (articles) => {
        this.articles = articles;
        this.filteredArticles = articles;
        this.loading = false;
      },
      error: () => { this.loading = false; },
    });
  }

  get filtered(): NewsArticle[] {
    if (!this.symbolFilter.trim()) return this.articles;
    const q = this.symbolFilter.toUpperCase().trim();
    return this.articles.filter(a =>
      a.related_symbols?.some(s => s.includes(q)) || a.headline.toUpperCase().includes(q)
    );
  }

  ngDoCheck(): void {
    this.filteredArticles = this.filtered;
  }

  getSentimentLabel(score: number): string {
    if (score > 0.05) return 'Positive';
    if (score < -0.05) return 'Negative';
    return 'Neutral';
  }
}
