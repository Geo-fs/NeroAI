import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App";
import { ThinkBoxApp } from "./ThinkBoxApp";
import "./styles.css";

const params = new URLSearchParams(window.location.search);
const isThinkBox = params.get("thinkbox") === "1";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    {isThinkBox ? <ThinkBoxApp /> : <App />}
  </React.StrictMode>
);
