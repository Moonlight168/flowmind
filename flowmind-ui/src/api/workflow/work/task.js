import request from '@/utils/request';

// 完成任务
export function complete(data) {
  return request({
    url: '/flowable/task/complete',
    method: 'post',
    data: data
  });
}

// 别名，保持兼容性
export const completeTask = complete;

// 委派任务
export function delegate(data) {
  return request({
    url: '/flowable/task/delegate',
    method: 'post',
    data: data
  });
}

// 别名，保持兼容性
export const delegateTask = delegate;

// 转办任务
export function transfer(data) {
  return request({
    url: '/flowable/task/transfer',
    method: 'post',
    data: data
  });
}

// 别名，保持兼容性
export const transferTask = transfer;

// 退回任务
export function returnTask(data) {
  return request({
    url: '/flowable/task/return',
    method: 'post',
    data: data
  });
}

// 拒绝任务
export function rejectTask(data) {
  return request({
    url: '/flowable/task/reject',
    method: 'post',
    data: data
  });
}

// 签收任务
export function claimTask(data) {
  return request({
    url: '/flowable/task/claim',
    method: 'post',
    data: data
  });
}

// 批量签收任务
export function batchClaimTask(data) {
  return request({
    url: '/flowable/task/batchClaim',
    method: 'post',
    data: data
  });
}

// 可退回任务列表
export function returnList(data) {
  return request({
    url: '/flowable/task/returnList',
    method: 'post',
    data: data
  });
}

// 撤回任务
export function revokeProcess(data) {
  return request({
    url: '/flowable/task/revokeProcess',
    method: 'post',
    data: data
  });
}

// 标记已读
export function markAsRead(data) {
  return request({
    url: '/flowable/task/markAsRead',
    method: 'post',
    data: data
  });
}
