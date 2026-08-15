import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 创建 axios 实例
// 通过 Vite 代理转发到后端，避免跨域；也可配置后端地址覆盖
const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 15000,
})

// 请求拦截器：自动附加 JWT
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：统一错误处理
http.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status
    const detail =
      error.response?.data?.detail || error.message || '请求失败'

    // 401 未认证：清除 token 并提示
    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      ElMessage.error('登录状态已过期，请重新登录')
      // 避免重复跳转
      if (router.currentRoute.value.name !== 'login') {
        router.push({ name: 'login' })
      }
    } else {
      const msg =
        typeof detail === 'string' ? detail : JSON.stringify(detail)
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  }
)

export default http