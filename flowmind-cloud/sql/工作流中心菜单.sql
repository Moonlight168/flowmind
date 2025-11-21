-- 一级菜单
insert into sys_menu values('2350', '流程管理', '0', '4', 'process',  null, '','', 1, 0, 'M', '0', '0', '', 'skill',    'admin', sysdate(), '', null, '流程管理目录');
insert into sys_menu values('2355', '办公管理', '0', '5', 'work',     null, '','', 1, 0, 'M', '0', '0', '', 'job',      'admin', sysdate(), '', null, '办公管理目录');



-- 二级菜单
-- 流程管理
insert into sys_menu values('2351',  '流程分类', '2350',   '1', 'category',   'workflow/category/index',      '','', 1, 0, 'C', '0', '0', 'workflow:category:list',   'nested',    'admin', sysdate(), '', null, '流程分类菜单');
insert into sys_menu values('2352',  '表单配置', '2350',   '2', 'form',       'workflow/form/index',          '','', 1, 0, 'C', '0', '0', 'workflow:form:list',       'form',      'admin', sysdate(), '', null, '表单配置菜单');
insert into sys_menu values('2353',  '流程模型', '2350',   '3', 'model',      'workflow/model/index',         '','', 1, 0, 'C', '0', '0', 'workflow:model:list',      'component', 'admin', sysdate(), '', null, '流程模型菜单');
insert into sys_menu values('2354',  '部署管理', '2350',   '4', 'deploy',     'workflow/deploy/index',        '','', 1, 0, 'C', '0', '0', 'workflow:deploy:list',     'example',   'admin', sysdate(), '', null, '部署管理菜单');
-- 办公管理
insert into sys_menu values('2356',  '新建流程', '2355',   '1', 'create',     'workflow/work/index',       '','', 1, 0, 'C', '0', '0', 'workflow:process:startList',    'guide',      'admin', sysdate(), '', null, '新建流程菜单');
insert into sys_menu values('2357',  '我的流程', '2355',   '2', 'own',        'workflow/work/own',         '','', 1, 0, 'C', '0', '0', 'workflow:process:ownList',      'cascader',   'admin', sysdate(), '', null, '我的流程菜单');
insert into sys_menu values('2358',  '待办任务', '2355',   '3', 'todo',       'workflow/work/todo',        '','', 1, 0, 'C', '0', '0', 'workflow:process:todoList',     'time-range', 'admin', sysdate(), '', null, '待办任务菜单');
insert into sys_menu values('2359',  '待签任务', '2355',   '4', 'claim',      'workflow/work/claim',       '','', 1, 0, 'C', '0', '0', 'workflow:process:claimList',    'checkbox',   'admin', sysdate(), '', null, '待签任务菜单');
insert into sys_menu values('2362',  '已办任务', '2355',   '5', 'finished',   'workflow/work/finished',    '','', 1, 0, 'C', '0', '0', 'workflow:process:finishedList', 'checkbox',   'admin', sysdate(), '', null, '已办任务菜单');
insert into sys_menu values('2361',  '抄送我的', '2355',   '6', 'copy',       'workflow/work/copy',        '','', 1, 0, 'C', '0', '0', 'workflow:process:copyList',     'checkbox',   'admin', sysdate(), '', null, '抄送我的菜单');


-- 三级菜单
-- 流程分类管理
insert into sys_menu values('2363', '分类查询', '2351', '1', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:category:query',  '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2364', '分类新增', '2351', '2', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:category:add',    '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2365', '分类编辑', '2351', '3', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:category:edit',   '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2366', '分类删除', '2351', '4', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:category:remove', '#', 'admin', sysdate(), '', null, '');
-- 表单配置
insert into sys_menu values('2367', '表单查询', '2352', '1', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:form:query',   '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2368', '表单新增', '2352', '2', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:form:add',     '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2369', '表单修改', '2352', '3', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:form:edit',    '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2370', '表单删除', '2352', '4', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:form:remove',  '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2371', '表单导出', '2352', '5', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:form:export',  '#', 'admin', sysdate(), '', null, '');
-- 流程模型
insert into sys_menu values('2372', '模型查询', '2353', '1', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:model:query',    '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2373', '模型新增', '2353', '2', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:model:add',      '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2374', '模型修改', '2353', '3', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:model:edit',     '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2375', '模型删除', '2353', '4', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:model:remove',   '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2376', '模型导出', '2353', '5', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:model:export',   '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2377', '模型导入', '2353', '6', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:model:import',   '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2378', '模型设计', '2353', '7', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:model:designer', '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2379', '模型保存', '2353', '8', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:model:save',     '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2380', '流程部署', '2353', '9', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:model:deploy',   '#', 'admin', sysdate(), '', null, '');
-- 部署管理
insert into sys_menu values('2381', '部署查询', '2354', '1', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:deploy:query',   '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2382', '部署删除', '2354', '2', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:deploy:remove',  '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2383', '更新状态', '2354', '3', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:deploy:status',  '#', 'admin', sysdate(), '', null, '');
-- 新建流程
insert into sys_menu values('2384', '发起流程',    '2356', '1', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:process:start',       '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2385', '新建流程导出', '2356', '2', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:process:startExport', '#', 'admin', sysdate(), '', null, '');
-- 我的流程
insert into sys_menu values('2386', '流程详情',    '2357', '1', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:process:query',     '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2387', '流程删除',    '2357', '2', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:process:remove',    '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2388', '流程取消',    '2357', '3', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:process:cancel',    '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2389', '我的流程导出', '2357', '4', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:process:ownExport', '#', 'admin', sysdate(), '', null, '');
-- 待办任务
insert into sys_menu values('2390', '流程办理',    '2358', '1', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:process:approval',   '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2391', '待办流程导出', '2358', '2', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:process:todoExport', '#', 'admin', sysdate(), '', null, '');
-- 待签任务
insert into sys_menu values('2392', '流程签收',    '2359', '1', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:process:claim',        '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2393', '待签流程导出', '2359', '2', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:process:claimExport',  '#', 'admin', sysdate(), '', null, '');
-- 已办任务
insert into sys_menu values('2394', '流程撤回',    '2362', '1', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:process:revoke',         '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2395', '已办流程导出', '2362', '2', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:process:finishedExport', '#', 'admin', sysdate(), '', null, '');
-- 抄送我的
insert into sys_menu values('2396', '抄送流程导出', '2361', '1', '#', '', '','', 1, 0, 'F', '0', '0', 'workflow:process:copyExport', '#', 'admin', sysdate(), '', null, '');