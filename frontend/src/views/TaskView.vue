<script setup lang="ts">
import { ref, watch, nextTick, onMounted } from 'vue'
import { useTaskStore } from '../stores/task'
import MarkdownIt from 'markdown-it'

// 1. 初始化 Store
const taskStore = useTaskStore()

// 2. 初始化渲染器（严格对齐你的配置）
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
})

const scrollContainer = ref<HTMLElement | null>(null)

// 🕵️ 核心逻辑还原：监视文字变化，自动滚动置底
watch(() => taskStore.task?.description, async () => {
  if (scrollContainer.value) {
    await nextTick()
    scrollContainer.value.scrollTo({
      top: scrollContainer.value.scrollHeight,
      behavior: 'smooth'
    })
  }
})

// 初始加载历史
onMounted(() => {
  taskStore.fetchHistory()
})
</script>

<template>
  <div class="h-full flex flex-col bg-white overflow-hidden">
    <main class="flex-1 overflow-y-auto p-8 relative custom-scrollbar">

      <div v-if="taskStore.loading && (!taskStore.task || !taskStore.task.description)"
           class="h-full flex flex-col items-center justify-center">
        <div class="animate-spin rounded-full h-10 w-10 border-4 border-blue-500 border-t-transparent mb-4"></div>
        <p class="text-gray-500 font-medium">AI 正在构思您的任务...</p>
      </div>

      <div v-else-if="taskStore.error" class="h-full flex flex-col items-center justify-center text-red-500">
        <p class="font-bold text-xl">{{ taskStore.error }}</p>
        <button @click="taskStore.generateNewTask"
                class="mt-4 px-6 py-2 bg-red-600 text-white rounded-xl shadow-lg">重试连接
        </button>
      </div>

      <div v-else-if="taskStore.task" class="max-w-4xl mx-auto space-y-10 animate-fade-in">
        <header>
          <div class="flex items-center gap-3 mb-4">
            <span class="px-3 py-1 bg-blue-50 text-blue-700 text-[10px] font-black rounded-full uppercase tracking-widest border border-blue-100">
              ID: {{ taskStore.task.id }}
            </span>
            <span class="text-slate-400 text-xs font-medium ml-auto">{{ taskStore.task.created_at }}</span>
          </div>

          <div
            ref="scrollContainer"
            class="markdown-body text-slate-800 bg-slate-50/50 p-8 rounded-3xl border border-slate-100"
            v-html="md.render(taskStore.task.description + (taskStore.isStreaming ? ' ▌' : ''))"
          ></div>
        </header>

        <section class="space-y-6">
          <div class="relative group">
            <div class="absolute -top-3 left-6 px-3 py-1 bg-slate-900 text-white text-[10px] font-bold rounded-md z-10">
              PYTHON CODE EDITOR
            </div>
            <textarea
              v-model="taskStore.userCode"
              rows="10"
              class="w-full p-8 pt-10 bg-slate-900 text-green-400 font-mono text-sm rounded-3xl border-none focus:ring-4 focus:ring-blue-500/10 transition-all shadow-2xl outline-none"
              placeholder="def solution():\n    # 在这里编写你的代码..."
            ></textarea>
          </div>

          <button
            @click="taskStore.checkCode"
            :disabled="taskStore.isChecking || !taskStore.userCode"
            class="w-full py-5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 text-white font-black rounded-2xl shadow-xl transition-all flex items-center justify-center gap-3 active:scale-[0.98]"
          >
            <svg v-if="taskStore.isChecking" class="animate-spin" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
            </svg>
            {{ taskStore.isChecking ? 'AI 导师正在审阅中...' : '提交代码获取评价' }}
          </button>

          <div v-if="taskStore.feedback || taskStore.isChecking"
               class="p-8 bg-blue-50 rounded-3xl border-2 border-dashed border-blue-200 animate-fade-in shadow-inner">
            <div class="flex items-center gap-3 mb-4">
              <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs">🎓</div>
              <h3 class="font-black text-blue-800 uppercase tracking-tight">导师反馈</h3>
            </div>
            <div
              class="markdown-body text-blue-700/90 leading-relaxed text-sm italic"
              v-html="md.render(taskStore.feedback + (taskStore.isChecking ? ' ▌' : ''))"
            ></div>
          </div>
        </section>
      </div>

      <div v-else class="h-full flex flex-col items-center justify-center text-slate-300">
        <h3 class="text-xl font-bold text-slate-400">选择一个挑战开始你的练习</h3>
        <button @click="taskStore.generateNewTask"
                class="mt-6 px-8 py-3 bg-blue-600 text-white rounded-2xl font-bold shadow-lg hover:scale-105 transition-all">
          生成今日新挑战
        </button>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* 此处粘贴你之前的 :deep(.markdown-body) 相关样式，确保渲染效果一致 */
:deep(.markdown-body) {
  line-height: 1.8;
  word-wrap: break-word;
}
:deep(.markdown-body pre) {
  background-color: #1e293b;
  color: #e2e8f0;
  padding: 1.25rem;
  border-radius: 0.75rem;
  overflow-x: auto;
}
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 10px; }
.animate-fade-in { animation: fadeIn 0.4s ease-out forwards; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>
