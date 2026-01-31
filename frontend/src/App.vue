<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <el-container>
        <el-header>
          <div class="header-content">
            <div class="logo-area">
              <el-icon 
                class="collapse-btn" 
                size="24" 
                @click="toggleCollapse"
              >
                <component :is="isCollapse ? 'Expand' : 'Fold'" />
              </el-icon>
              <div class="logo">
                <span>{{ pageTitle }}</span>
              </div>
            </div>
          </div>
        </el-header>
        
        <el-container class="main-container">
          <div 
            v-if="isMobile && !isCollapse" 
            class="mobile-mask"
            @click="toggleCollapse"
          ></div>

          <el-aside :width="asideWidth">
            <div class="aside-layout">
              <el-menu
                :default-active="route.path"
                router
                class="side-menu"
                :collapse="isCollapse"
                :collapse-transition="false"
              >
                <el-menu-item index="/">
                  <el-icon><HomeFilled /></el-icon>
                  <template #title>首页</template>
                </el-menu-item>
                <el-menu-item index="/login">
                  <el-icon><User /></el-icon>
                  <template #title>账号管理</template>
                </el-menu-item>
                <el-menu-item index="/tasks">
                  <el-icon><List /></el-icon>
                  <template #title>任务列表</template>
                </el-menu-item>
                <el-menu-item index="/create-task">
                  <el-icon><Plus /></el-icon>
                  <template #title>创建任务</template>
                </el-menu-item>
                <el-menu-item index="/query">
                  <el-icon><Search /></el-icon>
                  <template #title>车票查询</template>
                </el-menu-item>
                <el-menu-item index="/notification">
                  <el-icon><Bell /></el-icon>
                  <template #title>通知配置</template>
                </el-menu-item>
              </el-menu>
              
              <div class="user-info-footer" v-if="userStore.currentUser">
                <el-dropdown placement="top" style="width: 100%;">
                  <div class="user-dropdown-footer" :class="{ 'collapsed': isCollapse }">
                    <el-avatar :size="32" class="user-avatar">{{ userStore.currentUser.username[0] }}</el-avatar>
                    <div class="user-details" v-if="!isCollapse">
                      <span class="username-text">{{ userStore.currentUser.username }}</span>
                    </div>
                    <el-icon v-if="!isCollapse" class="dropdown-icon"><ArrowUp /></el-icon>
                  </div>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="handleLogout">
                        <el-icon><SwitchButton /></el-icon>
                        退出登录
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </el-aside>
          
          <el-main>
            <router-view />
          </el-main>
        </el-container>
      </el-container>
    </div>
  </el-config-provider>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from './stores/user'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { Bell } from '@element-plus/icons-vue'

const route = useRoute()
const userStore = useUserStore()
const isCollapse = ref(false)
const isMobile = ref(false)

const asideWidth = computed(() => {
  if (isMobile.value) {
    return isCollapse.value ? '0px' : '200px'
  }
  return isCollapse.value ? '64px' : '200px'
})

const pageTitle = computed(() => {
  const path = route.path
  if (path === '/') return '首页'
  if (path === '/login') return '账号管理'
  if (path === '/tasks') return '任务列表'
  if (path === '/create-task') return '创建任务'
  if (path === '/query') return '车票查询'
  if (path === '/notification') return '通知配置'
  if (path.startsWith('/task/')) return '任务详情'
  if (path.startsWith('/edit-task/')) return '编辑任务'
  return '12306 自动化抢票系统'
})

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}


// 应用启动时恢复用户状态
onMounted(async () => {
  await userStore.restoreUser()
  
  // 检测屏幕尺寸并设置初始折叠状态
  checkScreenSize()
  
  // 监听窗口尺寸变化
  window.addEventListener('resize', checkScreenSize)
})

// 检测屏幕尺寸
const checkScreenSize = () => {
  const width = window.innerWidth
  isMobile.value = width < 768
  // 屏幕宽度小于 768px 时自动折叠
  if (width < 768) {
    isCollapse.value = true
  } else {
    isCollapse.value = false
  }
}

const handleLogout = () => {
  userStore.logout()
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}

.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.el-container {
  height: 100%;
}

.main-container {
  position: relative;
}

.el-header {
  background: linear-gradient(90deg, #409EFF 0%, #3a8ee6 100%);
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
  height: 50px;
  flex-shrink: 0;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  cursor: pointer;
  opacity: 0.8;
  transition: opacity 0.3s;
}

.collapse-btn:hover {
  opacity: 1;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
}

.el-aside {
  background: #fff;
  border-right: 1px solid #e4e7ed;
  transition: width 0.3s;
  overflow: hidden;
}

.aside-layout {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.side-menu {
  border-right: none;
  background: transparent;
  flex: 1;
  overflow-y: auto;
}

.el-menu--collapse .el-menu-item {
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  padding: 0 !important;
}

.el-menu--collapse .el-menu-item .el-icon {
  margin: 0 !important;
  /* 确保图标自身没有偏移 */
  position: static !important; 
  left: auto !important;
  transform: none !important;
}

/* 隐藏折叠时的文字，防止撑开布局 */
.el-menu--collapse .el-menu-item span {
  display: none !important;
}

.el-menu--collapse .el-menu-item .el-menu-tooltip__trigger {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  padding: 0 !important;
}

/* 如果有 tooltip wrapper，需要穿透样式 */
.el-menu--collapse > div > .el-menu-item,
.el-menu--collapse > .el-sub-menu > .el-sub-menu__title {
  display: flex !important;
  justify-content: center !important;
  padding: 0 !important;
}

.user-info-footer {
  padding: 12px;
  border-top: 1px solid #eba6a6; /* Just a placeholder border color, will use lighter one */
  border-top: 1px solid #f0f0f0;
}

.user-dropdown-footer {
  display: flex;
  align-items: center;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.3s;
  width: 100%;
  box-sizing: border-box;
  color: #606266;
  overflow: hidden;
}

.user-dropdown-footer:hover {
  background-color: #f5f7fa;
}

.user-dropdown-footer.collapsed {
  justify-content: center;
  padding: 8px 0;
}

.user-avatar {
  background: #764ba2;
  color: white;
  flex-shrink: 0;
}

.user-details {
  margin-left: 12px;
  flex: 1;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.username-text {
  font-size: 14px;
  font-weight: 500;
}

.dropdown-icon {
  margin-left: auto;
  font-size: 12px;
}

.el-main {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .el-header {
    padding: 0 12px;
    height: 48px;
  }
  
  .logo span {
    font-size: 16px;
  }
  
  .el-main {
    padding: 12px;
  }
  
  /* 移动端折叠侧边栏更窄 (now controlled by computed prop, but keep important override just in case or remove it) */
  /* Remove width override since we use computed style */
  /* .el-aside { width: 50px !important; } */
  
  .user-info-footer {
    padding: 8px 4px;
  }
  
  /* 移动端叠加样式 */
  .el-aside {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    z-index: 2000;
    /* width 由 inline style (computed asideWidth) 控制，不需要在这里强制设置 */
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
  }
  
  /* 当折叠时宽度为 0，这一条由 inline style 或者 computed 控制，但在 CSS 中也可以辅助控制 */
  /* 注意：inline style 优先级高，这里只需要负责非折叠状态的样式 */
  
  .mobile-mask {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 1999;
  }
}
</style>
