import request from '@/utils/request';

// 分页查询流程监听器
export function queryListenerPage(query) {
  return request({
    url: '/flowable/listener/queryPage',
    method: 'get',
    params: query
  });
}

// 列表查询流程监听器
export function queryListenerList(query) {
  return request({
    url: '/flowable/listener/queryList',
    method: 'get',
    params: query
  });
}

// 详细查询流程监听器
export function getListener(formId) {
  return request({
    url: '/flowable/listener/query/' + formId,
    method: 'get'
  });
}

// 新增流程监听器
export function addListener(data) {
  return request({
    url: '/flowable/listener/insert',
    method: 'post',
    data: data
  });
}

// 修改流程监听器
export function updateListener(data) {
  return request({
    url: '/flowable/listener/update',
    method: 'post',
    data: data
  });
}

// 删除流程监听器
export function delListener(listenerId) {
  return request({
    url: '/flowable/listener/delete/' + listenerId,
    method: 'post'
  });
}

// 新增流程监听器字段
export function insertListenerFieldAPI(datam) {
  return request({
    url: '/flowable/listener/insertField',
    method: 'post',
    data: data
  });
}

// 修改流程监听器字段
export function updateListenerFieldAPI(datam) {
  return request({
    url: '/flowable/listener/updateField',
    method: 'post',
    data: data
  });
}

// 删除流程监听器字段
export function deleteListenerFieldAPI(fieldIds) {
  return request({
    url: '/flowable/listener/deleteField/' + fieldIds,
    method: 'post'
  });
}
