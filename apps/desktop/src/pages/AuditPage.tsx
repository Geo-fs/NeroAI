import { useEffect, useState } from "react";
import { api, ArtifactItem, RunDetail, RunItem } from "../api";

export function AuditPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [runs, setRuns] = useState<RunItem[]>([]);
  const [selectedRun, setSelectedRun] = useState<RunDetail | null>(null);
  const [artifacts, setArtifacts] = useState<ArtifactItem[]>([]);
  const [artifactName, setArtifactName] = useState("Run Report");
  const [artifactContent, setArtifactContent] = useState("");
  const [artifactType, setArtifactType] = useState("report");

  async function load() {
    setRows(await api.listAudit());
    setRuns(await api.listRuns());
    setArtifacts(await api.listArtifacts());
  }
  useEffect(() => { load().catch(console.error); }, []);

  async function loadRun(id: string) {
    const run = await api.getRun(id);
    setSelectedRun(run);
  }

  async function createArtifact() {
    if (!artifactName || !artifactContent) return;
    await api.createArtifact({ name: artifactName, content: artifactContent, type: artifactType, run_id: selectedRun?.id ?? undefined });
    setArtifactContent("");
    await load();
  }

  async function deleteArtifact(id: string) {
    await api.deleteArtifact(id);
    await load();
  }

  return (
    <div>
      <div className="card">
        <h3>Audit Log</h3>
        <button className="secondary" onClick={load}>Refresh</button>
        <div style={{ marginTop: 10 }}>
          {rows.map((r) => (
            <div key={r.id} className="audit-row">
              <div><strong>{r.event_type}</strong> at {r.created_at}</div>
              <div className="small">session: {r.session_id ?? "-"}</div>
              <div className="small">{r.summary}</div>
              <div className="small">{JSON.stringify(r.payload ?? {})}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h3>Runs</h3>
        <div className="row">
          <button className="secondary" onClick={load}>Refresh Runs</button>
        </div>
        <div style={{ marginTop: 10 }}>
          {runs.map((run) => (
            <div key={run.id} className="audit-row">
              <div><strong>{run.mode}</strong> at {run.created_at}</div>
              <div className="small">run_id: {run.id}</div>
              <div className="small">model: {run.model_name ?? "-"}</div>
              <div className="small">duration_ms: {run.duration_ms ?? "-"}</div>
              <button className="secondary" onClick={() => loadRun(run.id)}>View</button>
            </div>
          ))}
        </div>
      </div>

      {selectedRun && (
        <div className="card">
          <h3>Run Details</h3>
          <div className="small">run_id: {selectedRun.id}</div>
          <div className="small">input_hash: {selectedRun.input_hash}</div>
          {selectedRun.input_text && <div className="small">input_text: {selectedRun.input_text}</div>}
          <div style={{ marginTop: 8 }}>
            {(selectedRun.events || []).map((evt, idx) => (
              <div key={idx} className="audit-row">
                <div><strong>{evt.event_type}</strong> at {evt.created_at}</div>
                <div className="small">{JSON.stringify(evt.payload)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <h3>Artifacts</h3>
        <div className="row">
          <input value={artifactName} onChange={(e) => setArtifactName(e.target.value)} placeholder="Artifact name" />
          <select value={artifactType} onChange={(e) => setArtifactType(e.target.value)}>
            <option value="report">report</option>
            <option value="summary">summary</option>
            <option value="code">code</option>
            <option value="workflow">workflow</option>
            <option value="config">config</option>
          </select>
          <button onClick={createArtifact}>Save Artifact</button>
        </div>
        <textarea style={{ width: "100%", minHeight: 100, marginTop: 8 }} value={artifactContent} onChange={(e) => setArtifactContent(e.target.value)} placeholder="Paste artifact content" />
        <div style={{ marginTop: 10 }}>
          {artifacts.map((a) => (
            <div key={a.id} className="audit-row">
              <div><strong>{a.name}</strong> ({a.type})</div>
              <div className="small">run_id: {a.run_id ?? "-"}</div>
              <div className="small">created: {a.created_at}</div>
              <button className="secondary" onClick={() => deleteArtifact(a.id)}>Delete</button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
