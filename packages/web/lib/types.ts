export type Verdict = "BUY" | "PASS" | null;

export interface BidLine {
  part_id: string;
  name: string;
  category: string | null;
  qty: number;
  unit_price: number | null;
  line_total: number;
}

export interface BidProjection {
  gross: number;
  fees: number;
  shipping: number;
  net: number;
  roi: number;
}

export interface BidResult {
  machine: string;
  specs: string | null;
  verdict: Verdict;
  warning: string | null;
  parts_value: number | null;
  max_bid: number | null;
  total_cost: number;
  projection: BidProjection | null;
  lines: BidLine[];
}

export interface ApiErrorShape {
  error: { code: string; message: string; detail?: unknown };
}

export interface Paged<T> {
  items: T[];
  total: number;
}

// ── inventory ────────────────────────────────────────────────────────────────
export type InvStatus = "in_stock" | "listed" | "sold" | "scrapped";

export interface InventoryItem {
  id: number;
  title: string;
  product_id: number | null;
  machine_model: string | null;
  condition: string | null;
  buy_price: number;
  buy_shipping: number;
  buy_date: string;
  source_id: number | null;
  status: InvStatus;
  sell_price: number | null;
  sell_fees: number | null;
  sell_shipping: number | null;
  sell_date: string | null;
  sold_on: string | null;
  notes: string | null;
  net_profit: number;
  roi_pct: number | null;
  primary_photo?: string | null; // filename of cover photo (Tier 4)
  photo_count?: number;
}

export interface PnlSummary {
  period: string;
  realized_profit: number;
  unrealized_cost: number;
  item_count: number;
  by_status: Partial<Record<InvStatus, number>>;
}

// ── sources / leads ──────────────────────────────────────────────────────────
export interface Source {
  id: number;
  name: string;
  type: string;
  reliability_score: number;
  notes: string | null;
}

export interface SourcePerf extends Source {
  items_bought: number;
  total_spend: number;
  realized_profit: number;
  sold_count: number;
  avg_roi_pct: number | null;
}

export interface Lead {
  id: number;
  kind: string;
  name: string;
  contact: string | null;
  location: string | null;
  schedule_note: string | null;
  last_contacted: string | null;
  url: string | null;
  notes: string | null;
}

// ── catalog ──────────────────────────────────────────────────────────────────
export interface PriceSummary {
  avg_price_30d: number;
  avg_price_90d: number | null;
  lowest_price: number;
  highest_price: number;
  sample_count: number;
}

export interface Part {
  id: string;
  name: string;
  category: string;
  subcategory: string | null;
  price: PriceSummary | null;
  net_profit: number | null;
  sell_speed: string;
}

export interface Category {
  id: number;
  name: string;
  icon: string | null;
  parent_id: number | null;
  sort_order: number;
}

// ── scanner ──────────────────────────────────────────────────────────────────
export interface FlaggedDeal {
  id: number;
  source: string;
  lot_key: string | null;
  title: string;
  matched_model: string | null;
  current_bid: number | null;
  max_bid: number | null;
  headroom: number | null;
  margin_good: number;
  url: string | null;
  flagged_at: string;
  dismissed: number;
  quantity: number | null;
  per_unit_cost: number | null;
  max_bid_per_unit: number | null;
}

export interface Watch {
  id: number;
  search_text: string;
  category_ids: string | null;
  location_state: string | null;
}

export interface ScanLot {
  title: string;
  matched_model: string | null;
  current_bid: number | null;
  max_bid?: number;
  headroom?: number;
  margin_good?: boolean;
  priced: boolean;
  is_new: boolean;
  quantity: number;
  total_cost: number;
  per_unit_cost: number;
  max_bid_per_unit?: number;
  quantity_confident?: boolean;
  is_sold?: boolean;
  url?: string | null;
}

export interface ScanResult {
  scanned: number;
  matched: number;
  good: number;
  sold?: number;
  lots: ScanLot[];
  warnings?: string[];
  warning?: string;
}

