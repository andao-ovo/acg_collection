<template>
  <div class="login-page">
    <!-- 左侧品牌区 -->
    <div class="brand-side">
      <div class="brand-inner">
        <div class="brand-logo">
          <span class="logo-emoji">🎌</span>
          <span class="logo-text">ACG 收藏馆</span>
        </div>
        <h1 class="brand-title">你的 ACG 收藏与评价空间</h1>
        <p class="brand-desc">
          收藏动漫、漫画与小说，记录评分、写下短评，
          用标签梳理你的次元收藏清单。
        </p>
        <ul class="brand-features">
          <li><el-icon><Collection /></el-icon> 一站式管理全部收藏</li>
          <li><el-icon><DataAnalysis /></el-icon> 多维度统计你的追番足迹</li>
          <li><el-icon><MagicStick /></el-icon> 随机推荐，发现下一部好作品</li>
        </ul>
      </div>
    </div>

    <!-- 右侧表单区 -->
    <div class="form-side">
      <div class="form-box">
        <h2 class="form-title">{{ isRegister ? '创建账号' : '欢迎回来' }}</h2>
        <p class="form-subtitle">
          {{ isRegister ? '注册一个账号，开启你的收藏之旅' : '登录以管理你的收藏' }}
        </p>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          size="large"
          @submit.prevent
        >
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              placeholder="用户名"
              :prefix-icon="User"
              @keyup.enter="handleSubmit"
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              show-password
              placeholder="密码"
              :prefix-icon="Lock"
              @keyup.enter="handleSubmit"
            />
          </el-form-item>

          <el-form-item v-if="isRegister" prop="confirm">
            <el-input
              v-model="form.confirm"
              type="password"
              show-password
              placeholder="确认密码"
              :prefix-icon="Lock"
              @keyup.enter="handleSubmit"
            />
          </el-form-item>

          <el-button
            type="primary"
            class="submit-btn"
            size="large"
            :loading="loading"
            @click="handleSubmit"
          >
            {{ isRegister ? '注 册' : '登 录' }}
          </el-button>
        </el-form>

        <div class="switch-line">
          <span>{{ isRegister ? '已有账号？' : '还没有账号？' }}</span>
          <el-button link type="primary" @click="toggleMode">
            {{ isRegister ? '去登录' : '去注册' }}
          </el-button>
        </div>

        <div class="back-home">
          <el-button link @click="router.push('/')">
            <el-icon><Back /></el-icon>&nbsp;返回主页
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const isRegister = ref(false)
const loading = ref(false)
const formRef = ref()

const form = reactive({
  username: '',
  password: '',
  confirm: '',
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度为 2-20 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 4, max: 50, message: '密码长度至少 4 位', trigger: 'blur' },
  ],
  confirm: [
    {
      validator: (rule, value, callback) => {
        if (form.confirm !== form.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

function toggleMode() {
  isRegister.value = !isRegister.value
  formRef.value?.clearValidate?.()
}

async function handleSubmit() {
  await formRef.value.validate()
  loading.value = true
  try {
    if (isRegister.value) {
      await auth.register({
        username: form.username,
        password: form.password,
      })
      ElMessage.success('注册成功，请登录')
      // 注册后自动登录
      await auth.login({
        username: form.username,
        password: form.password,
      })
      ElMessage.success('已自动登录')
    } else {
      await auth.login({
        username: form.username,
        password: form.password,
      })
      ElMessage.success('登录成功')
    }
    router.push('/')
  } catch (e) {
    // 错误已在拦截器统一提示
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100%;
  display: flex;
}

.brand-side {
  flex: 1.2;
  background: linear-gradient(135deg, #2a2146 0%, #16182a 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}
.brand-side::after {
  content: '';
  position: absolute;
  width: 420px;
  height: 420px;
  background: radial-gradient(circle, rgba(124, 92, 255, 0.35) 0%, transparent 70%);
  top: -80px;
  right: -80px;
  border-radius: 50%;
}

.brand-inner {
  max-width: 420px;
  padding: 40px;
}
.brand-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 40px;
}
.logo-emoji {
  font-size: 30px;
}
.logo-text {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 1px;
}
.brand-title {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.4;
  margin: 0 0 16px;
}
.brand-desc {
  font-size: 15px;
  color: #b9b4d6;
  line-height: 1.8;
  margin: 0 0 28px;
}
.brand-features {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.brand-features li {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #ddd8f0;
}

.form-side {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f6fb;
}
.form-box {
  width: 360px;
  padding: 40px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(31, 35, 65, 0.08);
}
.form-title {
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 6px;
  color: #24293f;
}
.form-subtitle {
  color: #8b90a3;
  font-size: 13px;
  margin: 0 0 24px;
}
.submit-btn {
  width: 100%;
  margin-top: 4px;
  font-size: 15px;
}
.switch-line {
  margin-top: 18px;
  text-align: center;
  font-size: 13px;
  color: #8b90a3;
}
.back-home {
  margin-top: 14px;
  text-align: center;
}

@media (max-width: 768px) {
  .brand-side {
    display: none;
  }
}
</style>