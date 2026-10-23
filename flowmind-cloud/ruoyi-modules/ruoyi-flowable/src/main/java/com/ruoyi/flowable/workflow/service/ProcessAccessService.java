package com.ruoyi.flowable.workflow.service;

import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.ruoyi.common.core.exception.ServiceException;
import com.ruoyi.common.security.utils.SecurityUtils;
import com.ruoyi.flowable.utils.TaskUtils;
import com.ruoyi.flowable.workflow.domain.WfCopy;
import com.ruoyi.flowable.workflow.mapper.WfCopyMapper;
import lombok.RequiredArgsConstructor;
import org.flowable.engine.HistoryService;
import org.flowable.engine.TaskService;
import org.flowable.engine.history.HistoricProcessInstance;
import org.flowable.task.api.Task;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Objects;

/** 流程实例的数据访问边界；登录身份不等同于流程访问权限。 */
@Service
@RequiredArgsConstructor
public class ProcessAccessService {
    private final HistoryService historyService;
    private final TaskService taskService;
    private final WfCopyMapper copyMapper;

    public void requireOwner(String startUserId) {
        Long userId = currentUserId();
        if (!SecurityUtils.isAdmin(userId) && !userId.toString().equals(startUserId)) {
            throw new ServiceException("无权操作此流程");
        }
    }

    public HistoricProcessInstance requireRead(String instanceId) {
        Long userId = currentUserId();
        HistoricProcessInstance process = historyService.createHistoricProcessInstanceQuery()
            .processInstanceId(instanceId).singleResult();
        if (process == null) {
            throw new ServiceException("流程不存在或无权访问");
        }
        String user = userId.toString();
        if (SecurityUtils.isAdmin(userId) || user.equals(process.getStartUserId())) {
            return process;
        }
        if (historyService.createHistoricTaskInstanceQuery().processInstanceId(instanceId)
            .taskAssignee(user).count() > 0) {
            return process;
        }
        List<String> groups = TaskUtils.getCandidateGroup();
        for (Task task : taskService.createTaskQuery().processInstanceId(instanceId).list()) {
            if (user.equals(task.getAssignee()) || user.equals(task.getOwner())) {
                return process;
            }
            if (task.getAssignee() == null && taskService.getIdentityLinksForTask(task.getId()).stream()
                .anyMatch(link -> "candidate".equals(link.getType())
                    && (user.equals(link.getUserId())
                        || (link.getGroupId() != null && groups.contains(link.getGroupId()))))) {
                return process;
            }
        }
        if (copyMapper.selectCount(Wrappers.<WfCopy>lambdaQuery()
            .eq(WfCopy::getInstanceId, instanceId).eq(WfCopy::getUserId, userId)) > 0) {
            return process;
        }
        throw new ServiceException("流程不存在或无权访问");
    }

    public void requireTaskRead(String taskId) {
        var task = historyService.createHistoricTaskInstanceQuery().taskId(taskId).singleResult();
        if (task == null) {
            throw new ServiceException("任务不存在或无权访问");
        }
        requireRead(task.getProcessInstanceId());
    }

    public void requireTaskInInstance(String taskInstanceId, String instanceId) {
        if (!Objects.equals(taskInstanceId, instanceId)) {
            throw new ServiceException("任务与流程实例不匹配");
        }
    }

    private Long currentUserId() {
        Long userId = SecurityUtils.getUserId();
        if (userId == null || userId <= 0) {
            throw new ServiceException("登录状态已失效");
        }
        return userId;
    }
}
