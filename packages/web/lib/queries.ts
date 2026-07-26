"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./api";
import type {
  Agent,
  AgentCosts,
  AgentDetail,
  AgentPrompt,
  AgentRun,
  AgentRunResult,
  AgentScore,
  Bid,
  BidList,
  BidResult,
  CompareResult,
  Intel,
  Category,
  Dashboard,
  FlaggedDeal,
  Health,
  InventoryItem,
  InventorySuggestion,
  ItadCompany,
  ItadDetail,
  Lead,
  MachineProfile,
  Paged,
  InventoryPhoto,
  NotificationLogEntry,
  NotificationPrefs,
  Part,
  PendingPrompt,
  PnlSummary,
  TestResult,
  VoiceLogResult,
  Product,
  RefreshResult,
  ScanResult,
  ScrapResult,
  Source,
  SourcePerf,
  Staleness,
  WhatIfResult,
  Watch,
  WatchedListing,
} from "./types";

// ── bid ──────────────────────────────────────────────────────────────────────
interface BidInput {
  machine: string;
  price: number;
  shipping: number;
}

export function useBid() {
  return useMutation<BidResult, Error, BidInput>({
    mutationFn: (input) => api.post<BidResult>("/bid", input),
  });
}

export function useWhatIf() {
  return useMutation<WhatIfResult, Error, { machine: string; buy_price: number; sell_discount?: number; shipping_override?: number }>({
    mutationFn: (input) => api.post<WhatIfResult>("/what-if", input),
  });
}

export function useScrap() {
  return useMutation<ScrapResult, Error, { count: number; price: number; shipping?: number; expected_working_pct?: number; value_per_working?: number }>({
    mutationFn: (input) => api.post<ScrapResult>("/scrap", input),
  });
}

export function useCompare() {
  return useMutation<CompareResult, Error, { lots: Array<{ name: string; price: number; shipping?: number }> }>({
    mutationFn: (input) => api.post<CompareResult>("/compare", input),
  });
}

export function useRecordPrice() {
  const qc = useQueryClient();
  return useMutation<Part, Error, { partId: string; price: number; source?: string; condition?: string }>({
    mutationFn: ({ partId, ...data }) => api.post<Part>(`/parts/${partId}/prices`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["parts"] });
      qc.invalidateQueries({ queryKey: ["staleness"] });
    },
  });
}

export function useMachines(search: string) {
  return useQuery<Paged<string>>({
    queryKey: ["machines", search],
    queryFn: () => api.get<Paged<string>>(`/machines?search=${encodeURIComponent(search)}`),
    enabled: search.length >= 2,
    staleTime: 5 * 60_000,
  });
}

export function useAllMachines() {
  return useQuery<Paged<string>>({
    queryKey: ["machines", "all"],
    queryFn: () => api.get<Paged<string>>("/machines"),
    staleTime: 5 * 60_000,
  });
}

export function useMachineProfile(model: string) {
  return useQuery<MachineProfile>({
    queryKey: ["machine", model],
    queryFn: () => api.get<MachineProfile>(`/machines/${encodeURIComponent(model)}`),
    enabled: !!model,
  });
}

function invalidateMachines(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ["machines"] });
  qc.invalidateQueries({ queryKey: ["machine"] });
}

export function useCreateMachine() {
  const qc = useQueryClient();
  return useMutation<MachineProfile, Error, Record<string, unknown>>({
    mutationFn: (data) => api.post<MachineProfile>("/machines", data),
    onSuccess: () => invalidateMachines(qc),
  });
}

export function useUpdateMachine() {
  const qc = useQueryClient();
  return useMutation<MachineProfile, Error, { model: string; data: Record<string, unknown> }>({
    mutationFn: ({ model, data }) => api.put<MachineProfile>(`/machines/${encodeURIComponent(model)}`, data),
    onSuccess: () => invalidateMachines(qc),
  });
}

export function useDeleteMachine() {
  const qc = useQueryClient();
  return useMutation<unknown, Error, string>({
    mutationFn: (model) => api.del(`/machines/${encodeURIComponent(model)}`),
    onSuccess: () => invalidateMachines(qc),
  });
}

// ── inventory ────────────────────────────────────────────────────────────────
export function useInventory(status?: string) {
  const qs = status ? `?status=${status}` : "";
  return useQuery<Paged<InventoryItem>>({
    queryKey: ["inventory", status ?? "all"],
    queryFn: () => api.get<Paged<InventoryItem>>(`/inventory${qs}`),
  });
}

