export const PARTICLE_COLORS = {
  muon: "#ff6b9d",
  electron: "#5ce1e6",
  positron: "#f3a74f",
  proton: "#73b4ff",
  photon: "#ffe566",
  pion: "#b0ff9b",
  kaon: "#d4a5ff",
  "pi+": "#b0ff9b",
  "pi-": "#b0ff9b",
  default: "#8aa3c2"
};

export const particleColor = (type) => PARTICLE_COLORS[type] || PARTICLE_COLORS.default;
