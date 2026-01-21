<template>
  <div class="tasks-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>任务列表</span>
          <div class="header-actions">
            <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 120px; margin-right: 12px;">
              <el-option label="全部" value="" />
              <el-option label="待运行" value="pending" />
              <el-option label="运行中" value="running" />
              <el-option label="已暂停" value="paused" />
              <el-option label="成功" value="success" />
              <el-option label="失败" value="failed" />
            </el-select>
            <el-button type="primary" @click="$router.push('/create-task')">
              <el-icon><Plus /></el-icon>
              创建任务
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="filteredTasks" stripe v-loading="taskStore.loading">
        <el-table-column prop="name" label="任务名称" min-width="150">
          <template #default="{ row }">
            <el-link type="primary" @click="$router.push(`/task/${row.id}`)">
              {{ row.name }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column label="行程" min-width="160">
          <template #default="{ row }">
            {{ row.from_station }} → {{ row.to_station }}
          </template>
        </el-table-column>
        <el-table-column prop="train_date" label="日期" width="110" />
        <el-table-column prop="seat_types" label="席别" width="100" />
        <el-table-column prop="retry_count" label="重试次数" width="90" align="center" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button 
                v-if="row.status === 'pending' || row.status === 'paused' || row.status === 'failed' || row.status === 'cancelled'"
                type="primary" 
                size="small"
                @click="$router.push(`/edit-task/${row.id}`)"
              >
                编辑
              </el-button>
              <el-button 
                v-if="['pending', 'paused'].includes(row.status)"
                type="success" 
                size="small"
                :loading="processingTasks[row.id]"
                @click="handleStart(row)"
              >
                启动
              </el-button>
              <el-button 
                v-if="row.status === 'running'" 
                type="warning" 
                size="small"
                :loading="processingTasks[row.id]"
                @click="handleStop(row)"
              >
                暂停
              </el-button>
              <el-button 
                v-if="row.status !== 'success' && row.status !== 'cancelled'" 
                type="danger" 
                size="small"
                :loading="processingTasks[row.id]"
                @click="handleCancel(row)"
              >
                取消
              </el-button>
              <el-button 
                v-if="row.status !== 'running'" 
                type="danger" 
                size="small"
                text
                :loading="processingTasks[row.id]"
                @click="handleDelete(row)"
              >
                删除
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
      
      <el-empty v-if="filteredTasks.length === 0 && !taskStore.loading" description="暂无任务">
        <el-button type="primary" @click="$router.push('/create-task')">创建任务</el-button>
      </el-empty>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useTaskStore } from '../stores/task'
import { useUserStore } from '../stores/user'

const taskStore = useTaskStore()
const userStore = useUserStore()

const filterStatus = ref('')
const processingTasks = ref({})

const filteredTasks = computed(() => {
  if (!filterStatus.value) return taskStore.tasks
  return taskStore.tasks.filter(t => t.status === filterStatus.value)
})

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

const handleStart = async (task) => {
  processingTasks.value[task.id] = true
  try {
    await taskStore.startTask(task.id)
    ElMessage.success('任务已启动')
    await taskStore.fetchTasks()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    processingTasks.value[task.id] = false
  }
}

const handleStop = async (task) => {
  processingTasks.value[task.id] = true
  try {
    await taskStore.stopTask(task.id)
    ElMessage.success('任务已暂停')
    await taskStore.fetchTasks()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    processingTasks.value[task.id] = false
  }
}

const handleCancel = async (task) => {
  try {
    await ElMessageBox.confirm('确定要取消该任务吗？', '确认')
    processingTasks.value[task.id] = true
    await taskStore.cancelTask(task.id)
    ElMessage.success('任务已取消')
    await taskStore.fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message)
    }
  } finally {
    processingTasks.value[task.id] = false
  }
}

const handleDelete = async (task) => {
  try {
    await ElMessageBox.confirm('确定要删除该任务吗？此操作不可恢复。', '确认删除', { type: 'warning' })
    processingTasks.value[task.id] = true
    await taskStore.deleteTask(task.id)
    ElMessage.success('任务已删除')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message)
    }
  } finally {
     if (task) processingTasks.value[task.id] = false
  }
}

onMounted(async () => {
  await taskStore.fetchTasks()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
}
</style>
