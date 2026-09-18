// 作品类型：类型值 -> 展示信息
export const WORK_TYPES = {
  小说: { label: '小说', color: '#f56c6c', icon: 'Notebook' },
  漫画: { label: '漫画', color: '#409eff', icon: 'Picture' },
  动漫: { label: '动漫', color: '#67c23a', icon: 'Film' },
  电影: { label: '电影', color: '#e6a23c', icon: 'VideoCamera' },
  电视剧: { label: '电视剧', color: '#9b59b6', icon: 'Monitor' },
}

// 作品可见范围：决定列表页展示哪一批作品
export const SCOPE_OPTIONS = [
  { label: '全部作品', value: 'all' },
  { label: '我的收藏', value: 'favorites' },
  { label: '我上传的', value: 'mine' },
]

export const WORK_TYPE_OPTIONS = Object.entries(WORK_TYPES).map(
  ([value, { label }]) => ({ label, value })
)

// 作品状态：状态值 -> 展示信息
export const STATUS_MAP = {
  连载中: { label: '连载中', type: 'primary' },
  已完结: { label: '已完结', type: 'success' },
  已搁置: { label: '已搁置', type: 'warning' },
  已弃坑: { label: '已弃坑', type: 'danger' },
  未开始: { label: '未开始', type: 'info' },
}

export const STATUS_OPTIONS = Object.entries(STATUS_MAP).map(
  ([value, { label }]) => ({ label, value })
)

// 分数可选项
export const RATING_OPTIONS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

// 排序字段
export const SORT_FIELDS = [
  { label: '最新添加', value: 'created_at' },
  { label: '评分最高', value: 'rating' },
  { label: '作品编号', value: 'id' },
]

// 类型展示辅助函数（兼容未知类型）
export function typeInfo(type) {
  return WORK_TYPES[type] || { label: type || '未知', color: '#909399', icon: 'Collection' }
}

export function statusInfo(status) {
  return STATUS_MAP[status] || { label: status || '未标记', type: 'info' }
}