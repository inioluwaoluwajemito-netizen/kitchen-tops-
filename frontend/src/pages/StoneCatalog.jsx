import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";

export default function StoneCatalog() {
  const [stones, setStones] = useState({ catalog: [], custom: [] });

  useEffect(() => {
    api.get("/stones").then(({ data }) => setStones(data));
  }, []);

  const sections = [
    { title: "Your Uploads", items: stones.custom, empty: "No custom stones yet. Upload from the visualizer." },
    { title: "House Collection", items: stones.catalog, empty: null },
  ];

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-10 py-12">
      <div className="flex items-end justify-between mb-10">
        <div>
          <div className="text-xs uppercase tracking-[0.3em] text-zinc-500 mb-2">Stone Library</div>
          <h1 className="font-serif text-4xl tracking-tight">Curated, characterful, ready to render.</h1>
        </div>
        <Link to="/dashboard">
          <Button variant="outline" className="border-white/10 text-zinc-200" data-testid="back-to-visualizer">
            Back to visualizer
          </Button>
        </Link>
      </div>

      {sections.map((sec) => (
        <div key={sec.title} className="mb-12">
          <div className="flex items-center gap-3 mb-5">
            <div className="font-serif text-2xl">{sec.title}</div>
            <div className="h-px flex-1 bg-white/10" />
            <div className="font-mono text-xs text-zinc-500">{sec.items.length} items</div>
          </div>
          {sec.items.length === 0 ? (
            <div className="text-sm text-zinc-500 py-6">{sec.empty}</div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {sec.items.map((s) => (
                <div key={s.id} data-testid={`catalog-stone-${s.id}`} className="group relative aspect-[4/5] overflow-hidden rounded-lg border border-white/5 hover-lift">
                  <img src={s.image_url} alt={s.name} className="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/20 to-transparent" />
                  <div className="absolute bottom-0 left-0 right-0 p-4">
                    <div className="font-serif text-lg text-white leading-tight">{s.name}</div>
                    <div className="text-[10px] uppercase tracking-[0.2em] text-zinc-300 mt-1">
                      {s.type} <span className="text-gold">·</span> {s.finish}
                    </div>
                    {s.origin && <div className="text-xs text-zinc-400 mt-1 font-mono">{s.origin}</div>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
