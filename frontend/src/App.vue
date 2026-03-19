<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import MarkdownIt from 'markdown-it'

// 1. 定义任务接口（修复了之前的语法错误）
type TaskPriority = '高' | '中' | '低'

interface AITask {
  id: number
  description: string
  status: string
  priority: TaskPriority
  estimated_hours: number
  tags: string[]
  created_at: string
  user_code?: string
  feedback?: string
}

// 初始化渲染器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
})

const scrollContainer = ref<HTMLElement | null>(null)
const task = ref<AITask | null>(null)
const historyTasks = ref<AITask[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const isStreaming = ref(false)
const userCode = ref('')
const feedback = ref('')
const isChecking = ref(false)

// 🕵️ 核心逻辑：监视文字变化，自动滚动置底
watch(() => task.value?.description, async () => {
  if (scrollContainer.value) {
    await nextTick()
    scrollContainer.value.scrollTo({
      top: scrollContainer.value.scrollHeight,
      behavior: 'smooth'
    })
  }
})

// 获取历史任务列表
const fetchHistory = async () => {
  try {
    const response = await fetch('http://localhost:8003/task/history')
    if (response.ok) {
      const data = await response.json()
      historyTasks.value = data
      // 如果当前没有选中任务，默认展示最新的一个
      if (!task.value && data.length > 0) {
        selectTask(data[0])
      }
    }
  } catch (err) {
    console.error('加载历史失败:', err)
  }
}

// 切换选中的任务
const selectTask = (selected: AITask) => {
  task.value = selected
  userCode.value = selected.user_code || ''
  feedback.value = selected.feedback || ''
}

const fetchTask = async () => {
  loading.value = true
  isStreaming.value = true
  error.value = null
  userCode.value = ''
  feedback.value = ''

  task.value = {
    id: Date.now(),
    description: '',
    status: '进行中',
    priority: '中',
    estimated_hours: 1,
    tags: ['AI 生成'],
    created_at: new Date().toLocaleString()
  }

  try {
    const response = await fetch('http://localhost:8003/task/stream')
    if (!response.ok) throw new Error('网络响应异常')

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    if (!reader) return

    loading.value = false

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const rawChunk = decoder.decode(value)
      const lines = rawChunk.split('\n\n')
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const content = line.replace('data: ', '')
          task.value.description += content
        }
      }
    }
    // 生成结束后，刷新历史记录列表
    await fetchHistory()
  } catch (err) {
    console.error(err)
    error.value = '❌ 连接 AI 服务失败，请检查后端是否启动'
  } finally {
    loading.value = false
    isStreaming.value = false
  }
}

const checkCode = async () => {
  if (!userCode.value || !task.value) return;

  isChecking.value = true;
  feedback.value = '';

  try {
    const response = await fetch('http://localhost:8003/task/check', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        task_id: task.value.id,
        task_description: task.value.description,
        user_code: userCode.value
      })
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    if (!reader) return;

    while (true) {
      const {done, value} = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const content = line.replace('data: ', '');
          feedback.value += content;
          if (task.value) task.value.feedback = feedback.value;
        }
      }
    }
    await fetchHistory()
  } catch (error) {
    feedback.value = '❌ 批改服务暂时不可用';
  } finally {
    isChecking.value = false;
  }
}

onMounted(() => {
  fetchHistory()
})
</script>

