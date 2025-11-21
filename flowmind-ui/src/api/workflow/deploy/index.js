import request from '@/utils/request';

// 查询流程部署列表
export function listDeploy(query) {
  return request({
    url: '/flowable/deploy/list',
    method: 'get',
    params: query
  });
}

export function listPublish(query){
  return request({
    url: '/flowable/deploy/publishList',
    method: 'get',
    params: query
  });
}

// 获取流程模型流程图
export function getBpmnXml(definitionId) {
  return request({
    url: '/flowable/deploy/bpmnXml/' + definitionId,
    method: 'get'
  });
}

// 修改流程状态
export function changeState(params) {
  return request({
    url: '/flowable/deploy/changeState',
    method: 'put',
    params: params
  });
}

// 删除流程部署
export function delDeploy(deployIds) {
  return request({
    url: '/flowable/deploy/' + deployIds,
    method: 'delete'
  });
}
