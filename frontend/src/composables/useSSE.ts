import {ref, onUnmounted} from 'vue'

export function useSSE() {
  const isStreaming = ref(false)
  const error = ref<string | null>(null)
  let abortController: AbortController | null = null;

  /**
   * 核心流处理函数
   * @param url 请求地址
   * @param options 配置项 (method, body 等)
   * @param onChunk 每一帧攒下的文字回调
   */
  const run = async (
    url: string,
    options: { method?: 'GET' | 'POST'; body?: any } = {},
    onChunk: (content: string) => void
  ) => {
    // 1.资源清理，防止并发导致的僵尸流
    if (abortController) abortController.abort();
    abortController = new AbortController();

    isStreaming.value = true
    error.value = null

    try {
      const response = await fetch(url, {
        method: options.method || 'GET',
        headers: options.body ? {'Content-Type': 'application/json'} : {},
        body: options.body ? JSON.stringify(options.body) : null,
        signal: abortController.signal
      })

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      if (!reader) throw new Error('ReadableStream not supported.')

      // ---工业级优化缓冲区
      let leftover = ''      // 数据截断缓冲区
      let displayBuffer = '' // 分帧渲染缓冲区
      let isFrameActive = false

      try {
        while (true) {
          const {done, value} = await reader.read()
          if (done) break

          //处理分包与截断
          const chunk = leftover + decoder.decode(value, {stream: true})
          const lines = chunk.split('\n\n');
          leftover = lines.pop() || '';

          for (const line of lines) {
            if (line.trim().startsWith('data: ')) {
              const content = line.replace('data: ', '');

              // 1. 【只管存】不管循环多少次，先把所有字都攒到这个大桶里
              displayBuffer += content;

              // 2. 【只管申请】如果还没申请过这一帧的渲染，就申请一次
              if (!isFrameActive) {
                isFrameActive = true;

                requestAnimationFrame(() => {
                  // 3. 【回调时才取】当浏览器准备好画画了，一次性把桶里的字全拿走
                  const snapshot = displayBuffer;
                  displayBuffer = '';    // 拿走了才清空，保证没拿走之前一直攒着
                  isFrameActive = false; // 释放锁，允许申请下一帧

                  if (snapshot) {
                    onChunk(snapshot);
                  }
                });
              }
            }
          }
        }
      } finally {
        reader.releaseLock()
      }


    } catch (err: any) {
      if (err.name === 'AbortError') {
        console.log('[SSE] Request aborted')
      } else {
        error.value = err.message
        throw err
      }
    } finally {
      isStreaming.value = false;
      abortController = null;
    }
  }


  onUnmounted(() => {
    if (abortController) abortController.abort();
  })

  return {
    run,
    isStreaming,
    error
  }


}
