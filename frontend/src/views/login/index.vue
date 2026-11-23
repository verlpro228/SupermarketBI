<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { APP_NAME_SHORT, APP_SUBTITLE } from '@/constants'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const form = reactive({ username: '', password: '' })

const rules: FormRules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const features = [
  { icon: 'Box', title: '批次追溯', desc: '先进先出，变动可查' },
  { icon: 'AlarmClock', title: '临期预警', desc: '三档提醒，处理留痕' },
  { icon: 'TrendCharts', title: '数据可视', desc: '看板与趋势分析' },
]

async function handleLogin() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const result = await userStore.login(form.username, form.password)
    ElMessage.success('登录成功')

    const redirect = route.query.redirect as string | undefined
    if (redirect) {
      router.replace(redirect)
    } else {
      router.replace(result.user.role === 'admin' ? '/dashboard' : '/stock')
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-shell">
      <!-- 左侧图片区 -->
      <section class="visual-panel">
        <div class="visual-bg"></div>

        <div class="visual-content">
          <span class="brand-badge">
            <el-icon :size="20"><Shop /></el-icon>
          </span>

          <h1>{{ APP_NAME_SHORT }}</h1>
          <p class="visual-sub">{{ APP_SUBTITLE }}</p>

          <ul class="visual-list">
            <li v-for="item in features" :key="item.title">
              <span class="item-icon">
                <el-icon :size="15"><component :is="item.icon" /></el-icon>
              </span>
              <span class="item-text">
                <strong>{{ item.title }}</strong>
                <em>{{ item.desc }}</em>
              </span>
            </li>
          </ul>
        </div>

        <div class="visual-foot">库存、临期、出入库一体化管理</div>
      </section>

      <!-- 右侧表单区 -->
      <section class="form-panel">
        <div class="form-inner">
          <header class="form-head">
            <h2>账号登录</h2>
            <p>请使用系统分配的账号登录</p>
          </header>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            class="login-form"
            @keyup.enter="handleLogin"
          >
            <div class="field">
              <label class="field-label">账号</label>
              <el-form-item prop="username">
                <el-input
                  v-model="form.username"
                  placeholder="请输入账号"
                  :prefix-icon="'User'"
                  clearable
                />
              </el-form-item>
            </div>

            <div class="field">
              <label class="field-label">密码</label>
              <el-form-item prop="password">
                <el-input
                  v-model="form.password"
                  type="password"
                  placeholder="请输入密码"
                  :prefix-icon="'Lock'"
                  show-password
                />
              </el-form-item>
            </div>

            <el-button type="primary" class="submit-btn" :loading="loading" @click="handleLogin">
              登 录
            </el-button>
          </el-form>

          <footer class="form-foot">
            <span>登录即表示您已阅读并同意系统使用规范与数据安全要求</span>
          </footer>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped lang="scss">
.login-page {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: #eef1f7;
}

/* ---------- 整体卡片 ---------- */
.login-shell {
  display: grid;
  grid-template-columns: 42% 58%;
  width: min(940px, 100%);
  height: min(600px, 92vh);
  border-radius: 24px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 32px 80px rgba(15, 30, 55, 0.16);
}

/* ---------- 左侧图片区 ---------- */
.visual-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 42px 38px 34px;
  overflow: hidden;
  color: #fff;
}

.visual-bg {
  position: absolute;
  inset: 0;
  background: url('/images/login-bg.jpg') center / cover no-repeat;
  filter: brightness(0.88) saturate(0.96);
}

.visual-bg::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    165deg,
    rgba(8, 18, 34, 0.36) 0%,
    rgba(8, 18, 34, 0.34) 42%,
    rgba(8, 18, 34, 0.3) 62%,
    rgba(8, 18, 34, 0.46) 100%
  );
}

.visual-content {
  position: relative;
  z-index: 1;
}

.brand-badge {
  width: 44px;
  height: 44px;
  border-radius: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #3f7df3;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 8px 20px rgba(8, 18, 34, 0.24);
  margin-bottom: 22px;
}

.visual-content h1 {
  margin: 0 0 8px;
  font-size: 30px;
  font-weight: 700;
  letter-spacing: 1px;
  color: #fff;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.6);
}

.visual-sub {
  margin: 0 0 26px;
  font-size: 13.5px;
  color: rgba(255, 255, 255, 0.96);
  letter-spacing: 0.5px;
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.65);
}

.visual-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;

  li {
    display: flex;
    align-items: center;
    gap: 11px;
  }
}

.item-icon {
  width: 28px;
  height: 28px;
  flex: none;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #3f7df3;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 4px 12px rgba(8, 18, 34, 0.2);
}

.item-text {
  display: flex;
  align-items: baseline;
  gap: 8px;

  strong {
    font-size: 13.5px;
    font-weight: 600;
    color: #fff;
    text-shadow: 0 1px 5px rgba(0, 0, 0, 0.65);
  }

  em {
    font-style: normal;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.92);
    text-shadow: 0 1px 5px rgba(0, 0, 0, 0.65);
  }
}

.visual-foot {
  position: relative;
  z-index: 1;
  font-size: 11.5px;
  color: rgba(255, 255, 255, 0.82);
  letter-spacing: 0.5px;
  text-shadow: 0 1px 5px rgba(0, 0, 0, 0.65);
}

/* ---------- 右侧表单区 ---------- */
.form-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 60px;
  background: #fff;
}

.form-inner {
  width: 100%;
  max-width: 340px;
}

.form-head {
  margin-bottom: 30px;

  h2 {
    margin: 0 0 8px;
    font-size: 26px;
    font-weight: 700;
    color: #16233a;
    letter-spacing: 0.5px;
  }

  p {
    margin: 0;
    font-size: 13px;
    color: #8b98ac;
  }
}

.field {
  margin-bottom: 18px;
}

.field-label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  color: #57667e;
  font-weight: 500;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.login-form :deep(.el-input__wrapper) {
  height: 48px;
  border-radius: 36px;
  background: #fff;
  box-shadow: 0 0 0 1px #dfe6f0 inset;
  padding: 0 16px;
}

.login-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #c7d4e6 inset;
}

.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1.5px #3f7df3 inset;
}

.login-form :deep(.el-input__inner::placeholder) {
  color: #aab5c7;
}

.submit-btn {
  width: 100%;
  height: 48px;
  margin-top: 12px;
  font-size: 15px;
  letter-spacing: 4px;
  border-radius: 36px;
  background: linear-gradient(135deg, #5b9bff, #3f7df3);
  border: none;
  box-shadow: 0 10px 24px rgba(63, 125, 243, 0.28);
}

.submit-btn:hover {
  background: linear-gradient(135deg, #6ba5ff, #4a86f5);
}

.form-foot {
  margin-top: 26px;
  padding-top: 18px;
  border-top: 1px solid #f0f3f8;
  text-align: center;

  span {
    font-size: 12px;
    color: #a3aebe;
  }
}

/* ---------- 响应式 ---------- */
@media (max-width: 860px) {
  .login-shell {
    grid-template-columns: 1fr;
    height: auto;
    max-height: 96vh;
  }

  .visual-panel {
    display: none;
  }

  .form-panel {
    padding: 40px 32px;
  }
}
</style>
