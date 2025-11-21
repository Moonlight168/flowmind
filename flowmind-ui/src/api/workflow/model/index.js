import request from '@/utils/request';

// 查询流程模型信息
export function listModel(query){
  return request({
    url: '/flowable/model/list',
    method: 'get',
    params: query
  });
}

// 查询流程模型信息
export function historyModel(query) {
  return request({
    url: '/flowable/model/historyList',
    method: 'get',
    params: query
  });
}

export function getModel(modelId) {
  return request({
    url: '/flowable/model/' + modelId,
    method: 'get'
  });
}

// 新增模型信息
export function addModel(data) {
  return request({
    url: '/flowable/model',
    method: 'post',
    data: data
  });
}

// 修改模型信息
export function updateModel(data) {
  return request({
    url: '/flowable/model',
    method: 'put',
    data: data
  });
}

// 保存流程模型
export function saveModel(data) {
  return request({
    url: '/flowable/model/save',
    method: 'post',
    data: data
  });
}

export function latestModel(params) {
  return request({
    url: '/flowable/model/latest',
    method: 'post',
    params: params
  });
}

export function delModel(modelIds) {
  return request({
    url: '/flowable/model/' + modelIds,
    method: 'delete'
  });
}

export function deployModel(params) {
  return request({
    url: '/flowable/model/deploy',
    method: 'post',
    params: params
  });
}

// 获取流程模型流程图
export function getBpmnXml(modelId) {
  return request({
    url: '/flowable/model/bpmnXml/' + modelId,
    method: 'get'
  });
}
