import React, { useEffect, useState } from "react";
import api, { formatApiError } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Sparkles, CreditCard, Smartphone, Apple, Globe, Check, Loader2 } from "lucide-react";
import { toast } from "sonner";

const METHODS = [
  { id: "stripe", label: "Card (Stripe)", icon: CreditCard },
  { id: "paypal", label: "PayPal", icon: Globe },
  { id: "apple_pay", label: "Apple Pay", icon: Apple },
  { id: "google_pay", label: "Google Pay", icon: Smartphone },
];

export default function Credits() {
  const { user, updateCredits } = useAuth();
  const [data, setData] = useState({ balance: 0, packs: [], transactions: [] });
  const [open, setOpen] = useState(null); // selected pack
  const [busy, setBusy] = useState(false);

  const load = async () => {
    const { data: d } = await api.get("/credits");
    setData(d);
  };

  useEffect(() => {
    load();
  }, []);

  const purchase = async (method) => {
    if (!open) return;
    setBusy(true);
    try {
      const { data: res } = await api.post("/credits/purchase", { pack_id: open.id, method });
      updateCredits(res.balance);
      toast.success(`+${open.credits} credits added (mock payment)`);
      setOpen(null);
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail) || "Purchase failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-6 lg:px-10 py-12">
      <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between gap-4 mb-10">
        <div>
          <div className="text-xs uppercase tracking-[0.3em] text-zinc-500 mb-2">Account</div>
          <h1 className="font-serif text-4xl tracking-tight">Credits & Billing</h1>
        </div>
        <div className="panel rounded-lg p-5">
          <div className="text-[10px] uppercase tracking-[0.3em] text-zinc-500">Current balance</div>
          <div className="flex items-baseline gap-2 mt-2">
            <Sparkles className="w-5 h-5 text-gold" />
            <span data-testid="credits-balance-value" className="font-mono text-4xl text-white">
              {user?.credits ?? data.balance}
            </span>
            <span className="text-zinc-500 text-sm">credits</span>
          </div>
        </div>
      </div>

      <div className="grid sm:grid-cols-3 gap-5">
        {data.packs.map((p) => (
          <div
            key={p.id}
            data-testid={`pack-card-${p.id}`}
            className={`panel rounded-lg p-7 relative ${p.popular ? "border-gold" : ""}`}
            style={p.popular ? { borderColor: "#CBA153" } : {}}
          >
            {p.popular && (
              <div className="absolute -top-3 left-6 px-2 py-0.5 bg-gold text-black text-[10px] uppercase tracking-widest rounded">
                Best value
              </div>
            )}
            <div className="font-serif text-2xl">{p.name}</div>
            <div className="mt-5 flex items-baseline gap-1">
              <span className="font-serif text-5xl">£{p.price_gbp}</span>
            </div>
            <div className="mt-1 font-mono text-sm text-gold">{p.credits} credits</div>
            <div className="text-xs text-zinc-500 mt-1">£{(p.price_gbp / p.credits).toFixed(2)} / render</div>

            <Button
              onClick={() => setOpen(p)}
              data-testid={`buy-pack-${p.id}`}
              className={`mt-7 w-full ${p.popular ? "bg-gold text-black hover:bg-[#B38C44]" : "bg-white/5 hover:bg-white/10 text-white border border-white/10"}`}
            >
              Buy
            </Button>
          </div>
        ))}
      </div>

      <div className="mt-14">
        <div className="font-serif text-2xl mb-4">Recent transactions</div>
        {data.transactions.length === 0 ? (
          <div className="text-sm text-zinc-500 panel rounded-lg p-6">No transactions yet.</div>
        ) : (
          <div className="panel rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="text-xs uppercase tracking-wider text-zinc-500 border-b border-white/5">
                <tr>
                  <th className="text-left p-4">Pack</th>
                  <th className="text-left p-4">Credits</th>
                  <th className="text-left p-4">Method</th>
                  <th className="text-left p-4">Status</th>
                  <th className="text-left p-4">Date</th>
                </tr>
              </thead>
              <tbody>
                {data.transactions.map((t) => (
                  <tr key={t.id} className="border-b border-white/5 last:border-0">
                    <td className="p-4 font-serif">{t.pack_name}</td>
                    <td className="p-4 font-mono text-gold">+{t.credits}</td>
                    <td className="p-4 text-zinc-300">{t.method.replace("_", " ")}</td>
                    <td className="p-4 text-zinc-400">{t.status}</td>
                    <td className="p-4 text-zinc-400 font-mono text-xs">{new Date(t.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Dialog open={!!open} onOpenChange={(o) => !o && !busy && setOpen(null)}>
        <DialogContent className="bg-zinc-950 border-white/10 max-w-md">
          <DialogHeader>
            <DialogTitle className="font-serif text-2xl">
              Buy {open?.name} pack
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              {open?.credits} credits for £{open?.price_gbp}. Payments are currently MOCKED — credits will be added instantly.
            </DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-3 mt-3">
            {METHODS.map((m) => (
              <Button
                key={m.id}
                disabled={busy}
                onClick={() => purchase(m.id)}
                data-testid={`pay-method-${m.id}`}
                variant="outline"
                className="border-white/10 bg-zinc-900/40 hover:bg-zinc-900 text-zinc-200 h-12 justify-start"
              >
                {busy ? <Loader2 className="w-4 h-4 mr-3 animate-spin" /> : <m.icon className="w-4 h-4 mr-3" />}
                {m.label}
              </Button>
            ))}
          </div>
          <div className="mt-2 text-[11px] text-zinc-500 flex items-center gap-2">
            <Check className="w-3 h-3 text-gold" /> No real charges. Stripe goes live in v1.1.
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
