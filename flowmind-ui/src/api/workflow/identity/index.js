import request from '@/utils/request';

// 查询流程模型信息
export function selectUser(query) {
  return request({
    url: '/system/user/list',
    method: 'get',
    params: query
  });
}

export function deptTreeSelect() {
  return request({
    url: '/system/user/deptTree',
    method: 'get'
  });
}
