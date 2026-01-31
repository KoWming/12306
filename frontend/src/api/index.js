import axios from 'axios'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 60000  // 增加到60秒，给后端更多处理时间
})

// 响应拦截器
request.interceptors.response.use(
  response => response.data,
  error => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    console.error('API Error:', message)
    return Promise.reject(new Error(message))
  }
)

export default {
  // ========== 用户相关 ==========
  createUser(data) {
    return request.post('/auth/users', data)
  },

  getUsers() {
    return request.get('/auth/users')
  },

  getUser(userId) {
    return request.get(`/auth/users/${userId}`)
  },

  checkLoginStatus(userId) {
    return request.get(`/auth/status/${userId}`)
  },

  getQRCode(userId) {
    return request.post(`/auth/qrcode/${userId}`)
  },

  checkQRStatus(userId, uuid) {
    return request.get(`/auth/qrcode/${userId}/status`, { params: { uuid } })
  },

  logout(userId) {
    return request.post(`/auth/logout/${userId}`)
  },

  deleteUser(userId) {
    return request.delete(`/auth/users/${userId}`)
  },

  getPassengers(userId) {
    return request.get(`/users/${userId}/passengers`)
  },

  // ========== 查票相关 ==========
  queryTickets(params) {
    return request.get('/trains/query', { params })
  },

  searchStations(keyword) {
    return request.get('/trains/stations/search', { params: { keyword } })
  },

  // ========== 任务相关 ==========
  getTasks(params) {
    return request.get('/tasks', { params })
  },

  getTask(taskId) {
    return request.get(`/tasks/${taskId}`)
  },

  createTask(data, userId) {
    return request.post('/tasks', data, { params: { user_id: userId } })
  },

  updateTask(taskId, data) {
    return request.put(`/tasks/${taskId}`, data)
  },

  deleteTask(taskId) {
    return request.delete(`/tasks/${taskId}`)
  },

  startTask(taskId) {
    return request.post(`/tasks/${taskId}/start`)
  },

  stopTask(taskId) {
    return request.post(`/tasks/${taskId}/stop`)
  },

  cancelTask(taskId) {
    return request.post(`/tasks/${taskId}/cancel`)
  },

  getTaskLogs(taskId, params) {
    return request.get(`/tasks/${taskId}/logs`, { params })
  },

  // ========== 系统配置 ==========
  getGlobalSchedule() {
    return request.get('/config/global-schedule')
  },

  updateGlobalSchedule(data) {
    return request.post('/config/global-schedule', data)
  },

  // ========== 通知配置 ==========
  getNotificationConfig() {
    return request.get('/config/notification')
  },

  updateNotificationConfig(data) {
    return request.post('/config/notification', data)
  },

  testNotification(data) {
    return request.post('/config/notification/test', data)
  }
}
