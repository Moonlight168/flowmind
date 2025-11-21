package com.ruoyi.flowable.workflow.handler;

import cn.hutool.core.collection.CollUtil;
import cn.hutool.core.util.ObjectUtil;
import com.ruoyi.common.core.constant.SecurityConstants;
import com.ruoyi.common.core.domain.R;
import com.ruoyi.common.core.utils.StringUtils;
import com.ruoyi.flowable.common.constant.ProcessConstants;
import com.ruoyi.system.api.RemoteUserService;
import com.ruoyi.system.api.domain.SysUser;
import lombok.AllArgsConstructor;
import org.flowable.bpmn.model.FlowElement;
import org.flowable.bpmn.model.UserTask;
import org.flowable.engine.delegate.DelegateExecution;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * 多实例处理类
 *
 * @author KonBAI
 */
@AllArgsConstructor
@Component("multiInstanceHandler")
public class MultiInstanceHandler {
    @Autowired
    private RemoteUserService remoteUserService;
    public Set<String> getUserIds(DelegateExecution execution) {
        Set<String> candidateUserIds = new LinkedHashSet<>();
        FlowElement flowElement = execution.getCurrentFlowElement();
        if (ObjectUtil.isNotEmpty(flowElement) && flowElement instanceof UserTask) {
            UserTask userTask = (UserTask) flowElement;
            String dataType = userTask.getAttributeValue(ProcessConstants.NAMASPASE, ProcessConstants.PROCESS_CUSTOM_DATA_TYPE);
            if ("USERS".equals(dataType) && CollUtil.isNotEmpty(userTask.getCandidateUsers())) {
                // 添加候选用户id
                candidateUserIds.addAll(userTask.getCandidateUsers());
            } else if (CollUtil.isNotEmpty(userTask.getCandidateGroups())) {
                // 获取组的ID，角色ID集合或部门ID集合
                List<Long> groups = userTask.getCandidateGroups().stream()
                    .map(item -> Long.parseLong(item.substring(4)))
                    .collect(Collectors.toList());
                List<Long> userIds = new ArrayList<>();
                if ("ROLES".equals(dataType)) {
                    //todo 通过角色id，获取所有用户id集合
                    R<List<SysUser>> userList = remoteUserService.listByRoleIds(groups, SecurityConstants.INNER);
                    if(!StringUtils.isNull(userList) && !StringUtils.isNull(userList.getData())) {
                        List<SysUser> userListData = userList.getData();
                        for(SysUser user : userListData) {
                            userIds.add(user.getUserId());
                        }
                    }
                } else if ("DEPTS".equals(dataType)) {
                    //todo 通过部门id，获取所有用户id集合
                    R<List<SysUser>> userList = remoteUserService.listByDeptIds(groups, SecurityConstants.INNER);
                    if(!StringUtils.isNull(userList) && ! StringUtils.isNull(userList.getData())) {
                        List<SysUser> userListData = userList.getData();
                        for(SysUser user : userListData) {
                            userIds.add(user.getUserId());
                        }
                    }
                }
                // 添加候选用户id
                userIds.forEach(id -> candidateUserIds.add(String.valueOf(id)));
            }
        }
        return candidateUserIds;
    }
}
