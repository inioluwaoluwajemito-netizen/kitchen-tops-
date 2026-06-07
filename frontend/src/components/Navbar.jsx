import React from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { LogOut, Sparkles, ChevronRight } from "lucide-react";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const navItem = ({ isActive }) =>
    `text-sm tracking-wide transition-colors ${
      isActive ? "text-white" : "text-zinc-400 hover:text-white"
    }`;

  return (
    <header className="sticky top-0 z-40 glass">
      <div className="max-w-7xl mx-auto px-6 lg:px-10 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3" data-testid="brand-link">
          <div className="w-8 h-8 rounded-sm bg-gold flex items-center justify-center">
            <span className="font-serif text-black text-lg leading-none">R</span>
          </div>
          <div className="leading-tight">
            <div className="font-serif text-lg text-white">Rated Worktops</div>
            <div className="text-[10px] uppercase tracking-[0.3em] text-zinc-500">Stone Visualizer</div>
          </div>
        </Link>

        <nav className="hidden md:flex items-center gap-8">
          {user && user !== false ? (
            <>
              <NavLink to="/dashboard" className={navItem} data-testid="nav-dashboard">
                Visualizer
              </NavLink>
              <NavLink to="/catalog" className={navItem} data-testid="nav-catalog">
                Stone Catalog
              </NavLink>
              <NavLink to="/gallery" className={navItem} data-testid="nav-gallery">
                My Renders
              </NavLink>
              <NavLink to="/credits" className={navItem} data-testid="nav-credits">
                Credits
              </NavLink>
              {user.role === "admin" && (
                <>
                  <NavLink to="/admin/catalog" className={navItem} data-testid="nav-admin">
                    Admin
                  </NavLink>
                  <NavLink to="/admin/quotes" className={navItem} data-testid="nav-admin-quotes">
                    Quotes
                  </NavLink>
                </>
              )}
            </>
          ) : (
            <>
              <a href="/#how" className="text-sm text-zinc-400 hover:text-white" data-testid="nav-how">
                How it works
              </a>
              <a href="/#stones" className="text-sm text-zinc-400 hover:text-white" data-testid="nav-stones">
                Stones
              </a>
              <a href="/#pricing" className="text-sm text-zinc-400 hover:text-white" data-testid="nav-pricing">
                Pricing
              </a>
            </>
          )}
        </nav>

        <div className="flex items-center gap-3">
          {user && user !== false ? (
            <>
              <Link to="/credits" data-testid="credit-balance-display">
                <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full border border-white/10 hover:border-gold transition-colors">
                  <Sparkles className="w-3.5 h-3.5 text-gold" />
                  <span className="font-mono text-sm text-white">{user.credits}</span>
                  <span className="text-xs text-zinc-400">credits</span>
                </div>
              </Link>
              <Button
                variant="ghost"
                size="sm"
                onClick={async () => {
                  await logout();
                  navigate("/");
                }}
                data-testid="logout-btn"
                className="text-zinc-300 hover:text-white"
              >
                <LogOut className="w-4 h-4" />
              </Button>
            </>
          ) : (
            <>
              <Link to="/login" data-testid="nav-login">
                <Button variant="ghost" size="sm" className="text-zinc-200 hover:text-white">
                  Sign in
                </Button>
              </Link>
              <Link to="/register" data-testid="nav-register">
                <Button size="sm" className="bg-gold text-black hover:bg-[#B38C44]">
                  Start free <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
