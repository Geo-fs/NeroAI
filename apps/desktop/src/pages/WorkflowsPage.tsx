import { useEffect, useState } from "react";
import { api, WorkflowDef } from "../api";

const defaultWorkflow = JSON.stringify({
  steps: [
    { id: "s1", type: "set_var", name: "topic", value: "NeroAI" },
    { id: "s2", type: "prompt_agent", prompt_template: "Summarize {{vars.topic}} architecture." },
    { id: "s3", type: "return", value_template: "{{vars.s2.output}}" }
  ]
}, null, 2);

export function WorkflowsPage() {
  const [items, setItems] = useState<WorkflowDef[]>([]);
  const [id, setId] = useState("");
  const [name, setName] = useState("New Workflow");
  const [description, setDescription] = useState("Workflow description");
  const [definition, setDefinition] = useState(defaultWorkflow);
  const [runInput, setRunInput] = useState("{}");
  const [result, setResult] = useState("");

  async function load() { setItems(await api.listWorkflows()); }
  useEffect(() => { load().catch(console.error); }, []);

  async function save() {
    const saved = await api.saveWorkflow({ id: id || undefined, name, description, definition: JSON.parse(definition) });
    setId(saved.id);
    await load();
  }

  function pick(w: WorkflowDef) {
    setId(w.id);
    setName(w.name);
    setDescription(w.description);
    setDefinition(JSON.stringify(w.definition, null, 2));
  }

  async function run() {
    if (!id) return;
    const inputs = JSON.parse(runInput || "{}");
    const out = await api.runWorkflow(id, inputs);
    setResult(JSON.stringify(out.result, null, 2));
  }

  async function preview() {
    await run();
  }

  return (
    <div>
      <div className="card">
        <h3>Workflow Editor</h3>
        <div className="row">
          <input value={name} onChange={(e) => setName(e.target.value)} />
          <input value={description} onChange={(e) => setDescription(e.target.value)} style={{ minWidth: 380 }} />
          <button onClick={save}>Save</button>
        </div>
        <textarea style={{ width: "100%", minHeight: 220, marginTop: 8 }} value={definition} onChange={(e) => setDefinition(e.target.value)} />
      </div>
      <div className="card">
        <h3>Run Workflow</h3>
        <textarea style={{ width: "100%", minHeight: 100 }} value={runInput} onChange={(e) => setRunInput(e.target.value)} />
        <div className="row" style={{ marginTop: 8 }}>
          <button onClick={run}>Run Selected</button>
          <button className="secondary" onClick={preview}>Preview Run</button>
        </div>
        <pre>{result}</pre>
      </div>
      <div className="card">
        <h3>Saved Workflows</h3>
        {items.map((w) => (
          <div className="audit-row" key={w.id}>
            <strong>{w.name}</strong> - {w.description}
            <div className="small">{w.id}</div>
            <button className="secondary" onClick={() => pick(w)}>Load</button>
          </div>
        ))}
      </div>
    </div>
  );
}
