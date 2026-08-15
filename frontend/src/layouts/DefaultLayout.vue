<template>
  <div class="layout">
    <el-container class="layout-container">
      <!-- 侧边栏 -->
      <el-aside width="220px" class="sidebar">
        <div class="brand" @click="router.push('/')">
          <span class="brand-logo">🎌</span>
          <span class="brand-name">ACG 收藏馆</span>
        </div>
        <el-menu
          :default-active="activeMenu"
          class="side-menu"
          router
          background-color="transparent"
          text-color="#8a8fa3"
          active-text-color="#7c5cff"
        >
          <el-menu-item index="/">
            <el-icon><Collection /></el-icon>
            <span>作品列表</span>
          </el-menu-item>
          <el-menu-item index="/stats">
            <el-icon><DataAnalysis /></el-icon>
            <span>统计概览</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container>
        <!-- 顶栏 -->
        <el-header class="header">
          <div class="header-left">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
              <el-breadcrumb-item>{{ route.meta.title }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          <div class="header-right">
            <template v-if="auth.isLoggedIn">
              <el-tag effect="plain" round>{{ auth.username }}</el-tag>
              <el-button link type="primary" @click="handleLogout">
                <el-icon><SwitchButton /></el-icon>&nbsp;退出
              </el-button>
            </template>
            <template v-else>
              <el-button type="primary" round @click="router.push('/login')">
                登录 / 注册
              </el-button>
            </template>
          </div>
        </el-header>

        <!-- 内容区 -->
        <el-main class="main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessageBox, ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const activeMenu = computed(() => '/' + (route.path.split('/')[1] || ''))

async function handleLogout() {
  await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '退出',
    cancelButtonText: '取消',
    type: 'warning',
  })
  auth.logout()
  ElMessage.success('已退出登录')
  router.push('/')
}
</script>

<style scoped>
.layout {
  height: 100%;
}
.layout-container {
  height: 100%;
}

.sidebar {
  background: #16182a;
  display: flex;
  flex-direction: column;
}
.brand {
  height: 64px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 20px;
  cursor: pointer;
}
.brand-logo {
  font-size: 24px;
}
.brand-name {
  color: #fff;
  font-weight: 700;
  font-size: 17px;
  letter-spacing: 0.5px;
}
.side-menu {
  border-right: none;
  flex: 1;
}
.side-menu .el-menu-item {
  height: 48px;
  margin: 4px 10px;
  border-radius: 8px;
}
.side-menu .el-menu-item.is-active {
  background: rgba(124, 92, 255, 0.16);
}
.side-menu .el-menu-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.header {
  background: #fff;
  border-bottom: 1px solid #eef0f8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  padding: 0 24px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.main {
  background: var(--acg-bg);
  padding: 0;
  overflow-y: auto;
}
</style>