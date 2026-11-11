import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'

export type QueryKey = readonly unknown[]

export interface QueryClientConfig {
  onError?: (error: unknown) => void
}

interface CacheEntry {
  data: unknown
  updatedAt: number
}

export class QueryClient {
  private cache = new Map<string, CacheEntry>()
  private listeners = new Set<(keyPrefix?: string) => void>()
  readonly onError?: (error: unknown) => void

  constructor(config: QueryClientConfig = {}) {
    this.onError = config.onError
  }

  static serializeKey(queryKey: QueryKey): string {
    return JSON.stringify(queryKey)
  }

  getQueryData<T>(queryKey: QueryKey): T | undefined {
    const entry = this.cache.get(QueryClient.serializeKey(queryKey))
    return entry?.data as T | undefined
  }

  setQueryData<T>(queryKey: QueryKey, data: T): void {
    const serialized = QueryClient.serializeKey(queryKey)
    this.cache.set(serialized, { data, updatedAt: Date.now() })
    this.notify(serialized)
  }

  invalidateQueries(filter?: { queryKey?: QueryKey }): void {
    if (!filter?.queryKey) {
      this.cache.clear()
      this.notify()
      return
    }
    const prefix = JSON.stringify(filter.queryKey).slice(0, -1)
    for (const key of this.cache.keys()) {
      if (key.startsWith(prefix)) {
        this.cache.delete(key)
      }
    }
    this.notify(prefix)
  }

  clear(): void {
    this.cache.clear()
    this.notify()
  }

  subscribe(listener: (keyPrefix?: string) => void): () => void {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }

  private notify(keyPrefix?: string): void {
    for (const listener of this.listeners) {
      listener(keyPrefix)
    }
  }
}

const QueryClientContext = createContext<QueryClient | null>(null)

export function QueryClientProvider({
  client,
  children,
}: {
  client: QueryClient
  children: ReactNode
}) {
  return <QueryClientContext.Provider value={client}>{children}</QueryClientContext.Provider>
}

export function useQueryClient(): QueryClient {
  const client = useContext(QueryClientContext)
  if (!client) {
    throw new Error('useQueryClient deve ser utilizado dentro de um QueryClientProvider.')
  }
  return client
}

export interface UseQueryOptions<TData> {
  queryKey: QueryKey
  queryFn: () => Promise<TData> | TData
  initialData?: TData
  enabled?: boolean
}

export interface UseQueryResult<TData> {
  data: TData
  isLoading: boolean
  error: unknown
  refetch: () => Promise<TData>
}

export function useQuery<TData>({
  queryKey,
  queryFn,
  initialData,
  enabled = true,
}: UseQueryOptions<TData>): UseQueryResult<TData> {
  const client = useQueryClient()
  const serializedKey = useMemo(() => QueryClient.serializeKey(queryKey), [queryKey])
  const queryFnRef = useRef(queryFn)
  queryFnRef.current = queryFn

  const [version, setVersion] = useState(0)
  const [isLoading, setIsLoading] = useState<boolean>(() => {
    return enabled && client.getQueryData<TData>(queryKey) === undefined && initialData === undefined
  })
  const [error, setError] = useState<unknown>(null)

  const execute = useCallback(async (): Promise<TData> => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await queryFnRef.current()
      client.setQueryData(queryKey, result)
      return result
    } catch (err) {
      setError(err)
      client.onError?.(err)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [client, queryKey])

  useEffect(() => {
    if (!enabled) return
    const cached = client.getQueryData<TData>(queryKey)
    if (cached === undefined) {
      void execute().catch(() => undefined)
    }
  }, [client, enabled, execute, queryKey, serializedKey, version])

  useEffect(() => {
    return client.subscribe((keyPrefix) => {
      if (!keyPrefix || serializedKey.startsWith(keyPrefix)) {
        setVersion((v) => v + 1)
      }
    })
  }, [client, serializedKey])

  const cachedData = client.getQueryData<TData>(queryKey)
  const resolvedData = (cachedData !== undefined ? cachedData : initialData) as TData

  return {
    data: resolvedData,
    isLoading,
    error,
    refetch: execute,
  }
}

export interface UseMutationOptions<TData, TVariables> {
  mutationFn: (variables: TVariables) => Promise<TData> | TData
  onSuccess?: (data: TData, variables: TVariables) => Promise<void> | void
  onError?: (error: unknown, variables: TVariables) => void
}

export interface UseMutationResult<TData, TVariables> {
  mutate: (variables: TVariables) => void
  mutateAsync: (variables: TVariables) => Promise<TData>
  isPending: boolean
  error: unknown
}

export function useMutation<TData, TVariables = void>({
  mutationFn,
  onSuccess,
  onError,
}: UseMutationOptions<TData, TVariables>): UseMutationResult<TData, TVariables> {
  const client = useQueryClient()
  const [isPending, setIsPending] = useState(false)
  const [error, setError] = useState<unknown>(null)

  const mutateAsync = useCallback(
    async (variables: TVariables): Promise<TData> => {
      setIsPending(true)
      setError(null)
      try {
        const result = await mutationFn(variables)
        await onSuccess?.(result, variables)
        return result
      } catch (err) {
        setError(err)
        onError?.(err, variables)
        client.onError?.(err)
        throw err
      } finally {
        setIsPending(false)
      }
    },
    [client, mutationFn, onError, onSuccess],
  )

  const mutate = useCallback(
    (variables: TVariables) => {
      void mutateAsync(variables).catch(() => undefined)
    },
    [mutateAsync],
  )

  return {
    mutate,
    mutateAsync,
    isPending,
    error,
  }
}
