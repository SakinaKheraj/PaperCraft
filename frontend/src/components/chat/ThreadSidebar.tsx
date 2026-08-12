import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Loader2, Plus, Trash2, Upload } from 'lucide-react'
import { env } from '@/lib/env'
import { toast } from 'sonner'

import { Logo } from '@/components/Logo'
import { UserMenu } from '@/components/chat/UserMenu'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogMedia,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSkeleton,
  useSidebar,
} from '@/components/ui/sidebar'
import { useThreads } from '@/hooks/useThreads'
import type { ThreadSummary } from '@/lib/chat'
import { groupByRecency } from '@/lib/format'

export function ThreadSidebar() {
  const navigate = useNavigate()
  const { threadId } = useParams()
  const { setOpenMobile, isMobile } = useSidebar()
  const { threads, isLoading, error, createNewThread, deleteThread, refreshThreads } = useThreads()
  const [isCreating, setIsCreating] = useState(false)
  const [threadToDelete, setThreadToDelete] = useState<ThreadSummary | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const groups = groupByRecency(threads, (thread) => thread.updatedAt)

  async function handleNewChat() {
    setIsCreating(true)
    try {
      const id = await createNewThread()
      navigate(`/chats/${id}`)
      if (isMobile) setOpenMobile(false)
    } finally {
      setIsCreating(false)
    }
  }

  async function handleFileUpload(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    toast.info(`Uploading ${file.name}…`)
    let newThreadId: string | null = null
    try {
      // 1. Create a new thread named "Uploading..." immediately
      const tempTitle = `Uploading ${file.name}...`
      const { createThread } = await import('@/lib/chat')
      const thread = await createThread(tempTitle)
      newThreadId = thread.id
      await refreshThreads()

      // Redirect immediately to show the chat page
      navigate(`/chats/${newThreadId}`)
      if (isMobile) setOpenMobile(false)

      // 2. Perform the upload directly to backend
      const res = await fetch(`${env.apiBaseUrl}/api/documents/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || 'Upload failed')
      }

      const data = await res.json()
      localStorage.setItem('activeDocName', data.company_name)
      toast.success(`Uploaded ${data.company_name}!`)

      // Rename the thread to the document name
      const { updateThreadTitle } = await import('@/lib/chat')
      await updateThreadTitle(newThreadId, data.company_name)
      await refreshThreads()

      // Automatically generate a summary to start the chat!
      navigate(`/chats/${newThreadId}`, {
        state: { initialPrompt: 'Summarize the key points of my uploaded document.' },
      })
    } catch (err) {
      const msg = err instanceof Error ? err.message : `Failed to upload ${file.name}`
      toast.error(msg)
      if (newThreadId) {
        try {
          const { updateThreadTitle } = await import('@/lib/chat')
          await updateThreadTitle(newThreadId, 'Upload failed')
          await refreshThreads()
        } catch {
          // Ignore
        }
      }
    }
  }

  async function handleDeleteThread() {
    if (!threadToDelete) return

    setIsDeleting(true)
    try {
      await deleteThread(threadToDelete.id)
      toast.success('Conversation deleted')

      if (threadToDelete.id === threadId) {
        navigate('/chats', { replace: true })
      }

      if (isMobile) setOpenMobile(false)
      setThreadToDelete(null)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Could not delete conversation.'
      toast.error(message)
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <>
      <Sidebar>
        <SidebarHeader className="gap-3 p-3">
          <Logo className="px-1 py-1" />
          <div className="flex flex-col gap-2">
            <Button
              variant="outline"
              className="w-full justify-start gap-2 border-dashed bg-background/50 text-muted-foreground shadow-none hover:bg-muted/50 hover:text-foreground"
              onClick={() => void handleNewChat()}
              disabled={isCreating}
            >
              <Plus className="size-4" />
              {isCreating ? 'Creating…' : 'New chat'}
            </Button>
            <label className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-md border border-primary/30 bg-primary/10 px-3 py-2 text-xs font-medium text-primary hover:bg-primary/20">
              <Upload className="size-3.5" />
              Upload PDF / TXT
              <input
                type="file"
                accept=".pdf,.txt,.md"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) void handleFileUpload(file)
                }}
              />
            </label>
          </div>
        </SidebarHeader>

        <SidebarContent className="px-1">

          {isLoading ? (
            <SidebarGroup>
              <SidebarGroupContent>
                <SidebarMenu>
                  {Array.from({ length: 5 }).map((_, index) => (
                    <SidebarMenuItem key={index}>
                      <SidebarMenuSkeleton />
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          ) : null}

          {!isLoading && error ? (
            <p className="px-3 py-2 text-sm text-destructive" role="alert">
              {error}
            </p>
          ) : null}

          {!isLoading && !error && threads.length === 0 ? (
            <p className="px-3 py-2 text-sm text-muted-foreground">No conversations yet.</p>
          ) : null}

          {!isLoading && !error
            ? groups.map((group) => (
                <SidebarGroup key={group.label}>
                  <SidebarGroupLabel>{group.label}</SidebarGroupLabel>
                  <SidebarGroupContent>
                    <SidebarMenu>
                      {group.items.map((thread) => (
                        <SidebarMenuItem key={thread.id}>
                          <SidebarMenuButton
                            asChild
                            isActive={thread.id === threadId}
                            tooltip={thread.title}
                          >
                            <Link
                              to={`/chats/${thread.id}`}
                              onClick={() => {
                                if (isMobile) setOpenMobile(false)
                              }}
                            >
                              <span className="truncate">{thread.title}</span>
                            </Link>
                          </SidebarMenuButton>
                          <SidebarMenuAction
                            showOnHover
                            aria-label={`Delete conversation: ${thread.title}`}
                            title="Delete conversation"
                            className="text-muted-foreground hover:bg-destructive/10 hover:text-destructive focus-visible:text-destructive"
                            disabled={isDeleting}
                            onClick={(event) => {
                              event.preventDefault()
                              event.stopPropagation()
                              setThreadToDelete(thread)
                            }}
                          >
                            {isDeleting && threadToDelete?.id === thread.id ? (
                              <Loader2 className="animate-spin" />
                            ) : (
                              <Trash2 />
                            )}
                          </SidebarMenuAction>
                        </SidebarMenuItem>
                      ))}
                    </SidebarMenu>
                  </SidebarGroupContent>
                </SidebarGroup>
              ))
            : null}
        </SidebarContent>

        <SidebarFooter>
          <UserMenu />
        </SidebarFooter>
      </Sidebar>

      <AlertDialog
        open={threadToDelete !== null}
        onOpenChange={(open) => {
          if (!open && !isDeleting) setThreadToDelete(null)
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogMedia className="bg-destructive/10 text-destructive">
              <Trash2 />
            </AlertDialogMedia>
            <AlertDialogTitle>Delete this conversation?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete “{threadToDelete?.title}” and its message history.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              disabled={isDeleting}
              onClick={(event) => {
                event.preventDefault()
                void handleDeleteThread()
              }}
            >
              {isDeleting ? 'Deleting…' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}


