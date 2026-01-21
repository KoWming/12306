<template>
  <div class="task-detail-page" v-if="task">
    <el-page-header @back="$router.back()">
      <template #content>
        <span class="text-large font-600 mr-3">{{ task.name }}</span>
        <el-tag :type="getStatusType(task.status)">{{ getStatusText(task.status) }}</el-tag>
      </template>
      <template #extra>
        <el-button-group>
          <el-button 
            v-if="task.status === 'pending' || task.status === 'paused'" 
            type="success"
            @click="handleStart"
          >
            启动任务
          </el-button>
          <el-button 
            v-if="task.status === 'running'" 
            type="warning"
            @click="handleStop"
          >
            暂停任务
          </el-button>
          <el-button 
            v-if="task.status === 'running'" 
            type="danger"
            @click="handleCancel"
          >
            取消任务
          </el-button>
        </el-button-group>
      </template>
    </el-page-header>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>任务信息</template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="行程">
              {{ task.from_station }} → {{ task.to_station }}
            </el-descriptions-item>
            <el-descriptions-item label="日期">
              {{ task.train_date }}
            </el-descriptions-item>
            <el-descriptions-item label="车次类型">
              {{ task.train_types || '不限' }}
            </el-descriptions-item>
            <el-descriptions-item label="席别">
              {{ formatSeatTypes(task.seat_types) }}
            </el-descriptions-item>
            <el-descriptions-item label="指定车次">
              {{ task.train_codes || '不限' }}
            </el-descriptions-item>
            <el-descriptions-item label="时间段">
              {{ task.start_time_range || '全天' }}
            </el-descriptions-item>
            <el-descriptions-item label="刷票间隔">
              {{ task.query_interval }} 秒
            </el-descriptions-item>
            <el-descriptions-item label="重试次数">
              {{ task.retry_count }} / {{ task.max_retry_count }}
            </el-descriptions-item>
            <el-descriptions-item label="自动提交" :span="2">
              <el-tag :type="task.auto_submit ? 'success' : 'info'">
                {{ task.auto_submit ? '是' : '否' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatTime(task.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="开始时间">
              {{ formatTime(task.started_at) }}
            </el-descriptions-item>
          </el-descriptions>
          
          <div v-if="task.status === 'success'" class="success-info">
            <el-result icon="success" title="抢票成功！">
              <template #sub-title>
                订单号: {{ task.order_id }}
              </template>
              <template #extra>
                <el-button type="primary">去支付</el-button>
              </template>
            </el-result>
          </div>
          
          <div v-if="task.status === 'failed'" class="failed-info">
            <el-result icon="error" title="任务失败">
              <template #sub-title>
                {{ task.result_message }}
              </template>
            </el-result>
          </div>
        </el-card>
        
        <el-card style="margin-top: 16px;">
          <template #header>乘车人</template>
          <el-table :data="passengers" stripe>
            <el-table-column prop="passenger_name" label="姓名" />
            <el-table-column prop="passenger_id_no" label="证件号">
              <template #default="{ row }">
                {{ maskIdNo(row.passenger_id_no) }}
              </template>
            </el-table-column>
            <el-table-column prop="mobile_no" label="手机号" />
          </el-table>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>运行日志</span>
              <el-button text type="primary" @click="refreshLogs">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>
          
          <div class="log-container">
            <el-timeline>
              <el-timeline-item
                v-for="log in taskStore.taskLogs"
                :key="log.id"
                :type="getLogType(log.level)"
                :timestamp="formatTime(log.created_at)"
                placement="top"
              >
                <div style="white-space: pre-wrap; word-break: break-all; line-height: 1.5;">{{ log.message }}</div>
              </el-timeline-item>
            </el-timeline>
            
            <el-empty v-if="taskStore.taskLogs.length === 0" description="暂无日志" />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
  
  <el-empty v-else description="任务不存在" />
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useTaskStore } from '../stores/task'

const route = useRoute()
const router = useRouter()
const taskStore = useTaskStore()

const task = computed(() => taskStore.currentTask)

const passengers = computed(() => {
  if (!task.value?.passengers) return []
  try {
    return JSON.parse(task.value.passengers)
  } catch {
    return []
  }
})

let refreshTimer = null

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

const getLogType = (level) => {
  const types = {
    info: 'primary',
    success: 'success',
    warning: 'warning',
    error: 'danger'
  }
  return types[level] || 'primary'
}

const formatSeatTypes = (types) => {
  if (!types) return ''
  const map = {
    'O': '二等座',
    'M': '一等座',
    '9': '商务座',
    '3': '硬卧',
    '4': '软卧',
    '1': '硬座'
  }
  return types.split(',').map(t => map[t] || t).join(', ')
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const maskIdNo = (idNo) => {
  if (!idNo || idNo.length < 8) return idNo
  return idNo.slice(0, 4) + '****' + idNo.slice(-4)
}

const handleStart = async () => {
  try {
    await taskStore.startTask(task.value.id)
    ElMessage.success('任务已启动')
    await taskStore.getTask(task.value.id)
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const handleStop = async () => {
  try {
    await taskStore.stopTask(task.value.id)
    ElMessage.success('任务已暂停')
    await taskStore.getTask(task.value.id)
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const handleCancel = async () => {
  try {
    await ElMessageBox.confirm('确定要取消该任务吗？', '确认')
    await taskStore.cancelTask(task.value.id)
    ElMessage.success('任务已取消')
    await taskStore.getTask(task.value.id)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message)
    }
  }
}

const refreshLogs = async () => {
  if (task.value) {
    await taskStore.fetchTaskLogs(task.value.id)
  }
}

onMounted(async () => {
  const taskId = parseInt(route.params.id)
  await taskStore.getTask(taskId)
  await taskStore.fetchTaskLogs(taskId)
  
  // start log polling
  startLogPolling(taskId)
})

const startLogPolling = (taskId) => {
  stopLogPolling()
  refreshTimer = setInterval(async () => {
    // Only fetch if tab is visible/active (optional optimization, skipping for now)
    
    // Check if task is running to decide if we need aggressive polling
    // But logs might come in a bit after it stops, so we poll regardless or check status
    if (task.value?.status === 'running') {
       await taskStore.fetchTaskLogs(taskId)
       // Update task info too (to see status changes)
       await taskStore.getTask(taskId)
    } else {
       // If not running, maybe poll slower or stop?
       // For now let's just keep polling status to see if it starts, 
       // but maybe less frequent for logs?
       // Actually, just polling task status is enough if not running.
       await taskStore.getTask(taskId)
       // If status changed to running, we will catch it in next tick
    }
  }, 3000)
}

const stopLogPolling = () => {
    if (refreshTimer) {
        clearInterval(refreshTimer)
        refreshTimer = null
    }
}

onUnmounted(() => {
  stopLogPolling()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.success-info,
.failed-info {
  margin-top: 20px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.log-container {
  max-height: 600px;
  overflow-y: auto;
  padding-right: 10px;
}
</style>
