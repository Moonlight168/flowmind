import request from '@/utils/request';

// 查询流程列表
export function listProcess(query) {
  return request({
    url: '/flowable/process/list',
    method: 'get',
    params: query
  });
}

// 查询流程列表
export function getProcessForm(query) {
  return request({
    url: '/flowable/process/getProcessForm',
    method: 'get',
    params: query
  });
}

// 部署流程实例
export function startProcess(processDefId,data) {
  return request({
    url: '/flowable/process/start/' + processDefId,
    method: 'post',
    data: data
  });
}

// 删除流程实例
export function delProcess(ids) {
  return request({
    url: '/flowable/process/instance/' + ids,
    method: 'delete'
  });
}

// 获取流程图
export function getBpmnXml(processDefId) {
  return request({
    url: '/flowable/process/bpmnXml/' + processDefId,
    method: 'get'
  });
}

export function detailProcess(query) {
  return request({
    url: '/flowable/process/detail',
    method: 'get',
    params: query
  });
}

// 我的发起的流程
export function listOwnProcess(query) {
  return request({
    url: '/flowable/process/ownList',
    method: 'get',
    params: query
  });
}

// 我待办的流程
export function listTodoProcess(query) {
  return request({
    url: '/flowable/process/todoList',
    method: 'get',
    params: query
  });
}

// 我待签的流程
export function listClaimProcess(query) {
  return request({
    url: '/flowable/process/claimList',
    method: 'get',
    params: query
  });
}

// 我已办的流程
export function listFinishedProcess(query) {
  return request({
    url: '/flowable/process/finishedList',
    method: 'get',
    params: query
  });
}

// 查询流程抄送列表
export function listCopyProcess(query) {
  return request({
    url: '/flowable/process/copyList',
    method: 'get',
    params: query
  });
}

// 取消申请
export function stopProcess(data) {
  return request({
    url: '/flowable/task/stopProcess',
    method: 'post',
    data: data
  });
}

// 获取待办事项数量
export function getTodoCount() {
  return request({
    url: '/flowable/process/todoCount',
    method: 'get'
  });
}

// 获取已办事项数量
export function getFinishedCount() {
  return request({
    url: '/flowable/process/finishedCount',
    method: 'get'
  });
}

// 获取我的流程数量
export function getOwnCount() {
  return request({
    url: '/flowable/process/ownCount',
    method: 'get'
  });
}

// 获取抄送数量
export function getCopyCount() {
  return request({
    url: '/flowable/process/copyCount',
    method: 'get'
  });
}

// 获取待签收数量
export function getClaimCount() {
  return request({
    url: '/flowable/process/claimCount',
    method: 'get'
  });
}
