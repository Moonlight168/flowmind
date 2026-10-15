import { beforeEach, describe, expect, it, vi } from 'vitest'

import { postSse } from '@/utils/sse'

vi.mock('@/utils/auth', () => ({ getToken: () => 'test-token' }))

describe('postSse', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('parses SSE events split across network chunks', async () => {
    const encoder = new TextEncoder()
    const chunks = [
      encoder.encode('data: {"type":"delta","content":"你"}\r\n'),
      encoder.encode('\r\ndata: {"type":"done","response":"你好"}\n\n')
    ]
    const read = vi.fn()
      .mockResolvedValueOnce({ done: false, value: chunks[0] })
      .mockResolvedValueOnce({ done: false, value: chunks[1] })
      .mockResolvedValueOnce({ done: true, value: undefined })
    const releaseLock = vi.fn()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      body: { getReader: () => ({ read, cancel: vi.fn(), releaseLock }) }
    }))
    const events = []

    await postSse('/flowmind-ai/chat/stream', { user_input: 'hello' }, event => {
      events.push(event)
    })

    expect(events).toEqual([
      { type: 'delta', content: '你' },
      { type: 'done', response: '你好' }
    ])
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/flowmind-ai/chat/stream'),
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ Authorization: 'Bearer test-token' })
      })
    )
    expect(releaseLock).toHaveBeenCalledOnce()
  })

  it('rejects and cancels a stream that ends without done', async () => {
    const encoder = new TextEncoder()
    const read = vi.fn()
      .mockResolvedValueOnce({
        done: false,
        value: encoder.encode('data: {"type":"delta","content":"半段"}\n\n')
      })
      .mockResolvedValueOnce({ done: true, value: undefined })
    const cancel = vi.fn().mockResolvedValue(undefined)
    const releaseLock = vi.fn()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      body: { getReader: () => ({ read, cancel, releaseLock }) }
    }))

    await expect(
      postSse('/flowmind-ai/chat/stream', {}, vi.fn())
    ).rejects.toThrow('流式响应意外中断')
    expect(cancel).toHaveBeenCalledOnce()
    expect(releaseLock).toHaveBeenCalledOnce()
  })

  it('accepts an error event as a terminal event', async () => {
    const encoder = new TextEncoder()
    const read = vi.fn()
      .mockResolvedValueOnce({
        done: false,
        value: encoder.encode('data: {"type":"error","message":"失败"}\n\n')
      })
      .mockResolvedValueOnce({ done: true, value: undefined })
    const releaseLock = vi.fn()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      body: { getReader: () => ({ read, cancel: vi.fn(), releaseLock }) }
    }))
    const events = []

    await postSse('/flowmind-ai/design/flow', {}, event => events.push(event))

    expect(events).toEqual([{ type: 'error', message: '失败' }])
    expect(releaseLock).toHaveBeenCalledOnce()
  })
})
