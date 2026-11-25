"use client";
import { useEffect, useState } from "react";
import { BrainCircuit, CheckCircle2 } from "lucide-react";
import { AdminGuard } from "@/components/admin-guard";
import { PageHeader } from "@/components/page-header";
import { GlassCard } from "@/components/ui/card";
import { api, apiError } from "@/lib/api";
import { toast } from "sonner";
type Model = { id: number; disease: string; algorithm: string; version: string; metrics?: Record<string, number>; is_active: boolean; trained_at: string };
export default function ModelsPage() { const [models, setModels] = useState<Model[]>([]); useEffect(() => { api.get("/admin/model-versions").then(r => setModels(r.data)).catch(e => toast.error(apiError(e))); }, []); return <AdminGuard><PageHeader eyebrow="ADMINISTRATION" title="Model registry" description="Versioned model metadata and performance evidence for the academic screening engine." /><div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">{models.map(model => <GlassCard className="p-5" key={model.id}><div className="flex justify-between"><span className="grid h-10 w-10 place-items-center rounded-xl bg-blue-500/15 text-blue-300"><BrainCircuit className="h-5 w-5" /></span>{model.is_active && <span className="flex items-center gap-1 text-xs font-semibold text-emerald-300"><CheckCircle2 className="h-3.5 w-3.5" />Active</span>}</div><h3 className="mt-5 font-bold">{model.disease}</h3><p className="mt-1 text-sm text-slate-500">{model.algorithm} · {model.version}</p><div className="mt-5 grid grid-cols-3 gap-2">{Object.entries(model.metrics || {}).slice(0, 3).map(([key, value]) => <div key={key} className="rounded-lg bg-slate-950/45 p-2"><p className="text-[10px] uppercase text-slate-600">{key}</p><p className="mt-1 text-sm font-bold">{typeof value === "number" ? value.toFixed(2) : String(value)}</p></div>)}</div><p className="mt-5 text-xs text-slate-600">Trained {new Date(model.trained_at).toLocaleDateString()}</p></GlassCard>)}</div></AdminGuard>; }