<template>
  <div class="flex h-screen bg-slate-50 text-slate-900 font-sans overflow-hidden">
    <aside class="w-80 bg-white border-r border-slate-200 flex flex-col shadow-sm">
      <div class="p-6 border-b border-slate-100 flex items-center justify-between bg-white sticky top-0 z-10">
        <div class="flex items-center gap-2">
          <div class="p-1.5 bg-blue-600 rounded-lg text-white">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M9 3v18"/><path d="M3 9h6"/></svg>
          </div>
          <h2 class="text-lg font-bold tracking-tight text-slate-800">挑战历史</h2>
        </div>
        <button
          @click="fetchTask"
          :disabled="isStreaming"
          class="p-2 hover:bg-slate-100 rounded-full transition-all text-slate-500 hover:text-blue-600 disabled:opacity-50"
          title="生成新任务"
        >
          <svg v-if="!isStreaming" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v8"/><path d="M8 12h8"/></svg>
          <svg v-else class="animate-spin" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
        </button>
      </div>

      <div class="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
        <div v-if="historyTasks.length === 0" class="text-center py-10">
          <p class="text-slate-400 text-sm italic">暂无挑战记录</p>
        </div>

        <button
          v-for="hTask in historyTasks"
          :key="hTask.id"
          @click="selectTask(hTask)"
          class="w-full text-left p-4 rounded-2xl transition-all border border-transparent group relative overflow-hidden"
          :class="[
            task?.id === hTask.id
            ? 'bg-blue-50 border-blue-200 shadow-sm ring-1 ring-blue-200'
            : 'hover:bg-slate-50 hover:border-slate-200'
          ]"
        >
          <div v-if="task?.id === hTask.id" class="absolute left-0 top-0 bottom-0 w-1 bg-blue-600"></div>
          <div class="flex justify-between items-start mb-2">
            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{{ hTask.created_at }}</span>
            <svg v-if="hTask.feedback" class="text-emerald-500" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
            <svg v-else class="text-slate-300" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/></svg>
          </div>
          <p class="text-sm font-bold text-slate-700 line-clamp-2 leading-snug group-hover:text-blue-700 transition-colors">{{ hTask.description }}</p>
        </button>
      </div>
    </aside>

    <main class="flex-1 overflow-y-auto p-8 relative bg-white">
      <div v-if="loading && (!task || !task.description)" class="h-full flex flex-col items-center justify-center">
        <div class="animate-spin rounded-full h-10 w-10 border-4 border-blue-500 border-t-transparent mb-4"></div>
        <p class="text-gray-500 font-medium">AI 正在构思您的任务...</p>
      </div>

      <div v-else-if="error" class="h-full flex flex-col items-center justify-center text-red-500">
        <p class="font-bold text-xl">{{ error }}</p>
        <button @click="fetchTask" class="mt-4 px-6 py-2 bg-red-600 text-white rounded-xl shadow-lg">重试连接</button>
      </div>

      <div v-else-if="task" class="max-w-4xl mx-auto space-y-10 animate-fade-in">
        <header>
          <div class="flex items-center gap-3 mb-4">
            <span class="px-3 py-1 bg-blue-50 text-blue-700 text-[10px] font-black rounded-full uppercase tracking-widest border border-blue-100">
              预计 {{ task.estimated_hours }} 小时
            </span>
            <span class="text-slate-400 text-xs font-medium ml-auto">{{ task.created_at }}</span>
          </div>

          <div
            ref="scrollContainer"
            class="markdown-body text-slate-800 bg-slate-50/50 p-8 rounded-3xl border border-slate-100"
            v-html="md.render(task.description + (isStreaming ? ' ▌' : ''))"
          ></div>
        </header>

        <section class="space-y-6">
          <div class="relative group">
            <div class="absolute -top-3 left-6 px-3 py-1 bg-slate-900 text-white text-[10px] font-bold rounded-md z-10">PYTHON CODE EDITOR</div>
            <textarea
              v-model="userCode"
              rows="10"
              class="w-full p-8 pt-10 bg-slate-900 text-green-400 font-mono text-sm rounded-3xl border-none focus:ring-4 focus:ring-blue-500/10 transition-all shadow-2xl outline-none"
              placeholder="def solution():\n    # 在这里编写你的代码..."
            ></textarea>
          </div>

          <button
            @click="checkCode"
            :disabled="isChecking || !userCode"
            class="w-full py-5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 text-white font-black rounded-2xl shadow-xl transition-all flex items-center justify-center gap-3 active:scale-[0.98]"
          >
            <svg v-if="isChecking" class="animate-spin" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
            {{ isChecking ? 'AI 导师正在审阅中...' : '提交代码获取评价' }}
          </button>

          <div v-if="feedback || isChecking" class="p-8 bg-blue-50 rounded-3xl border-2 border-dashed border-blue-200 animate-fade-in shadow-inner">
            <div class="flex items-center gap-3 mb-4">
              <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs">🎓</div>
              <h3 class="font-black text-blue-800 uppercase tracking-tight">导师反馈</h3>
            </div>
            <div
              class="markdown-body text-blue-700/90 leading-relaxed text-sm italic"
              v-html="md.render(feedback + (isChecking ? ' ▌' : ''))"
            ></div>
          </div>
        </section>
      </div>

      <div v-else class="h-full flex flex-col items-center justify-center text-slate-300">
        <h3 class="text-xl font-bold text-slate-400">选择一个挑战开始你的练习</h3>
        <button @click="fetchTask" class="mt-6 px-8 py-3 bg-blue-600 text-white rounded-2xl font-bold shadow-lg shadow-blue-200 hover:scale-105 transition-all">
          生成今日新挑战
        </button>
      </div>
    </main>
  </div>
</template>

<style scoped>
:deep(.markdown-body) {
  line-height: 1.8;
  word-wrap: break-word;
}
:deep(.markdown-body h1), :deep(.markdown-body h2), :deep(.markdown-body h3) {
  color: #1e3a8a;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  font-weight: 800;
}
:deep(.markdown-body pre) {
  background-color: #1e293b;
  color: #e2e8f0;
  padding: 1.25rem;
  border-radius: 0.75rem;
  margin: 1.25rem 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  word-break: break-all;
  overflow-x: hidden;
  font-family: 'Fira Code', monospace;
  font-size: 0.875rem;
}
:deep(.markdown-body code:not(pre code)) {
  background-color: #fee2e2;
  color: #dc2626;
  padding: 0.2rem 0.4rem;
  border-radius: 0.375rem;
  font-weight: 600;
}
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 10px;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in {
  animation: fadeIn 0.4s ease-out forwards;
}
</style>
