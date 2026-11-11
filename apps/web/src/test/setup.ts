import "@testing-library/jest-dom/vitest"
import { cleanup } from "@testing-library/react"
import { afterEach } from "vitest"
import { resetMemoryStore } from "@/lib/mock-api"

afterEach(() => {
  cleanup()
  resetMemoryStore()
})
