// 应用入口
import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import './styles/index.scss'

const app = createApp(App)

// 全局错误兜底：未捕获的组件异常不打断应用
app.config.errorHandler = (err, _instance, info) => {
  // eslint-disable-next-line no-console
  console.error(`[全局错误] ${info}:`, err)
}

app.use(createPinia())
app.use(router)

app.mount('#app')
