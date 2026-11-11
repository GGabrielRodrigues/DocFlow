import { useState } from "react"
import { AppShell } from "@/app/AppShell"
import { ErrorBoundary } from "@/components/ErrorBoundary"
import { ApiProblemError, notifyGlobalApiError } from "@/lib/http-client"
import { QueryClient, QueryClientProvider } from "@/lib/query"
import { BrowserRouter } from "@/lib/router"

export function createAppQueryClient(): QueryClient {
  return new QueryClient({
    onError: (error) => {
      if (error instanceof ApiProblemError) {
        notifyGlobalApiError(error)
        return
      }
      const message =
        error instanceof Error
          ? error.message
          : "Ocorreu um erro inesperado ao processar a operação."
      notifyGlobalApiError(
        new ApiProblemError({
          type: "https://api.docflow.com.br/errors/client-error",
          title: "Erro na aplicação",
          status: 500,
          detail: message,
        }),
      )
    },
  })
}

export function App() {
  const [queryClient] = useState(createAppQueryClient)

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AppShell />
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App