export function usePnl(period = "month") {
  return useQuery<PnlSummary>({
    queryKey: ["pnl", period],
    queryFn: () => api.get<PnlSummary>(`/inventory/pnl?period=${period}`),
  });
}

export function useInventoryItem(id: number) {
  return useQuery<InventoryItem>({
    queryKey: ["inventory", "item", id],
    queryFn: () => api.get<InventoryItem>(`/inventory/${id}`),
    enabled: id > 0,
  });
}

function invalidateInventory(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ["inventory"] });
  qc.invalidateQueries({ queryKey: ["pnl"] });
  qc.invalidateQueries({ queryKey: ["dashboard"] });
  qc.invalidateQueries({ queryKey: ["sources", "performance"] });
}

export function useLogPurchase() {
  const qc = useQueryClient();
  return useMutation<InventoryItem, Error, Record<string, unknown>>({
    mutationFn: (data) => api.post<InventoryItem>("/inventory", data),
    onSuccess: () => invalidateInventory(qc),
  });
}

export function useUpdateInventory(id: number) {
  const qc = useQueryClient();
  return useMutation<InventoryItem, Error, Record<string, unknown>>({
    mutationFn: (data) => api.patch<InventoryItem>(`/inventory/${id}`, data),
    onSuccess: () => invalidateInventory(qc),
  });
}

// ── inventory suggestions (Tier 1 gap-fill) ───────────────────────────────────
export function useInventorySuggestions() {
  return useQuery<Paged<InventorySuggestion>>({
    queryKey: ["inventory", "suggestions"],
    queryFn: () => api.get<Paged<InventorySuggestion>>("/inventory/suggestions"),
  });
}

export function useApplySuggestion() {
  const qc = useQueryClient();
  return useMutation<{ applied: number }, Error, number>({
    mutationFn: (id) => api.patch<{ applied: number }>(`/inventory/suggestions/${id}`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["inventory"] }),
  });
}

// ── voice logging (Tier 2) ────────────────────────────────────────────────────
export function useVoiceLog() {
  const qc = useQueryClient();
  return useMutation<VoiceLogResult, Error, string>({
    mutationFn: (transcript) => api.post<VoiceLogResult>("/voice/log", { transcript }),
    onSuccess: () => invalidateInventory(qc),
  });
}

// ── notifications (Tier 3) ────────────────────────────────────────────────────
export function useNotificationPrefs() {
  return useQuery<NotificationPrefs>({
    queryKey: ["notif", "prefs"],
    queryFn: () => api.get<NotificationPrefs>("/notifications/prefs"),
  });
}

export function useUpdateNotificationPref() {
  const qc = useQueryClient();
  return useMutation<
    NotificationPrefs,
    Error,
    { event_type: string; channel: string; enabled?: boolean; min_headroom?: number; throttle_hours?: number }
  >({
    mutationFn: (data) => api.patch<NotificationPrefs>("/notifications/prefs", data),
    onSuccess: (data) => qc.setQueryData(["notif", "prefs"], data),
  });
}

export function useNotificationLog() {
  return useQuery<Paged<NotificationLogEntry>>({
    queryKey: ["notif", "log"],
    queryFn: () => api.get<Paged<NotificationLogEntry>>("/notifications/log"),
  });
}

export function useSendTestNotification() {
  return useMutation<TestResult, Error, string[]>({
    mutationFn: (channels) => api.post<TestResult>("/notifications/test", { channels }),
  });
}

// ── inventory photos (Tier 4) ─────────────────────────────────────────────────
async function uploadPhotoFiles(itemId: number, files: File[]): Promise<Paged<InventoryPhoto>> {
  const fd = new FormData();
  files.forEach((f) => fd.append("files", f));
  // Raw fetch (not the JSON api wrapper) so the browser sets the multipart boundary.
  const res = await fetch(`/api/inventory/${itemId}/photos`, { method: "POST", body: fd });
  const text = await res.text();
  const body = text ? JSON.parse(text) : null;
  if (!res.ok) throw new Error(body?.error?.message || "Upload failed");
  return body as Paged<InventoryPhoto>;
}

export function useInventoryPhotos(itemId: number) {
  return useQuery<Paged<InventoryPhoto>>({
    queryKey: ["photos", itemId],
    queryFn: () => api.get<Paged<InventoryPhoto>>(`/inventory/${itemId}/photos`),
    enabled: itemId > 0,
  });
}

