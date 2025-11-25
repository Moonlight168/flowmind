package com.ruoyi.flowable.workflow.service.impl;

import cn.hutool.core.bean.BeanUtil;
import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.ruoyi.common.core.utils.StringUtils;
import com.ruoyi.common.core.utils.bean.BeanUtils;
import com.ruoyi.flowable.core.domain.model.PageQuery;
import com.ruoyi.flowable.core.page.TableDataInfo;
import com.ruoyi.flowable.workflow.domain.WfDraft;
import com.ruoyi.flowable.workflow.domain.bo.WfDraftBo;
import com.ruoyi.flowable.workflow.domain.vo.WfDraftVo;
import com.ruoyi.flowable.workflow.mapper.WfDraftMapper;
import com.ruoyi.flowable.workflow.service.IWfDraftService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.Collection;
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
public class WfDraftServiceImpl implements IWfDraftService {

    private final WfDraftMapper baseMapper;

    /**
     * 查询流程草稿
     *
     * @param draftId 流程草稿ID
     * @return 流程草稿
     */
    @Override
    public WfDraftVo queryById(Long draftId) {
        return baseMapper.selectVoById(draftId);
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
        return baseMapper.selectByUserIdAndDefId(userId, definitionId);
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
        Page<WfDraftVo> result = baseMapper.selectVoPage(pageQuery.build(), lqw);
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
        return baseMapper.selectVoList(lqw);
    }

    /**
     * 新增流程草稿
     *
     * @param bo 流程草稿
     * @return 结果
     */
    @Override
    public int insertDraft(WfDraftBo bo) {
        WfDraft wfDraft = BeanUtil.toBean(bo, WfDraft.class);
        return baseMapper.insert(wfDraft);
    }

    /**
     * 修改流程草稿
     *
     * @param bo 流程草稿
     * @return 结果
     */
    @Override
    public int updateDraft(WfDraftBo bo) {
        WfDraft wfDraft = BeanUtil.toBean(bo, WfDraft.class);
        return baseMapper.updateById(wfDraft);
    }

    /**
     * 批量删除流程草稿
     *
     * @param ids 需要删除的流程草稿ID
     * @return 结果
     */
    @Override
    public Boolean deleteWithValidByIds(Collection<Long> ids) {
        return baseMapper.deleteBatchIds(ids) > 0;
    }

    /**
     * 保存或更新草稿（确保同一流程只能存在一个草稿）
     *
     * @param bo 流程草稿
     * @return 结果
     */
    @Override
    public int saveOrUpdateDraft(WfDraftBo bo) {
        // 先查询是否已存在该用户和流程定义的草稿
        WfDraftVo existingDraft = queryByUserIdAndDefId(bo.getUserId(), bo.getDefinitionId());
        
        // 流程名称是必填字段，不需要设置默认值
        
        if (existingDraft != null) {
            // 如果存在，更新现有草稿
            bo.setDraftId(existingDraft.getDraftId());
            // 保留原有的部署ID（如果新的为空）
            if (bo.getDeployId() == null && existingDraft.getDeployId() != null) {
                bo.setDeployId(existingDraft.getDeployId());
            }
            return updateDraft(bo);
        } else {
            // 如果不存在，创建新草稿
            int result = insertDraft(bo);
            // 如果插入成功，获取生成的ID
            if (result > 0) {
                // 这里假设insertDraft方法会设置生成的ID到bo对象中
                // 如果没有，需要查询获取ID
                if (bo.getDraftId() == null) {
                    WfDraftVo newDraft = queryByUserIdAndDefId(bo.getUserId(), bo.getDefinitionId());
                    if (newDraft != null) {
                        bo.setDraftId(newDraft.getDraftId());
                    }
                }
            }
            return result;
        }
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