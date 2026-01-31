<template>
  <div class="login-page">
    <el-row :gutter="12" class="login-row">
      <el-col :xs="24" :span="12" class="mb-mobile">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span>账号列表</span>
              <el-button type="primary" size="small" @click="showCreateDialog = true">
                <el-icon><Plus /></el-icon>
                添加账号
              </el-button>
            </div>
          </template>
          
          <el-table :data="userStore.users" stripe highlight-current-row @current-change="handleSelectUser">
            <el-table-column prop="username" label="用户名" min-width="120" align="center" />
            <el-table-column prop="railway_username" label="12306账号" min-width="150" align="center" />
            <el-table-column prop="is_logged_in" label="登录状态" min-width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.is_logged_in ? 'success' : 'info'">
                  {{ row.is_logged_in ? '已登录' : '未登录' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" min-width="150" align="center">
              <template #default="{ row }">
                <div style="display: flex; justify-content: center; align-items: center; gap: 1px;">
                  <el-button 
                    v-if="!row.is_logged_in"
                    type="primary" 
                    size="small" 
                    text
                    style="margin: 0"
                    @click="startLogin(row)"
                  >
                    登录
                  </el-button>
                  <el-button 
                    v-else
                    type="warning" 
                    size="small" 
                    text
                    style="margin: 0"
                    @click="handleLogoutUser(row)"
                  >
                    退出
                  </el-button>
                  <el-popconfirm
                    title="确定要删除这个账号吗？"
                    confirm-button-text="确定"
                    cancel-button-text="取消"
                    @confirm="handleDeleteUser(row)"
                  >
                    <template #reference>
                      <el-button 
                        type="danger" 
                        size="small" 
                        text
                        style="margin: 0"
                      >
                        删除
                      </el-button>
                    </template>
                  </el-popconfirm>
                </div>
              </template>
            </el-table-column>
            
            <template #empty>
              <el-empty description="暂无账号" />
            </template>
          </el-table>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :span="12">
        <el-card>
          <template #header>
            <span>扫码登录</span>
          </template>
          
          <div class="qrcode-container">
            <template v-if="loginState === 'idle'">
              <el-empty description="请选择账号并点击登录">
                <template #image>
                  <el-icon size="80" color="#909399"><Iphone /></el-icon>
                </template>
              </el-empty>
            </template>
            
            <template v-else-if="loginState === 'loading'">
              <el-icon class="is-loading" size="60" color="#409EFF">
                <Loading />
              </el-icon>
              <p>{{ statusMessage }}</p>
            </template>
            
            <template v-else-if="loginState === 'qrcode'">
              <div class="qrcode-wrapper">
                <img :src="'data:image/png;base64,' + qrcodeImage" alt="登录二维码" />
                <div v-if="qrcodeExpired" class="qrcode-expired" @click="refreshQRCode">
                  <el-icon size="40"><RefreshRight /></el-icon>
                  <span>二维码已过期，点击刷新</span>
                </div>
              </div>
              <p>{{ statusMessage }}</p>
              <p class="tips">请使用 12306 APP 扫描二维码登录</p>
            </template>
            
            <template v-else-if="loginState === 'success'">
              <el-result icon="success" title="登录成功">
                <template #sub-title>
                  欢迎，{{ loginUsername }}
                </template>
              </el-result>
            </template>
            
            <template v-else-if="loginState === 'error'">
              <el-result icon="error" title="登录失败">
                <template #sub-title>
                  {{ statusMessage }}
                </template>
                <template #extra>
                  <el-button type="primary" @click="refreshQRCode">重试</el-button>
                </template>
              </el-result>
            </template>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 创建账号对话框 -->
    <el-dialog v-model="showCreateDialog" title="添加账号" width="400px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="createForm.username" placeholder="请输入用户名（用于标识账号）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateUser" :loading="creating">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import api from '../api'

const userStore = useUserStore()

const showCreateDialog = ref(false)
const creating = ref(false)
const createForm = reactive({
  username: ''
})

const loginState = ref('idle') // idle, loading, qrcode, success, error
const statusMessage = ref('')
const qrcodeImage = ref('')
const qrcodeUuid = ref('')
const qrcodeExpired = ref(false)
const loginUsername = ref('')
const currentLoginUser = ref(null)
let pollTimer = null

onMounted(async () => {
  await userStore.fetchUsers()
  // 如果已有选中的用户且已登录，显示登录成功状态
  if (userStore.currentUser && userStore.isLoggedIn) {
    loginState.value = 'success'
    loginUsername.value = userStore.currentUser.username
  }
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

const handleSelectUser = (user) => {
  if (user) {
    userStore.selectUser(user)
  }
}

const handleDeleteUser = async (user) => {
  try {
    await userStore.deleteUser(user.id)
    ElMessage.success('账号已删除')
    // 如果删除的是当前正在登录的账号，重置登录状态
    if (currentLoginUser.value && currentLoginUser.value.id === user.id) {
      currentLoginUser.value = null
      loginState.value = 'idle'
      if (pollTimer) clearInterval(pollTimer)
    }
  } catch (error) {
    ElMessage.error(error.message || '删除失败')
  }
}

const handleCreateUser = async () => {
  if (!createForm.username.trim()) {
    ElMessage.warning('请输入用户名')
    return
  }
  
  creating.value = true
  try {
    await userStore.createUser(createForm.username.trim())
    ElMessage.success('账号创建成功')
    showCreateDialog.value = false
    createForm.username = ''
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    creating.value = false
  }
}

const handleLogoutUser = async (user) => {
  try {
    await userStore.logoutUser(user)
    ElMessage.success('已退出登录')
  } catch (error) {
    ElMessage.error(error.message || '退出失败')
  }
}

const startLogin = async (user) => {
  currentLoginUser.value = user
  loginState.value = 'loading'
  statusMessage.value = '正在获取二维码...'
  qrcodeExpired.value = false
  
  try {
    const res = await api.getQRCode(user.id)
    if (res.success) {
      qrcodeImage.value = res.data.image_base64
      qrcodeUuid.value = res.data.uuid
      loginState.value = 'qrcode'
      statusMessage.value = '等待扫码...'
      startPolling()
    } else {
      loginState.value = 'error'
      statusMessage.value = res.message || '获取二维码失败'
    }
  } catch (error) {
    loginState.value = 'error'
    statusMessage.value = error.message
  }
}

const startPolling = () => {
  if (pollTimer) clearInterval(pollTimer)
  
  pollTimer = setInterval(async () => {
    if (!currentLoginUser.value || !qrcodeUuid.value) {
      clearInterval(pollTimer)
      return
    }
    
    try {
      const res = await api.checkQRStatus(currentLoginUser.value.id, qrcodeUuid.value)
      if (res.success) {
        const data = res.data
        statusMessage.value = data.message
        
        if (data.status === 0) {
          // 等待扫码
        } else if (data.status === 1) {
          statusMessage.value = '已扫码，请在手机上确认...'
        } else if (data.status === 2 && data.is_success) {
          clearInterval(pollTimer)
          loginState.value = 'success'
          loginUsername.value = currentLoginUser.value.username
          // 刷新用户列表并选中当前用户，确保登录状态持久化
          await userStore.fetchUsers()
          // 使用更新后的用户对象（包含最新的登录状态）
          const updatedUser = userStore.users.find(u => u.id === currentLoginUser.value.id)
          if (updatedUser) {
            await userStore.selectUser(updatedUser)
          }
        } else if (data.status === 3) {
          clearInterval(pollTimer)
          qrcodeExpired.value = true
          statusMessage.value = '二维码已过期'
        } else {
          clearInterval(pollTimer)
          loginState.value = 'error'
        }
      }
    } catch (error) {
      console.error('轮询状态失败:', error)
    }
  }, 2000)
}

const refreshQRCode = () => {
  if (currentLoginUser.value) {
    startLogin(currentLoginUser.value)
  }
}
</script>

<style scoped>
.login-page {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.qrcode-container {
  min-height: 350px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.qrcode-wrapper {
  position: relative;
  width: 200px;
  height: 200px;
  margin-bottom: 16px;
}

.qrcode-wrapper img {
  width: 100%;
  height: 100%;
}

.qrcode-expired {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  cursor: pointer;
  gap: 8px;
}

.tips {
  color: #909399;
  font-size: 14px;
}

.login-row {
  display: flex;
  align-items: stretch;
}

.login-row .el-col {
  display: flex;
  flex-direction: column;
}

.login-row .el-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 500px;
}

.login-row .el-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

@media (max-width: 768px) {
  .login-row {
    flex-wrap: wrap; /* 允许换行 */
  }
  
  .mb-mobile {
    margin-bottom: 12px; /* 移动端两列之间的间距 */
  }
  
  .login-row .el-card {
    min-height: 400px; /* 移动端减小最小高度 */
  }
}
</style>