function invalidatePhotos(qc: ReturnType<typeof useQueryClient>, itemId: number) {
  qc.invalidateQueries({ queryKey: ["photos", itemId] });
  qc.invalidateQueries({ queryKey: ["inventory"] });
}

export function useUploadPhotos(itemId: number) {
  const qc = useQueryClient();
  return useMutation<Paged<InventoryPhoto>, Error, File[]>({
    mutationFn: (files) => uploadPhotoFiles(itemId, files),
    onSuccess: () => invalidatePhotos(qc, itemId),
  });
}

export function useDeletePhoto(itemId: number) {
  const qc = useQueryClient();
  return useMutation<{ deleted: number }, Error, number>({
    mutationFn: (photoId) => api.del<{ deleted: number }>(`/inventory/${itemId}/photos/${photoId}`),
    onSuccess: () => invalidatePhotos(qc, itemId),
  });
}

export function useSetPrimaryPhoto(itemId: number) {
  const qc = useQueryClient();
  return useMutation<Paged<InventoryPhoto>, Error, number>({
    mutationFn: (photoId) =>
      api.patch<Paged<InventoryPhoto>>(`/inventory/${itemId}/photos/${photoId}/primary`, {}),
    onSuccess: () => invalidatePhotos(qc, itemId),
  });
}

// ── sources / leads ──────────────────────────────────────────────────────────
export function useSources() {
  return useQuery<Paged<Source>>({
    queryKey: ["sources"],
    queryFn: () => api.get<Paged<Source>>("/sources"),
    staleTime: 60_000,
  });
}

export function useSourcePerformance() {
  return useQuery<Paged<SourcePerf>>({
    queryKey: ["sources", "performance"],
    queryFn: () => api.get<Paged<SourcePerf>>("/sources/performance"),
  });
}

export function useCreateSource() {
  const qc = useQueryClient();
  return useMutation<Source, Error, { name: string; type: string }>({
    mutationFn: (data) => api.post<Source>("/sources", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
  });
}

export function useLeads(kind?: string) {
  const qs = kind ? `?kind=${kind}` : "";
  return useQuery<Paged<Lead>>({
    queryKey: ["leads", kind ?? "all"],
    queryFn: () => api.get<Paged<Lead>>(`/leads${qs}`),
  });
}

export function useCreateLead() {
  const qc = useQueryClient();
  return useMutation<Lead, Error, Record<string, unknown>>({
    mutationFn: (data) => api.post<Lead>("/leads", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["leads"] }),
  });
}

// ── catalog ──────────────────────────────────────────────────────────────────
export function useParts(search: string, category: string) {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (category) params.set("category", category);
  return useQuery<Paged<Part>>({
    queryKey: ["parts", search, category],
    queryFn: () => api.get<Paged<Part>>(`/parts?${params.toString()}`),
    staleTime: 60_000,
  });
}

export function useCategories() {
  return useQuery<Paged<Category>>({
    queryKey: ["categories"],
    queryFn: () => api.get<Paged<Category>>("/categories"),
    staleTime: 5 * 60_000,
  });
}

// ── products (expanded resale catalog) ───────────────────────────────────────
export function useProducts(search: string, category: string) {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (category) params.set("category", category);
  return useQuery<Paged<Product>>({
    queryKey: ["products", search, category],
    queryFn: () => api.get<Paged<Product>>(`/products?${params.toString()}`),
  });
}

function invalidateProducts(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ["products"] });
}

export function useCreateProduct() {
  const qc = useQueryClient();
  return useMutation<Product, Error, Record<string, unknown>>({
    mutationFn: (data) => api.post<Product>("/products", data),
    onSuccess: () => invalidateProducts(qc),
  });
}

export function useUpdateProduct() {
  const qc = useQueryClient();
  return useMutation<Product, Error, { id: number; data: Record<string, unknown> }>({
    mutationFn: ({ id, data }) => api.put<Product>(`/products/${id}`, data),
    onSuccess: () => invalidateProducts(qc),
  });
}

export function useDeleteProduct() {
  const qc = useQueryClient();
  return useMutation<unknown, Error, number>({
    mutationFn: (id) => api.del(`/products/${id}`),
    onSuccess: () => invalidateProducts(qc),
  });
}

