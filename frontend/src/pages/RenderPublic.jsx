import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";
import { API } from "@/lib/api";
import { Button } from "@/components/ui/button";
import CompareSlider from "@/components/CompareSlider";
import QuoteDialog from "@/components/QuoteDialog";
import { ArrowRight, Loader2, MessageSquare, Share2 } from "lucide-react";
import { toast } from "sonner";

export default function RenderPublic() {
  const { id } = useParams();
  const [render, setRender] = useState(null);
  const [loading, setLoading] = useState(true);
  const [openQuote, setOpenQuote] = useState(false);

  useEffect(() => {
    axios
      .get(`${API}/public/renders/${id}`)
      .then(({ data }) => setRender(data))
      .catch(() => setRender(false))
      .finally(() => setLoading(false));
  }, [id]);

  const share = async () => {
    const url = window.location.href;
    try {
      if (navigator.share) {
        await navigator.share({ title: `Kitchen rendered in ${render?.stone_name}`, url });
      } else {
        await navigator.clipboard.writeText(url);
        toast.success("Link copied to clipboard");
      }
    } catch {
      // user dismissed
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-zinc-400">
        <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading render…
      </div>
    );
  }

  if (!render) {
    return (
      <div className="min-h-screen flex items-center justify-center flex-col gap-4 px-6 text-center">
        <div className="font-serif text-3xl">Render not found</div>
        <p className="text-zinc-400 text-sm max-w-md">This kitchen render link is invalid or has been removed.</p>
        <Link to="/">
          <Button className="bg-gold text-black hover:bg-[#B38C44]">Visit Rated Worktops</Button>
        </Link>
      </div>
    );
  }

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
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={share} data-testid="public-share-btn" className="border-white/10 text-zinc-200">
              <Share2 className="w-4 h-4 mr-2" /> Share
            </Button>
            <Link to="/register">
              <Button size="sm" className="bg-gold text-black hover:bg-[#B38C44]">
                Try the visualizer <ArrowRight className="w-3.5 h-3.5 ml-1" />
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 lg:px-10 py-10">
        <div className="text-xs uppercase tracking-[0.3em] text-zinc-500 mb-3">Customer Render</div>
        <h1 className="font-serif text-4xl sm:text-5xl tracking-tight">
          {render.stone_name} <span className="text-gold">·</span> visualized
        </h1>
        <p className="text-zinc-400 mt-3 text-sm font-mono">
          Rendered {new Date(render.created_at).toLocaleDateString()} · {render.mode} mode
        </p>

        <div className="mt-8">
          <CompareSlider before={render.kitchen_image} after={render.result_image} alt={render.stone_name} />
        </div>

        <div className="mt-12 panel rounded-lg p-8 grid sm:grid-cols-2 gap-6 items-center">
          <div>
            <div className="text-xs uppercase tracking-[0.3em] text-gold mb-3">Like what you see?</div>
            <div className="font-serif text-2xl tracking-tight">
              Get a quote for {render.stone_name}
            </div>
            <p className="text-zinc-400 text-sm mt-3 leading-relaxed">
              We'll send pricing, availability, and installation timing direct to your inbox. No spam, ever.
            </p>
          </div>
          <div className="flex flex-col gap-3">
            <Button onClick={() => setOpenQuote(true)} data-testid="public-quote-btn" className="bg-gold text-black hover:bg-[#B38C44] h-12">
              <MessageSquare className="w-4 h-4 mr-2" /> Request a quote
            </Button>
            <Link to="/register" className="text-center text-xs text-zinc-400 hover:text-white">
              Or try the visualizer with 3 free credits →
            </Link>
          </div>
        </div>
      </main>

      <footer className="border-t border-white/10 py-6 mt-12">
        <div className="max-w-6xl mx-auto px-6 lg:px-10 text-center text-xs text-zinc-500 font-mono">
          © 2026 Rated Worktops · Stone visualizations powered by AI
        </div>
      </footer>

      <QuoteDialog
        open={openQuote}
        onOpenChange={setOpenQuote}
        visualizationId={render.id}
        stoneId={render.stone_id}
        stoneName={render.stone_name}
      />
    </div>
  );
}
