<template>
  <div class="acg-page">
    <!-- 页头 -->
    <div class="page-header">
      <div>
        <h1 class="page-title">作品列表</h1>
        <p class="page-subtitle">共 {{ total }} 部作品 · 发现并收藏你喜欢的动漫、漫画与小说</p>
      </div>
      <div class="header-actions">
        <el-button @click="surprise" :loading="surpriseLoading">
          <el-icon><MagicStick /></el-icon>&nbsp;随机推荐
        </el-button>
        <el-button type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>&nbsp;新增作品
        </el-button>
      </div>
    </div>

    <!-- 筛选卡片 -->
    <el-card shadow="never" class="filter-card acg-card">
      <div class="filter-row">
        <el-input
          v-model="filters.title"
          placeholder="搜索作品名…"
          clearable
          class="filter-title"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>

        <el-select
          v-model="filters.type"
          placeholder="全部类型"
          clearable
          class="filter-type"
          @change="handleSearch"
        >
          <el-option
            v-for="t in WORK_TYPE_OPTIONS"
            :key="t.value"
            :label="t.label"
            :value="t.value"
          />
        </el-select>

        <el-select
          v-model="filters.status"
          placeholder="全部状态"
          clearable
          class="filter-status"
          @change="handleSearch"
        >
          <el-option
            v-for="s in STATUS_OPTIONS"
            :key="s.value"
            :label="s.label"
            :value="s.value"
          />
        </el-select>

        <el-select
          v-model="sortKey"
          placeholder="排序"
          clearable
          class="filter-sort"
          @change="handleSearch"
        >
          <el-option
            v-for="s in SORT_FIELDS"
            :key="s.value"
            :label="s.label"
            :value="s.value"
          />
        </el-select>

        <el-tooltip :content="sortOrder === 'desc' ? '点击切换为升序' : '点击切换为降序'">
          <el-button @click="toggleOrder">
            <el-icon>
              <Sort :style="{ transform: sortOrder === 'asc' ? 'scaleY(-1)' : '' }" />
            </el-icon>
          </el-button>
        </el-tooltip>

        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>&nbsp;查询
        </el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
    </el-card>

    <!-- 列表 -->
    <div v-loading="loading">
      <el-empty v-if="!loading && works.length === 0" description="没有找到符合条件的作品" />

      <div v-else class="work-list">
        <div
          v-for="work in works"
          :key="work.id"
          class="work-card acg-card"
          @click="router.push(`/work/${work.id}`)"
        >
          <!-- 左侧类型色块 -->
          <div class="work-cover" :style="{ background: workType(work).color }">
            <el-icon :size="30"><component :is="workType(work).icon" /></el-icon>
            <span class="cover-type">{{ work.type || '未知' }}</span>
          </div>

          <!-- 信息区 -->
          <div class="work-body">
            <div class="work-title-row">
              <span class="work-title">{{ work.title }}</span>
              <el-tag :type="workStatus(work).type" size="small" effect="light" round>
                {{ workStatus(work).label }}
              </el-tag>
            </div>

            <div class="work-meta">
              <span v-if="work.author" class="meta-item">
                <el-icon><User /></el-icon>{{ work.author }}
              </span>
              <span class="meta-item">
                <el-icon><Clock /></el-icon>{{ formatDate(work.created_at) }}
              </span>
            </div>

            <div class="work-comment" v-if="work.comment">
              {{ work.comment }}
            </div>
          </div>

          <!-- 右侧评分 -->
          <div class="work-side">
            <div class="rating" v-if="work.rating != null">
              <span class="rating-num">{{ work.rating }}</span>
              <span class="rating-max">/10</span>
            </div>
            <div class="rating-empty" v-else>暂无评分</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="total > 0">
      <el-pagination
        background
        layout="total, prev, pager, next, jumper"
        :total="total"
        :page-size="filters.limit"
        :current-page="filters.page"
        :pager-count="7"
        @current-change="handlePageChange"
      />
    </div>

    <!-- 新增/编辑弹窗 -->
    <WorkFormDialog
      v-model="formVisible"
      :work="editingWork"
      @saved="handleSaved"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getWorks, getWorksStats, getRandomWork } from '@/api'
