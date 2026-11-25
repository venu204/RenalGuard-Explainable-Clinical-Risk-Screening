"use client";
import { useEffect, useState } from "react";
import { Clock3 } from "lucide-react";
import { AdminGuard } from "@/components/admin-guard";
import { PageHeader } from "@/components/page-header";
import { GlassCard } from "@/components/ui/card";
import { api, apiError } from "@/lib/api";
import { toast } from "sonner";
type Log = { id: number; action: string; result: string; timestamp: string; user_id?: number; patient_id?: number };
export default function AuditPage() { const [logs, setLogs] = useState<Log[]>([]); useEffect(() => { api.get("/admin/audit-logs").then(r => setLogs(r.data)).catch(e => toast.error(apiError(e))); }, []); return <AdminGuard><PageHeader eyebrow="ADMINISTRATION" title="Audit logs" description="Immutable operational history for screening and workspace actions." /><GlassCard className="p-5"><div className="space-y-3">{logs.map(log => <div className="flex gap-4 rounded-xl border border-slate-800 bg-slate-950/35 p-4" key={log.id}><span className="grid h-9 w-9 place-items-center rounded-xl bg-violet-500/10 text-violet-300"><Clock3 className="h-4 w-4" /></span><div className="flex-1"><div className="flex justify-between gap-3"><p className="font-semibold">{log.action.replaceAll("_", " ")}</p><span className="text-xs text-slate-500">{new Date(log.timestamp).toLocaleString()}</span></div><p className="mt-1 text-xs text-slate-500">Result: {log.result} · User #{log.user_id || "system"} · Patient #{log.patient_id || "—"}</p></div></div>)}{!logs.length && <p className="py-10 text-center text-sm text-slate-500">No audit events yet.</p>}</div></GlassCard></AdminGuard>; }
