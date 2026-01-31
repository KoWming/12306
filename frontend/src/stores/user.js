import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import api from '../api'

export const useUserStore = defineStore('user', () => {
  const users = ref([])
  const currentUser = ref(null)
  const loginStatus = ref(null)
  const initialized = ref(false)

  const isLoggedIn = computed(() => {
    return currentUser.value && loginStatus.value?.is_logged_in
  })

  // 监听 loginStatus 变化，持久化到 localStorage
  watch(loginStatus, (newStatus) => {
    if (currentUser.value && newStatus) {
      localStorage.setItem(`loginStatus_${currentUser.value.id}`, JSON.stringify(newStatus))
    }
  }, { deep: true })

  // 监听 currentUser 变化
  watch(currentUser, (newUser) => {
    if (newUser) {
      localStorage.setItem('currentUserId', newUser.id.toString())
      localStorage.setItem('currentUser', JSON.stringify(newUser))
    }
  }, { deep: true })

  async function fetchUsers() {
    try {
      const res = await api.getUsers()
      if (res.success) {
        users.value = res.data
      }
    } catch (error) {
      console.error('获取用户列表失败:', error)
    }
  }

  async function createUser(username) {
    try {
      const res = await api.createUser({ username })
      if (res.success) {
        users.value.push(res.data)
        return res.data
      }
    } catch (error) {
      throw error
    }
  }

  async function selectUser(user) {
    currentUser.value = user
    localStorage.setItem('currentUserId', user.id.toString())
    localStorage.setItem('currentUser', JSON.stringify(user))

    // 如果用户已登录状态，先设置一个临时的 loginStatus 避免状态丢失
    if (user.is_logged_in) {
      loginStatus.value = {
        is_logged_in: true,
        username: user.username,
        railway_username: user.railway_username
      }
      // 持久化到 localStorage
      localStorage.setItem(`loginStatus_${user.id}`, JSON.stringify(loginStatus.value))
    }

    // 然后从服务器获取最新状态
    await checkLoginStatus()
  }

  async function checkLoginStatus() {
    if (!currentUser.value) return
    try {
      const res = await api.checkLoginStatus(currentUser.value.id)
      if (res.success) {
        loginStatus.value = res.data
        // 确保持久化最新状态
        localStorage.setItem(`loginStatus_${currentUser.value.id}`, JSON.stringify(res.data))
      }
    } catch (error) {
      console.error('检查登录状态失败:', error)
      // 检查失败时保持本地缓存的状态
    }
  }

  async function logout() {
    if (!currentUser.value) return
    try {
      await api.logout(currentUser.value.id)
      loginStatus.value = null
      // 清除本地存储的登录状态
      localStorage.removeItem(`loginStatus_${currentUser.value.id}`)
    } catch (error) {
      console.error('登出失败:', error)
    }
  }

  async function logoutUser(user) {
    if (!user) return
    try {
      await api.logout(user.id)
      // 清除本地存储的登录状态
      localStorage.removeItem(`loginStatus_${user.id}`)

      // 如果退出的是当前选中用户, 更新状态
      if (currentUser.value && currentUser.value.id === user.id) {
        loginStatus.value = null
      }

      // 更新列表中的状态
      const target = users.value.find(u => u.id === user.id)
      if (target) {
        target.is_logged_in = false
      }
      return true
    } catch (error) {
      console.error('登出失败:', error)
      throw error
    }
  }

  async function deleteUser(userId) {
    try {
      const res = await api.deleteUser(userId)
      if (res.success) {
        // 从列表中移除用户
        users.value = users.value.filter(u => u.id !== userId)
        // 如果删除的是当前用户，清除当前用户状态
        if (currentUser.value && currentUser.value.id === userId) {
          currentUser.value = null
          loginStatus.value = null
          localStorage.removeItem('currentUserId')
          localStorage.removeItem('currentUser')
          localStorage.removeItem(`loginStatus_${userId}`)
        }
        return true
      }
      return false
    } catch (error) {
      console.error('删除用户失败:', error)
      throw error
    }
  }

  // 恢复上次选择的用户
  async function restoreUser() {
    if (initialized.value) return
    initialized.value = true

    const savedUserId = localStorage.getItem('currentUserId')
    const savedUser = localStorage.getItem('currentUser')
    const savedLoginStatus = savedUserId ? localStorage.getItem(`loginStatus_${savedUserId}`) : null

    // 先从缓存恢复，保证页面切换时状态不丢失
    if (savedUser) {
      try {
        currentUser.value = JSON.parse(savedUser)
      } catch (e) {
        console.error('解析缓存用户失败:', e)
      }
    }

    if (savedLoginStatus) {
      try {
        loginStatus.value = JSON.parse(savedLoginStatus)
      } catch (e) {
        console.error('解析缓存登录状态失败:', e)
      }
    }

    // 然后从服务器刷新最新状态
    if (savedUserId) {
      try {
        await fetchUsers()
        const user = users.value.find(u => u.id === parseInt(savedUserId))
        if (user) {
          currentUser.value = user
          // 更新缓存
          localStorage.setItem('currentUser', JSON.stringify(user))
          await checkLoginStatus()
        }
      } catch (e) {
        console.error('从服务器刷新状态失败:', e)
        // 失败时保持缓存状态，不清除
      }
    }
  }

  return {
    users,
    currentUser,
    loginStatus,
    isLoggedIn,
    initialized,
    fetchUsers,
    createUser,
    selectUser,
    checkLoginStatus,
    logout,
    logoutUser,
    deleteUser,
    restoreUser
  }
})
