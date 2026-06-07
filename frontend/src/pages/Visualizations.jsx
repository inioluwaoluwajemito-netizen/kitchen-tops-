import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import CompareSlider from "@/components/CompareSlider";
import { toast } from "sonner";
import { Trash2, Eye, Download, Share2, MessageSquare, Globe, GlobeLock } from "lucide-react";
import QuoteDialog from "@/components/QuoteDialog";

export default function Visualizations() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(null);
  const [quoteFor, setQuoteFor] = useState(null);

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

  const share = async (it) => {
    const url = `${window.location.origin}/r/${it.id}`;
    try {
      if (navigator.share) {
        await navigator.share({ title: `Kitchen rendered in ${it.stone_name}`, url });
      } else {
        await navigator.clipboard.writeText(url);
        toast.success("Public link copied — paste it anywhere");
      }
    } catch {
      /* dismissed */
    }
  };

  const togglePublished = async (it) => {
    const next = it.published === false ? true : false;
    try {
      const { data } = await api.patch(`/visualizations/${it.id}`, { published: next });
      setItems((arr) => arr.map((i) => (i.id === it.id ? { ...i, published: data.published } : i)));
      toast.success(next ? "Showing in stone showroom" : "Hidden from stone showroom");
    } catch {
      toast.error("Update failed");
    }
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
                {it.published === false && (
                  <div className="absolute top-2 left-2 px-2 py-0.5 bg-black/80 text-[10px] uppercase tracking-widest text-zinc-300 rounded flex items-center gap-1">
                    <GlobeLock className="w-3 h-3" /> Private
                  </div>
                )}
              </div>
              <div className="p-4">
                <div className="flex items-center justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <div className="font-serif text-lg truncate">{it.stone_name}</div>
                    <div className="text-[11px] font-mono text-zinc-500">
                      {new Date(it.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <Button size="icon" variant="ghost" onClick={() => remove(it.id)} data-testid={`viz-delete-${it.id}`} className="h-8 w-8 text-red-400/80 hover:text-red-400 shrink-0">
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
                <div className="mt-3 grid grid-cols-5 gap-1">
                  <Button size="sm" variant="ghost" onClick={() => setOpen(it)} data-testid={`viz-view-${it.id}`} className="text-zinc-300 hover:text-white h-8" title="View">
                    <Eye className="w-3.5 h-3.5" />
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => download(it.result_image, it.id)} data-testid={`viz-download-${it.id}`} className="text-zinc-300 hover:text-white h-8" title="Download">
                    <Download className="w-3.5 h-3.5" />
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => share(it)} data-testid={`viz-share-${it.id}`} className="text-zinc-300 hover:text-white h-8" title="Share link">
                    <Share2 className="w-3.5 h-3.5" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => togglePublished(it)}
                    data-testid={`viz-published-${it.id}`}
                    className={`h-8 ${it.published === false ? "text-zinc-500 hover:text-white" : "text-zinc-300 hover:text-white"}`}
                    title={it.published === false ? "Show in stone showroom" : "Hide from stone showroom"}
                  >
                    {it.published === false ? <GlobeLock className="w-3.5 h-3.5" /> : <Globe className="w-3.5 h-3.5" />}
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setQuoteFor(it)} data-testid={`viz-quote-${it.id}`} className="text-gold hover:text-gold/80 h-8" title="Get a quote">
                    <MessageSquare className="w-3.5 h-3.5" />
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

      <QuoteDialog
        open={!!quoteFor}
        onOpenChange={(o) => !o && setQuoteFor(null)}
        visualizationId={quoteFor?.id}
        stoneId={quoteFor?.stone_id}
        stoneName={quoteFor?.stone_name}
      />
    </div>
  );
}
