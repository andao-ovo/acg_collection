// 作品类型：类型值 -> 展示信息
export const WORK_TYPES = {
  小说: { label: '小说', color: '#f56c6c', icon: 'Notebook' },
  漫画: { label: '漫画', color: '#409eff', icon: 'Picture' },
  动漫: { label: '动漫', color: '#67c23a', icon: 'Film' },
}

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