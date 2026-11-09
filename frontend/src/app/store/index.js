import { configureStore } from "@reduxjs/toolkit"
import { daymarkApi } from "./api"
import { reducers } from "./slices"

export const store = configureStore({ reducer: { ...reducers, [daymarkApi.reducerPath]: daymarkApi.reducer }, middleware: (getDefaultMiddleware) => getDefaultMiddleware().concat(daymarkApi.middleware) })

