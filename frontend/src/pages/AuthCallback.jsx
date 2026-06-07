import React, { useEffect, useRef, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import api from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
export default function AuthCallback() {
  const nav = useNavigate();
  const location = useLocation();
  const { refreshMe } = useAuth();
  const hasProcessed = useRef(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const hash = location.hash || window.location.hash;
    const match = hash.match(/session_id=([^&]+)/);
    if (!match) {
      setError("Missing session_id. Please try signing in again.");
      return;
    }
    const sessionId = decodeURIComponent(match[1]);

    (async () => {
      try {
        const { data } = await api.post("/auth/google", { session_id: sessionId });
        localStorage.setItem("rw_token", data.access_token);
        await refreshMe();
        // Clean URL and navigate
        window.history.replaceState(null, "", window.location.pathname);
        toast.success(`Welcome${data.user?.name ? `, ${data.user.name.split(" ")[0]}` : ""}`);
        nav("/dashboard", { replace: true });
      } catch (e) {
        setError(e.response?.data?.detail || "Google sign-in failed");
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center flex-col gap-4 px-6 text-center">
      {error ? (
        <>
          <div className="font-serif text-3xl">Sign-in failed</div>
          <p className="text-zinc-400 text-sm max-w-md">{error}</p>
          <button
            onClick={() => nav("/login")}
            className="mt-3 text-gold hover:underline text-sm"
            data-testid="auth-callback-back"
          >
            Back to sign in →
          </button>
        </>
      ) : (
        <>
          <Loader2 className="w-8 h-8 animate-spin text-gold" />
          <div className="text-zinc-300 tracking-widest uppercase text-sm">Signing you in…</div>
        </>
      )}
    </div>
  );
}
