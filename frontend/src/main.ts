import { createApp } from 'vue'
import { createPinia } from 'pinia' // 1. 引入 Pinia 构造函数
import App from './App.vue'
import router from './router'      // 2. 引入路由配置文件（我们下一步创建）
import './assets/main.css'

const app = createApp(App)
const pinia = createPinia()   // 3. 创建 Pinia 实例

app.use(pinia)                     // 4. 注册状态管理
app.use(router)                    // 5. 注册路由系统

app.mount('#app')
