"use client";

import { useState } from "react";

import { ErrorState, LoadingSkeleton } from "@/components/common/states";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { Eyebrow, PageHeader } from "@/components/ui/primitives";
import { money } from "@/lib/format";
import {
  useCategories,
  useCreateCategory,
  useCreateProduct,
  useDeleteCategory,
  useDeleteProduct,
  useProducts,
  useUpdateProduct,
} from "@/lib/queries";
import type { Product } from "@/lib/types";

export default function ProductsPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const categories = useCategories();
  const products = useProducts(search, category);
  const create = useCreateProduct();
  const [form, setForm] = useState({ category_id: "", brand: "", model: "", est_low: "", est_high: "" });

  const submit = () => {
    if (!form.model.trim() || !form.category_id) return;
    create.mutate(
      {
        category_id: Number(form.category_id),
        model: form.model.trim(),
        brand: form.brand.trim() || undefined,
        est_low: form.est_low ? Number(form.est_low) : undefined,
        est_high: form.est_high ? Number(form.est_high) : undefined,
      },
      { onSuccess: () => setForm({ category_id: "", brand: "", model: "", est_low: "", est_high: "" }) },
    );
  };

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <PageHeader
        title="Products"
        subtitle="Expanded resale catalog — phones, monitors, laptops, peripherals — with estimated ranges."
      />

      <div className="flex gap-2">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search brand / model"
          className="glass-field w-full text-sm"
        />
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="glass-field text-sm"
        >
          <option value="">All</option>
          {categories.data?.items.map((c) => (
            <option key={c.id} value={c.name}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      {/* Add product */}
      <GlassPanel className="p-5">
        <Eyebrow className="mb-3">Add a product</Eyebrow>
        <div className="flex gap-2">
          <select
            value={form.category_id}
            onChange={(e) => setForm({ ...form, category_id: e.target.value })}
            className="glass-field text-sm"
          >
            <option value="">Category…</option>
            {categories.data?.items.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <input
            value={form.brand}
            onChange={(e) => setForm({ ...form, brand: e.target.value })}
            placeholder="Brand"
            className="glass-field w-full text-sm"
          />
        </div>
        <input
          value={form.model}
          onChange={(e) => setForm({ ...form, model: e.target.value })}
          placeholder="Model (required)"
          className="glass-field mt-2 w-full text-sm"
        />
        <div className="mt-2 flex gap-2">
          <input
            value={form.est_low}
            onChange={(e) => setForm({ ...form, est_low: e.target.value })}
            inputMode="decimal"
            placeholder="Est. low $"
            className="glass-field mono w-full text-sm"
          />
          <input
            value={form.est_high}
            onChange={(e) => setForm({ ...form, est_high: e.target.value })}
            inputMode="decimal"
            placeholder="Est. high $"
            className="glass-field mono w-full text-sm"
          />
        </div>
        <button
          onClick={submit}
          disabled={create.isPending || !form.model.trim() || !form.category_id}
          className="btn-accent mt-2 w-full disabled:opacity-50"
        >
          {create.isPending ? "Adding…" : "Add product"}
        </button>
      </GlassPanel>

      {products.isLoading && <LoadingSkeleton rows={4} />}
      {products.isError && <ErrorState message={products.error.message} />}
      {products.data && products.data.items.length === 0 && (
        <p className="text-sm text-ink/40">No products yet.</p>
      )}
      <div className="space-y-3">
        {products.data?.items.map((p) => (
          <ProductRow key={p.id} product={p} />
        ))}
      </div>

      <CategoryManager />
    </div>
  );
}

function CategoryManager() {
  const categories = useCategories();
  const create = useCreateCategory();
  const del = useDeleteCategory();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");

  return (
    <div>
      <button onClick={() => setOpen((v) => !v)} className="!min-h-0">
        <Eyebrow>Manage categories {open ? "▾" : "▸"}</Eyebrow>
      </button>
      {open && (
        <GlassPanel className="mt-2 p-4">
          <div className="flex gap-2">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="New category name"
              className="glass-field w-full text-sm"
            />
            <button
              onClick={() =>
                name.trim() && create.mutate({ name: name.trim() }, { onSuccess: () => setName("") })
              }
              disabled={create.isPending || !name.trim()}
              className="btn-accent shrink-0 disabled:opacity-50"
            >
              Add
            </button>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {categories.data?.items.map((c) => (
              <span
                key={c.id}
                className="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs"
              >
                {c.name}
                <button
                  onClick={() => {
                    if (confirm(`Delete category "${c.name}"?`)) del.mutate(c.id);
                  }}
                  className="!min-h-0 text-ink/40 hover:text-loss"
                  aria-label={`delete ${c.name}`}
                >
                  ✕
                </button>
              </span>
            ))}
          </div>
        </GlassPanel>
      )}
    </div>
  );
}

function ProductRow({ product }: { product: Product }) {
  const del = useDeleteProduct();
  const update = useUpdateProduct();
  const [editing, setEditing] = useState(false);
  const [low, setLow] = useState(product.est_low?.toString() ?? "");
  const [high, setHigh] = useState(product.est_high?.toString() ?? "");

  const save = () => {
    // PUT is a full replace — send the product back with the edited estimates.
    update.mutate(
      {
        id: product.id,
        data: {
          category_id: product.category_id,
          brand: product.brand ?? undefined,
          model: product.model,
          specs: product.specs ?? undefined,
          condition_tiers: product.condition_tiers ?? undefined,
          est_low: low ? Number(low) : undefined,
          est_high: high ? Number(high) : undefined,
          notes: product.notes ?? undefined,
        },
      },
      { onSuccess: () => setEditing(false) },
    );
  };

  return (
    <GlassPanel className="p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate font-medium">
            {product.brand ? `${product.brand} ` : ""}
            {product.model}
          </div>
          <div className="mt-0.5 text-xs text-ink/50">
            {product.category_name}
            {(product.est_low != null || product.est_high != null) &&
              ` · ${money(product.est_low)}–${money(product.est_high)}`}
          </div>
        </div>
        <div className="flex shrink-0 gap-3 text-xs">
          <button onClick={() => setEditing((v) => !v)} className="!min-h-0 text-ink/40 hover:text-accent">
            {editing ? "Cancel" : "Edit"}
          </button>
          <button onClick={() => del.mutate(product.id)} className="!min-h-0 text-ink/40 hover:text-loss">
            Remove
          </button>
        </div>
      </div>
      {editing && (
        <div className="mt-2.5 flex items-center gap-2 text-xs">
          <span className="text-ink/40">Est. $</span>
          <input
            value={low}
            onChange={(e) => setLow(e.target.value)}
            inputMode="decimal"
            aria-label="estimate low"
            className="glass-field mono !min-h-0 w-16 !py-1.5"
          />
          <span className="text-ink/40">–</span>
          <input
            value={high}
            onChange={(e) => setHigh(e.target.value)}
            inputMode="decimal"
            aria-label="estimate high"
            className="glass-field mono !min-h-0 w-16 !py-1.5"
          />
          <button
            onClick={save}
            disabled={update.isPending}
            className="btn-accent !min-h-0 !py-1.5 !text-xs disabled:opacity-50"
          >
            Save
          </button>
        </div>
      )}
    </GlassPanel>
  );
}
