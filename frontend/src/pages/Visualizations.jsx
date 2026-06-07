import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import CompareSlider from "@/components/CompareSlider";
import { toast } from "sonner";
import { Trash2, Eye, Download } from "lucide-react";

export default function Visualizations() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/visualizations");
      setItems(data.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const remove = async (id) => {
    if (!confirm("Delete this render?")) return;
    await api.delete(`/visualizations/${id}`);
    setItems((arr) => arr.filter((i) => i.id !== id));
    toast.success("Deleted");
  };

  const download = (url, id) => {
    const a = document.createElement("a");
    a.href = url;
    a.download = `rated-worktops-${id}.png`;
    a.click();
  };

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-10 py-12">
      <div className="flex items-end justify-between mb-10">
        <div>
          <div className="text-xs uppercase tracking-[0.3em] text-zinc-500 mb-2">Your Renders</div>
          <h1 className="font-serif text-4xl tracking-tight">My Visualizations</h1>
        </div>
        <Link to="/dashboard">
          <Button className="bg-gold text-black hover:bg-[#B38C44]" data-testid="new-render-btn">
            New render
          </Button>
        </Link>
      </div>

      {loading ? (
        <div className="text-sm text-zinc-500">Loading...</div>
      ) : items.length === 0 ? (
        <div className="panel rounded-lg p-12 text-center">
          <div className="font-serif text-2xl text-white mb-2">No renders yet</div>
          <div className="text-sm text-zinc-400 mb-6">Create your first kitchen visualization to see it here.</div>
          <Link to="/dashboard">
            <Button className="bg-gold text-black hover:bg-[#B38C44]">Start a render</Button>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {items.map((it) => (
            <div key={it.id} data-testid={`viz-card-${it.id}`} className="panel rounded-lg overflow-hidden group hover-lift">
              <div className="relative aspect-[4/3] bg-black">
                <img src={it.result_image} alt={it.stone_name} className="w-full h-full object-cover" />
                <div className="absolute top-2 right-2 px-2 py-0.5 bg-black/70 text-[10px] uppercase tracking-widest text-zinc-200 rounded">
                  {it.mode}
                </div>
              </div>
              <div className="p-4 flex items-center justify-between">
                <div className="min-w-0">
                  <div className="font-serif text-lg truncate">{it.stone_name}</div>
                  <div className="text-[11px] font-mono text-zinc-500">
                    {new Date(it.created_at).toLocaleDateString()}
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <Button size="icon" variant="ghost" onClick={() => setOpen(it)} data-testid={`viz-view-${it.id}`} className="h-8 w-8 text-zinc-300">
                    <Eye className="w-4 h-4" />
                  </Button>
                  <Button size="icon" variant="ghost" onClick={() => download(it.result_image, it.id)} className="h-8 w-8 text-zinc-300">
                    <Download className="w-4 h-4" />
                  </Button>
                  <Button size="icon" variant="ghost" onClick={() => remove(it.id)} data-testid={`viz-delete-${it.id}`} className="h-8 w-8 text-red-400/80 hover:text-red-400">
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={!!open} onOpenChange={(o) => !o && setOpen(null)}>
        <DialogContent className="bg-zinc-950 border-white/10 max-w-4xl">
          {open && (
            <div>
              <div className="font-serif text-2xl mb-1">{open.stone_name}</div>
              <div className="text-xs text-zinc-500 font-mono mb-4">
                {new Date(open.created_at).toLocaleString()} · {open.mode} mode
              </div>
              <CompareSlider before={open.kitchen_image} after={open.result_image} />
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
