package com.ruoyi.flowable.workflow.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.ruoyi.flowable.core.domain.model.PageQuery;
import com.ruoyi.flowable.workflow.domain.bo.WfDraftBo;
import com.ruoyi.flowable.workflow.domain.vo.WfDraftVo;

import java.util.Collection;
import java.util.List;

/**
 * 流程草稿Service接口
 *
 * @author ruoyi
 * @createTime 2025/01/01 00:00
 */
public interface IWfDraftService {
    /**
     * 查询流程草稿
     *
     * @param draftId 流程草稿ID
     * @return 流程草稿
     */
    WfDraftVo queryById(Long draftId);

    /**
     * 根据用户ID和流程定义ID查询草稿
     *
     * @param userId 用户ID
     * @param definitionId 流程定义ID
     * @return 流程草稿
     */
    WfDraftVo queryByUserIdAndDefId(Long userId, String definitionId);

    /**
     * 查询流程草稿列表
     *
     * @param bo 流程草稿
     * @return 流程草稿集合
     */
    Page<WfDraftVo> queryPageList(WfDraftBo bo, PageQuery pageQuery);

    /**
     * 查询流程草稿列表
     *
     * @param bo 流程草稿
     * @return 流程草稿集合
     */
    List<WfDraftVo> queryList(WfDraftBo bo);



    /**
     * 批量删除流程草稿
     *
     * @param draftIds 需要删除的流程草稿ID
     * @return 结果
     */
    Boolean deleteWithValidByIds(Collection<Long> draftIds);

    /**
     * 保存或更新草稿（确保同一流程只能存在一个草稿）
     *
     * @param bo 流程草稿
     * @return 结果
     */
    Boolean saveOrUpdateDraft(WfDraftBo bo);

    /**
     * 根据流程定义ID逻辑删除草稿
     *
     * @param dartId 流程定义ID
     * @return 结果
     */
    int deleteByDefinitionId(String dartId);
}