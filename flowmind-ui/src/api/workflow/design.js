import request from '@/utils/request'

export function designCategory(data) {
  return request({
    url: '/flowmind-ai/design/category',
    method: 'post',
    data
  })
}

export function designFlow(data) {
  return request({
    url: '/flowmind-ai/design/flow',
    method: 'post',
    data
  })
}

export function designForm(data) {
  return request({
    url: '/flowmind-ai/design/form',
    method: 'post',
    data
  })
}

export function clearDesignState(designType) {
  return request({
    url: '/flowmind-ai/design/state/' + designType,
    method: 'delete'
  })
}