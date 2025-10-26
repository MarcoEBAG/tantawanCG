import React from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import AppRouter from "./routes/AppRouter";

const root = createRoot(document.getElementById("root")!);
root.render(
  <React.StrictMode>
    <AppRouter />
  </React.StrictMode>
);
