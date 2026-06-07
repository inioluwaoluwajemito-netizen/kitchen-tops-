import React, { useState } from "react";
import api, { formatApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Loader2, Check } from "lucide-react";

export default function QuoteDialog({ open, onOpenChange, visualizationId, stoneId, stoneName }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);

  const reset = () => {
    setName("");
    setEmail("");
    setPhone("");
    setNotes("");
    setSent(false);
  };

  const submit = async (e) => {
    e?.preventDefault();
    if (!name.trim() || !email.trim()) {
      toast.error("Name and email are required");
      return;
    }
    setBusy(true);
    try {
      await api.post("/quotes", {
        name,
        email,
        phone,
        notes,
        visualization_id: visualizationId,
        stone_id: stoneId,
      });
      setSent(true);
      toast.success("Quote request sent — we'll be in touch shortly");
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail) || "Failed to send");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o && !busy) { onOpenChange(false); setTimeout(reset, 200); } }}>
      <DialogContent className="bg-zinc-950 border-white/10 max-w-md">
        <DialogHeader>
          <DialogTitle className="font-serif text-2xl">
            {sent ? "Request received" : "Get a quote for this stone"}
          </DialogTitle>
          <DialogDescription className="text-zinc-400">
            {sent
              ? "Thank you — our team will reach out with pricing & availability within one business day."
              : `Leave your details and we'll get back to you with pricing${stoneName ? ` for ${stoneName}` : ""}.`}
          </DialogDescription>
        </DialogHeader>

        {sent ? (
          <div className="py-6 flex flex-col items-center gap-3">
            <div className="w-14 h-14 rounded-full bg-gold/15 flex items-center justify-center">
              <Check className="w-7 h-7 text-gold" />
            </div>
            <div className="text-sm text-zinc-300">{email}</div>
            <Button onClick={() => { onOpenChange(false); setTimeout(reset, 200); }} className="bg-gold text-black hover:bg-[#B38C44] mt-3" data-testid="quote-close-btn">
              Close
            </Button>
          </div>
        ) : (
          <form onSubmit={submit} className="space-y-4 mt-2">
            <div>
              <Label className="text-xs uppercase tracking-[0.2em] text-zinc-500">Name</Label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                data-testid="quote-name"
                className="mt-2 bg-zinc-900 border-zinc-800 focus:border-gold"
                placeholder="Jane Doe"
              />
            </div>
            <div>
              <Label className="text-xs uppercase tracking-[0.2em] text-zinc-500">Email</Label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                data-testid="quote-email"
                className="mt-2 bg-zinc-900 border-zinc-800 focus:border-gold"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <Label className="text-xs uppercase tracking-[0.2em] text-zinc-500">Phone (optional)</Label>
              <Input
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                data-testid="quote-phone"
                className="mt-2 bg-zinc-900 border-zinc-800 focus:border-gold"
                placeholder="+44 7…"
              />
            </div>
            <div>
              <Label className="text-xs uppercase tracking-[0.2em] text-zinc-500">Notes</Label>
              <Textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                data-testid="quote-notes"
                className="mt-2 bg-zinc-900 border-zinc-800 focus:border-gold min-h-[80px]"
                placeholder="Anything you'd like us to know — kitchen size, timeline, postcode…"
              />
            </div>
            <Button type="submit" disabled={busy} className="w-full bg-gold text-black hover:bg-[#B38C44] h-11" data-testid="quote-submit-btn">
              {busy ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              Send quote request
            </Button>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
