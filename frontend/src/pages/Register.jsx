import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { ChevronLeft, Sparkles, Phone, Globe } from "lucide-react";

const SIDE_IMG = "https://images.unsplash.com/photo-1628745277862-bc0b2d68c50c?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400";

export default function Register() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (password.length < 6) {
      toast.error("Password must be at least 6 characters");
      return;
    }
    setBusy(true);
    const res = await register(email, password, name);
    setBusy(false);
    if (res.ok) {
      toast.success("Welcome to Rated Worktops — enjoy your 3 free credits");
      nav("/dashboard");
    } else {
      toast.error(res.error || "Registration failed");
    }
  };

  const notImpl = (label) =>
    toast.info(`${label} sign-up coming soon. Use email & password for now.`);

  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  const googleSignIn = () => {
    const redirectUrl = window.location.origin + "/dashboard";
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      <div className="relative hidden lg:block">
        <img src={SIDE_IMG} alt="Showroom" className="absolute inset-0 w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-tr from-black/80 via-black/30 to-transparent" />
        <Link to="/" className="absolute top-8 left-8 flex items-center gap-3">
          <div className="w-8 h-8 rounded-sm bg-gold flex items-center justify-center">
            <span className="font-serif text-black leading-none">R</span>
          </div>
          <div className="font-serif text-white text-lg">Rated Worktops</div>
        </Link>
        <div className="absolute bottom-12 left-12 right-12">
          <div className="flex items-center gap-2 text-gold mb-3">
            <Sparkles className="w-4 h-4" />
            <span className="text-xs uppercase tracking-[0.3em]">3 free credits</span>
          </div>
          <div className="font-serif text-4xl text-white tracking-tight max-w-md leading-tight">
            See your dream kitchen finished — before the quote.
          </div>
        </div>
      </div>

      <div className="flex flex-col p-8 sm:p-12 lg:p-16 justify-center">
        <Link to="/" className="lg:hidden text-zinc-400 text-sm flex items-center gap-1 mb-8">
          <ChevronLeft className="w-4 h-4" /> Back
        </Link>
        <div className="max-w-md w-full mx-auto">
          <h1 className="font-serif text-4xl tracking-tight">Create your account</h1>
          <p className="text-zinc-400 mt-2 text-sm">
            Already have one?{" "}
            <Link to="/login" className="text-gold hover:underline" data-testid="link-login">
              Sign in
            </Link>
          </p>

          <form onSubmit={submit} className="mt-10 space-y-5">
            <div>
              <Label htmlFor="name" className="text-xs uppercase tracking-[0.2em] text-zinc-500">Name</Label>
              <Input id="name" data-testid="register-name" value={name} onChange={(e) => setName(e.target.value)} required className="mt-2 bg-zinc-900 border-zinc-800 focus:border-gold text-white h-11" placeholder="Jane Doe" />
            </div>
            <div>
              <Label htmlFor="email" className="text-xs uppercase tracking-[0.2em] text-zinc-500">Email</Label>
              <Input id="email" data-testid="register-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="mt-2 bg-zinc-900 border-zinc-800 focus:border-gold text-white h-11" placeholder="you@kitchen.com" />
            </div>
            <div>
              <Label htmlFor="password" className="text-xs uppercase tracking-[0.2em] text-zinc-500">Password</Label>
              <Input id="password" data-testid="register-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required className="mt-2 bg-zinc-900 border-zinc-800 focus:border-gold text-white h-11" placeholder="At least 6 characters" />
            </div>
            <Button type="submit" disabled={busy} className="w-full bg-gold text-black hover:bg-[#B38C44] h-11" data-testid="register-submit">
              {busy ? "Creating..." : "Create account & claim 3 credits"}
            </Button>
          </form>

          <div className="my-8 flex items-center gap-4">
            <div className="h-px flex-1 bg-white/10" />
            <div className="text-[10px] uppercase tracking-[0.3em] text-zinc-500">or sign up with</div>
            <div className="h-px flex-1 bg-white/10" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Button variant="outline" onClick={googleSignIn} data-testid="register-google" className="border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900 text-zinc-200">
              <Globe className="w-4 h-4 mr-2" /> Google
            </Button>
            <Button variant="outline" onClick={() => notImpl("Phone")} data-testid="register-phone" className="border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900 text-zinc-200">
              <Phone className="w-4 h-4 mr-2" /> Phone
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
