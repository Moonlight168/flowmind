import request from '@/utils/request';

// 查询流程分类列表
export function listCategory(query) {
  return request({
    url: '/flowable/category/list',
    method: 'get',
    params: query
  });
}

// 查询流程分类列表
export function listAllCategory(query){
  return request({
    url: '/flowable/category/listAll',
    method: 'get',
    params: query
  });
}

// 查询流程分类详细
export function getCategory(categoryId) {
  return request({
    url: '/flowable/category/' + categoryId,
    method: 'get'
  });
}

// 新增流程分类
export function addCategory(data) {
  return request({
    url: '/flowable/category',
    method: 'post',
    data: data
  });
}

// 修改流程分类
export function updateCategory(data) {
  return request({
    url: '/flowable/category',
    method: 'put',
    data: data
  });
}

// 删除流程分类
export function delCategory(categoryIds) {
  return request({
    url: '/flowable/category/' + categoryIds,
    method: 'delete'
  });
}
