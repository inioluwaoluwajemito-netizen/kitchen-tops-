import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { API } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { ArrowRight, Upload, Wand2, Eye, Check } from "lucide-react";

const STONE_FALLBACK = [
  { name: "Carrara White", image_url: "https://images.unsplash.com/photo-1558346648-9757f2fa4474?crop=entropy&cs=srgb&fm=jpg&q=85&w=900" },
  { name: "Nero Marquina", image_url: "https://images.unsplash.com/photo-1550053808-52a75a05955d?crop=entropy&cs=srgb&fm=jpg&q=85&w=900" },
  { name: "Charcoal Granite", image_url: "https://images.pexels.com/photos/7683580/pexels-photo-7683580.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940" },
  { name: "Arabescato", image_url: "https://images.unsplash.com/photo-1604147706283-d7119b5b822c?crop=entropy&cs=srgb&fm=jpg&q=85&w=900" },
];

const HERO_IMG = "https://images.unsplash.com/photo-1628745277862-bc0b2d68c50c?crop=entropy&cs=srgb&fm=jpg&q=85&w=1800";
const GALLERY_IMG = "https://images.unsplash.com/photo-1725257928373-dc6d2ac7b145?crop=entropy&cs=srgb&fm=jpg&q=85&w=1600";

export default function Landing() {
  const [stones, setStones] = useState(STONE_FALLBACK);

  useEffect(() => {
    axios
      .get(`${API}/public/stones`)
      .then(({ data }) => {
        if (Array.isArray(data.items) && data.items.length) {
          // Prefer featured if any, then top of sort order — slice to 4
          const featured = data.items.filter((s) => s.featured);
          const rest = data.items.filter((s) => !s.featured);
          setStones([...featured, ...rest].slice(0, 4));
        }
      })
      .catch(() => {
        /* keep fallback */
      });
  }, []);

  return (
    <div className="relative">
      {/* HERO */}
      <section className="relative h-[88vh] min-h-[640px] overflow-hidden">
        <img src={HERO_IMG} alt="Luxury kitchen" className="absolute inset-0 w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-b from-black/55 via-black/30 to-[#09090b]" />
        <div className="absolute inset-0 grain" />
        <div className="relative h-full max-w-7xl mx-auto px-6 lg:px-10 flex flex-col justify-end pb-20">
          <div className="max-w-3xl">
            <div className="text-xs uppercase tracking-[0.4em] text-gold mb-6" data-testid="hero-eyebrow">
              The Rated Worktops Visualizer
            </div>
            <h1 className="font-serif text-5xl sm:text-6xl lg:text-7xl tracking-tighter leading-[0.95] text-white">
              See your kitchen in <em className="italic text-gold not-italic font-serif"> real stone</em>, before you buy it.
            </h1>
            <p className="mt-6 text-zinc-300 text-base sm:text-lg max-w-2xl leading-relaxed">
              Upload a photo of your kitchen, choose a stone from our gallery, and our visualizer renders
              your worktop and splashback in the exact material — photorealistic, in seconds.
            </p>
            <div className="mt-10 flex flex-wrap items-center gap-4">
              <Link to="/register" data-testid="hero-cta-primary">
                <Button size="lg" className="bg-gold text-black hover:bg-[#B38C44] h-12 px-6 text-base">
                  Try with 3 free credits <ArrowRight className="ml-2 w-4 h-4" />
                </Button>
              </Link>
              <a href="#how" data-testid="hero-cta-secondary">
                <Button size="lg" variant="ghost" className="text-white hover:bg-white/10 h-12 px-5">
                  See how it works
                </Button>
              </a>
              <div className="text-xs text-zinc-400 font-mono">No card needed. Cancel anytime.</div>
            </div>
          </div>
        </div>
      </section>

      {/* RIBBON */}
      <section className="border-y border-white/10 py-6 overflow-hidden">
        <div className="flex marquee-track whitespace-nowrap gap-16 text-zinc-500">
          {Array.from({ length: 2 }).map((_, k) => (
            <div key={k} className="flex gap-16 items-center">
              {["Calacatta Gold", "Nero Marquina", "Arabescato Vagli", "Verde Alpi", "Statuario Venato", "Charcoal Granite", "Pearl Quartz", "Taj Mahal Quartzite", "Blue Bahia", "Travertine"].map((s) => (
                <span key={s} className="font-serif text-2xl tracking-tight">
                  {s} <span className="text-gold mx-2">·</span>
                </span>
              ))}
            </div>
          ))}
        </div>
      </section>

      {/* HOW */}
      <section id="how" className="max-w-7xl mx-auto px-6 lg:px-10 py-24">
        <div className="grid lg:grid-cols-12 gap-12">
          <div className="lg:col-span-4">
            <div className="text-xs uppercase tracking-[0.3em] text-zinc-500 mb-4">The Process</div>
            <h2 className="font-serif text-4xl sm:text-5xl tracking-tight">Three steps. One showroom in your pocket.</h2>
          </div>
          <div className="lg:col-span-8 grid sm:grid-cols-3 gap-6">
            {[
              { icon: Upload, t: "Upload", d: "Snap your kitchen. Daylight or evening — our model handles both." },
              { icon: Wand2, t: "Choose Stone", d: "Pick from 12 curated stones, or upload your own sample." },
              { icon: Eye, t: "Visualize", d: "AI applies the texture onto your worktop & splashback in seconds." },
            ].map((s, i) => (
              <div key={s.t} className="panel rounded-lg p-6 hover-lift">
                <div className="text-gold font-mono text-xs mb-6">0{i + 1}</div>
                <s.icon className="w-6 h-6 text-gold mb-6" />
                <div className="font-serif text-xl text-white">{s.t}</div>
                <p className="text-sm text-zinc-400 mt-2 leading-relaxed">{s.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* STONE TEASER */}
      <section id="stones" className="max-w-7xl mx-auto px-6 lg:px-10 py-12">
        <div className="flex items-end justify-between mb-10">
          <div>
            <div className="text-xs uppercase tracking-[0.3em] text-zinc-500 mb-3">Curated Catalog</div>
            <h2 className="font-serif text-4xl sm:text-5xl tracking-tight">12 stones. Hand-picked.</h2>
          </div>
          <Link to="/register" className="hidden sm:block text-sm text-gold hover:underline" data-testid="catalog-link">
            View full catalog →
          </Link>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {stones.map((s) => {
            const Wrap = s.id ? Link : "div";
            const wrapProps = s.id
              ? { to: `/stones/${s.id}`, "data-testid": `landing-stone-${s.id}` }
              : {};
            return (
              <Wrap
                key={s.id || s.name}
                {...wrapProps}
                className="group relative aspect-[4/5] overflow-hidden rounded-lg border border-white/5 hover-lift block"
              >
                <img src={s.image_url} alt={s.name} className="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/10 to-transparent" />
                {s.featured && (
                  <div className="absolute top-3 right-3 px-2 py-0.5 bg-gold text-black text-[10px] uppercase tracking-widest rounded">
                    Featured
                  </div>
                )}
                <div className="absolute bottom-4 left-4 right-4">
                  <div className="font-serif text-lg text-white">{s.name}</div>
                  <div className="text-xs text-zinc-400 mt-0.5 uppercase tracking-wider">
                    {s.type || "Natural Stone"}
                  </div>
                </div>
              </Wrap>
            );
          })}
        </div>
      </section>

      {/* SHOWCASE */}
      <section className="max-w-7xl mx-auto px-6 lg:px-10 py-24">
        <div className="grid lg:grid-cols-12 gap-10 items-center">
          <div className="lg:col-span-7 relative aspect-[4/3] rounded-xl overflow-hidden border border-white/5">
            <img src={GALLERY_IMG} alt="Kitchen visual" className="w-full h-full object-cover" />
            <div className="absolute top-4 left-4 px-3 py-1 bg-black/60 backdrop-blur rounded text-xs uppercase tracking-widest text-zinc-300">
              AI Rendered
            </div>
          </div>
          <div className="lg:col-span-5">
            <div className="text-xs uppercase tracking-[0.3em] text-zinc-500 mb-3">Photoreal</div>
            <h2 className="font-serif text-4xl tracking-tight mb-6">
              Real lighting. Real perspective. <em className="italic text-gold not-italic">Zero guesswork.</em>
            </h2>
            <ul className="space-y-3">
              {[
                "Auto-detects worktop & splashback surfaces",
                "Hybrid refinement for tricky kitchens",
                "Download high-resolution before/after comparisons",
                "Upload custom stone samples from suppliers",
              ].map((t) => (
                <li key={t} className="flex items-start gap-3 text-sm text-zinc-300">
                  <Check className="w-4 h-4 text-gold mt-0.5 shrink-0" />
                  {t}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* PRICING */}
      <section id="pricing" className="max-w-7xl mx-auto px-6 lg:px-10 py-24">
        <div className="text-center mb-14">
          <div className="text-xs uppercase tracking-[0.3em] text-zinc-500 mb-3">Credits</div>
          <h2 className="font-serif text-4xl sm:text-5xl tracking-tight">Pay per render. No subscription.</h2>
          <p className="text-zinc-400 mt-4 max-w-xl mx-auto">
            Every account starts with 3 free credits. Buy more whenever you need.
          </p>
        </div>
        <div className="grid sm:grid-cols-3 gap-6">
          {[
            { id: "starter", name: "Starter", credits: 10, price: 5, popular: false },
            { id: "pro", name: "Pro", credits: 30, price: 12, popular: true },
            { id: "studio", name: "Studio", credits: 100, price: 35, popular: false },
          ].map((p) => (
            <div
              key={p.id}
              data-testid={`pricing-card-${p.id}`}
              className={`panel rounded-lg p-8 relative ${p.popular ? "border-gold" : ""}`}
              style={p.popular ? { borderColor: "#CBA153" } : {}}
            >
              {p.popular && (
                <div className="absolute -top-3 left-6 px-2 py-0.5 bg-gold text-black text-[10px] uppercase tracking-widest rounded">
                  Most popular
                </div>
              )}
              <div className="font-serif text-2xl">{p.name}</div>
              <div className="mt-6 flex items-baseline gap-1">
                <span className="font-serif text-5xl">£{p.price}</span>
                <span className="text-zinc-500 text-sm">/ one-off</span>
              </div>
              <div className="mt-2 font-mono text-sm text-gold">{p.credits} credits</div>
              <Link to="/register">
                <Button className={`mt-8 w-full ${p.popular ? "bg-gold text-black hover:bg-[#B38C44]" : "bg-white/5 hover:bg-white/10 text-white border border-white/10"}`}>
                  Get started
                </Button>
              </Link>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-white/10 py-10 mt-12">
        <div className="max-w-7xl mx-auto px-6 lg:px-10 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="font-serif text-zinc-400">Rated Worktops</div>
          <div className="text-xs text-zinc-500 font-mono">© 2026 · Built for stone showrooms.</div>
        </div>
      </footer>
    </div>
  );
}
