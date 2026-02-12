const { spawn } = require("child_process");

const env = { ...process.env, VITE_DEV_SERVER_URL: "http://localhost:5173" };
delete env.ELECTRON_RUN_AS_NODE;

const electronBinary = require("electron");
const child = spawn(electronBinary, ["."], {
  cwd: process.cwd(),
  stdio: "inherit",
  env,
  shell: false,
});

child.on("exit", (code) => {
  process.exit(code ?? 0);
});