// ── price refresh ────────────────────────────────────────────────────────────
export interface RefreshResult {
  source: string;
  parts: number;
  inserted: number;
  warning?: string;
  warnings?: string[];
}

export interface Staleness {
  total: number;
  blind: number;
  items: Array<{ id: string; name: string; newest: string | null; samples_30d: number }>;
}

// ── ITAD CRM ─────────────────────────────────────────────────────────────────
export type ItadStatus = "not-contacted" | "contacted" | "active" | "dead";

export interface ItadCompany {
  id: number;
  name: string;
  phone: string | null;
  address: string | null;
  city: string;
  state: string;
  website: string | null;
  contact_person: string | null;
  status: ItadStatus;
  reliability: number;
  sells_singles: boolean;
  typical_bare_price: number | null;
  typical_loaded_price: number | null;
  notes: string | null;
  latitude: number | null;
  longitude: number | null;
  // from itad_company_summary
  call_count: number;
  last_call_date: string | null;
  purchase_count: number;
  total_spent: number;
  total_units: number;
  avg_unit_price: number | null;
  win_rate_pct: number | null;
}

export interface ItadCall {
  id: number;
  company_id: number;
  call_date: string;
  spoke_with: string | null;
  notes: string;
  has_inventory: number;
  pricing_text: string | null;
  follow_up: string | null;
}

export interface ItadPurchase {
  id: number;
  company_id: number;
  purchase_date: string;
  model: string | null;
  quantity: number;
  unit_price: number;
  total_cost: number;
  had_ram: number;
  had_storage: number;
  working_count: number | null;
  notes: string | null;
}

export interface ItadDetail {
  company: ItadCompany;
  calls: ItadCall[];
  purchases: ItadPurchase[];
}

// ── dashboard ────────────────────────────────────────────────────────────────
export interface Dashboard {
  period: string;
  profit_this_period: number;
  items_in_stock: number;
  items_listed: number;
  unrealized_cost: number;
  best_deals: FlaggedDeal[];
  recent_sales: Array<{
    id: number;
    title: string;
    sell_price: number | null;
    sell_date: string | null;
    net_profit: number;
    roi_pct: number | null;
  }>;
  staleness_warnings: number;
}

// ── agents ───────────────────────────────────────────────────────────────────
export interface Agent {
  id: string;
  display_name: string;
  layer: "operational" | "strategic";
  provider: string;
  model: string;
  schedule_cron: string | null;
  daily_budget_usd: number;
  enabled: number;
  last_status: string | null;
  last_run_at: string | null;
  runs_today: number;
  cost_today: number;
  errors_today: number;
}

export interface AgentRun {
  id: number;
  agent_id: string;
  started_at: string;
  finished_at: string | null;
  trigger: string;
  provider: string | null;
  model: string | null;
  tokens_in: number;
  tokens_out: number;
  cost_usd: number;
  status: string;
  output_summary: string | null;
  error: string | null;
  prompt_version: string | null;
}

export interface AgentCosts {
  by_agent: Array<{ agent_id: string; total: number; runs: number }>;
  by_day: Array<{ day: string; cost: number }>;
  month_total: number;
  projected_month: number;
}

export interface AgentRunResult {
  run_id: number;
  status: string;
  agent_id: string;
  cost_usd?: number;
  tokens_in?: number;
  tokens_out?: number;
  summary?: string;
  error?: string;
}

export interface AgentScore {
  id: number;
  agent_id: string;
  week_start: string;
  week_end: string;
  score: number | null;
  prev_score: number | null;
  trend: string | null;
  notes: string | null;
  created_at: string;
}

export interface PendingPrompt {
  id: number;
  agent_id: string;
  display_name: string;
  version: string;
  body: string;
  created_at: string;
}

export interface AgentPrompt {
  id: number;
  version: string;
  body: string;
  created_by: string;
  active: number;
  created_at: string;
}

export interface AgentDetail {
  agent: Agent;
  active_prompt: { version: string; body: string; created_by: string; created_at: string } | null;
  recent_runs: AgentRun[];
}

