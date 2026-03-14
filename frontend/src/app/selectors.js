export const selectSelectedEvent = (state) => {
  const selectedId = state.eventStream.selectedEventId;
  if (selectedId == null) {
    return null;
  }
  return state.eventStream.events.find((event) => event.event_id === selectedId) ?? null;
};

export const selectPayload = (state) => state.simulationState.payload;

export const selectHealthLabel = (state) => {
  if (state.simulationState.health === "ok") {
    return "Backend: healthy";
  }
  if (state.simulationState.health === "error") {
    return "Backend: unavailable";
  }
  return "Backend: checking";
};
