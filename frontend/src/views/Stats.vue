<template>
  <div class="acg-page stats-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">统计概览</h1>
        <p class="page-subtitle">你的收藏足迹 · 汇总维度一屏掌握</p>
      </div>
      <el-button @click="loadData" :loading="loading">
        <el-icon><Refresh /></el-icon>&nbsp;刷新
      </el-button>
    </div>

    <el-skeleton v-if="loading && !loaded" :rows="8" animated />

    <template v-else>
      <!-- 指标卡 -->
      <div class="kpi-row">
        <div class="kpi-card acg-card">
          <div class="kpi-label">收藏总量</div>
          <div class="kpi-value">{{ stats.total ?? totalCount }}</div>
          <div class="kpi-icon" style="background:#eaf0ff;color:#2a78d6"><el-icon><Collection /></el-icon></div>
        </div>
        <div class="kpi-card acg-card">
          <div class="kpi-label">平均评分</div>
          <div class="kpi-value">{{ formatRating(stats.avg_rating) }}</div>
          <div class="kpi-icon" style="background:#fff3ea;color:#eb6834"><el-icon><Star /></el-icon></div>
        </div>
        <div class="kpi-card acg-card">
          <div class="kpi-label">覆盖类型</div>
          <div class="kpi-value">{{ typeCount }}</div>
          <div class="kpi-icon" style="background:#e9faf3;color:#1baf7a"><el-icon><Grid /></el-icon></div>
        </div>
        <div class="kpi-card acg-card">
          <div class="kpi-label">已完结</div>
          <div class="kpi-value">{{ statusCount('已完结') }}</div>
          <div class="kpi-icon" style="background:#eafaf1;color:#0ca30c"><el-icon><CircleCheck /></el-icon></div>
        </div>
      </div>

      <!-- 图表区 -->
      <div class="charts-grid">
        <div class="chart-card acg-card">
          <h3 class="chart-title">类型分布</h3>
          <div ref="typeChartRef" class="chart-box"></div>
        </div>
        <div class="chart-card acg-card">
          <h3 class="chart-title">作品状态</h3>
          <div ref="statusChartRef" class="chart-box"></div>
        </div>
      </div>

      <div class="chart-card acg-card wide">
        <h3 class="chart-title">评分分布</h3>
        <div ref="ratingChartRef" class="chart-box tall"></div>
      </div>

      <!-- 明细表 -->
      <div class="chart-card acg-card wide">
        <div class="table-head">
          <h3 class="chart-title">收藏明细</h3>
          <el-input
            v-model="tableKeyword"
            placeholder="在当前明细中搜索…"
            clearable
            class="table-search"
            :prefix-icon="'Search'"
          />
        </div>
        <el-table :data="tableRows" stripe style="width: 100%">
          <el-table-column prop="title" label="作品名" min-width="180" />
          <el-table-column prop="type" label="类型" width="90" />
          <el-table-column prop="author" label="作者" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">{{ row.author || '—' }}</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="statusInfo(row.status).type" size="small" effect="light">
                {{ statusInfo(row.status).label }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="rating" label="评分" width="100">
            <template #default="{ row }">{{ row.rating ?? '—' }}</template>
          </el-table-column>
          <el-table-column prop="created_at" label="添加时间" width="170">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
        </el-table>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from '@/utils/echarts'
import { getWorksStats, getWorks } from '@/api'
import { STATUS_MAP, statusInfo } from '@/constants'

const loading = ref(false)
const loaded = ref(false)
const stats = ref({})
const allWorks = ref([])
const tableKeyword = ref('')

const typeChartRef = ref()
const statusChartRef = ref()
const ratingChartRef = ref()

let charts = []

const totalCount = computed(() => allWorks.value.length)
const typeCount = computed(() => new Set(allWorks.value.map((w) => w.type || '未知')).size)

function statusCount(status) {
  return allWorks.value.filter((w) => w.status === status).length
}

function formatRating(v) {
  if (v == null) return '—'
  return Number(v).toFixed(2)
}

function formatDate(str) {
  if (!str) return ''
  return String(str).replace('T', ' ').slice(0, 10)
}

const tableRows = computed(() => {
  const kw = tableKeyword.value.trim()
  if (!kw) return allWorks.value
  return allWorks.value.filter(
    (w) =>
      (w.title || '').toLowerCase().includes(kw.toLowerCase()) ||
      (w.author || '').toLowerCase().includes(kw.toLowerCase())
  )
})

// 类型分布（south 3 个类型槽）
function buildTypeOption() {
  const map = {}
  for (const w of allWorks.value) {
    const t = w.type || '未知'
    map[t] = (map[t] || 0) + 1
  }
  const names = Object.keys(map)
  const colors = ['#2a78d6', '#eb6834', '#1baf7a']
  return {
    color: colors,
    tooltip: { trigger: 'item', formatter: '{b}: {c} 部 ({d}%)' },
    legend: { bottom: 0, icon: 'circle', itemWidth: 10, itemHeight: 10 },
    series: [
      {
        type: 'pie',
        radius: ['52%', '72%'],
        center: ['50%', '44%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, formatter: '{b}\n{c} 部', color: '#52514e', fontSize: 12 },
        emphasis: { label: { show: true, fontWeight: 'bold' } },
        data: names.map((n) => ({ name: n, value: map[n] })),
      },
    ],
  }
}

// 状态分布（单一蓝色系有序色阶，带数值标签）
function buildStatusOption() {
  const statusOrder = Object.keys(STATUS_MAP)
  const counts = statusOrder.map((s) => ({
    name: STATUS_MAP[s].label,
    value: allWorks.value.filter((w) => w.status === s).length,
  }))
  return {
    grid: { left: 10, right: 30, top: 20, bottom: 30, containLabel: true },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: { type: 'category', data: counts.map((c) => c.name), axisLine: { lineStyle: { color: '#c3c2b7' } }, axisLabel: { color: '#52514e' } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#e1e0d9' } }, axisLabel: { color: '#898781' } },
    series: [
      {
        name: '数量',
        type: 'bar',
        barWidth: '46%',
        itemStyle: { borderRadius: [6, 6, 0, 0], color: '#2a78d6' },
        label: { show: true, position: 'top', color: '#0b0b0b', fontWeight: 600 },
        data: counts.map((c) => c.value),
      },
    ],
  }
}

// 评分分布（单色蓝，显示数量标签）
function buildRatingOption() {
  const buckets = {}
  for (let i = 0; i <= 10; i++) buckets[i] = 0
  for (const w of allWorks.value) {
    if (w.rating != null) buckets[Math.round(w.rating)]++
  }
  const keys = Object.keys(buckets)
    .map(Number)
    .sort((a, b) => a - b)
  const steps = ['#9ec5f4', '#6da7ec', '#5598e7', '#3987e5', '#2a78d6']
  return {
    grid: { left: 10, right: 20, top: 30, bottom: 30, containLabel: true },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: '{b} 分：{c} 部' },
    xAxis: { type: 'category', data: keys, name: '评分', nameLocation: 'middle', nameGap: 28, axisLine: { lineStyle: { color: '#c3c2b7' } }, axisLabel: { color: '#52514e' } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#e1e0d9' } }, axisLabel: { color: '#898781' } },
    series: [
      {
        name: '数量',
        type: 'bar',
        barWidth: '55%',
        itemStyle: {
          borderRadius: [5, 5, 0, 0],
          color: (p) => steps[Math.min(p.dataIndex, steps.length - 1)],
        },
        label: { show: true, position: 'top', color: '#0b0b0b' },
        data: keys.map((k) => buckets[k]),
      },
    ],
  }
}

function renderCharts() {
  const opts = [
    { el: typeChartRef.value, opt: buildTypeOption() },
    { el: statusChartRef.value, opt: buildStatusOption() },
    { el: ratingChartRef.value, opt: buildRatingOption() },
  ]
  opts.forEach(({ el, opt }) => {
    if (!el) return
    const chart = echarts.getInstanceByDom(el) || echarts.init(el)
    chart.setOption(opt)
    charts.push(chart)
  })
}

async function loadData() {
  loading.value = true
  try {
    const [s, works] = await Promise.all([
      getWorksStats().catch(() => ({})),
      getWorks({ skip: 0, limit: 10000, sort_by: 'created_at', order: 'desc' }).catch(() => []),
    ])
    stats.value = s || {}
    allWorks.value = works || []
    loaded.value = true
    await nextTick()
    renderCharts()
  } finally {
    loading.value = false
  }
}

function handleResize() {
  charts.forEach((c) => c && c.resize())
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  loadData()
})
onBeforeUnmount(() => {
  charts.forEach((c) => c && c.dispose())
  charts = []
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.kpi-card {
  position: relative;
  padding: 20px;
}
.kpi-label {
  font-size: 13px;
  color: #8b90a3;
}
.kpi-value {
  font-size: 30px;
  font-weight: 700;
  color: #24293f;
  margin-top: 6px;
}
.kpi-icon {
  position: absolute;
  right: 18px;
  top: 50%;
  transform: translateY(-50%);
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
.chart-card {
  padding: 20px;
}
.chart-card.wide {
  margin-bottom: 16px;
}
.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: #2c3042;
  margin: 0 0 16px;
}
.chart-box {
  height: 300px;
}
.chart-box.tall {
  height: 320px;
}

.table-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.table-search {
  width: 220px;
  margin-bottom: 16px;
}

@media (max-width: 900px) {
  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>