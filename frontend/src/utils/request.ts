import axios, { AxiosError, type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

// 创建axios实例
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求队列（用于防止重复请求）
const pendingRequests = new Map()

// 生成请求key
const getRequestKey = (config: AxiosRequestConfig): string => {
  return `${config.method}_${config.url}_${JSON.stringify(config.params)}_${JSON.stringify(config.data)}`
}

// 添加请求到队列
const addPendingRequest = (config: AxiosRequestConfig): void => {
  const key = getRequestKey(config)
  if (!pendingRequests.has(key)) {
    pendingRequests.set(key, config)
  }
}

// 移除请求从队列
const removePendingRequest = (config: AxiosRequestConfig): void => {
  const key = getRequestKey(config)
  if (pendingRequests.has(key)) {
    pendingRequests.delete(key)
  }
}

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 添加token
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }

    // 防止重复请求
    removePendingRequest(config)
    addPendingRequest(config)

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    removePendingRequest(response.config)

    const { code, message, data } = response.data

    // 业务错误处理
    if (code !== 200) {
      ElMessage.error(message || '请求失败')
      return Promise.reject(new Error(message))
    }

    return data
  },
  async (error: AxiosError) => {
    const config = error.config as AxiosRequestConfig
    if (config) {
      removePendingRequest(config)
    }

    const { response } = error

    if (response) {
      const { status, data } = response

      switch (status) {
        case 401:
          // Token过期，尝试刷新
          const authStore = useAuthStore()
          try {
            await authStore.refreshAccessToken()
            // 重试原请求
            if (config) {
              return request(config)
            }
          } catch {
            // 刷新失败，登出
            authStore.logout()
            window.location.href = '/login'
          }
          break

        case 403:
          ElMessage.error('没有权限执行此操作')
          break

        case 404:
          ElMessage.error('请求的资源不存在')
          break

        case 500:
          ElMessage.error('服务器内部错误')
          break

        default:
          ElMessage.error((data as { message?: string })?.message || '网络错误')
      }
    } else {
      ElMessage.error('网络连接失败')
    }

    return Promise.reject(error)
  }
)

// 封装请求方法
export const http = {
  get: <T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    return request.get(url, config)
  },

  post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> => {
    return request.post(url, data, config)
  },

  put: <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> => {
    return request.put(url, data, config)
  },

  patch: <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> => {
    return request.patch(url, data, config)
  },

  delete: <T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    return request.delete(url, config)
  },
}

export default request
