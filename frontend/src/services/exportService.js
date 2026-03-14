const downloadBlob = (blob, filename) => {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 250);
};

const toCsv = (rows) => {
  if (!rows.length) {
    return "";
  }
  const headers = [...new Set(rows.flatMap((row) => Object.keys(row)))];
  const lines = [
    headers.join(","),
    ...rows.map((row) =>
      headers
        .map((header) => JSON.stringify(row[header] ?? ""))
        .join(",")
    ),
  ];
  return lines.join("\n");
};

export const exportEvents = (events, format = "json") => {
  const rows = events ?? [];
  const payload =
    format === "csv"
      ? new Blob([toCsv(rows)], { type: "text/csv;charset=utf-8" })
      : new Blob([JSON.stringify(rows, null, 2)], { type: "application/json;charset=utf-8" });
  downloadBlob(payload, `collision-events.${format === "csv" ? "csv" : "json"}`);
};

export const exportTracks = (tracks, format = "json") => {
  const rows = tracks ?? [];
  const payload =
    format === "csv"
      ? new Blob(
          [
            toCsv(
              rows.map((track) => ({
                particle_id: track.particle_id,
                type: track.type,
                x: track.position?.x ?? 0,
                y: track.position?.y ?? 0,
                z: track.position?.z ?? 0,
              }))
            ),
          ],
          { type: "text/csv;charset=utf-8" }
        )
      : new Blob([JSON.stringify(rows, null, 2)], { type: "application/json;charset=utf-8" });
  downloadBlob(payload, `particle-tracks.${format === "csv" ? "csv" : "json"}`);
};

export const exportExperiment = (experiment, format = "json") => {
  const payload =
    format === "csv"
      ? new Blob([toCsv([experiment ?? {}])], { type: "text/csv;charset=utf-8" })
      : new Blob([JSON.stringify(experiment ?? {}, null, 2)], { type: "application/json;charset=utf-8" });
  downloadBlob(payload, `experiment-run.${format === "csv" ? "csv" : "json"}`);
};

export const exportChart = async (node, filename = "analytics-chart.png") => {
  if (!node) {
    return;
  }
  if (node instanceof HTMLCanvasElement) {
    const anchor = document.createElement("a");
    anchor.href = node.toDataURL("image/png");
    anchor.download = filename;
    anchor.click();
    return;
  }
  if (!(node instanceof SVGElement)) {
    throw new Error("chart export supports canvas or svg nodes only");
  }
  const serialized = new XMLSerializer().serializeToString(node);
  const svgBlob = new Blob([serialized], { type: "image/svg+xml;charset=utf-8" });
  const svgUrl = URL.createObjectURL(svgBlob);
  const image = new Image();
  image.src = svgUrl;
  await image.decode();
  const canvas = document.createElement("canvas");
  canvas.width = node.viewBox.baseVal.width || node.clientWidth || 800;
  canvas.height = node.viewBox.baseVal.height || node.clientHeight || 600;
  const context = canvas.getContext("2d");
  context?.drawImage(image, 0, 0, canvas.width, canvas.height);
  URL.revokeObjectURL(svgUrl);
  const anchor = document.createElement("a");
  anchor.href = canvas.toDataURL("image/png");
  anchor.download = filename;
  anchor.click();
};
