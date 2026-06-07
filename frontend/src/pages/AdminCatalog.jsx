import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { formatApiError } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Plus, Pencil, Trash2, Eye, EyeOff, Loader2 } from "lucide-react";

const EMPTY = {
  name: "",
  type: "Marble",
  finish: "Polished",
  origin: "",
  description: "",
  image_url: "",
  swatch_color: "#A1A1A1",
  featured: false,
};

export default function AdminCatalog() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null); // null | "new" | stone object
  const [form, setForm] = useState(EMPTY);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/admin/stones");
      setItems(data.items);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail) || "Failed to load");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const openNew = () => {
    setForm(EMPTY);
    setEditing("new");
  };
  const openEdit = (s) => {
    setForm({
      name: s.name,
      type: s.type,
      finish: s.finish,
      origin: s.origin || "",
      description: s.description || "",
      image_url: s.image_url,
      swatch_color: s.swatch_color || "#A1A1A1",
      featured: !!s.featured,
    });
    setEditing(s);
  };
  const close = () => {
    setEditing(null);
    setForm(EMPTY);
  };

  const save = async () => {
    if (!form.name.trim() || !form.image_url.trim()) {
      toast.error("Name and image URL are required");
      return;
    }
    setBusy(true);
    try {
      if (editing === "new") {
        await api.post("/admin/stones", form);
        toast.success("Stone added");
      } else {
        await api.patch(`/admin/stones/${editing.id}`, form);
        toast.success("Stone updated");
      }
      close();
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail) || "Save failed");
    } finally {
      setBusy(false);
    }
  };

  const toggleActive = async (s) => {
    try {
      await api.patch(`/admin/stones/${s.id}`, { active: !s.active });
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail) || "Update failed");
    }
  };

  const remove = async (s) => {
    if (!confirm(`Delete "${s.name}" permanently? This cannot be undone.`)) return;
    try {
      await api.delete(`/admin/stones/${s.id}`);
      toast.success("Deleted");
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail) || "Delete failed");
    }
  };

  if (user?.role !== "admin") {
    return (
      <div className="max-w-2xl mx-auto px-6 py-24 text-center">
        <div className="font-serif text-3xl mb-3">Admin access only</div>
        <p className="text-zinc-400 mb-6">This area is reserved for showroom administrators.</p>
        <Link to="/dashboard">
          <Button className="bg-gold text-black hover:bg-[#B38C44]">Back to visualizer</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-10 py-12">
      <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between gap-4 mb-10">
        <div>
          <div className="text-xs uppercase tracking-[0.3em] text-zinc-500 mb-2">Admin · Catalog</div>
          <h1 className="font-serif text-4xl tracking-tight">House Stone Library</h1>
          <p className="text-sm text-zinc-400 mt-2">Manage the stones available to every customer.</p>
        </div>
        <Button onClick={openNew} className="bg-gold text-black hover:bg-[#B38C44]" data-testid="admin-add-stone-btn">
          <Plus className="w-4 h-4 mr-2" /> Add new stone
        </Button>
      </div>

      {loading ? (
        <div className="text-sm text-zinc-500 flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin" /> Loading catalog...
        </div>
      ) : items.length === 0 ? (
        <div className="panel rounded-lg p-12 text-center">
          <div className="font-serif text-2xl mb-2">No stones in catalog yet</div>
          <Button onClick={openNew} className="bg-gold text-black hover:bg-[#B38C44]">
            Add your first stone
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {items.map((s) => (
            <div
              key={s.id}
              data-testid={`admin-stone-${s.id}`}
              className={`panel rounded-lg overflow-hidden hover-lift ${s.active === false ? "opacity-50" : ""}`}
            >
              <div className="relative aspect-[4/3] bg-zinc-900">
                <img src={s.image_url} alt={s.name} className="w-full h-full object-cover" />
                {s.active === false && (
                  <div className="absolute top-2 left-2 px-2 py-0.5 bg-black/80 text-[10px] uppercase tracking-widest text-zinc-300 rounded">
                    Hidden
                  </div>
                )}
                {s.featured && (
                  <div className="absolute top-2 right-2 px-2 py-0.5 bg-gold text-black text-[10px] uppercase tracking-widest rounded">
                    Featured
                  </div>
                )}
              </div>
              <div className="p-4">
                <div className="flex items-start justify-between gap-2 mb-1">
                  <div className="min-w-0">
                    <div className="font-serif text-lg truncate">{s.name}</div>
                    <div className="text-[10px] uppercase tracking-[0.2em] text-zinc-500">
                      {s.type} · {s.finish}
                    </div>
                  </div>
                  <div
                    className="w-8 h-8 rounded-full border border-white/10 shrink-0"
                    style={{ background: s.swatch_color }}
                    title={s.swatch_color}
                  />
                </div>
                {s.origin && <div className="text-xs text-zinc-500 mt-1 font-mono">{s.origin}</div>}
                <div className="flex items-center gap-1 mt-4 pt-3 border-t border-white/5">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => openEdit(s)}
                    data-testid={`admin-edit-${s.id}`}
                    className="text-zinc-300 hover:text-white flex-1"
                  >
                    <Pencil className="w-3.5 h-3.5 mr-1.5" /> Edit
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => toggleActive(s)}
                    data-testid={`admin-toggle-${s.id}`}
                    className="text-zinc-300 hover:text-white"
                    title={s.active === false ? "Show in catalog" : "Hide from catalog"}
                  >
                    {s.active === false ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => remove(s)}
                    data-testid={`admin-delete-${s.id}`}
                    className="text-red-400/80 hover:text-red-400"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={!!editing} onOpenChange={(o) => !o && !busy && close()}>
        <DialogContent className="bg-zinc-950 border-white/10 max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-serif text-2xl">
              {editing === "new" ? "Add new stone" : `Edit "${editing?.name}"`}
            </DialogTitle>
          </DialogHeader>

          <div className="grid sm:grid-cols-2 gap-4 mt-2">
            <div>
              <Label className="text-xs uppercase tracking-[0.2em] text-zinc-500">Name *</Label>
              <Input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Calacatta Gold"
                data-testid="admin-form-name"
                className="mt-2 bg-zinc-900 border-zinc-800 focus:border-gold"
              />
            </div>
            <div>
              <Label className="text-xs uppercase tracking-[0.2em] text-zinc-500">Type *</Label>
              <Input
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value })}
                placeholder="Marble"
                data-testid="admin-form-type"
                className="mt-2 bg-zinc-900 border-zinc-800 focus:border-gold"
              />
            </div>
            <div>
              <Label className="text-xs uppercase tracking-[0.2em] text-zinc-500">Finish *</Label>
              <Input
                value={form.finish}
                onChange={(e) => setForm({ ...form, finish: e.target.value })}
                placeholder="Polished"
                data-testid="admin-form-finish"
                className="mt-2 bg-zinc-900 border-zinc-800 focus:border-gold"
              />
            </div>
            <div>
              <Label className="text-xs uppercase tracking-[0.2em] text-zinc-500">Origin</Label>
              <Input
                value={form.origin}
                onChange={(e) => setForm({ ...form, origin: e.target.value })}
                placeholder="Carrara, Italy"
                data-testid="admin-form-origin"
                className="mt-2 bg-zinc-900 border-zinc-800 focus:border-gold"
              />
            </div>
          </div>

          <div className="mt-4">
            <Label className="text-xs uppercase tracking-[0.2em] text-zinc-500">Image URL *</Label>
            <Input
              value={form.image_url}
              onChange={(e) => setForm({ ...form, image_url: e.target.value })}
              placeholder="https://images.unsplash.com/..."
              data-testid="admin-form-image-url"
              className="mt-2 bg-zinc-900 border-zinc-800 focus:border-gold"
            />
            {form.image_url && (
              <div className="mt-3 aspect-[4/2] rounded-md overflow-hidden border border-white/5 bg-zinc-900">
                <img src={form.image_url} alt="preview" className="w-full h-full object-cover" />
              </div>
            )}
          </div>

          <div className="grid sm:grid-cols-2 gap-4 mt-4">
            <div>
              <Label className="text-xs uppercase tracking-[0.2em] text-zinc-500">Swatch color (hex)</Label>
              <div className="flex gap-2 mt-2">
                <Input
                  type="color"
                  value={form.swatch_color}
                  onChange={(e) => setForm({ ...form, swatch_color: e.target.value })}
                  className="bg-zinc-900 border-zinc-800 h-10 w-16 p-1"
                  data-testid="admin-form-swatch"
                />
                <Input
                  value={form.swatch_color}
                  onChange={(e) => setForm({ ...form, swatch_color: e.target.value })}
                  className="bg-zinc-900 border-zinc-800 focus:border-gold font-mono"
                />
              </div>
            </div>
            {editing !== "new" && editing && (
              <div>
                <Label className="text-xs uppercase tracking-[0.2em] text-zinc-500">Visible in catalog</Label>
                <div className="flex items-center gap-3 mt-3 h-10">
                  <Switch
                    checked={editing.active !== false}
                    onCheckedChange={() => toggleActive(editing)}
                    data-testid="admin-form-active"
                  />
                  <span className="text-sm text-zinc-400">
                    {editing.active === false ? "Hidden from customers" : "Live"}
                  </span>
                </div>
              </div>
            )}
          </div>

          <div className="mt-4">
            <Label className="text-xs uppercase tracking-[0.2em] text-zinc-500">Featured stone</Label>
            <div className="flex items-center gap-3 mt-3">
              <Switch
                checked={!!form.featured}
                onCheckedChange={(v) => setForm({ ...form, featured: v })}
                data-testid="admin-form-featured"
              />
              <span className="text-sm text-zinc-400">
                {form.featured
                  ? "Spotlighted on landing page & top of catalog"
                  : "Standard catalog item"}
              </span>
            </div>
          </div>

          <div className="mt-4">
            <Label className="text-xs uppercase tracking-[0.2em] text-zinc-500">Description</Label>
            <Textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Brilliant white with sharp linear grey veins..."
              data-testid="admin-form-description"
              className="mt-2 bg-zinc-900 border-zinc-800 focus:border-gold min-h-[80px]"
            />
          </div>

          <div className="mt-6 flex items-center justify-end gap-3">
            <Button variant="ghost" onClick={close} disabled={busy} className="text-zinc-300">
              Cancel
            </Button>
            <Button onClick={save} disabled={busy} className="bg-gold text-black hover:bg-[#B38C44]" data-testid="admin-form-save">
              {busy ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              {editing === "new" ? "Add stone" : "Save changes"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
