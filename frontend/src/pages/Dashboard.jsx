import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import api, { formatApiError } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import CompareSlider from "@/components/CompareSlider";
import { toast } from "sonner";
import { Upload, Wand2, Image as ImageIcon, Plus, X, Loader2, Sparkles, Check, Download } from "lucide-react";

function readFileAsDataURL(file) {
  return new Promise((res, rej) => {
    const r = new FileReader();
    r.onload = () => res(r.result);
    r.onerror = rej;
    r.readAsDataURL(file);
  });
}

export default function Dashboard() {
  const { user, updateCredits } = useAuth();
  const [stones, setStones] = useState({ catalog: [], custom: [] });
  const [kitchen, setKitchen] = useState(null); // data URL
  const [selectedStone, setSelectedStone] = useState(null);
  const [mode, setMode] = useState("auto");
  const [instructions, setInstructions] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null); // data URL
  const fileRef = useRef(null);
  const stoneFileRef = useRef(null);

  const loadStones = async () => {
    try {
      const { data } = await api.get("/stones");
      setStones(data);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail) || "Failed to load stones");
    }
  };

  useEffect(() => {
    loadStones();
  }, []);

  const onPick = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 8 * 1024 * 1024) {
      toast.error("Image too large (max 8MB)");
      return;
    }
    const data = await readFileAsDataURL(file);
    setKitchen(data);
    setResult(null);
  };

  const onPickStone = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 6 * 1024 * 1024) {
      toast.error("Stone image too large (max 6MB)");
      return;
    }
    const data = await readFileAsDataURL(file);
    const name = prompt("Name this stone:", file.name.replace(/\.[^.]+$/, "")) || "Custom Stone";
    try {
      const { data: created } = await api.post("/stones/custom", {
        name,
        type: "Custom",
        finish: "Custom",
        image_base64: data,
      });
      toast.success("Custom stone added");
      setStones((s) => ({ ...s, custom: [created, ...s.custom] }));
      setSelectedStone(created);
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail) || "Upload failed");
    }
  };

  const generate = async () => {
    if (!kitchen) {
      toast.error("Please upload a kitchen photo first");
      return;
    }
    if (!selectedStone) {
      toast.error("Please select a stone");
      return;
    }
    if ((user?.credits || 0) < 1) {
      toast.error("You have no credits left. Visit the Credits page to top up.");
      return;
    }
    setBusy(true);
    setResult(null);
    try {
      const { data } = await api.post("/visualize", {
        kitchen_image_base64: kitchen,
        stone_id: selectedStone.id,
        mode,
        instructions,
      });
      setResult(data.visualization.result_image);
      updateCredits(data.credits_remaining);
      toast.success("Render complete");
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail) || "Generation failed");
    } finally {
      setBusy(false);
    }
  };

  const downloadResult = () => {
    if (!result) return;
    const a = document.createElement("a");
    a.href = result;
    a.download = `rated-worktops-${Date.now()}.png`;
    a.click();
  };

  const allStones = [...stones.custom, ...stones.catalog];

  return (
    <div className="max-w-[1600px] mx-auto px-4 lg:px-8 py-6">
      <div className="flex items-end justify-between mb-6">
        <div>
          <div className="text-xs uppercase tracking-[0.3em] text-zinc-500">Visualizer Studio</div>
          <h1 className="font-serif text-3xl tracking-tight mt-1">Design your worktop</h1>
        </div>
        <div className="hidden md:flex items-center gap-2 text-sm text-zinc-400">
          <Sparkles className="w-4 h-4 text-gold" />
          <span className="font-mono text-white">{user?.credits ?? 0}</span> credits
        </div>
      </div>

      <div className="grid lg:grid-cols-12 gap-6">
        {/* LEFT: stones */}
        <aside className="lg:col-span-3 panel rounded-lg p-4 max-h-[80vh] flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <div className="text-xs uppercase tracking-[0.2em] text-zinc-500">Stone Catalog</div>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => stoneFileRef.current?.click()}
              data-testid="upload-custom-stone-btn"
              className="text-gold hover:text-gold/80 text-xs h-7"
            >
              <Plus className="w-3 h-3 mr-1" /> Upload
            </Button>
            <input ref={stoneFileRef} type="file" accept="image/*" hidden onChange={onPickStone} data-testid="custom-stone-file" />
          </div>
          <div className="overflow-y-auto pr-1 space-y-2">
            {allStones.map((s) => {
              const active = selectedStone?.id === s.id;
              return (
                <button
                  key={s.id}
                  onClick={() => setSelectedStone(s)}
                  data-testid={`stone-option-${s.id}`}
                  className={`w-full text-left flex gap-3 items-center p-2 rounded-md border transition-colors ${
                    active ? "border-gold bg-gold/5" : "border-white/5 hover:border-white/20 bg-zinc-950/40"
                  }`}
                >
                  <img src={s.image_url} alt={s.name} className="w-14 h-14 rounded object-cover border border-white/5" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-white truncate">{s.name}</div>
                    <div className="text-[10px] uppercase tracking-wider text-zinc-500">
                      {s.type} · {s.finish}
                    </div>
                  </div>
                  {active && <Check className="w-4 h-4 text-gold shrink-0" />}
                </button>
              );
            })}
          </div>
        </aside>

        {/* CENTER: canvas */}
        <section className="lg:col-span-6 panel rounded-lg p-4 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <div className="text-xs uppercase tracking-[0.2em] text-zinc-500">Workspace</div>
            {kitchen && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  setKitchen(null);
                  setResult(null);
                }}
                data-testid="clear-photo-btn"
                className="text-zinc-400 text-xs h-7"
              >
                <X className="w-3 h-3 mr-1" /> Clear
              </Button>
            )}
          </div>

          {!kitchen && (
            <div
              onClick={() => fileRef.current?.click()}
              data-testid="upload-photo-dropzone"
              className="flex-1 min-h-[440px] rounded-lg border border-dashed border-white/10 hover:border-gold/50 transition-colors cursor-pointer flex flex-col items-center justify-center gap-4 text-center p-12"
            >
              <Upload className="w-10 h-10 text-zinc-500" />
              <div>
                <div className="font-serif text-2xl text-white">Upload your kitchen</div>
                <div className="text-sm text-zinc-400 mt-1">JPG or PNG, up to 8MB</div>
              </div>
              <Button className="bg-gold text-black hover:bg-[#B38C44]" data-testid="upload-photo-btn">
                <ImageIcon className="w-4 h-4 mr-2" /> Choose file
              </Button>
              <input ref={fileRef} type="file" accept="image/*" hidden onChange={onPick} data-testid="kitchen-file-input" />
            </div>
          )}

          {kitchen && !result && (
            <div className="relative rounded-lg overflow-hidden border border-white/5">
              <img src={kitchen} alt="Kitchen" className="w-full object-contain bg-black max-h-[600px]" />
              {busy && (
                <div className="absolute inset-0 bg-black/70 flex flex-col items-center justify-center gap-4">
                  <Loader2 className="w-10 h-10 text-gold animate-spin" />
                  <div className="text-sm text-zinc-300 tracking-widest uppercase">Rendering with Nano Banana...</div>
                  <div className="text-xs text-zinc-500 font-mono">This usually takes 15-40 seconds</div>
                </div>
              )}
            </div>
          )}

          {result && kitchen && (
            <div className="space-y-3">
              <CompareSlider before={kitchen} after={result} />
              <div className="flex items-center justify-between">
                <div className="text-xs text-zinc-500 font-mono">Drag the slider to compare</div>
                <Button variant="outline" size="sm" onClick={downloadResult} data-testid="download-render-btn" className="border-white/10 text-zinc-200">
                  <Download className="w-4 h-4 mr-2" /> Download
                </Button>
              </div>
            </div>
          )}
        </section>

        {/* RIGHT: settings */}
        <aside className="lg:col-span-3 panel rounded-lg p-4 space-y-5">
          <div>
            <div className="text-xs uppercase tracking-[0.2em] text-zinc-500 mb-2">Mode</div>
            <Tabs value={mode} onValueChange={setMode}>
              <TabsList className="grid grid-cols-2 bg-zinc-950 border border-white/5">
                <TabsTrigger value="auto" data-testid="mode-auto" className="data-[state=active]:bg-gold data-[state=active]:text-black">
                  Auto
                </TabsTrigger>
                <TabsTrigger value="hybrid" data-testid="mode-hybrid" className="data-[state=active]:bg-gold data-[state=active]:text-black">
                  Hybrid
                </TabsTrigger>
              </TabsList>
            </Tabs>
            <div className="text-[11px] text-zinc-500 mt-2 leading-relaxed">
              {mode === "auto"
                ? "AI detects worktop & splashback surfaces automatically."
                : "AI detection + your refinement instructions."}
            </div>
          </div>

          {mode === "hybrid" && (
            <div>
              <div className="text-xs uppercase tracking-[0.2em] text-zinc-500 mb-2">Refinement</div>
              <Textarea
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                placeholder="e.g. Only the island worktop, leave the wall area alone."
                data-testid="instructions-input"
                className="bg-zinc-950 border-zinc-800 focus:border-gold text-white min-h-[100px] text-sm"
              />
            </div>
          )}

          <div className="border-t border-white/5 pt-4">
            <div className="text-xs uppercase tracking-[0.2em] text-zinc-500">Selected</div>
            {selectedStone ? (
              <div className="mt-2 flex items-center gap-3">
                <img src={selectedStone.image_url} alt={selectedStone.name} className="w-12 h-12 rounded object-cover" />
                <div className="min-w-0">
                  <div className="text-sm text-white truncate">{selectedStone.name}</div>
                  <div className="text-[10px] uppercase tracking-wider text-zinc-500">{selectedStone.type}</div>
                </div>
              </div>
            ) : (
              <div className="mt-2 text-sm text-zinc-500">Pick a stone from the catalog</div>
            )}
          </div>

          <Button
            onClick={generate}
            disabled={busy || !kitchen || !selectedStone}
            data-testid="generate-render-btn"
            className="w-full bg-gold text-black hover:bg-[#B38C44] h-11"
          >
            {busy ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Rendering
              </>
            ) : (
              <>
                <Wand2 className="w-4 h-4 mr-2" /> Generate render
              </>
            )}
          </Button>
          <div className="text-[11px] text-center text-zinc-500 font-mono">
            Costs 1 credit · Balance: {user?.credits ?? 0}
          </div>
          {(user?.credits ?? 0) === 0 && (
            <Link to="/credits" data-testid="buy-credits-link" className="block text-center text-xs text-gold hover:underline">
              Top up credits →
            </Link>
          )}
        </aside>
      </div>
    </div>
  );
}
