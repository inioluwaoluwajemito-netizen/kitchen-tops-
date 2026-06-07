import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";
import { API } from "@/lib/api";
import { Button } from "@/components/ui/button";
import QuoteDialog from "@/components/QuoteDialog";
import { ArrowRight, Loader2, MessageSquare, MapPin, Sparkles } from "lucide-react";

export default function StonePublic() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [openQuote, setOpenQuote] = useState(false);

  useEffect(() => {
    axios
      .get(`${API}/public/stones/${id}`)
      .then(({ data }) => setData(data))
      .catch(() => setData(false))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (data?.stone?.name) {
      document.title = `${data.stone.name} — Rated Worktops`;
    }
    return () => {
      document.title = "Rated Worktops";
    };
  }, [data]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-zinc-400">
        <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading stone…
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center flex-col gap-4 px-6 text-center">
        <div className="font-serif text-3xl">Stone not found</div>
        <p className="text-zinc-400 text-sm max-w-md">This stone isn't available right now.</p>
        <Link to="/">
          <Button className="bg-gold text-black hover:bg-[#B38C44]">Back to Rated Worktops</Button>
        </Link>
      </div>
    );
  }

  const { stone, renders } = data;

  return (
    <div className="min-h-screen relative">
      <header className="border-b border-white/10 glass sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-6 lg:px-10 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3" data-testid="public-brand-link">
            <div className="w-8 h-8 rounded-sm bg-gold flex items-center justify-center">
              <span className="font-serif text-black leading-none">R</span>
            </div>
            <div className="font-serif text-lg">Rated Worktops</div>
          </Link>
          <Link to="/register">
            <Button size="sm" className="bg-gold text-black hover:bg-[#B38C44]" data-testid="stone-try-cta">
              Try in your kitchen <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Button>
          </Link>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 lg:px-10 py-12">
        <div className="grid lg:grid-cols-12 gap-10">
          <div className="lg:col-span-7">
            <div className="relative aspect-[4/3] rounded-xl overflow-hidden border border-white/5">
              <img src={stone.image_url} alt={stone.name} className="w-full h-full object-cover" />
              {stone.featured && (
                <div className="absolute top-4 right-4 px-2 py-0.5 bg-gold text-black text-[10px] uppercase tracking-widest rounded">
                  Featured
                </div>
              )}
            </div>
          </div>

          <div className="lg:col-span-5 flex flex-col">
            <div className="text-xs uppercase tracking-[0.3em] text-zinc-500 mb-3">
              {stone.type} <span className="text-gold">·</span> {stone.finish}
            </div>
            <h1 className="font-serif text-5xl tracking-tighter leading-none">{stone.name}</h1>
            {stone.origin && (
              <div className="mt-4 flex items-center gap-2 text-sm text-zinc-400 font-mono">
                <MapPin className="w-3.5 h-3.5 text-gold" /> {stone.origin}
              </div>
            )}
            {stone.description && (
              <p className="text-zinc-300 mt-6 leading-relaxed text-base">{stone.description}</p>
            )}

            <div className="mt-8 grid grid-cols-2 gap-3">
              <div className="panel rounded-lg p-4">
                <div className="text-[10px] uppercase tracking-[0.2em] text-zinc-500">Type</div>
                <div className="mt-1 font-serif text-lg">{stone.type}</div>
              </div>
              <div className="panel rounded-lg p-4">
                <div className="text-[10px] uppercase tracking-[0.2em] text-zinc-500">Finish</div>
                <div className="mt-1 font-serif text-lg">{stone.finish}</div>
              </div>
            </div>

            <div className="mt-auto pt-8 flex flex-col gap-3">
              <Link to="/register" data-testid="stone-primary-cta">
                <Button className="w-full bg-gold text-black hover:bg-[#B38C44] h-12">
                  <Sparkles className="w-4 h-4 mr-2" /> See it in your kitchen — free
                </Button>
              </Link>
              <Button
                variant="outline"
                onClick={() => setOpenQuote(true)}
                data-testid="stone-quote-btn"
                className="w-full border-white/10 text-zinc-200 h-12"
              >
                <MessageSquare className="w-4 h-4 mr-2" /> Request a quote
              </Button>
            </div>
          </div>
        </div>

        {renders && renders.length > 0 && (
          <section className="mt-20">
            <div className="flex items-end justify-between mb-6">
              <div>
                <div className="text-xs uppercase tracking-[0.3em] text-zinc-500 mb-2">Customer renders</div>
                <h2 className="font-serif text-3xl tracking-tight">{stone.name} in real kitchens</h2>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {renders.map((r) => (
                <Link
                  key={r.id}
                  to={`/r/${r.id}`}
                  data-testid={`stone-render-${r.id}`}
                  className="group relative aspect-[4/3] overflow-hidden rounded-lg border border-white/5 hover-lift"
                >
                  <img
                    src={r.result_image}
                    alt={`${stone.name} render`}
                    className="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-transparent to-transparent" />
                  <div className="absolute bottom-2 left-3 right-3 text-xs font-mono text-zinc-300">
                    {new Date(r.created_at).toLocaleDateString()}
                  </div>
                </Link>
              ))}
            </div>
          </section>
        )}
      </main>

      <footer className="border-t border-white/10 py-8 mt-16">
        <div className="max-w-6xl mx-auto px-6 lg:px-10 flex flex-col sm:flex-row gap-3 items-center justify-between">
          <div className="font-serif text-zinc-400">Rated Worktops</div>
          <div className="text-xs text-zinc-500 font-mono">© 2026 · Premium stone, photoreal previews.</div>
        </div>
      </footer>

      <QuoteDialog
        open={openQuote}
        onOpenChange={setOpenQuote}
        stoneId={stone.id}
        stoneName={stone.name}
      />
    </div>
  );
}
