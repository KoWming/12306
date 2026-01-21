<template>
  <div class="home-page">
    <el-row :gutter="20">
      <el-col :span="24">
        <div class="welcome-banner">
          <el-icon size="64"><Promotion /></el-icon>
          <h1>欢迎使用 12306 自动化抢票系统</h1>
          <p>自动刷票、智能抢票、支持多任务并行</p>
        </div>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <el-icon size="40" color="#409EFF"><User /></el-icon>
            <div class="stat-info">
              <span class="stat-value">{{ userStore.users.length }}</span>
              <span class="stat-label">账号数量</span>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <el-icon size="40" color="#67C23A"><List /></el-icon>
            <div class="stat-info">
              <span class="stat-value">{{ taskStore.tasks.length }}</span>
              <span class="stat-label">任务总数</span>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <el-icon size="40" color="#E6A23C"><Loading /></el-icon>
            <div class="stat-info">
              <span class="stat-value">{{ runningTasks }}</span>
              <span class="stat-label">运行中</span>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <el-icon size="40" color="#F56C6C"><SuccessFilled /></el-icon>
            <div class="stat-info">
              <span class="stat-value">{{ successTasks }}</span>
              <span class="stat-label">成功订单</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>快速开始</span>
            </div>
          </template>
          <el-steps :active="currentStep" finish-status="success" simple>
            <el-step title="创建账号" />
            <el-step title="扫码登录" />
            <el-step title="创建任务" />
            <el-step title="开始抢票" />
          </el-steps>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/login')">
              <el-icon><User /></el-icon>
              管理账号
            </el-button>
            <el-button type="success" @click="$router.push('/create-task')">
              <el-icon><Plus /></el-icon>
              创建任务
            </el-button>
            <el-button @click="$router.push('/query')">
              <el-icon><Search /></el-icon>
              查询车票
            </el-button>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近任务</span>
              <el-button text type="primary" @click="$router.push('/tasks')">
                查看全部
              </el-button>
            </div>
          </template>
          <el-table :data="recentTasks" stripe style="width: 100%" max-height="300">
            <el-table-column prop="name" label="任务名称" />
            <el-table-column prop="train_date" label="出发日期" width="120" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="recentTasks.length === 0" description="暂无任务" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import { useTaskStore } from '../stores/task'

const userStore = useUserStore()
const taskStore = useTaskStore()

const runningTasks = computed(() => 
  taskStore.tasks.filter(t => t.status === 'running').length
)

const successTasks = computed(() => 
  taskStore.tasks.filter(t => t.status === 'success').length
)

const currentStep = computed(() => {
  if (successTasks.value > 0) return 4
  if (taskStore.tasks.length > 0) return 3
  if (userStore.isLoggedIn) return 2
  if (userStore.users.length > 0) return 1
  return 0
})

const recentTasks = computed(() => 
  taskStore.tasks.slice(0, 5)
)

const getStatusType = (status) => {
  const types = {
    pending: 'info',
    running: 'warning',
    paused: '',
    success: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    pending: '待运行',
    running: '运行中',
    paused: '已暂停',
    success: '成功',
    failed: '失败',
    cancelled: '已取消'
  }
  return texts[status] || status
}

onMounted(async () => {
  // 只刷新任务列表，用户状态已在 App.vue 中恢复
  await taskStore.fetchTasks()
})
</script>

<style scoped>
.home-page {
  padding: 0;
}

.welcome-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 40px;
  border-radius: 8px;
  text-align: center;
  margin-bottom: 20px;
}

.welcome-banner h1 {
  margin: 16px 0 8px;
}

.welcome-banner p {
  opacity: 0.9;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  color: #909399;
  font-size: 14px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.quick-actions {
  margin-top: 24px;
  display: flex;
  gap: 12px;
  justify-content: center;
}
</style>
