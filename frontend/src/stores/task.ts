import { defineStore } from 'pinia'
import { ref } from 'vue'
import type {ITask} from "../types/task";

export const useTaskStore = defineStore('task', () => {
  // --- 状态 (State) ---
  const historyTasks = ref<ITask[]>([])
  const task = ref<ITask | null>(null)
  const loading = ref(false)
  const isStreaming = ref(false)     // 任务生成流状态
  const isChecking = ref(false)      // 代码批改流状态
  const userCode = ref('')
  const feedback = ref('')
  const error = ref<string | null>(null)

  // --- 动作 (Actions) ---

  // 1. 获取历史记录
  const fetchHistory = async () => {
    try {
      const response = await fetch('http://localhost:8003/task/history')
      const data: ITask[] = await response.json() // 强制要求符合接口
      if (response.ok) {
        historyTasks.value = data
      }
    } catch (err) {
      console.error('加载历史失败:', err)
    }
  }

  // 2. 选中任务
  const selectTask = (selected: ITask) => {
    task.value = selected
    userCode.value = selected.user_code || ''
    feedback.value = selected.feedback || ''
  }

  // 3. 流式生成任务 (严格还原老代码逻辑)
  const generateNewTask = async () => {
    if (isStreaming.value) return

    loading.value = true
    isStreaming.value = true
    error.value = null
    userCode.value = ''
    feedback.value = ''

    try {
      // 1. 【关键一步】先向后端申请真实的数据库 ID
      const createRes = await fetch('http://localhost:8003/task/create', {
        method: 'POST'
      })

      if (!createRes.ok) throw new Error('初始化任务失败')
      const { id } = await createRes.json()
      // 2. 使用后端返回的真实 ID 初始化前端状态
      task.value = {
        id: id,
        description: '',
        status: '生成中',
        priority: '中',         // 补全接口要求的字段
        estimated_hours: 1,    // 补全接口要求的字段
        tags: ["Python", "每日挑战"], // 补全接口要求的字段
        user_code: null,
        feedback: null,
        created_at: new Date().toLocaleString()
      }
      const response = await fetch(`http://localhost:8003/task/stream/${id}`)
      if (!response.ok) throw new Error('流式连接失败')

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      if (!reader) return

      loading.value = false

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const rawChunk = decoder.decode(value)
        const lines = rawChunk.split('\n\n') // 保持你的双换行分割
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const content = line.replace('data: ', '')
            if (task.value) {
              task.value.description += content;
            }
          }
        }
      }
      await fetchHistory()
    } catch (err) {
      error.value = '❌ 连接 AI 服务失败'
      console.error(err)
    } finally {
      loading.value = false
      isStreaming.value = false
    }
  }

  // 4. 流式批改代码 (严格还原老代码逻辑)
  const checkCode = async () => {
    if (!userCode.value || !task.value || isChecking.value) return

    isChecking.value = true
    feedback.value = ''

    try {
      const response = await fetch('http://localhost:8003/task/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: task.value.id,
          task_description: task.value.description,
          user_code: userCode.value
        })
      })

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      if (!reader) return

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n\n') // 保持你的双换行分割
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const content = line.replace('data: ', '')
            feedback.value += content
            // 同步更新到当前任务对象中，方便持久化感官
            if (task.value) task.value.feedback = feedback.value
          }
        }
      }
      // 批改完刷新历史，确保后端存下了 user_code 和 feedback
      await fetchHistory()
    } catch (err) {
      feedback.value = '❌ 批改服务暂时不可用'
      console.error(err)
    } finally {
      isChecking.value = false
    }
  }

  return {
    historyTasks,
    task,
    loading,
    isStreaming,
    isChecking,
    userCode,
    feedback,
    error,
    fetchHistory,
    selectTask,
    generateNewTask,
    checkCode
  }
})
