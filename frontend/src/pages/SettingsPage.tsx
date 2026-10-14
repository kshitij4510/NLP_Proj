import { useQuery } from "@tanstack/react-query";
import apiClient from "@/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { errorMessage } from "@/lib/errors";
export default function SettingsPage() {
  const runtime = useQuery({ queryKey: ["runtime"], queryFn: () => apiClient.get("/system/runtime").then(r => r.data) });
  return <div className="p-8 space-y-6 max-w-4xl">
    <h1 className="text-2xl font-bold">Runtime Diagnostics</h1>
    <p className="text-muted-foreground">Current backend configuration. Configure providers through backend/.env.local and restart the server.</p>
    <Button onClick={() => runtime.refetch()} disabled={runtime.isFetching}>Refresh Diagnostics</Button>
    {runtime.error && <p role="alert" className="text-destructive">{errorMessage(runtime.error)}</p>}
    {runtime.data && <Card><CardHeader><CardTitle>Active Configuration</CardTitle></CardHeader><CardContent>
      <dl className="grid grid-cols-2 gap-4">{Object.entries(runtime.data).map(([key, value]) => <div key={key}><dt className="text-sm text-muted-foreground">{key.replace(/_/g, " ")}</dt><dd className="font-medium">{String(value)}</dd></div>)}</dl>
      <p className="mt-6 text-sm text-muted-foreground">Local mode indexes abstracts and uploaded PDFs. Lexical hashing uses token overlap; it is not a trained semantic model. Experiment runs record supplied measurements.</p>
    </CardContent></Card>}
  </div>;
}
