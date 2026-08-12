import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload } from 'lucide-react'
import { toast } from 'sonner'

import { LogoMark } from '@/components/Logo'
import { PromptSuggestion } from '@/components/ui/prompt-suggestion'
import { useThreads } from '@/hooks/useThreads'
import { EXAMPLE_QUESTIONS } from '@/lib/suggestions'
import { env } from '@/lib/env'

export function ChatEmptyPage() {
  const navigate = useNavigate()
  const { createNewThread, refreshThreads } = useThreads()
  const [isStarting, setIsStarting] = useState(false)

  async function startConversation(prompt?: string) {
    if (isStarting) return
    setIsStarting(true)
    try {
      const id = await createNewThread()
      navigate(`/chats/${id}`, {
        state: prompt ? { initialPrompt: prompt } : undefined,
      })
    } catch {
      toast.error('Failed to create new chat')
    } finally {
      setIsStarting(false)
    }
  }

  async function handleFileUpload(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    toast.info(`Uploading ${file.name}…`)
    try {
      // 1. Perform upload directly to backend
      const res = await fetch(`${env.apiBaseUrl}/api/documents/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || 'Upload failed')
      }

      const data = await res.json()
      const docName = data.company_name || file.name

      // 2. Set active doc name in localStorage BEFORE thread creation/navigation
      localStorage.setItem('activeDocName', docName)

      // 3. Create thread directly with the uploaded document name
      const { createThread } = await import('@/lib/chat')
      const thread = await createThread(docName)
      await refreshThreads()

      toast.success(`Uploaded ${docName} successfully!`)

      // 4. Navigate directly to new thread with initial prompt
      navigate(`/chats/${thread.id}`, {
        state: { initialPrompt: 'Summarize the key points of my uploaded document.' },
      })
    } catch (err) {
      const msg = err instanceof Error ? err.message : `Failed to upload ${file.name}`
      toast.error(msg)
    }
  }

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-8 p-6">
      <div className="flex flex-col items-center gap-4 text-center">
        <LogoMark className="size-12" />
        <div className="space-y-1.5">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Paper Craft & Translator
          </h1>
          <p className="max-w-md text-sm text-muted-foreground">
            Upload any document (PDF, TXT, Markdown) to ask questions, generate summaries, and translate answers into 15+ languages.
          </p>
        </div>

        <label className="mt-2 flex cursor-pointer items-center justify-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-medium text-primary-foreground shadow-md hover:bg-primary/90">
          <Upload className="size-4" />
          Upload PDF / TXT Document
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

      <div className="grid w-full max-w-xl gap-2 sm:grid-cols-2">
        {EXAMPLE_QUESTIONS.map((question) => (
          <PromptSuggestion
            key={question}
            variant="outline"
            size="default"
            className="h-auto justify-start rounded-xl px-4 py-3 text-left text-sm font-normal whitespace-normal"
            disabled={isStarting}
            onClick={() => void startConversation(question)}
          >
            {question}
          </PromptSuggestion>
        ))}
      </div>
    </div>
  )
}
