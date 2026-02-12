import { useEffect, useState } from "react";
import { api, PermissionType } from "../api";

const perms: PermissionType[] = [
  "filesystem.read",
  "filesystem.write",
  "web.search",
  "screen.capture",
  "clipboard.read",
  "clipboard.write",
  "process.run"
];

export function PermissionsPage() {
  const [grants, setGrants] = useState<any[]>([]);
  const [permission, setPermission] = useState<PermissionType>("filesystem.read");
  const [scope, setScope] = useState<"once" | "session" | "always">("once");
  const [paths, setPaths] = useState("C:\\Users\\mike\\OneDrive\\Desktop\\AIs.etc\\NeroAI");
  const [status, setStatus] = useState("");

  async function load() {
    setGrants(await api.listPermissions());
  }

  useEffect(() => {
    load().catch((e) => setStatus(String(e)));
  }, []);

  async function grant() {
    await api.grantPermission({ permission, scope, allowed_paths: paths.split(";").map((x) => x.trim()).filter(Boolean) });
    setStatus("Permission granted.");
    await load();
  }

  async function revoke(p: PermissionType) {
    await api.revokePermission(p);
    await load();
  }

  return (
    <div>
      <div className="card">
        <h3>Grant Permission</h3>
        <div className="row">
          <select value={permission} onChange={(e) => setPermission(e.target.value as PermissionType)}>{perms.map((p) => <option key={p}>{p}</option>)}</select>
          <select value={scope} onChange={(e) => setScope(e.target.value as any)}>
            <option value="once">once</option>
            <option value="session">session</option>
            <option value="always">always</option>
          </select>
          <input style={{ minWidth: 450 }} value={paths} onChange={(e) => setPaths(e.target.value)} placeholder="Path scopes separated by ;" />
          <button onClick={grant}>Grant</button>
        </div>
        <p className="small">Default should be once. File permissions are path-scoped and enforced by policy guard.</p>
        {status && <p>{status}</p>}
      </div>
      <div className="card">
        <h3>Current Grants</h3>
        {grants.map((g, i) => (
          <div className="audit-row" key={i}>
            <div><span className="code">{g.permission}</span> | {g.scope} | session: {g.session_id ?? "global"}</div>
            <div className="small">paths: {(g.allowed_paths ?? []).join(", ") || "-"}</div>
            <button className="danger" onClick={() => revoke(g.permission)}>Revoke</button>
          </div>
        ))}
      </div>
    </div>
  );
}