export function useStaleness() {
  return useQuery<Staleness>({
    queryKey: ["staleness"],
    queryFn: () => api.get<Staleness>("/parts/staleness"),
    staleTime: 60_000,
  });
}

export function useRefreshComps() {
  const qc = useQueryClient();
  return useMutation<RefreshResult, Error, { all?: boolean; part?: string; source?: string }>({
    mutationFn: (data) => api.post<RefreshResult>("/parts/refresh-comps", { source: "rapidapi", ...data }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["parts"] });
      qc.invalidateQueries({ queryKey: ["staleness"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

// ── scanner ──────────────────────────────────────────────────────────────────
export function useWatches() {
  return useQuery<Paged<Watch>>({
    queryKey: ["watches"],
    queryFn: () => api.get<Paged<Watch>>("/scan/govdeals/watches"),
    staleTime: 5 * 60_000,
  });
}

export function useDeals() {
  return useQuery<Paged<FlaggedDeal>>({
    queryKey: ["deals"],
    queryFn: () => api.get<Paged<FlaggedDeal>>("/deals?open=true"),
  });
}

export function useRunScan() {
  const qc = useQueryClient();
  return useMutation<ScanResult, Error, { watch?: string; dry_run?: boolean; active_only?: boolean }>({
    mutationFn: (data) => api.post<ScanResult>("/scan/govdeals", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["deals"] }),
  });
}

export function useDismissDeal() {
  const qc = useQueryClient();
  return useMutation<unknown, Error, number>({
    mutationFn: (id) => api.patch(`/deals/${id}`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["deals"] }),
  });
}

// ── ITAD CRM ─────────────────────────────────────────────────────────────────
export function useSuppliers(search: string, city: string, status: string) {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (city) params.set("city", city);
  if (status) params.set("status", status);
  return useQuery<Paged<ItadCompany>>({
    queryKey: ["suppliers", search, city, status],
    queryFn: () => api.get<Paged<ItadCompany>>(`/itad/companies?${params.toString()}`),
  });
}

export interface Bounds {
  minLat: number;
  minLng: number;
  maxLat: number;
  maxLng: number;
}

/** Suppliers within a map viewport (bounding box). Rows without coordinates are
 *  excluded server-side. `enabled` lets the caller hold off until the map is ready. */
export function useSuppliersInBounds(bounds: Bounds | null, enabled = true) {
  const params = new URLSearchParams();
  if (bounds) {
    params.set("min_lat", String(bounds.minLat));
    params.set("min_lng", String(bounds.minLng));
    params.set("max_lat", String(bounds.maxLat));
    params.set("max_lng", String(bounds.maxLng));
  }
  return useQuery<Paged<ItadCompany>>({
    queryKey: ["suppliers-bbox", bounds],
    queryFn: () => api.get<Paged<ItadCompany>>(`/itad/companies?${params.toString()}`),
    enabled: enabled && bounds !== null,
  });
}

export function useGeocodeMissing() {
  const qc = useQueryClient();
  return useMutation<{ checked: number; geocoded: number }, Error, void>({
    mutationFn: () => api.post("/itad/companies/geocode-missing", {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["suppliers-bbox"] }),
  });
}

export function useSupplier(id: number) {
  return useQuery<ItadDetail>({
    queryKey: ["supplier", id],
    queryFn: () => api.get<ItadDetail>(`/itad/companies/${id}`),
    enabled: id > 0,
  });
}

function invalidateSuppliers(qc: ReturnType<typeof useQueryClient>, id?: number) {
  qc.invalidateQueries({ queryKey: ["suppliers"] });
  if (id) qc.invalidateQueries({ queryKey: ["supplier", id] });
}

export function useCreateSupplier() {
  const qc = useQueryClient();
  return useMutation<ItadDetail, Error, Record<string, unknown>>({
    mutationFn: (data) => api.post<ItadDetail>("/itad/companies", data),
    onSuccess: () => invalidateSuppliers(qc),
  });
}

export function useUpdateSupplier(id: number) {
  const qc = useQueryClient();
  return useMutation<ItadDetail, Error, Record<string, unknown>>({
    mutationFn: (data) => api.patch<ItadDetail>(`/itad/companies/${id}`, data),
    onSuccess: () => invalidateSuppliers(qc, id),
  });
}

export function useLogCall(id: number) {
  const qc = useQueryClient();
  return useMutation<ItadDetail, Error, Record<string, unknown>>({
    mutationFn: (data) => api.post<ItadDetail>(`/itad/companies/${id}/calls`, data),
    onSuccess: () => invalidateSuppliers(qc, id),
  });
}

export function useLogItadPurchase(id: number) {
  const qc = useQueryClient();
  return useMutation<ItadDetail, Error, Record<string, unknown>>({
    mutationFn: (data) => api.post<ItadDetail>(`/itad/companies/${id}/purchases`, data),
    onSuccess: () => invalidateSuppliers(qc, id),
  });
}

// ── agents ───────────────────────────────────────────────────────────────────
export function useAgents() {
  return useQuery<Paged<Agent>>({
    queryKey: ["agents"],
    queryFn: () => api.get<Paged<Agent>>("/agents"),
    refetchInterval: 30_000,
  });
}

export function useAgentCosts() {
  return useQuery<AgentCosts>({
    queryKey: ["agents", "costs"],
    queryFn: () => api.get<AgentCosts>("/agents/costs"),
  });
}

export function useHealth() {
  return useQuery<Health>({
    queryKey: ["health"],
    queryFn: () => api.get<Health>("/health"),
    refetchInterval: 30_000,
  });
}

export function useRunAgent() {
  const qc = useQueryClient();
  return useMutation<AgentRunResult, Error, { id: string; params?: Record<string, unknown> }>({
    mutationFn: ({ id, params }) =>
      api.post<AgentRunResult>(`/agents/${id}/run`, params ? { params } : {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["agents"] }); // also covers ["agents","costs"]
      qc.invalidateQueries({ queryKey: ["agent"] });
      qc.invalidateQueries({ queryKey: ["agent-runs"] });
      qc.invalidateQueries({ queryKey: ["health"] });
      qc.invalidateQueries({ queryKey: ["agent-scores"] });
      qc.invalidateQueries({ queryKey: ["pending-prompts"] });
      qc.invalidateQueries({ queryKey: ["intel"] });
    },
  });
}

export function useUpdateAgent() {
  const qc = useQueryClient();
  return useMutation<unknown, Error, { id: string; data: Record<string, unknown> }>({
    mutationFn: ({ id, data }) => api.patch(`/agents/${id}`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["agents"] }),
  });
}

export function useAgentScores() {
  return useQuery<Paged<AgentScore>>({
    queryKey: ["agent-scores"],
    queryFn: () => api.get<Paged<AgentScore>>("/agents/scores"),
  });
}

export function useAgentDetail(id: string) {
  return useQuery<AgentDetail>({
    queryKey: ["agent", id],
    queryFn: () => api.get<AgentDetail>(`/agents/${id}`),
    enabled: !!id,
  });
}

export function useAgentRuns(agentId?: string) {
  const qs = agentId ? `?agent_id=${agentId}` : "";
  return useQuery<Paged<AgentRun>>({
    queryKey: ["agent-runs", agentId ?? "all"],
    queryFn: () => api.get<Paged<AgentRun>>(`/agents/runs${qs}`),
  });
}

export function useAgentPrompts(id: string) {
  return useQuery<Paged<AgentPrompt>>({
    queryKey: ["agent-prompts", id],
    queryFn: () => api.get<Paged<AgentPrompt>>(`/agents/${id}/prompts`),
    enabled: !!id,
  });
}

export function useIntel() {
  return useQuery<Paged<Intel>>({
    queryKey: ["intel"],
    queryFn: () => api.get<Paged<Intel>>("/intel"),
  });
}

export function usePendingPrompts() {
  return useQuery<Paged<PendingPrompt>>({
    queryKey: ["pending-prompts"],
    queryFn: () => api.get<Paged<PendingPrompt>>("/agents/prompts/pending"),
  });
}

export function useActivatePrompt() {
  const qc = useQueryClient();
  return useMutation<{ activated: number; agent_id: string }, Error, number>({
    mutationFn: (id) => api.post(`/agents/prompts/${id}/activate`, {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pending-prompts"] });
      qc.invalidateQueries({ queryKey: ["agent-prompts"] });
      qc.invalidateQueries({ queryKey: ["agent"] });
    },
  });
}

// ── watch list + bids ────────────────────────────────────────────────────────
export function useWatchlist(status?: string) {
  const qs = status ? `?status=${status}` : "";
  return useQuery<Paged<WatchedListing>>({
    queryKey: ["watchlist", status ?? "all"],
    queryFn: () => api.get<Paged<WatchedListing>>(`/watchlist${qs}`),
  });
}

export function useCreateWatch() {
  const qc = useQueryClient();
  return useMutation<WatchedListing, Error, Record<string, unknown>>({
    mutationFn: (data) => api.post<WatchedListing>("/watchlist", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["watchlist"] }),
  });
}

export function useUpdateWatch() {
  const qc = useQueryClient();
  return useMutation<WatchedListing, Error, { id: number; data: Record<string, unknown> }>({
    mutationFn: ({ id, data }) => api.patch<WatchedListing>(`/watchlist/${id}`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["watchlist"] }),
  });
}

