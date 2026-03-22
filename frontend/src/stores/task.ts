import { defineStore } from 'pinia'
import { ref } from 'vue'
import type {ICreateTaskResponse, ITask} from "../types/task";
import {useSSE} from "../composables/useSSE";

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

  const sse = useSSE();
  const API_BASE = import.meta.env.VITE_API_BASE_URL;


  // --- 动作 (Actions) ---

  // 1. 获取历史记录
  const fetchHistory = async () => {
    try {
      const response = await fetch(`${API_BASE}/task/history`)
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
    loading.value = true

    try {
      // 1. 【关键一步】先向后端申请真实的数据库 ID
      const createRes = await fetch(`${API_BASE}/task/create`, {
        method: 'POST'
      })
      if (!createRes.ok) throw new Error('初始化任务失败')
      const { id } = await createRes.json() as ICreateTaskResponse;
      task.value = {
        id,
        description: '',
        status: '生成中',
        priority: '中',         // 补全接口要求的字段
        estimated_hours: 1,    // 补全接口要求的字段
        tags: ["Python", "每日挑战"], // 补全接口要求的字段
        user_code: null,
        feedback: null,
        created_at: new Date().toLocaleString()
      }
      // 调用 Composable，逻辑极其清晰
      await sse.run(`${API_BASE}/task/stream?task_id=${id}`, { method: 'GET' }, (content) => {
        if (loading.value) loading.value = false // 首字节关闭 loading
        if (task.value) task.value.description += content
      })

      await fetchHistory()
    } catch (err) {
      error.value = '❌ 连接 AI 服务失败'
      console.error(err)
    }
  }

  // 4. 流式批改代码 (严格还原老代码逻辑)
  const checkCode = async () => {
    if (!task.value || !userCode.value || isChecking.value) return;
    isChecking.value = true
    feedback.value = ''

    try {
      await sse.run(`${API_BASE}/task/check`, {
            method: 'POST',
            body: { task_id: task.value.id, user_code: userCode.value, task_description: task.value.description }
          }, (content) => {
            if (loading.value) loading.value = false
            feedback.value += content
          })

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