import {
  WORK_TYPE_OPTIONS,
  STATUS_OPTIONS,
  SORT_FIELDS,
  typeInfo,
  statusInfo,
} from '@/constants'
import WorkFormDialog from '@/components/WorkFormDialog.vue'

const router = useRouter()

const loading = ref(false)
const works = ref([])
const total = ref(0)

const filters = reactive({
  title: '',
  type: null,
  status: null,
  page: 1,
  limit: 10,
})

// 排序：字段 + 方向
const sortKey = ref('created_at')
const sortOrder = ref('desc')

async function fetchWorks() {
  loading.value = true
  try {
    const params = {
      skip: (filters.page - 1) * filters.limit,
      limit: filters.limit,
      sort_by: sortKey.value || 'id',
      order: sortOrder.value,
    }
    if (filters.title) params.title = filters.title
    if (filters.type) params.type = filters.type
    if (filters.status) params.status = filters.status

    const [list, stats] = await Promise.all([
      getWorks(params),
      getWorksStats().catch(() => null),
    ])
    works.value = list
    // 用统计接口的 total 驱动分页（/works 本身不返回总数）
    total.value = stats?.total ?? works.value.length
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  filters.page = 1
  fetchWorks()
}

function resetFilters() {
  filters.title = ''
  filters.type = null
  filters.status = null
  sortKey.value = 'created_at'
  sortOrder.value = 'desc'
  handleSearch()
}

function handlePageChange(page) {
  filters.page = page
  fetchWorks()
}

function toggleOrder() {
  sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
  handleSearch()
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

// ---------- 新增 / 编辑 ----------
const formVisible = ref(false)
const editingWork = ref(null)

function openCreate() {
  editingWork.value = null
  formVisible.value = true
}

function handleSaved() {
  formVisible.value = false
  fetchWorks()
}

// ---------- 随机推荐 ----------
const surpriseLoading = ref(false)
async function surprise() {
  surpriseLoading.value = true
  try {
    const w = await getRandomWork()
    if (w && w.id) {
      router.push(`/work/${w.id}`)
    }
  } finally {
    surpriseLoading.value = false
  }
}

onMounted(fetchWorks)
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
}
.header-actions {
  display: flex;
  gap: 10px;
}

.filter-card {
  margin-bottom: 20px;
}
.filter-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.filter-title {
  width: 260px;
}
.filter-type,
.filter-status {
  width: 150px;
}
.filter-sort {
  width: 130px;
}

.work-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.work-card {
  display: flex;
  align-items: stretch;
  padding: 16px;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.work-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(31, 35, 65, 0.12);
}

.work-cover {
  width: 68px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #fff;
  flex-shrink: 0;
}
.cover-type {
  font-size: 13px;
  font-weight: 600;
}

.work-body {
  flex: 1;
  min-width: 0;
  padding: 4px 20px;
}
.work-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.work-title {
  font-size: 17px;
  font-weight: 600;
  color: #24293f;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.work-meta {
  display: flex;
  gap: 16px;
  margin-top: 8px;
  color: #8b90a3;
  font-size: 13px;
}
.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.work-comment {
  margin-top: 10px;
  color: #5a5f73;
  font-size: 13px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.work-side {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 90px;
  border-left: 1px solid #f0f2f9;
  padding-left: 16px;
}
.rating {
  display: flex;
  align-items: baseline;
  color: #f7b500;
}
.rating-num {
  font-size: 28px;
  font-weight: 700;
}
.rating-max {
  font-size: 13px;
  color: #b9bed1;
}
.rating-empty {
  color: #b9bed1;
  font-size: 13px;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>