package com.ruoyi.flowable.workflow.service.impl;

import com.ruoyi.common.core.exception.ServiceException;
import com.ruoyi.common.security.utils.SecurityUtils;
import com.ruoyi.flowable.utils.TaskUtils;
import com.ruoyi.flowable.workflow.mapper.WfCopyMapper;
import com.ruoyi.flowable.workflow.service.ProcessAccessService;
import org.flowable.engine.HistoryService;
import org.flowable.engine.TaskService;
import org.flowable.engine.history.HistoricProcessInstance;
import org.flowable.engine.history.HistoricProcessInstanceQuery;
import org.flowable.identitylink.api.IdentityLink;
import org.flowable.task.api.Task;
import org.flowable.task.api.TaskQuery;
import org.flowable.task.api.history.HistoricTaskInstanceQuery;
import org.junit.jupiter.api.*;
import org.mockito.MockedStatic;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/** 流程访问矩阵：所有者、参与人、候选人、抄送人及管理员。 */
class ProcessAccessServiceTest {
    private final HistoryService history = mock(HistoryService.class);
    private final TaskService tasks = mock(TaskService.class);
    private final WfCopyMapper copies = mock(WfCopyMapper.class);
    private final HistoricProcessInstance process = mock(HistoricProcessInstance.class);
    private final HistoricTaskInstanceQuery historyTasks = mock(HistoricTaskInstanceQuery.class, RETURNS_SELF);
    private final TaskQuery currentTasks = mock(TaskQuery.class, RETURNS_SELF);
    private final ProcessAccessService access = new ProcessAccessService(history, tasks, copies);
    private MockedStatic<SecurityUtils> security;
    private MockedStatic<TaskUtils> taskUtils;

    @BeforeEach
    void setup() {
        security = mockStatic(SecurityUtils.class, CALLS_REAL_METHODS);
        security.when(SecurityUtils::getUserId).thenReturn(42L);
        taskUtils = mockStatic(TaskUtils.class);
        taskUtils.when(TaskUtils::getCandidateGroup).thenReturn(List.of("ROLE7"));
        var query = mock(HistoricProcessInstanceQuery.class, RETURNS_SELF);
        when(history.createHistoricProcessInstanceQuery()).thenReturn(query);
        when(query.singleResult()).thenReturn(process);
        when(process.getStartUserId()).thenReturn("99");
        when(history.createHistoricTaskInstanceQuery()).thenReturn(historyTasks);
        when(tasks.createTaskQuery()).thenReturn(currentTasks);
        when(currentTasks.list()).thenReturn(List.of());
    }

    @AfterEach
    void close() { security.close(); taskUtils.close(); }

    @Test
    void strangerCannotReadOrManage() {
        assertThrows(ServiceException.class, () -> access.requireRead("instance"));
        assertThrows(ServiceException.class, () -> access.requireOwner("99"));
    }

    @Test
    void initiatorCanReadAndManage() {
        when(process.getStartUserId()).thenReturn("42");
        assertSame(process, access.requireRead("instance"));
        assertDoesNotThrow(() -> access.requireOwner("42"));
    }

    @Test
    void administratorCanReadAndManage() {
        security.when(SecurityUtils::getUserId).thenReturn(1L);
        assertSame(process, access.requireRead("instance"));
        assertDoesNotThrow(() -> access.requireOwner("99"));
    }

    @Test
    void historicParticipantCanReadButCannotManage() {
        when(historyTasks.count()).thenReturn(1L);
        assertSame(process, access.requireRead("instance"));
        verify(historyTasks).processInstanceId("instance");
        verify(historyTasks).taskAssignee("42");
        assertThrows(ServiceException.class, () -> access.requireOwner("99"));
    }

    @Test
    void copyRecipientCanRead() {
        when(copies.selectCount(any())).thenReturn(1L);
        assertSame(process, access.requireRead("instance"));
    }

    @Test
    void roleCandidateCanReadUnclaimedTask() {
        Task task = mock(Task.class);
        when(task.getId()).thenReturn("task");
        when(currentTasks.list()).thenReturn(List.of(task));
        IdentityLink link = mock(IdentityLink.class);
        when(link.getType()).thenReturn("candidate");
        when(link.getGroupId()).thenReturn("ROLE7");
        when(tasks.getIdentityLinksForTask("task")).thenReturn(List.of(link));
        assertSame(process, access.requireRead("instance"));
        when(task.getAssignee()).thenReturn("99");
        assertThrows(ServiceException.class, () -> access.requireRead("instance"));
    }

    @Test
    void rejectsMixedInstancesAndMissingIdentity() {
        assertThrows(ServiceException.class, () -> access.requireTaskInInstance("a", "b"));
        security.when(SecurityUtils::getUserId).thenReturn(0L);
        assertThrows(ServiceException.class, () -> access.requireRead("instance"));
    }
}