export interface WhatIfResult {
  machine: string;
  parts_value?: number;
  baseline_max_bid?: number;
  adjusted_max_bid?: number;
  sell_discount?: number;
  shipping_used?: number;
  verdict: Verdict;
  warning: string | null;
}

export interface ScrapResult {
  count: number;
  total_cost: number;
  expected_working: number;
  expected_value: number;
  value_per_working: number;
  max_bid: number;
  verdict: Verdict;
}

export interface CompareResult {
  ranked: Array<{ name: string; price: number; shipping: number; total: number }>;
}

export interface MachineProfile {
  model: string;
  brand: string | null;
  generation: string | null;
  standard_ram: string | null;
  standard_ssd: string | null;
  standard_cpu: string | null;
  standard_wifi: string | null;
  standard_psu: string | null;
  has_cooler: number;
  estimated_total_value: number | null;
  safe_max_bid: number | null;
  notes: string | null;
  parts: { part_id: string; qty: number }[];
}

export interface Product {
  id: number;
  category_id: number;
  category_name: string;
  brand: string | null;
  model: string;
  specs: Record<string, unknown> | null;
  condition_tiers: string[] | null;
  est_low: number | null;
  est_high: number | null;
  notes: string | null;
  created_at: string;
}

export interface Intel {
  id: number;
  category: string;
  subject: string;
  signal: string;
  action: string | null;
  confidence: string | null;
  week_start: string;
  consumed: number;
  created_at: string;
}

export interface HealthAgents {
  scheduler: { running: boolean; jobs: number };
  providers: Record<string, boolean>;
  last_success: Record<string, string>;
}

export interface Health {
  status: string;
  db_ok: boolean;
  phase1_ok: boolean;
  migration_version: string | null;
  agents: HealthAgents;
}

// ── watch list + bids ────────────────────────────────────────────────────────
export interface WatchedListing {
  id: number;
  item_name: string;
  url: string | null;
  source: string | null;
  target_price: number | null;
  max_bid: number | null;
  last_price_seen: number | null;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Bid {
  id: number;
  watched_listing_id: number | null;
  item_name: string;
  url: string | null;
  bid_amount: number;
  max_bid: number | null;
  auction_end: string | null;
  status: string;
  result_price: number | null;
  created_at: string;
}

export interface BidList extends Paged<Bid> {
  win_rate: number | null;
}

// ── inventory suggestions (Tier 1 gap-fill) ──────────────────────────────────
export interface InventorySuggestion {
  id: number;
  inventory_id: number;
  suggested_price: number | null;
  suggested_platform: string | null;
  reasoning: string;
  days_held: number | null;
  applied: number;
  agent_run_id: number | null;
  created_at: string;
  // joined from inventory
  title: string;
  buy_price: number;
  status: string;
}

// ── voice logging (Tier 2) ───────────────────────────────────────────────────
export interface VoiceLogResult {
  transcript: string;
  items: InventoryItem[];
  items_created: number;
  cost_usd: number;
}

// ── notifications (Tier 3) ───────────────────────────────────────────────────
export interface NotificationPref {
  id: number;
  event_type: string;
  channel: string;
  enabled: number;
  min_headroom: number | null;
  throttle_hours: number;
}

export interface NotificationPrefs {
  items: NotificationPref[];
  channels: Record<string, boolean>;
  vapid_public_key: string;
}

export interface NotificationLogEntry {
  id: number;
  event_type: string;
  channel: string;
  title: string | null;
  body: string | null;
  success: number;
  error: string | null;
  created_at: string;
}

export interface TestResult {
  results: Record<string, boolean>;
  errors: Record<string, string>;
}

// ── inventory photos (Tier 4) ────────────────────────────────────────────────
export interface InventoryPhoto {
  id: number;
  inventory_id: number;
  filename: string;
  original_name: string | null;
  file_size: number | null;
  width: number | null;
  height: number | null;
  sort_order: number;
  is_primary: number;
  url: string;
  created_at: string;
}
