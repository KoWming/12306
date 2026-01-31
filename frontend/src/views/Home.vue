<template>
  <div class="home-page">
    <el-row :gutter="12" class="banner-row">
      <el-col :span="24">
        <div class="welcome-banner">
          <div class="banner-content">
             <el-icon size="48"><Promotion /></el-icon>
             <div>
               <h1>欢迎使用 12306 自动化抢票系统</h1>
               <p>自动刷票 · 智能抢票 · 多任务并行</p>
             </div>
          </div>
        </div>
      </el-col>
    </el-row>
    
    <el-row :gutter="12" class="stats-row">
      <el-col :xs="12" :sm="12" :md="6" :lg="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="icon-wrapper bg-blue">
              <el-icon size="24" color="#409EFF"><User /></el-icon>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ userStore.users.length }}</span>
              <span class="stat-label">账号数量</span>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="12" :sm="12" :md="6" :lg="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
             <div class="icon-wrapper bg-green">
              <el-icon size="24" color="#67C23A"><List /></el-icon>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ taskStore.tasks.length }}</span>
              <span class="stat-label">任务总数</span>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="12" :sm="12" :md="6" :lg="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
             <div class="icon-wrapper bg-orange">
              <el-icon size="24" color="#E6A23C"><Loading /></el-icon>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ runningTasks }}</span>
              <span class="stat-label">运行中</span>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="12" :sm="12" :md="6" :lg="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
             <div class="icon-wrapper bg-red">
              <el-icon size="24" color="#F56C6C"><SuccessFilled /></el-icon>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ successTasks }}</span>
              <span class="stat-label">成功订单</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="12" class="section-row">
      <el-col :xs="24" :sm="24" :md="12" :lg="12">
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
            <el-button size="large" @click="$router.push('/login')" class="quick-btn">
              <el-icon><User /></el-icon>
              管理账号
            </el-button>
            <el-button type="success" size="large" @click="$router.push('/create-task')" class="quick-btn">
              <el-icon><Plus /></el-icon>
              创建任务
            </el-button>
            <el-button size="large" @click="$router.push('/query')" class="quick-btn">
              <el-icon><Search /></el-icon>
              查询车票
            </el-button>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="24" :md="12" :lg="12">
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
            <el-table-column prop="name" label="任务名称" min-width="120" show-overflow-tooltip />
            <el-table-column prop="train_date" label="出发日期" min-width="110" align="center" />
            <el-table-column prop="status" label="状态" min-width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <template #empty>
              <el-empty description="暂无任务" />
            </template>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useUserStore } from '../stores/user'
import { useTaskStore } from '../stores/task'

const userStore = useUserStore()
const taskStore = useTaskStore()
const isMobile = ref(false)

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

const checkScreenSize = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(async () => {
  // 只刷新任务列表，用户状态已在 App.vue 中恢复
  await taskStore.fetchTasks()
  checkScreenSize()
  window.addEventListener('resize', checkScreenSize)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkScreenSize)
})
</script>

<style scoped>
.home-page {
  padding: 0;
}

.welcome-banner {
  background: linear-gradient(135deg, #409EFF 0%, #3a8ee6 100%);
  color: white;
  padding: 16px 20px;
  border-radius: 8px;
  margin-bottom: 12px;
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.welcome-banner h1 {
  margin: 0 0 4px;
  font-size: 20px;
}

.welcome-banner p {
  margin: 0;
  opacity: 0.9;
  font-size: 13px;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .welcome-banner {
    padding: 12px 16px;
  }
  
  .welcome-banner h1 {
    font-size: 16px;
  }
  
  .welcome-banner p {
    font-size: 12px;
  }
  
  .banner-content {
    gap: 12px;
  }
  
  .banner-content .el-icon {
    font-size: 36px !important;
  }
  
  /* 移除内部 margin，由 banner-row 统一控制 */
  .welcome-banner {
    margin-bottom: 0;
  }
}

.stats-row {
  margin-bottom: 12px;
}

.stat-card {
  cursor: pointer;
  transition: all 0.3s;
  border: none;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 0;
}

.icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.bg-blue { background-color: #ecf5ff; }
.bg-green { background-color: #f0f9eb; }
.bg-orange { background-color: #fdf6ec; }
.bg-red { background-color: #fef0f0; }

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  color: #909399;
  font-size: 12px;
  margin-top: 2px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

/* Ensure card body takes remaining space if needed, though mostly just card height matters */
.section-row .el-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.quick-actions {
  flex: 1;
  display: flex;
  gap: 12px;
  justify-content: center;
  align-items: center;
  margin-top: 0;
}

.section-row {
  display: flex;
  align-items: stretch;
}

.section-row .el-card {
  height: 100%;
  min-height: 280px;
  display: flex;
  flex-direction: column;
}

:deep(.el-step__title) {
  white-space: nowrap;
  font-size: 14px;
}

:deep(.el-card__header) {
    padding: 10px 20px;
}

.quick-btn {
  width: 140px;
}

/* 移动端按钮响应式布局 */
@media (max-width: 768px) {
  /* 移动端按钮响应式布局 */
  .quick-actions {
    flex-direction: row; /* 恢复水平排列 */
    gap: 8px; /* 减小间距 */
    padding: 0;
    margin-top: 12px; /* 增加与上方流程的间距 */
  }
  
  .quick-btn {
    width: auto;
    flex: 1; /* 平分宽度 */
    padding: 6px 0 !important; /* 极窄内边距 */
    font-size: 11px; /* 字体再小一点 */
    height: 32px !important; /* 高度减小 */
  }
  
  .quick-btn .el-icon {
    display: none; /* 移动端隐藏图标只显示文字，确保装得下 */
  }
  
  /* 缩小步骤条 */
  :deep(.el-step.is-simple .el-step__title) {
    font-size: 10px; /* 字体缩小到 10px */
    line-height: 1.2;
    padding: 0;
    font-weight: normal; /* 减轻视觉重量 */
  }
  
  :deep(.el-step.is-simple .el-step__icon) {
    width: 16px; /* 图标缩小 */
    height: 16px;
    font-size: 10px;
  }
  
  :deep(.el-steps--simple) {
    padding: 8px 4px; /* 减小步骤条容器内边距 */
    background: #f5f7fa50; /* 稍微淡一点的背景，或者保持原样 */
  }
  
  .section-row .el-card {
    min-height: auto;
  }
  
  .section-row .el-card :deep(.el-card__body) {
    padding: 12px;
  }
  
  :deep(.el-card__header) {
    padding: 8px 12px;
  }
  
  .stat-card :deep(.el-card__body) {
    padding: 12px;
  }
  
  /* 容器不设下边距，由内部卡片撑开，或者最后一行卡片提供下边距 */
  .stats-row {
     margin-bottom: 0px;
  }
  
  .banner-row {
    margin-bottom: 12px;
  }
  
  /* 统计卡片垂直间距（针对多行情况） */
  .stat-card {
    margin-bottom: 12px;
  }
  
  /* 快速开始和最近任务的垂直间距 */
  .section-row .el-col {
    margin-bottom: 12px;
  }
  
  .section-row .el-col:last-child {
     margin-bottom: 0;
  }
}
</style>
