package com.ruoyi.flowable.workflow.service.impl;

import com.ruoyi.common.core.exception.ServiceException;
import com.ruoyi.flowable.utils.TaskUtils;
import com.ruoyi.flowable.workflow.domain.bo.WfTaskBo;
import com.ruoyi.flowable.workflow.service.IWfCopyService;
import com.ruoyi.system.api.RemoteUserService;
import org.flowable.bpmn.model.BpmnModel;
import org.flowable.engine.IdentityService;
import org.flowable.engine.RepositoryService;
import org.flowable.engine.TaskService;
import org.flowable.identitylink.api.IdentityLink;
import org.flowable.task.api.Task;
import org.flowable.task.api.TaskQuery;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;
import java.util.List;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.*;

/** 审批归属与候选人回归，不连接实际流程引擎。 */
class WfTaskAuthorizationTest {
    @Test
    void cannotCompleteAnotherUsersTask() {
        verifyCompletion("other", false, false);
    }

    @Test
    void cannotCompleteUnassignedTaskWithoutCandidateAccess() {
        verifyCompletion(null, false, false);
    }

    @Test
    void assigneeCanComplete() {
        verifyCompletion("42", false, true);
    }

    @Test
    void candidateClaimsBeforeCompleting() {
        verifyCompletion(null, true, true);
    }

    @Test
    void cannotStealTaskThroughAssignmentEndpoints() {
        TaskService tasks = mock(TaskService.class);
        TaskQuery query = mock(TaskQuery.class, RETURNS_SELF);
        Task task = mock(Task.class);
        when(tasks.createTaskQuery()).thenReturn(query);
        when(query.singleResult()).thenReturn(task);
        when(task.getAssignee()).thenReturn("other");
        var service = new WfTaskServiceImpl(mock(RemoteUserService.class), mock(IWfCopyService.class));
        ReflectionTestUtils.setField(service, "taskService", tasks);
        WfTaskBo bo = new WfTaskBo();
        bo.setTaskId("task");
        bo.setUserId("42");
        try (var user = mockStatic(TaskUtils.class)) {
            user.when(TaskUtils::getUserId).thenReturn("42");
            assertThrows(ServiceException.class, () -> service.claim(bo));
            assertThrows(ServiceException.class, () -> service.unClaim(bo));
            assertThrows(ServiceException.class, () -> service.transferTask(bo));
            assertThrows(ServiceException.class, () -> service.delegateTask(bo));
            verify(tasks, never()).claim(anyString(), anyString());
            verify(tasks, never()).unclaim(anyString());
            verify(tasks, never()).setAssignee(anyString(), anyString());
        }
    }

    private void verifyCompletion(String assignee, boolean candidate, boolean allowed) {
        TaskService tasks = mock(TaskService.class);
        TaskQuery query = mock(TaskQuery.class, RETURNS_SELF);
        Task task = mock(Task.class);
        when(tasks.createTaskQuery()).thenReturn(query);
        when(query.singleResult()).thenReturn(task);
        when(task.getId()).thenReturn("task");
        when(task.getAssignee()).thenReturn(assignee);
        when(task.getProcessInstanceId()).thenReturn("instance");
        IdentityLink link = mock(IdentityLink.class);
        when(link.getType()).thenReturn("candidate");
        when(link.getGroupId()).thenReturn("ROLE7");
        when(tasks.getIdentityLinksForTask("task")).thenReturn(candidate ? List.of(link) : List.of());
        IWfCopyService copy = mock(IWfCopyService.class);
        when(copy.makeCopy(any())).thenReturn(true);
        var service = new WfTaskServiceImpl(mock(RemoteUserService.class), copy);
        RepositoryService repository = mock(RepositoryService.class);
        when(repository.getBpmnModel(any())).thenReturn(new BpmnModel());
        ReflectionTestUtils.setField(service, "taskService", tasks);
        ReflectionTestUtils.setField(service, "repositoryService", repository);
        ReflectionTestUtils.setField(service, "identityService", mock(IdentityService.class));
        WfTaskBo bo = new WfTaskBo();
        bo.setTaskId("task");
        try (var user = mockStatic(TaskUtils.class)) {
            user.when(TaskUtils::getUserId).thenReturn("42");
            user.when(TaskUtils::getCandidateGroup).thenReturn(List.of("ROLE7"));
            if (allowed) {
                service.complete(bo);
                verify(tasks).complete("task");
                if (assignee == null) {
                    var order = inOrder(tasks);
                    order.verify(tasks).claim("task", "42");
                    order.verify(tasks).complete("task");
                }
            } else {
                assertThrows(ServiceException.class, () -> service.complete(bo));
                verify(tasks, never()).complete(anyString());
                verify(tasks, never()).claim(anyString(), anyString());
            }
            verify(tasks, never()).setAssignee(anyString(), anyString());
        }
    }
}