export function useDeleteWatch() {
  const qc = useQueryClient();
  return useMutation<unknown, Error, number>({
    mutationFn: (id) => api.del(`/watchlist/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["watchlist"] }),
  });
}

export function useBids(status?: string) {
  const qs = status ? `?status=${status}` : "";
  return useQuery<BidList>({
    queryKey: ["bids", status ?? "all"],
    queryFn: () => api.get<BidList>(`/bids${qs}`),
  });
}

export function useCreateBid() {
  const qc = useQueryClient();
  return useMutation<Bid, Error, Record<string, unknown>>({
    mutationFn: (data) => api.post<Bid>("/bids", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["bids"] }),
  });
}

export function useUpdateBid() {
  const qc = useQueryClient();
  return useMutation<Bid, Error, { id: number; data: Record<string, unknown> }>({
    mutationFn: ({ id, data }) => api.patch<Bid>(`/bids/${id}`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["bids"] }),
  });
}

// ── edit / delete gaps ───────────────────────────────────────────────────────
export function useDeleteInventory() {
  const qc = useQueryClient();
  return useMutation<unknown, Error, number>({
    mutationFn: (id) => api.del(`/inventory/${id}`),
    onSuccess: () => invalidateInventory(qc),
  });
}

export function useUpdateLead() {
  const qc = useQueryClient();
  return useMutation<Lead, Error, { id: number; data: Record<string, unknown> }>({
    mutationFn: ({ id, data }) => api.put<Lead>(`/leads/${id}`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["leads"] }),
  });
}

export function useDeleteLead() {
  const qc = useQueryClient();
  return useMutation<unknown, Error, number>({
    mutationFn: (id) => api.del(`/leads/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["leads"] }),
  });
}

