// 严格对应你的 models.py
export interface ITask {
  id: number;
  description: string;
  status: '待处理' | '生成中' | '进行中' | '已完成'; // 结合你的 models.py 和业务逻辑
  priority: string;
  estimated_hours: number;
  tags: string[]; // 对应 models.py 中的 JSON 类型
  user_code: string | null;
  feedback: string | null;
  created_at: string;
}

// 统一 API 返回格式
export interface ICreateTaskResponse {
  id: number;
}
