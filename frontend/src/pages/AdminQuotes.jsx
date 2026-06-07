import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { formatApiError } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Mail, Phone, ExternalLink, Loader2, Trash2 } from "lucide-react";

const STATUSES = [
  { id: "all", label: "All" },
  { id: "new", label: "New" },
  { id: "contacted", label: "Contacted" },
  { id: "closed", label: "Closed" },
];

const STATUS_COLOR = {
  new: "bg-gold/20 text-gold border-gold/30",
  contacted: "bg-sky-500/20 text-sky-300 border-sky-500/30",
  closed: "bg-zinc-700/30 text-zinc-400 border-zinc-600/30",
};

export default function AdminQuotes() {
  const { user } = useAuth();
  const [data, setData] = useState({ items: [], counts: {} });
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const params = filter === "all" ? "" : `?status=${filter}`;
      const { data: d } = await api.get(`/admin/quotes${params}`);
      setData(d);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail) || "Failed to load");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  const setStatus = async (q, status) => {
    try {
      await api.patch(`/admin/quotes/${q.id}`, { status });
      toast.success(`Marked ${status}`);
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail) || "Update failed");
    }
  };

  const remove = async (q) => {
    if (!confirm(`Delete quote from ${q.email}? This cannot be undone.`)) return;
    try {
      await api.delete(`/admin/quotes/${q.id}`);
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
        <Link to="/dashboard">
          <Button className="bg-gold text-black hover:bg-[#B38C44]">Back</Button>
        </Link>
      </div>
    );
  }

  const total = (data.counts.new || 0) + (data.counts.contacted || 0) + (data.counts.closed || 0);

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-10 py-12">
      <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between gap-4 mb-8">
        <div>
          <div className="text-xs uppercase tracking-[0.3em] text-zinc-500 mb-2">Admin · Inbox</div>
          <h1 className="font-serif text-4xl tracking-tight">Quote Requests</h1>
          <p className="text-sm text-zinc-400 mt-2">
            <span className="font-mono text-white">{total}</span> total ·{" "}
            <span className="font-mono text-gold">{data.counts.new || 0}</span> new ·{" "}
            <span className="font-mono text-sky-300">{data.counts.contacted || 0}</span> contacted ·{" "}
            <span className="font-mono text-zinc-400">{data.counts.closed || 0}</span> closed
          </p>
        </div>
        <Tabs value={filter} onValueChange={setFilter}>
          <TabsList className="bg-zinc-950 border border-white/5">
            {STATUSES.map((s) => (
              <TabsTrigger
                key={s.id}
                value={s.id}
                data-testid={`filter-${s.id}`}
                className="data-[state=active]:bg-gold data-[state=active]:text-black"
              >
                {s.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>

      {loading ? (
        <div className="text-sm text-zinc-500 flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin" /> Loading…
        </div>
      ) : data.items.length === 0 ? (
        <div className="panel rounded-lg p-12 text-center">
          <div className="font-serif text-2xl mb-2">No quote requests {filter !== "all" ? `with status "${filter}"` : "yet"}</div>
          <p className="text-sm text-zinc-400">
            Quote requests will appear here as customers submit them from public render links.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {data.items.map((q) => (
            <div key={q.id} data-testid={`quote-${q.id}`} className="panel rounded-lg p-5 hover-lift">
              <div className="flex flex-col lg:flex-row gap-5">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="font-serif text-xl">{q.name}</div>
                    <Badge variant="outline" className={STATUS_COLOR[q.status] || STATUS_COLOR.new}>
                      {q.status}
                    </Badge>
                  </div>
                  <div className="flex flex-wrap gap-x-5 gap-y-1 text-sm text-zinc-300">
                    <a href={`mailto:${q.email}`} className="flex items-center gap-1.5 hover:text-gold" data-testid={`quote-email-${q.id}`}>
                      <Mail className="w-3.5 h-3.5" /> {q.email}
                    </a>
                    {q.phone && (
                      <a href={`tel:${q.phone}`} className="flex items-center gap-1.5 hover:text-gold">
                        <Phone className="w-3.5 h-3.5" /> {q.phone}
                      </a>
                    )}
                  </div>
                  {q.notes && (
                    <div className="mt-3 text-sm text-zinc-300 leading-relaxed border-l-2 border-gold/30 pl-3">
                      {q.notes}
                    </div>
                  )}
                  <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-zinc-500 font-mono">
                    <span>{new Date(q.created_at).toLocaleString()}</span>
                    {q.stone && <span>· stone: {q.stone.name}</span>}
                    {q.visualization && (
                      <Link to={`/r/${q.visualization.id}`} target="_blank" className="text-gold hover:underline flex items-center gap-1">
                        view render <ExternalLink className="w-3 h-3" />
                      </Link>
                    )}
                  </div>
                </div>

                <div className="flex flex-row lg:flex-col gap-2 shrink-0">
                  {q.status !== "contacted" && (
                    <Button size="sm" variant="outline" onClick={() => setStatus(q, "contacted")} data-testid={`quote-contacted-${q.id}`} className="border-sky-500/30 text-sky-300 hover:bg-sky-500/10">
                      Mark contacted
                    </Button>
                  )}
                  {q.status !== "closed" && (
                    <Button size="sm" variant="outline" onClick={() => setStatus(q, "closed")} data-testid={`quote-closed-${q.id}`} className="border-white/10 text-zinc-300">
                      Close
                    </Button>
                  )}
                  {q.status !== "new" && (
                    <Button size="sm" variant="ghost" onClick={() => setStatus(q, "new")} className="text-gold hover:bg-gold/10">
                      Reopen
                    </Button>
                  )}
                  <Button size="sm" variant="ghost" onClick={() => remove(q)} data-testid={`quote-delete-${q.id}`} className="text-red-400/80 hover:text-red-400">
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
