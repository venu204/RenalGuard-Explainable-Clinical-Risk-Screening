"use client";
import { useEffect, useMemo, useState } from "react";
import { Download, FileCheck2, FileText, Search, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { api, apiError } from "@/lib/api";
import { usePatients } from "@/hooks/use-patients";
import type { History } from "@/types";
import { PageHeader } from "@/components/page-header";
import { GlassCard } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingState } from "@/components/loading-state";
import { RiskBadge } from "@/components/risk-badge";
export default function ReportsPage() {
  const { patients, loading } = usePatients();
  const [patientId, setPatientId] = useState<number>();
  const [history, setHistory] = useState<History>();
  const [query, setQuery] = useState("");

  useEffect(() => {
    if (!patientId) { setHistory(undefined); return; }
    api.get<History>(`/patients/${patientId}/history`).then((response) => setHistory(response.data)).catch((error) => toast.error(apiError(error)));
  }, [patientId]);

  const visits = useMemo(() => (history?.visits || []).slice().reverse().filter((visit) => `${visit.visit_date} ${visit.risk_category}`.toLowerCase().includes(query.toLowerCase())), [history, query]);

  async function download(id: number) {
    try {
      const response = await api.post(`/reports/${id}`, {}, { responseType: "blob" });
      const url = URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = url; link.download = `renalguard-screening-${id}.pdf`; link.click();
      URL.revokeObjectURL(url); toast.success("Clinical report downloaded");
    } catch (error) { toast.error(apiError(error)); }
  }

  if (loading) return <LoadingState />;
  const selectedPatient = patients.find((patient) => patient.id === patientId);
  return <>
    <PageHeader eyebrow="REPORT CENTER" title="Clinical report library" description="Curated, export-ready screening summaries generated from saved clinical visits." />
    <GlassCard className="overflow-hidden">
      <div className="relative border-b border-slate-800 bg-[radial-gradient(circle_at_86%_0%,rgba(59,130,246,.18),transparent_25rem)] p-5 md:p-6">
        <div className="absolute right-0 top-0 h-24 w-24 rounded-full bg-blue-500/10 blur-3xl" />
        <div className="relative flex flex-col justify-between gap-5 md:flex-row md:items-end"><div><div className="flex items-center gap-2"><span className="grid h-9 w-9 place-items-center rounded-xl bg-blue-500/15 text-blue-300"><FileCheck2 className="h-4 w-4" /></span><div><p className="text-sm font-bold">Report workspace</p><p className="mt-0.5 text-xs text-slate-500">Choose a profile to access its saved assessment reports.</p></div></div></div><div className="flex items-center gap-2 rounded-xl border border-slate-700/80 bg-slate-950/50 px-3 py-2 text-xs text-slate-400"><Sparkles className="h-3.5 w-3.5 text-blue-400" />PDF-ready clinical summaries</div></div>
        <div className="relative mt-6 grid gap-3 md:grid-cols-[minmax(0,1fr)_260px]"><label className="text-xs font-bold uppercase tracking-[.12em] text-slate-500">Patient profile<select value={patientId || ""} onChange={(event) => setPatientId(Number(event.target.value))} className="mt-2 w-full px-3 py-3 text-sm normal-case tracking-normal text-slate-100"><option value="">Select a patient record</option>{patients.map((patient) => <option key={patient.id} value={patient.id}>{patient.patient_code} — {patient.full_name}</option>)}</select></label><label className="relative text-xs font-bold uppercase tracking-[.12em] text-slate-500">Filter visits<Search className="absolute bottom-3 left-3 h-4 w-4 text-slate-600" /><input value={query} onChange={(event) => setQuery(event.target.value)} className="mt-2 w-full py-3 pl-9 pr-3 text-sm normal-case tracking-normal" placeholder="Risk category or date" /></label></div>
      </div>
      <div className="p-5 md:p-6">
        {!patientId && <Empty text="Select a patient profile to open the report library." />}
        {patientId && !history && <Empty text="Loading saved clinical reports…" />}
        {history && !visits.length && <Empty text="No saved reports match this view. Run an assessment to create a reportable visit." />}
        {selectedPatient && visits.length > 0 && <><div className="mb-5 flex items-center justify-between"><div><p className="text-sm font-bold text-slate-200">{selectedPatient.full_name}</p><p className="mt-1 text-xs text-slate-500">{visits.length} assessment report{visits.length === 1 ? "" : "s"} available</p></div><p className="rounded-lg bg-slate-800/80 px-2.5 py-1 text-[10px] font-bold tracking-wider text-slate-400">CLINICAL EXPORTS</p></div><div className="grid gap-4 xl:grid-cols-2">{visits.map((visit, index) => <article key={String(visit.visit_id || visit.id)} className="group relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-950/40 p-5 transition hover:-translate-y-0.5 hover:border-blue-400/35 hover:bg-slate-900/85"><div className="absolute right-0 top-0 h-24 w-24 rounded-full bg-blue-500/0 blur-2xl transition group-hover:bg-blue-500/10" /><div className="relative flex items-start justify-between gap-4"><span className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-blue-500/25 to-indigo-500/10 text-blue-300"><FileText className="h-5 w-5" /></span><RiskBadge risk={visit.risk_category} /></div><div className="relative mt-5"><p className="text-[10px] font-bold tracking-[.14em] text-slate-500">SCREENING SUMMARY · {String(index + 1).padStart(2, "0")}</p><h3 className="mt-2 text-base font-bold">Risk assessment report</h3><p className="mt-1 text-xs text-slate-500">Generated from visit · {new Date(visit.visit_date).toLocaleString()}</p></div><div className="relative mt-5 grid grid-cols-4 divide-x divide-slate-800 rounded-xl border border-slate-800 bg-slate-900/45 p-3"><Metric label="ICRRI" value={Number(visit.icrri || 0).toFixed(1)} /><Metric label="CKD" value={`${(Number(visit.ckd || 0) * 100).toFixed(0)}%`} /><Metric label="DM" value={`${(Number(visit.diabetes || 0) * 100).toFixed(0)}%`} /><Metric label="HTN" value={`${(Number(visit.hypertension || 0) * 100).toFixed(0)}%`} /></div><Button className="relative mt-5 w-full" variant="outline" onClick={() => download(Number(visit.visit_id || visit.id))}><Download className="h-4 w-4" />Download clinical PDF</Button></article>)}</div></>}
      </div>
    </GlassCard>
  </>;
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="min-w-0 px-2 first:pl-0 last:pr-0"><p className="text-[9px] font-bold tracking-wider text-slate-600">{label}</p><p className="mt-1 truncate text-sm font-bold text-slate-200">{value}</p></div>; }
function Empty({ text }: { text: string }) { return <div className="grid min-h-[280px] place-items-center text-center"><div><span className="mx-auto grid h-11 w-11 place-items-center rounded-2xl bg-slate-800/70 text-slate-500"><FileText className="h-5 w-5" /></span><p className="mt-4 max-w-xs text-sm leading-6 text-slate-500">{text}</p></div></div>; }
