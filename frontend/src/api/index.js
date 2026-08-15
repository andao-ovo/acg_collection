import http from './http'

// ---------- 认证 ----------
export const register = (data) => http.post('/register', data)
export const login = (data) => http.post('/login', data)

// ---------- 作品 ----------
export const getWorks = (params) => http.get('/works', { params })
export const getWork = (id) => http.get(`/works/${id}`)
export const createWork = (data) => http.post('/works', data)
export const updateWork = (id, data) => http.put(`/works/${id}`, data)
export const deleteWork = (id) => http.delete(`/works/${id}`)
export const getRandomWork = () => http.get('/works/random')
export const getWorksStats = () => http.get('/works/stats')

// ---------- 标签 ----------
export const getWorkTags = (id) => http.get(`/works/${id}/tags`)
export const addTagToWork = (workId, tagId) =>
  http.post(`/works/${workId}/tags`, null, { params: { tag_id: tagId } })
export const removeTagFromWork = (workId, tagId) =>
  http.delete(`/works/${workId}/tags/${tagId}`)
export const createTag = (name, category) =>
  http.post('/tags', null, { params: { name, category } })
export const getWorksByTags = (tagIds) =>
  http.get('/works/tags/by-tags', { params: { tag_ids: tagIds.join(',') } })