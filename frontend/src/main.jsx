import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App.jsx";
import { AssetProvider } from "@assets";
import "@assets/styles.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AssetProvider bundles={["core"]} debug={false}>
      <App />
    </AssetProvider>
  </React.StrictMode>
);
