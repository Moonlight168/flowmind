import request from '@/utils/request';

// 保存草稿（确保同一流程只能存在一个草稿）
export function saveDraft(data) {
  return request({
    url: '/flowable/draft/saveDraft',
    method: 'post',
    data: data
  });
}

// 获取草稿列表
export function listDraft(query) {
  return request({
    url: '/flowable/draft/list',
    method: 'get',
    params: query
  });
}

// 获取草稿详情
export function getDraft(draftId) {
  return request({
    url: '/flowable/draft/' + draftId,
    method: 'get'
  });
}

// 删除草稿
export function delDraft(definitionId) {
  return request({
    url: '/flowable/draft/definition/' + definitionId,
    method: 'delete'
  });
}

// 批量删除草稿
export function delDrafts(draftIds) {
  return request({
    url: '/flowable/draft/batch/' + draftIds.join(','),
    method: 'delete'
  });
}

// 根据流程定义ID获取草稿（用于检查是否已存在草稿）
export function getDraftByDefId(definitionId) {
  return request({
    url: '/flowable/draft/definition/' + definitionId,
    method: 'get'
  });
}