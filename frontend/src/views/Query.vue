<template>
  <div class="query-page">
    <el-card>
      <template #header>
        <span>车票查询</span>
      </template>
      
      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item label="出发站">
          <el-select 
            v-model="queryForm.from_station" 
            filterable 
            remote
            :remote-method="searchFromStation"
            :loading="loadingFrom"
            placeholder="输入站名"
            style="width: 150px;"
          >
            <el-option 
              v-for="s in fromStations" 
              :key="s.code" 
              :label="s.name" 
              :value="s.name"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button :icon="Switch" circle @click="swapStations" />
        </el-form-item>
        
        <el-form-item label="到达站">
          <el-select 
            v-model="queryForm.to_station" 
            filterable 
            remote
            :remote-method="searchToStation"
            :loading="loadingTo"
            placeholder="输入站名"
            style="width: 150px;"
          >
            <el-option 
              v-for="s in toStations" 
              :key="s.code" 
              :label="s.name" 
              :value="s.name"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="出发日期">
          <el-date-picker
            v-model="queryForm.train_date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 150px;"
          />
        </el-form-item>
        
        <el-form-item label="车次类型">
          <el-select v-model="queryForm.train_types" placeholder="全部" clearable style="width: 120px;">
            <el-option label="高铁 G" value="G" />
            <el-option label="动车 D" value="D" />
            <el-option label="城际 C" value="C" />
            <el-option label="直达 Z" value="Z" />
            <el-option label="特快 T" value="T" />
            <el-option label="快速 K" value="K" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="queryForm.only_has_ticket">只看有票</el-checkbox>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleQuery" :loading="loading">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card style="margin-top: 16px;" v-if="trains.length > 0 || loading">
      <template #header>
        <div class="result-header">
          <div style="display: flex; gap: 10px; align-items: center;">
            <span>查询结果 ({{ trains.length }} 趟)</span>
            <el-tag v-if="queryForm.train_date">{{ queryForm.train_date }}</el-tag>
          </div>
          <el-button 
            type="success" 
            size="small" 
            :icon="Ticket" 
            :disabled="selectedTrains.length === 0"
            @click="handleCreateTask"
          >
            创建抢票任务 (选 {{ selectedTrains.length }})
          </el-button>
        </div>
      </template>
      
      <el-table :data="trains" stripe v-loading="loading" max-height="500" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="45" fixed />
        <el-table-column prop="train_code" label="车次" width="80" fixed>
          <template #default="{ row }">
            <el-tag :type="getTrainType(row.train_code)" size="small">
              {{ row.train_code }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="出发/到达" width="180">
          <template #default="{ row }">
            <div class="station-info">
              <div>{{ row.from_station }}</div>
              <div class="time">{{ row.start_time }}</div>
            </div>
            <el-icon><Right /></el-icon>
            <div class="station-info">
              <div>{{ row.to_station }}</div>
              <div class="time">{{ row.arrive_time }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="历时" width="80" align="center" />
        <el-table-column prop="business_seat" label="商务座" width="70" align="center">
          <template #default="{ row }">
            <span :class="getSeatClass(row.business_seat)">{{ row.business_seat }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="first_seat" label="一等座" width="70" align="center">
          <template #default="{ row }">
            <span :class="getSeatClass(row.first_seat)">{{ row.first_seat }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="second_seat" label="二等座" width="70" align="center">
          <template #default="{ row }">
            <span :class="getSeatClass(row.second_seat)">{{ row.second_seat }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="soft_sleeper" label="软卧" width="70" align="center">
          <template #default="{ row }">
            <span :class="getSeatClass(row.soft_sleeper)">{{ row.soft_sleeper }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="hard_sleeper" label="硬卧" width="70" align="center">
          <template #default="{ row }">
            <span :class="getSeatClass(row.hard_sleeper)">{{ row.hard_sleeper }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="hard_seat" label="硬座" width="70" align="center">
          <template #default="{ row }">
            <span :class="getSeatClass(row.hard_seat)">{{ row.hard_seat }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="no_seat" label="无座" width="70" align="center">
          <template #default="{ row }">
            <span :class="getSeatClass(row.no_seat)">{{ row.no_seat }}</span>
          </template>
        </el-table-column>
        <el-table-column label="备注" min-width="100">
          <template #default="{ row }">
            <el-tag v-if="!row.can_buy" type="info" size="small">不可购买</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Switch, Right, Search, Ticket } from '@element-plus/icons-vue'
import api from '../api'

const router = useRouter()
const loading = ref(false)
const loadingFrom = ref(false)
const loadingTo = ref(false)
const fromStations = ref([])
const selectedTrains = ref([])
const toStations = ref([])
const trains = ref([])

const queryForm = reactive({
  from_station: '',
  to_station: '',
  train_date: '',
  train_types: '',
  only_has_ticket: true
})

const searchFromStation = async (query) => {
  if (!query) return
  loadingFrom.value = true
  try {
    const res = await api.searchStations(query)
    fromStations.value = res.stations || []
  } catch (error) {
    console.error(error)
  } finally {
    loadingFrom.value = false
  }
}

const searchToStation = async (query) => {
  if (!query) return
  loadingTo.value = true
  try {
    const res = await api.searchStations(query)
    toStations.value = res.stations || []
  } catch (error) {
    console.error(error)
  } finally {
    loadingTo.value = false
  }
}

const swapStations = () => {
  const temp = queryForm.from_station
  queryForm.from_station = queryForm.to_station
  queryForm.to_station = temp
}

const handleQuery = async () => {
  if (!queryForm.from_station || !queryForm.to_station || !queryForm.train_date) {
    ElMessage.warning('请填写完整查询条件')
    return
  }
  
  loading.value = true
  try {
    const res = await api.queryTickets({
      from_station: queryForm.from_station,
      to_station: queryForm.to_station,
      train_date: queryForm.train_date,
      train_types: queryForm.train_types || undefined,
      only_has_ticket: queryForm.only_has_ticket
    })
    
    if (res.success) {
      trains.value = res.trains
      if (trains.value.length === 0) {
        ElMessage.info('未找到符合条件的车次')
      }
    } else {
      ElMessage.error(res.message || '查询失败')
    }
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

const handleSelectionChange = (selection) => {
  selectedTrains.value = selection
}

const handleCreateTask = () => {
  const codes = selectedTrains.value.map(t => t.train_code)
  router.push({
    name: 'CreateTask',
    query: {
      from: queryForm.from_station,
      to: queryForm.to_station,
      date: queryForm.train_date,
      codes: codes.join(',')
    }
  })
}

const getTrainType = (code) => {
  if (code.startsWith('G')) return 'danger'
  if (code.startsWith('D')) return 'warning'
  if (code.startsWith('C')) return ''
  if (code.startsWith('Z')) return 'success'
  return 'info'
}

const getSeatClass = (value) => {
  if (!value || value === '--' || value === '无' || value === '*') {
    return 'seat-none'
  }
  if (value === '有') return 'seat-has'
  const num = parseInt(value)
  if (!isNaN(num) && num > 0) return 'seat-has'
  return 'seat-none'
}
</script>

<style scoped>
.query-form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.station-info {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
}

.station-info .time {
  font-size: 12px;
  color: #909399;
}

.seat-has {
  color: #67C23A;
  font-weight: bold;
}

.seat-none {
  color: #C0C4CC;
}
</style>
