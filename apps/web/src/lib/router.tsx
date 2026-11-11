import {
  Children,
  createContext,
  isValidElement,
  ReactElement,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'

export interface LocationState {
  pathname: string
}

export interface NavigateOptions {
  replace?: boolean
}

export type NavigateFunction = (to: string, options?: NavigateOptions) => void

interface RouterContextValue {
  location: LocationState
  navigate: NavigateFunction
}

const RouterContext = createContext<RouterContextValue | null>(null)

function normalizePath(path: string): string {
  if (!path) return '/'
  const clean = path.split('?')[0]?.split('#')[0] || '/'
  if (clean.length > 1 && clean.endsWith('/')) {
    return clean.slice(0, -1)
  }
  return clean.startsWith('/') ? clean : `/${clean}`
}

export function BrowserRouter({ children }: { children: ReactNode }) {
  const [pathname, setPathname] = useState<string>(() =>
    normalizePath(typeof window !== 'undefined' ? window.location.pathname : '/'),
  )

  useEffect(() => {
    const handlePopState = () => {
      setPathname(normalizePath(window.location.pathname))
    }
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  const navigate = useCallback<NavigateFunction>((to, options) => {
    const target = normalizePath(to)
    if (typeof window !== 'undefined') {
      if (options?.replace) {
        window.history.replaceState(null, '', target)
      } else {
        window.history.pushState(null, '', target)
      }
    }
    setPathname(target)
  }, [])

  const value = useMemo(
    () => ({ location: { pathname }, navigate }),
    [pathname, navigate],
  )

  return <RouterContext.Provider value={value}>{children}</RouterContext.Provider>
}

export function MemoryRouter({
  initialEntries = ['/'],
  children,
}: {
  initialEntries?: string[]
  children: ReactNode
}) {
  const [pathname, setPathname] = useState<string>(() =>
    normalizePath(initialEntries[initialEntries.length - 1] ?? '/'),
  )

  const navigate = useCallback<NavigateFunction>((to) => {
    setPathname(normalizePath(to))
  }, [])

  const value = useMemo(
    () => ({ location: { pathname }, navigate }),
    [pathname, navigate],
  )

  return <RouterContext.Provider value={value}>{children}</RouterContext.Provider>
}

export function useLocation(): LocationState {
  const context = useContext(RouterContext)
  if (!context) {
    throw new Error('useLocation deve ser utilizado dentro de um Router.')
  }
  return context.location
}

export function useNavigate(): NavigateFunction {
  const context = useContext(RouterContext)
  if (!context) {
    throw new Error('useNavigate deve ser utilizado dentro de um Router.')
  }
  return context.navigate
}

export interface RouteProps {
  path: string
  element: ReactNode
}

export function Route(_props: RouteProps): ReactElement | null {
  return null
}

export function Routes({ children }: { children: ReactNode }) {
  const { pathname } = useLocation()
  let fallbackElement: ReactNode = null

  const childArray = Children.toArray(children)
  for (const child of childArray) {
    if (!isValidElement<RouteProps>(child)) continue
    const routePath = child.props.path
    if (routePath === '*') {
      fallbackElement = child.props.element
      continue
    }
    if (normalizePath(routePath) === pathname) {
      return <>{child.props.element}</>
    }
  }

  return <>{fallbackElement}</>
}

export function Navigate({ to, replace = false }: { to: string; replace?: boolean }) {
  const navigate = useNavigate()
  useEffect(() => {
    navigate(to, { replace })
  }, [navigate, replace, to])
  return null
}
