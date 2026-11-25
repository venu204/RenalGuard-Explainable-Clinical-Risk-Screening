"use client";
import { useEffect, useMemo, useState } from "react";
import { Plus, Search } from "lucide-react";
import { toast } from "sonner";
import { api, apiError } from "@/lib/api";
import { usePatients } from "@/hooks/use-patients";
import type { Visit } from "@/types";
import { PageHeader } from "@/components/page-header";
import { PatientCard } from "@/components/patient-card";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/card";
import { LoadingState } from "@/components/loading-state";

export default function PatientsPage() {
  const { patients, loading, error, refresh } = usePatients();
  const [query, setQuery] = useState("");
  const [addOpen, setAddOpen] = useState(false);
  const [latest, setLatest] = useState<Record<number, Visit>>({});

  useEffect(() => {
    if (!patients.length) return;
    Promise.all(patients.map(async (patient) => {
      try {
        const { data } = await api.get<{ visits: Visit[] }>(`/patients/${patient.id}/history`);
        return [patient.id, data.visits.at(-1)] as const;
      } catch {
        return [patient.id, undefined] as const;
      }
    })).then((entries) => {
      setLatest(Object.fromEntries(entries.filter((entry): entry is [number, Visit] => Boolean(entry[1]))));
    });
  }, [patients]);

  const visible = useMemo(() => patients.filter((patient) =>
    `${patient.full_name} ${patient.patient_code}`.toLowerCase().includes(query.toLowerCase()),
  ), [patients, query]);

  if (loading) return <LoadingState label="Loading patient intelligence…" />;
  return <>
    <PageHeader eyebrow="PATIENT INTELLIGENCE" title="Patient directory" description="Search profiles, inspect their latest screening signal, and open the next clinical workflow." action={<Button onClick={() => setAddOpen(true)}><Plus className="h-4 w-4" />Add patient</Button>} />
    {error && <p className="mb-4 text-sm text-red-300">{error}</p>}
    <div className="relative mb-5 max-w-md"><Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-500" /><input value={query} onChange={e => setQuery(e.target.value)} className="w-full py-2.5 pl-10 pr-3 text-sm" placeholder="Search name or patient ID" /></div>
    <p className="mb-4 text-xs text-slate-500">{visible.length} patient profile{visible.length !== 1 ? "s" : ""} shown</p>
    <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">{visible.map((patient) => <PatientCard key={patient.id} patient={patient} visit={latest[patient.id]} />)}</div>
    {!visible.length && <GlassCard className="p-10 text-center text-sm text-slate-500">No matching patient profile.</GlassCard>}
    {addOpen && <CreatePatient onClose={() => setAddOpen(false)} onCreated={() => { setAddOpen(false); refresh(); }} />}
  </>;
}
function CreatePatient({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) { const [saving, setSaving] = useState(false); async function submit(form: FormData) { setSaving(true); try { await api.post("/patients", { full_name: form.get("name"), gender: form.get("gender"), date_of_birth: new Date(String(form.get("dob"))).toISOString(), contact_number: form.get("contact") || null }); toast.success("Patient profile created"); onCreated(); } catch (e) { toast.error(apiError(e)); } finally { setSaving(false); } } return <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/70 p-4 backdrop-blur-sm"><GlassCard className="w-full max-w-lg p-6"><div className="flex items-start justify-between"><div><h3 className="font-bold">New patient profile</h3><p className="mt-1 text-sm text-slate-500">Create a profile before recording a screening visit.</p></div><button onClick={onClose} className="text-slate-500 hover:text-white">✕</button></div><form action={submit} className="mt-6 grid gap-4"><label className="text-sm text-slate-300">Full name *<input name="name" required className="mt-1.5 w-full px-3 py-2.5" /></label><div className="grid grid-cols-2 gap-3"><label className="text-sm text-slate-300">Gender *<select name="gender" className="mt-1.5 w-full px-3 py-2.5"><option>MALE</option><option>FEMALE</option><option>OTHER</option></select></label><label className="text-sm text-slate-300">Date of birth *<input name="dob" type="date" required className="mt-1.5 w-full px-3 py-2.5" /></label></div><label className="text-sm text-slate-300">Contact number<input name="contact" className="mt-1.5 w-full px-3 py-2.5" /></label><div className="mt-2 flex justify-end gap-2"><Button type="button" variant="outline" onClick={onClose}>Cancel</Button><Button disabled={saving}>{saving ? "Creating…" : "Create profile"}</Button></div></form></GlassCard></div>; }
