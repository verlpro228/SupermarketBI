<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { changeMyPassword } from '@/api/auth'
import { APP_NAME_SHORT, ROLE_LABEL } from '@/constants'
import { filterMenuGroups } from '@/router/menu'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const collapsed = ref(false)

const menuGroups = computed(() => filterMenuGroups(userStore.user?.role ?? ''))
const activeMenu = computed(() => route.path)
const currentTitle = computed(() => (route.meta.title as string) ?? '')
const roleLabel = computed(() => ROLE_LABEL[userStore.user?.role ?? ''] ?? '')

const pwdVisible = ref(false)
const pwdLoading = ref(false)
const pwdForm = reactive({ old_password: '', new_password: '', confirm_password: '' })

function openPwdDialog() {
  pwdForm.old_password = ''
  pwdForm.new_password = ''
  pwdForm.confirm_password = ''
  pwdVisible.value = true
}

async function submitPwd() {
  if (!pwdForm.old_password || !pwdForm.new_password) {
    ElMessage.warning('请填写完整')
    return
  }
  if (pwdForm.new_password.length < 6) {
    ElMessage.warning('新密码至少 6 位')
    return
  }
  if (pwdForm.new_password !== pwdForm.confirm_password) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  pwdLoading.value = true
  try {
    await changeMyPassword({
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password,
    })
    ElMessage.success('密码修改成功，请重新登录')
    pwdVisible.value = false
    userStore.logout()
    router.push('/login')
  } finally {
    pwdLoading.value = false
  }
}

async function handleLogout() {
  await ElMessageBox.confirm('确定要退出登录吗？', '提示', { type: 'warning' })
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<template>
  <el-container class="layout">
    <el-aside :width="collapsed ? '64px' : '210px'" class="aside">
      <div class="logo">
        <span class="logo-badge">
          <el-icon :size="18"><Shop /></el-icon>
        </span>
        <span v-show="!collapsed" class="logo-text">{{ APP_NAME_SHORT }}</span>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="collapsed"
        :collapse-transition="false"
        router
        background-color="#ffffff"
        text-color="#5a6b85"
        active-text-color="#3f7df3"
        class="menu"
      >
        <el-menu-item-group
          v-for="(group, index) in menuGroups"
          :key="index"
          :title="collapsed ? '' : group.title"
        >
          <el-menu-item v-for="item in group.items" :key="item.path" :index="item.path">
            <el-icon><component :is="item.icon" /></el-icon>
            <template #title>{{ item.title }}</template>
          </el-menu-item>
        </el-menu-item-group>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" :size="18" @click="collapsed = !collapsed">
            <Fold v-if="!collapsed" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <el-dropdown trigger="click">
          <span class="user-entry">
            <el-avatar :size="32" src="/images/avatar.jpg" class="user-avatar" />
            <span class="username">{{ userStore.displayName }}</span>
            <el-tag size="small" :type="userStore.isAdmin ? 'danger' : 'info'" effect="plain">
              {{ roleLabel }}
            </el-tag>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="openPwdDialog">修改密码</el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>

  <el-dialog v-model="pwdVisible" title="修改密码" width="420px">
    <el-form label-width="88px">
      <el-form-item label="原密码">
        <el-input v-model="pwdForm.old_password" type="password" show-password />
      </el-form-item>
      <el-form-item label="新密码">
        <el-input v-model="pwdForm.new_password" type="password" show-password />
      </el-form-item>
      <el-form-item label="确认密码">
        <el-input v-model="pwdForm.confirm_password" type="password" show-password />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="pwdVisible = false">取消</el-button>
      <el-button type="primary" :loading="pwdLoading" @click="submitPwd">确定</el-button>
    </template>
  </el-dialog>
</template>

<style scoped lang="scss">
.layout {
  height: 100%;
}

.aside {
  background-color: #fff;
  border-right: 1px solid #eef2f8;
  transition: width 0.2s;
  overflow-x: hidden;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid #f2f5fa;
}

.logo-badge {
  width: 32px;
  height: 32px;
  flex: none;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: linear-gradient(135deg, #5b9bff, #3f7df3);
  box-shadow: 0 6px 14px rgba(63, 125, 243, 0.28);
}

.logo-text {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.5px;
  color: #1b2a41;
  white-space: nowrap;
}

.menu {
  border-right: none;
  padding: 6px 0;

  :deep(.el-menu-item) {
    height: 44px;
    line-height: 44px;
    margin: 4px 10px;
    border-radius: 10px;
    font-size: 14px;
  }

  :deep(.el-menu-item:hover) {
    background-color: #f4f8ff;
  }

  :deep(.el-menu-item.is-active) {
    background-color: #eaf2ff;
    font-weight: 600;
  }

  :deep(.el-menu-item-group__title) {
    padding: 12px 0 4px 22px;
    font-size: 12px;
    color: #9aa7bb;
  }

  :deep(.el-menu--collapse .el-menu-item) {
    margin: 4px 8px;
  }
}

.header {
  height: 64px;
  padding: 0 20px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #eef2f8;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  cursor: pointer;
  color: #606266;
}

.user-entry {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  outline: none;
}

.user-avatar {
  flex: none;
  border: 2px solid #fff;
  box-shadow: 0 2px 10px rgba(31, 45, 61, 0.18);
}

.user-avatar :deep(img) {
  object-fit: cover;
  object-position: center 45%;
}

.username {
  font-size: 14px;
  color: #303133;
}

.main {
  padding: 18px;
  background-color: #f5f7fb;
  overflow-y: auto;
}
</style>
