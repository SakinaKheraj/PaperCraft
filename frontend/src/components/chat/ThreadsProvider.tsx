import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { ThreadsContext } from '@/contexts/threads-context'
import { ApiError } from '@/lib/http'
import { createThread, deleteThread as deleteThreadRequest, listThreads } from '@/lib/chat'

export function ThreadsProvider({ children }: { children: ReactNode }) {
  const [threads, setThreads] = useState<Awaited<ReturnType<typeof listThreads>>>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refreshThreads = useCallback(async () => {
    setError(null)
    try {
      const nextThreads = await listThreads()
      setThreads(nextThreads)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Could not load conversations.')
      }
    }
  }, [])

  useEffect(() => {
    let mounted = true

    async function load() {
      setIsLoading(true)
      await refreshThreads()
      if (mounted) {
        setIsLoading(false)
      }
    }

    void load()

    return () => {
      mounted = false
    }
  }, [refreshThreads])

  const createNewThread = useCallback(async () => {
    const thread = await createThread()
    await refreshThreads()
    return thread.id
  }, [refreshThreads])

  const deleteThread = useCallback(async (threadId: string) => {
    await deleteThreadRequest(threadId)
    setThreads((current) => current.filter((thread) => thread.id !== threadId))
  }, [])

  const updateThreadTitleAction = useCallback(async (threadId: string, title: string) => {
    const { updateThreadTitle } = await import('@/lib/chat')
    await updateThreadTitle(threadId, title)
    setThreads((current) =>
      current.map((thread) => (thread.id === threadId ? { ...thread, title } : thread)),
    )
  }, [])

  const value = useMemo(
    () => ({
      threads,
      isLoading,
      error,
      refreshThreads,
      createNewThread,
      deleteThread,
      updateThreadTitle: updateThreadTitleAction,
    }),
    [threads, isLoading, error, refreshThreads, createNewThread, deleteThread, updateThreadTitleAction],
  )

  return <ThreadsContext.Provider value={value}>{children}</ThreadsContext.Provider>
}
