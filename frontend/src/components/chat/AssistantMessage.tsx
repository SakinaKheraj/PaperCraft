import { useState } from 'react'
import type { UIMessage } from 'ai'
import { Check, Copy } from 'lucide-react'
import { env } from '@/lib/env'

import { AssistantMarkdown } from '@/components/chat/AssistantMarkdown'
import { CitationChip } from '@/components/chat/CitationChip'
import { Button } from '@/components/ui/button'
import {
  citationsFromMessage,
  textFromMessage,
  type CitationPayload,
} from '@/lib/citations'

type AssistantMessageProps = {
  message: UIMessage
  selectedCitationIndex: number | null
  onSelectCitation: (citation: CitationPayload) => void
  isStreaming?: boolean
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon-sm"
      className="text-muted-foreground"
      onClick={() => void handleCopy()}
      aria-label="Copy answer"
    >
      {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
    </Button>
  )
}

function TranslateButton({ text }: { text: string }) {
  const [isTranslating, setIsTranslating] = useState(false)
  const [translatedText, setTranslatedText] = useState<string | null>(null)
  const [selectedLang, setSelectedLang] = useState('Spanish')

  async function handleTranslate(lang: string) {
    setSelectedLang(lang)
    setIsTranslating(true)
    try {
      const res = await fetch(`${env.apiBaseUrl}/api/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, target_language: lang }),
      })
      if (!res.ok) throw new Error('Translation failed')
      const data = await res.json()
      setTranslatedText(data.translated_text)
    } catch {
      // Ignore
    } finally {
      setIsTranslating(false)
    }
  }

  return (
    <div className="flex flex-col gap-2 pt-1">
      <div className="flex items-center gap-2">
        <CopyButton text={translatedText || text} />
        <select
          value={selectedLang}
          onChange={(e) => void handleTranslate(e.target.value)}
          className="h-7 rounded-md border border-input bg-background px-2 text-xs font-medium text-foreground hover:bg-accent focus:outline-none"
        >
          <option value="Spanish">Spanish 🇪🇸</option>
          <option value="French">French 🇫🇷</option>
          <option value="German">German 🇩🇪</option>
          <option value="Hindi">Hindi 🇮🇳</option>
          <option value="Japanese">Japanese 🇯🇵</option>
          <option value="Chinese">Chinese 🇨🇳</option>
          <option value="Italian">Italian 🇮🇹</option>
          <option value="Portuguese">Portuguese 🇵🇹</option>
        </select>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="h-7 px-2 text-xs"
          disabled={isTranslating}
          onClick={() => void handleTranslate(selectedLang)}
        >
          {isTranslating ? 'Translating…' : 'Translate'}
        </Button>
        {translatedText && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-xs text-muted-foreground"
            onClick={() => setTranslatedText(null)}
          >
            Show Original
          </Button>
        )}
      </div>

      {translatedText && (
        <div className="rounded-lg border border-primary/20 bg-primary/5 p-3 text-sm text-foreground">
          <p className="mb-1 text-xs font-semibold text-primary">Translated to {selectedLang}:</p>
          <div className="whitespace-pre-wrap">{translatedText}</div>
        </div>
      )}
    </div>
  )
}

export function AssistantMessage({
  message,
  selectedCitationIndex,
  onSelectCitation,
  isStreaming = false,
}: AssistantMessageProps) {
  const text = textFromMessage(message)
  const citations = citationsFromMessage(message)
  const hasNoEvidence = !isStreaming && text.length > 0 && citations.length === 0

  return (
    <div className="min-w-0 space-y-3">
      {text ? (
        <AssistantMarkdown
          text={text}
          citations={citations}
          selectedCitationIndex={selectedCitationIndex}
          onSelectCitation={onSelectCitation}
        />
      ) : null}

      {isStreaming && text ? (
        <span className="inline-block h-4 w-2 translate-y-0.5 animate-pulse rounded-sm bg-foreground" />
      ) : null}

      {citations.length > 0 ? (
        <div className="flex flex-wrap gap-1.5 pt-1">
          {citations.map((citation) => (
            <CitationChip
              key={`${citation.chunkId}-${citation.citationIndex}`}
              citation={citation}
              selected={selectedCitationIndex === citation.citationIndex}
              onSelect={onSelectCitation}
            />
          ))}
        </div>
      ) : null}

      {!isStreaming && text ? <TranslateButton text={text} /> : null}
    </div>
  )
}
