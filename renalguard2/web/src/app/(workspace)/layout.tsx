"use client";
import { AppShell } from "@/components/app-shell";
import { AuthProvider, useAuth } from "@/components/auth-provider";
function Guard({ children }: { children: React.ReactNode }) { const { loading, user } = useAuth(); if (loading || !user) return <div className="grid min-h-screen place-items-center bg-[#020817] text-slate-400">Loading clinical workspace…</div>; return <AppShell>{children}</AppShell>; }
export default function WorkspaceLayout({ children }: { children: React.ReactNode }) { return <AuthProvider><Guard>{children}</Guard></AuthProvider>; }
