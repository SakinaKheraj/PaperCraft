import { useState } from 'react'
import { useParams } from 'react-router-dom'
import type { ChatStatus } from 'ai'
import { ArrowUp, Square } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  PromptInput,
  PromptInputAction,
  PromptInputActions,
  PromptInputTextarea,
} from '@/components/ui/prompt-input'
import { useThreads } from '@/hooks/useThreads'

type ChatInputProps = {
  status: ChatStatus
  onSend: (text: string) => void
  onStop: () => void
}

function getActiveDocDisplayName(title: string | undefined): string {
  if (!title) return ''
  const trimmed = title.trim()
  if (!trimmed || trimmed === 'New chat' || trimmed === 'New conversation' || trimmed === 'Untitled') {
    return ''
  }
  if (/^uploading\s+/i.test(trimmed)) {
    return trimmed
      .replace(/^uploading\s+/i, '')
      .replace(/\.\.\.$/, '')
      .replace(/\.(pdf|txt|md|docx?)$/i, '')
      .replace(/[_\-]+/g, ' ')
      .trim()
  }
  return trimmed
}

export function ChatInput({ status, onSend, onStop }: ChatInputProps) {
  const [input, setInput] = useState('')
  const { threadId } = useParams()
  const { threads } = useThreads()
  const isBusy = status === 'submitted' || status === 'streaming'
  const activeThread = threads.find((t) => t.id === threadId)
  const activeDocName = getActiveDocDisplayName(activeThread?.title)

  function submit() {
    const text = input.trim()
    if (!text || isBusy) return
    onSend(text)
    setInput('')
  }

  return (
    <div className="bg-background px-4 pb-4">
      <div className="mx-auto w-full max-w-3xl">
        {activeDocName ? (
          <div className="mb-2 flex items-center gap-2 rounded-xl border border-primary/20 bg-primary/10 px-3 py-1.5 text-xs text-primary shadow-xs">
            <span className="font-semibold">📄 Active Document:</span>
            <span className="truncate font-medium">{activeDocName}</span>
          </div>
        ) : null}
        <PromptInput
          value={input}
          onValueChange={setInput}
          isLoading={isBusy}
          onSubmit={submit}
          className="rounded-2xl"
        >
          <PromptInputTextarea placeholder="Ask any question about your uploaded document…" />
          <PromptInputActions className="justify-end pt-1">
            {isBusy ? (
              <PromptInputAction tooltip="Stop">
                <Button type="button" size="icon" className="rounded-full" onClick={onStop}>
                  <Square className="size-4 fill-current" />
                </Button>
              </PromptInputAction>
            ) : (
              <PromptInputAction tooltip="Send">
                <Button
                  type="button"
                  size="icon"
                  className="rounded-full"
                  onClick={submit}
                  disabled={input.trim() === ''}
                  aria-label="Send message"
                >
                  <ArrowUp className="size-4" />
                </Button>
              </PromptInputAction>
            )}
          </PromptInputActions>
        </PromptInput>
        <p className="mt-2 text-center text-xs text-muted-foreground">
          Answers are generated from your uploaded document. Use the Translate button on any answer for multi-lingual translation.
        </p>
      </div>
    </div>
  )
}
