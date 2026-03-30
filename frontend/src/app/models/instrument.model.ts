export interface Instrument {
  id: number;
  symbol: string;
  exchange: string;
  segment: string;
  name: string;
  lot_size: number;
  tick_size: number;
  expiry: string | null;
  strike: number | null;
  option_type: string | null;
  is_active: boolean;
}

export interface ScanResult {
  symbol: string;
  exchange: string;
  segment: string;
  ltp: number;
  change_pct: number;
  volume: number;
  score: number;
  signal: string;
  stop_loss: number | null;
  target_1: number | null;
  target_2: number | null;
  target_3: number | null;
  entry_price: number | null;
  rsi: number | null;
  macd_signal_val: string;
  patterns_detected: string[];
  key_reason: string;
  reasoning: SignalReasoning;
  score_breakdown: ScoreBreakdown;
  volume_ratio: number | null;
  indicators: Record<string, number | null>;
}

export interface SignalReasoning {
  summary: string;
  details: string[];
}

export interface ScoreBreakdown {
  trend: CategoryBreakdown;
  momentum: CategoryBreakdown;
  volume: CategoryBreakdown;
  patterns: CategoryBreakdown;
  support_resistance: CategoryBreakdown;
}

export interface CategoryBreakdown {
  score: number;
  signals: [string, number, string][];
}

export interface Signal {
  id: number;
  symbol: string;
  signal_time: string;
  signal_type: string;
  entry_price: number;
  stop_loss: number | null;
  target_1: number | null;
  target_2: number | null;
  target_3: number | null;
  confidence_score: number;
  reasoning: SignalReasoning;
  status: string;
  exit_price: number | null;
  exit_time: string | null;
  pnl_percent: number | null;
}

export interface Candle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  oi: number | null;
}

export interface NewsArticle {
  id: number;
  headline: string;
  source: string;
  published_at: string;
  url: string;
  related_symbols: string[];
  sentiment_score: number;
  sentiment: 'positive' | 'negative' | 'neutral';
}

export interface FundamentalData {
  symbol: string;
  pe_ratio: number | null;
  pb_ratio: number | null;
  eps: number | null;
  roe: number | null;
  debt_to_equity: number | null;
  market_cap: number | null;
  revenue_growth_yoy: number | null;
  profit_growth_yoy: number | null;
  promoter_holding: number | null;
  fii_holding: number | null;
  dii_holding: number | null;
  updated_at: string;
}

export interface BacktestReport {
  total_signals: number;
  wins: number;
  losses: number;
  neutrals: number;
  win_rate: number;
  avg_profit_pct: number;
  avg_loss_pct: number;
  profit_factor: number;
  expectancy: number;
  total_profit_pct: number;
  total_loss_pct: number;
  results: BacktestResult[];
}

export interface BacktestResult {
  signal_id: number;
  symbol: string;
  signal_type: string;
  entry_price: number;
  exit_price: number;
  result: string;
  pnl_percent: number;
  holding_minutes: number;
}

export interface MarketStatus {
  nifty_ltp: number;
  nifty_change: number;
  banknifty_ltp: number;
  banknifty_change: number;
  india_vix: number;
  advancing: number;
  declining: number;
  time_to_close: string;
}
