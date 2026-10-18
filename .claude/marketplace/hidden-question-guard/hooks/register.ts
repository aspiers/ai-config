import type { Register } from 'claude-code'

// On Claude Opus 5.5 (and Fable 5/5.1, Sonnet 5.5) prose written right before
// a tool call often comes back as a progress-update `thinking` block, not a
// `text` block. The user sees at most a one-line summary, while the model
// believes they read it, which wrecks a questionnaire that depends on it. See
// https://platform.claude.com/docs/en/build-with-claude/thinking#progress-updates
//
// This was a PreToolUse command hook reading the transcript, but Claude Code
// writes the current response to the transcript only after PreToolUse hooks
// return, so it never saw the call (bead ai-fxh3). `turn.step` sees the
// response as it streams, before the tool call runs.
//
// Detection assumes `thinking.display: "updates"`, where only progress updates
// carry text. Under `"summarized"` ordinary reasoning carries text too, which
// costs one extra round trip per question but nothing worse.

// The deny text must not mention a later question or a mechanism: told that,
// the model tends to end its turn with "next I'll ask..." and never ask.
export const DENY_REASON =
    'Not shown to the user: nothing you wrote since the last tool result ' +
    'reached them as visible text, so they cannot see the context this ' +
    'question depends on. Reply now with that content written out in full ' +
    '(drafts, tables, findings, trade-offs), as plain text with no tool call ' +
    'in the same message.'

export const STOP_REASON =
    'The user can now see that context. Call AskUserQuestion now, with no text ' +
    'before the call.'

const MAIN = 'main'

type Step = { hidden: boolean; visible: boolean }

// Keyed by agent loop, so a subagent's step cannot mask the main loop's.
const steps = new Map<string, Step>()
// Loops whose question was denied ('denied') or whose re-ask was prompted
// ('reask'); either lets the next question through, so the pair cannot loop.
const pending = new Map<string, 'denied' | 'reask'>()

export const register: Register = on => {
    on('turn.step', async function* ($, e, next) {
        const step: Step = { hidden: false, visible: false }
        steps.set(e.agentId ?? MAIN, step)
        const stream = next(e)
        for await (const chunk of stream) {
            if (chunk.kind === 'thinking' && chunk.text.trim()) step.hidden = true
            if (chunk.kind === 'text' && chunk.text.trim()) step.visible = true
            yield chunk
        }
        return await stream.result
    })

    // Any failure lets the question through: a broken guard must not block
    // every questionnaire.
    on('tool.call', { tool: 'AskUserQuestion' }, ($, e, next) => {
        const loop = e.agentId ?? MAIN
        if (pending.delete(loop)) return next(e)
        const step = steps.get(loop)
        if (!step?.hidden || step.visible) return next(e)
        pending.set(loop, 'denied')
        return { deny: DENY_REASON }
    }).catch(($, e, next) => next(e))

    on('classic.Stop', ($, e, next) => {
        if (pending.get(MAIN) !== 'denied') return next(e)
        pending.set(MAIN, 'reask')
        return { block: STOP_REASON }
    }).catch(($, e, next) => next(e))

    // A new prompt from the user drops a re-ask that never happened, so it
    // cannot wave a later question through.
    on('prompt.submit', ($, e, next) => {
        pending.clear()
        return next(e)
    })
}
