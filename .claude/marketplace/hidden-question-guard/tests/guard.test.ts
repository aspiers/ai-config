import { describe, expect, test } from 'claude-code/testing'
import type { Engine } from 'claude-code/testing'
import type { On } from 'claude-code'
import { DENY_REASON, STOP_REASON } from '../hooks/register'

type Piece = { kind: 'thinking' | 'text'; text: string }

// Stands for the model: streams the given pieces, then the question call.
function model(on: On, pieces: Piece[]) {
    on('turn.step', async function* ($, e) {
        let index = 0
        for (const p of pieces) yield { ...p, index: index++, ref: 0 }
        yield { kind: 'tool', index, id: 'toolu_test', name: 'AskUserQuestion', ref: 0 }
        return { turnId: e.turnId, index: e.index, answer: '', toolUses: [], stopReason: 'tool_use', usage: null }
    })
}

async function step($: Engine, agentId?: string) {
    const stream = $.turn.step({ turnId: 't', index: 0, model: 'm', messageCount: 1, agentId })
    for await (const _ of stream) { /* drain */ }
}

async function denied($: Engine, agentId?: string) {
    const r = await $.tool.call({ tool: 'AskUserQuestion', questions: [], agentId } as never)
    return r.deny
}

// Stands for the tool itself and for Claude Code's own Stop handling.
function answerer(on: On) {
    on('tool.call', { tool: 'AskUserQuestion' }, () => ({ result: { answers: {} } as never }))
    on('classic.Stop', () => ({}))
}

describe('hidden-question-guard', () => {
    // The ai-fxh3 incident: a progress update (thinking with text) and no
    // visible text before the question.
    test('denies a question preceded only by a hidden progress update', async ($, on) => {
        model(on, [{ kind: 'thinking', text: 'Five checks: ...' }])
        answerer(on)
        await step($)
        expect(await denied($)).toBe(DENY_REASON)
    })

    test('allows a question preceded by visible text', async ($, on) => {
        model(on, [{ kind: 'thinking', text: 'notes' }, { kind: 'text', text: 'Five checks: ...' }])
        answerer(on)
        await step($)
        expect(await denied($)).toBeUndefined()
    })

    test('allows a question with nothing before it', async ($, on) => {
        model(on, [{ kind: 'thinking', text: '  ' }])
        answerer(on)
        await step($)
        expect(await denied($)).toBeUndefined()
    })

    test('blocks the stop once after a deny, then lets the re-ask through', async ($, on) => {
        model(on, [{ kind: 'thinking', text: 'table' }])
        answerer(on)
        await step($)
        await denied($)
        expect((await $.classic.Stop({ stop_hook_active: false })).block).toBe(STOP_REASON)
        expect((await $.classic.Stop({ stop_hook_active: true })).block).toBeUndefined()
        await step($)
        expect(await denied($)).toBeUndefined()
        // The re-ask was consumed: the next hidden-context question is denied.
        await step($)
        expect(await denied($)).toBe(DENY_REASON)
    })

    test('a user prompt drops a pending re-ask', async ($, on) => {
        model(on, [{ kind: 'thinking', text: 'table' }])
        answerer(on)
        on('prompt.submit', () => ({ text: '' }) as never)
        await step($)
        await denied($)
        await $.prompt.submit({ text: 'something else' } as never)
        await step($)
        expect(await denied($)).toBe(DENY_REASON)
    })

    test("a subagent's visible step does not mask the main loop's hidden one", async ($, on) => {
        on('turn.step', async function* ($, e) {
            yield e.agentId
                ? { kind: 'text', index: 0, text: 'visible', ref: 0 }
                : { kind: 'thinking', index: 0, text: 'hidden', ref: 0 }
            return { turnId: e.turnId, index: e.index, answer: '', toolUses: [], stopReason: 'tool_use', usage: null }
        })
        answerer(on)
        await step($)
        await step($, 'agent-1')
        expect(await denied($)).toBe(DENY_REASON)
    })
})
