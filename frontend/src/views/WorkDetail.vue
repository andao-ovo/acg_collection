<template>
  <div class="acg-page detail-page">
    <el-skeleton v-if="loading" :rows="8" animated />

    <template v-else-if="work">
      <!-- 返回 -->
      <div class="back-bar">
        <el-button link @click="router.push('/')">
          <el-icon><Back /></el-icon>&nbsp;返回列表
        </el-button>
      </div>

      <el-card shadow="never" class="acg-card detail-card">
        <div class="detail-head">
          <!-- 类型大色块 -->
          <div
            class="detail-cover"
            :style="{ background: `linear-gradient(135deg, ${workType(work).color}, ${shade(workType(work).color)})` }"
          >
            <el-icon :size="48"><component :is="workType(work).icon" /></el-icon>
          </div>

          <div class="detail-info">
            <div class="title-row">
              <h1 class="detail-title">{{ work.title }}</h1>
              <el-tag :type="workStatus(work).type" size="large" effect="light" round>
                {{ workStatus(work).label }}
              </el-tag>
            </div>

            <div class="detail-meta">
              <div class="meta-block">
                <span class="meta-label">类型</span>
                <span class="meta-value">{{ work.type || '未知' }}</span>
              </div>
              <div class="meta-block">
                <span class="meta-label">作者</span>
                <span class="meta-value">{{ work.author || '—' }}</span>
              </div>
              <div class="meta-block">
                <span class="meta-label">添加时间</span>
                <span class="meta-value">{{ formatDate(work.created_at) }}</span>
              </div>
            </div>

            <!-- 评分 -->
            <div class="rating-block">
              <el-rate
                :model-value="work.rating ?? 0"
                :max="10"
                disabled
                show-score
                score-template="{value}"
              />
            </div>

            <div class="head-actions" v-if="auth.isLoggedIn">
              <el-button type="primary" plain @click="openEdit">
                <el-icon><Edit /></el-icon>&nbsp;编辑
              </el-button>
              <el-button type="danger" plain @click="handleDelete">
                <el-icon><Delete /></el-icon>&nbsp;删除
              </el-button>
            </div>
          </div>
        </div>

        <!-- 短评 -->
        <div class="section" v-if="work.comment">
          <h3 class="section-title">短评</h3>
          <p class="comment-text">{{ work.comment }}</p>
        </div>

        <!-- 标签 -->
        <div class="section">
          <div class="section-head">
            <h3 class="section-title">标签</h3>
            <el-button
              v-if="auth.isLoggedIn"
              link
              type="primary"
              size="small"
              @click="showAddTag = true"
            >
              <el-icon><Plus /></el-icon>&nbsp;管理标签
            </el-button>
          </div>

          <div class="tag-list" v-if="tags.length > 0">
            <el-tag v-for="t in tags" :key="t" class="work-tag" effect="plain">
              {{ t }}
            </el-tag>
          </div>
          <el-empty v-else description="暂无标签" :image-size="60" />
        </div>
      </el-card>

      <!-- 编辑弹窗（复用） -->
      <WorkFormDialog v-model="editVisible" :work="work" @saved="onEdited" />

      <!-- 添加标签弹窗 -->
      <el-dialog v-model="showAddTag" title="添加标签" width="440px">
        <el-form label-width="70px" label-position="left">
          <el-form-item label="标签名">
            <el-input v-model="newTagName" placeholder="输入标签名，如：战斗 / 治愈" />
          </el-form-item>
          <el-form-item label="分类">
            <el-input v-model="newTagCategory" placeholder="分类，如：题材 / 风格 / 其他" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showAddTag = false">取消</el-button>
          <el-button type="primary" :loading="tagLoading" @click="confirmAddTag">
            添加
          </el-button>
        </template>
      </el-dialog>
    </template>

    <el-empty v-else description="作品不存在或已被删除">
      <el-button type="primary" @click="router.push('/')">返回列表</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getWork, getWorkTags, deleteWork, addTagToWork, removeTagFromWork, createTag } from '@/api'
import { typeInfo, statusInfo } from '@/constants'
import { useAuthStore } from '@/stores/auth'
import WorkFormDialog from '@/components/WorkFormDialog.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const loading = ref(true)
const work = ref(null)
const tags = ref([])

const editVisible = ref(false)
const showAddTag = ref(false)
const newTagName = ref('')
const newTagCategory = ref('')
const tagLoading = ref(false)

async function fetchDetail() {
  loading.value = true
  try {
    const [w, t] = await Promise.all([
      getWork(route.params.id),
      getWorkTags(route.params.id).catch(() => []),
    ])
    work.value = w
    tags.value = t
  } catch (e) {
    work.value = null
  } finally {
    loading.value = false
  }
}

function openEdit() {
  editVisible.value = true
}

async function onEdited() {
  editVisible.value = false
  ElMessage.success('已保存')
  fetchDetail()
}

async function handleDelete() {
  await ElMessageBox.confirm(
    `确定要删除作品《${work.value.title}》吗？此操作不可恢复。`,
    '删除确认',
    { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
  )
  await deleteWork(work.value.id)
  ElMessage.success('已删除')
  router.push('/')
}

async function confirmAddTag() {
  if (!newTagName.value.trim()) {
    ElMessage.warning('请输入标签名')
    return
  }
  tagLoading.value = true
  try {
    // 先创建标签（若已存在会返回 400，交由拦截器提示）
    const tag = await createTag(newTagName.value.trim(), newTagCategory.value.trim() || '未分类')
    await addTagToWork(work.value.id, tag.id)
    ElMessage.success('标签已添加')
    newTagName.value = ''
    newTagCategory.value = ''
    showAddTag.value = false
    fetchDetail()
  } catch (e) {
    // 错误已提示
  } finally {
    tagLoading.value = false
  }
}

function formatDate(str) {
  if (!str) return ''
  return String(str).replace('T', ' ').slice(0, 16)
}
function workType(work) {
  return typeInfo(work.type)
}
function workStatus(work) {
  return statusInfo(work.status)
}
function shade(color) {
  return color + '66'
}

onMounted(fetchDetail)
</script>

<style scoped>
.back-bar {
  margin-bottom: 16px;
}
.detail-card {
  padding: 8px 8px 24px;
}
.detail-head {
  display: flex;
  gap: 28px;
  padding: 16px;
}
.detail-cover {
  width: 120px;
  height: 120px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.detail-info {
  flex: 1;
  min-width: 0;
}
.title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.detail-title {
  font-size: 26px;
  font-weight: 700;
  margin: 0;
  color: #24293f;
}
.detail-meta {
  display: flex;
  gap: 36px;
  margin: 20px 0 12px;
  flex-wrap: wrap;
}
.meta-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.meta-label {
  font-size: 12px;
  color: #b9bed1;
}
.meta-value {
  font-size: 15px;
  color: #3a3f57;
  font-weight: 500;
}
.rating-block {
  max-width: 240px;
}
.head-actions {
  margin-top: 16px;
  display: flex;
  gap: 10px;
}

.section {
  margin: 8px 16px 0;
  padding-top: 20px;
  border-top: 1px solid #f0f2f9;
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.section-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 12px;
  color: #2c3042;
}
.section-head .section-title {
  margin-bottom: 12px;
}
.comment-text {
  color: #4a4f68;
  font-size: 15px;
  line-height: 1.8;
  margin: 0;
}
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.work-tag {
  font-size: 13px;
}
</style>