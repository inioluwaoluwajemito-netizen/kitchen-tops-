import React, { useEffect } from "react";
import { Routes, Route, BrowserRouter, Navigate, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { Toaster } from "@/components/ui/sonner";

import Landing from "@/pages/Landing";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Dashboard from "@/pages/Dashboard";
import StoneCatalog from "@/pages/StoneCatalog";
import Visualizations from "@/pages/Visualizations";
import Credits from "@/pages/Credits";
import Navbar from "@/components/Navbar";

function Protected({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading || user === null) {
    return (
      <div className="min-h-screen flex items-center justify-center text-zinc-400 text-sm tracking-widest uppercase">
        Loading...
      </div>
    );
  }
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  return children;
}

function Layout({ children, hideNav = false }) {
  return (
    <div className="min-h-screen flex flex-col">
      {!hideNav && <Navbar />}
      <main className="flex-1">{children}</main>
    </div>
  );
}

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => window.scrollTo(0, 0), [pathname]);
  return null;
}

function AppShell() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <Layout>
            <Landing />
          </Layout>
        }
      />
      <Route
        path="/login"
        element={
          <Layout hideNav>
            <Login />
          </Layout>
        }
      />
      <Route
        path="/register"
        element={
          <Layout hideNav>
            <Register />
          </Layout>
        }
      />
      <Route
        path="/dashboard"
        element={
          <Protected>
            <Layout>
              <Dashboard />
            </Layout>
          </Protected>
        }
      />
      <Route
        path="/catalog"
        element={
          <Protected>
            <Layout>
              <StoneCatalog />
            </Layout>
          </Protected>
        }
      />
      <Route
        path="/gallery"
        element={
          <Protected>
            <Layout>
              <Visualizations />
            </Layout>
          </Protected>
        }
      />
      <Route
        path="/credits"
        element={
          <Protected>
            <Layout>
              <Credits />
            </Layout>
          </Protected>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ScrollToTop />
        <AppShell />
        <Toaster theme="dark" position="top-center" />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
