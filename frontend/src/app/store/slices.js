import { createSlice } from "@reduxjs/toolkit"

const organizationSlice = createSlice({
  name: "organization",
  initialState: { selectedId: null },
  reducers: {
    organizationSelected: (state, action) => { state.selectedId = action.payload },
    organizationCleared: (state) => { state.selectedId = null },
  },
})

const authSlice = createSlice({
  name: "auth",
  initialState: { user: null, token: null },
  reducers: {
    signedIn: (state, action) => Object.assign(state, action.payload),
    signedOut: (state) => { state.user = null; state.token = null },
  },
})

const syncSlice = createSlice({
  name: "sync",
  initialState: { state: "checking", pending: 0, failed: 0, conflicts: 0, lastSyncedAt: null, message: null },
  reducers: {
    connectivityChanged: (state, action) => { state.state = action.payload ? "online" : "offline" },
    syncStateChanged: (state, action) => Object.assign(state, action.payload),
  },
})

export const { organizationSelected, organizationCleared } = organizationSlice.actions
export const { signedIn, signedOut } = authSlice.actions
export const { connectivityChanged, syncStateChanged } = syncSlice.actions
export const reducers = {
  organization: organizationSlice.reducer,
  auth: authSlice.reducer,
  sync: syncSlice.reducer,
}
