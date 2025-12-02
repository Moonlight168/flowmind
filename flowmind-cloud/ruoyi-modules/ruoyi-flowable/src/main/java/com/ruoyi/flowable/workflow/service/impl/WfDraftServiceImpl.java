package com.ruoyi.flowable.workflow.service.impl;

import cn.hutool.core.bean.BeanUtil;
import cn.hutool.core.util.ObjectUtil;
import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.ruoyi.common.core.exception.ServiceException;
import com.ruoyi.common.core.utils.DateUtils;
import com.ruoyi.common.core.utils.StringUtils;
import com.ruoyi.common.security.utils.SecurityUtils;
import com.ruoyi.flowable.core.domain.model.PageQuery;
import com.ruoyi.flowable.factory.FlowServiceFactory;
import com.ruoyi.flowable.workflow.domain.WfDraft;
import com.ruoyi.flowable.workflow.domain.bo.WfDraftBo;
import com.ruoyi.flowable.workflow.domain.vo.WfDraftVo;
import com.ruoyi.flowable.workflow.mapper.WfDraftMapper;
import com.ruoyi.flowable.workflow.service.IWfDraftService;
import lombok.RequiredArgsConstructor;
import org.flowable.engine.repository.ProcessDefinition;
import org.springframework.stereotype.Service;

import java.util.Collection;
import java.util.Date;
import java.util.List;
import java.util.Map;

/**
 * 流程草稿Service业务层处理
 *
 * @author ruoyi
 * @createTime 2025/01/01 00:00
 */
@RequiredArgsConstructor
@Service
public class WfDraftServiceImpl extends FlowServiceFactory implements IWfDraftService {

    private final WfDraftMapper draftMapper;

    /**
     * 查询流程草稿
     *
     * @param draftId 流程草稿ID
     * @return 流程草稿
     */
    @Override
    public WfDraftVo queryById(Long draftId) {
        return draftMapper.selectVoById(draftId);
    }

    /**
     * 根据用户ID和流程定义ID查询草稿
     *
     * @param userId 用户ID
     * @param definitionId 流程定义ID
     * @return 流程草稿
     */
    @Override
    public WfDraftVo queryByUserIdAndDefId(Long userId, String definitionId) {
        return draftMapper.selectByUserIdAndDefId(userId, definitionId);
    }

    /**
     * 查询流程草稿列表
     *
     * @param bo 流程草稿
     * @return 流程草稿
     */
    @Override
    public Page<WfDraftVo> queryPageList(WfDraftBo bo, PageQuery pageQuery) {
        LambdaQueryWrapper<WfDraft> lqw = buildQueryWrapper(bo);
        Page<WfDraftVo> result = draftMapper.selectVoPage(pageQuery.build(), lqw);
        return result;
    }

    /**
     * 查询流程草稿列表（不分页）
     *
     * @param bo 流程草稿
     * @return 流程草稿
     */
    @Override
    public List<WfDraftVo> queryList(WfDraftBo bo) {
        LambdaQueryWrapper<WfDraft> lqw = buildQueryWrapper(bo);
        return draftMapper.selectVoList(lqw);
    }


    /**
     * 批量删除流程草稿
     *
     * @param ids 需要删除的流程草稿ID
     * @return 结果
     */
    @Override
    public Boolean deleteWithValidByIds(Collection<Long> ids) {
        return draftMapper.deleteBatchIds(ids) > 0;
    }

    /**
     * 新增或更新流程草稿
     *
     * @param bo 草稿业务对象
     * @return 结果
     */
    @Override
    public Boolean saveOrUpdateDraft(WfDraftBo bo) {
        // 根据流程定义ID获取流程名称
        if (StringUtils.isNotBlank(bo.getDefinitionId()) && StringUtils.isBlank(bo.getProcessName())) {
            ProcessDefinition processDefinition = repositoryService.createProcessDefinitionQuery()
                .processDefinitionId(bo.getDefinitionId())
                .singleResult();
            if (processDefinition != null) {
                bo.setProcessName(processDefinition.getName());
            }
        }

        //由于是逻辑删除，应该先搜索现有草稿是否存在，避免唯一索引冲突
        //根据用户id跟流程id,查询是否已存在草稿(因为是保存，所以如果逻辑删除的话直接恢复delflag字段为0即可)
        WfDraftVo existingDraft = draftMapper.selectByUserIdAndDefIdWithDelFlag(bo.getUserId(), bo.getDefinitionId());
        if (ObjectUtil.isNotNull(existingDraft)) {
            // 如果存在，插入草稿id
            bo.setDraftId(existingDraft.getDraftId());
        }

        WfDraft draft = BeanUtil.toBean(bo, WfDraft.class);

        // 判断是新增还是修改
        if (ObjectUtil.isNotNull(draft.getDraftId())) {
            // 修改，先恢复草稿
            restoreByDefinitionId(bo.getDefinitionId());
            draft.setUpdateBy(SecurityUtils.getUsername());
            draft.setUpdateTime(DateUtils.getNowDate());
            return draftMapper.updateById(draft) > 0;
        } else {
            // 新增
            draft.setCreateBy(SecurityUtils.getUsername());
            draft.setCreateTime(DateUtils.getNowDate());
            draft.setDelFlag("0");
            return draftMapper.insert(draft) > 0;
        }
    }

    /**
     * 根据流程定义ID逻辑删除草稿
     *
     * @param definitionId 流程定义ID
     * @return 结果
     */
    @Override
    public int deleteByDefinitionId(String definitionId) {
        if (StrUtil.isBlank(definitionId)) {
            return 0;
        }
        return draftMapper.deleteByDefinitionId(definitionId);
    }

    /**
     * 根据流程定义ID逻辑恢复草稿
     *
     * @param definitionId 流程定义ID
     * @return 结果
     */
    public int restoreByDefinitionId(String definitionId) {
        if (StrUtil.isBlank(definitionId)) {
            return 0;
        }
        return draftMapper.restoreByDefinitionId(definitionId);
    }



    private LambdaQueryWrapper<WfDraft> buildQueryWrapper(WfDraftBo bo) {
        Map<String, Object> params = bo.getParams();
        LambdaQueryWrapper<WfDraft> lqw = Wrappers.lambdaQuery();
        lqw.eq(bo.getUserId() != null, WfDraft::getUserId, bo.getUserId());
        lqw.eq(bo.getDefinitionId() != null, WfDraft::getDefinitionId, bo.getDefinitionId());
        lqw.like(StringUtils.isNotBlank(bo.getProcessName()), WfDraft::getProcessName, bo.getProcessName());
        lqw.eq(StringUtils.isNotBlank(bo.getDelFlag()), WfDraft::getDelFlag, bo.getDelFlag());
        lqw.orderByDesc(WfDraft::getUpdateTime);
        return lqw;
    }
}