export function useUpdateSource() {
  const qc = useQueryClient();
  return useMutation<Source, Error, { id: number; data: Record<string, unknown> }>({
    mutationFn: ({ id, data }) => api.put<Source>(`/sources/${id}`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
  });
}

export function useDeleteSource() {
  const qc = useQueryClient();
  return useMutation<unknown, Error, number>({
    mutationFn: (id) => api.del(`/sources/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
  });
}

export function useCreateCategory() {
  const qc = useQueryClient();
  return useMutation<Category, Error, { name: string; icon?: string }>({
    mutationFn: (data) => api.post<Category>("/categories", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["categories"] }),
  });
}

export function useDeleteCategory() {
  const qc = useQueryClient();
  return useMutation<unknown, Error, number>({
    mutationFn: (id) => api.del(`/categories/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["categories"] }),
  });
}

export function useDeleteSupplier() {
  const qc = useQueryClient();
  return useMutation<unknown, Error, number>({
    mutationFn: (id) => api.del(`/itad/companies/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["suppliers"] }),
  });
}

export function useDeleteCall() {
  const qc = useQueryClient();
  return useMutation<unknown, Error, { companyId: number; callId: number }>({
    mutationFn: ({ callId }) => api.del(`/itad/calls/${callId}`),
    onSuccess: (_d, { companyId }) => invalidateSuppliers(qc, companyId),
  });
}

export function useDeletePurchase() {
  const qc = useQueryClient();
  return useMutation<unknown, Error, { companyId: number; purchaseId: number }>({
    mutationFn: ({ purchaseId }) => api.del(`/itad/purchases/${purchaseId}`),
    onSuccess: (_d, { companyId }) => invalidateSuppliers(qc, companyId),
  });
}

// ── dashboard ────────────────────────────────────────────────────────────────
export function useDashboard(period = "month") {
  return useQuery<Dashboard>({
    queryKey: ["dashboard", period],
    queryFn: () => api.get<Dashboard>(`/dashboard?period=${period}`),
  });
}
