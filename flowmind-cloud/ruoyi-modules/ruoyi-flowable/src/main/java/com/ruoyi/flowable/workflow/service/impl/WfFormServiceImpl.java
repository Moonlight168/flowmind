package com.ruoyi.flowable.workflow.service.impl;

import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.ruoyi.common.core.utils.StringUtils;
import com.ruoyi.common.security.utils.SecurityUtils;
import com.ruoyi.flowable.core.domain.model.PageQuery;
import com.ruoyi.flowable.core.page.TableDataInfo;
import com.ruoyi.flowable.workflow.domain.WfForm;
import com.ruoyi.flowable.workflow.domain.bo.WfFormBo;
import com.ruoyi.flowable.workflow.domain.vo.WfFormVo;
import com.ruoyi.flowable.workflow.mapper.WfFormMapper;
import com.ruoyi.flowable.workflow.service.IWfFormService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.Collection;
import java.util.Date;
import java.util.List;
import java.util.Map;

/**
 * 流程表单Service业务层处理
 *
 * @author KonBAI
 * @createTime 2022/3/7 22:07
 */
@RequiredArgsConstructor
@Service
public class WfFormServiceImpl implements IWfFormService {

    private final WfFormMapper baseMapper;

    /**
     * 查询流程表单
     *
     * @param formId 流程表单ID
     * @return 流程表单
     */
    @Override
    public WfFormVo queryById(Long formId) {
        return baseMapper.selectVoById(formId);
    }

    /**
     * 查询流程表单列表
     *
     * @param bo 流程表单
     * @return 流程表单
     */
    @Override
    public TableDataInfo<WfFormVo> queryPageList(WfFormBo bo, PageQuery pageQuery) {
        LambdaQueryWrapper<WfForm> lqw = buildQueryWrapper(bo);
        Page<WfFormVo> result = baseMapper.selectVoPage(pageQuery.build(), lqw);
        return TableDataInfo.build(result);
    }

    /**
     * 查询流程表单列表
     *
     * @param bo 流程表单
     * @return 流程表单
     */
    @Override
    public List<WfFormVo> queryList(WfFormBo bo) {
        LambdaQueryWrapper<WfForm> lqw = buildQueryWrapper(bo);
        return baseMapper.selectVoList(lqw);
    }

    /**
     * 新增流程表单
     *
     * @param bo 流程表单
     * @return 结果
     */
    @Override
    public int insertForm(WfFormBo bo) {
        WfForm wfForm = new WfForm();
        wfForm.setFormName(bo.getFormName());
        wfForm.setContent(bo.getContent());
        wfForm.setRemark(bo.getRemark());

        // 设置审计字段
        String username = SecurityUtils.getUsername();
        Date now = new Date();
        wfForm.setCreateBy(username);
        wfForm.setCreateTime(now);
        wfForm.setUpdateBy(username);
        wfForm.setUpdateTime(now);

        return baseMapper.insert(wfForm);
    }

    /**
     * 修改流程表单
     *
     * @param bo 流程表单
     * @return 结果
     */
    @Override
    public int updateForm(WfFormBo bo) {
        // 设置审计字段
        String username = SecurityUtils.getUsername();
        Date now = new Date();

        return baseMapper.update(new WfForm(), new LambdaUpdateWrapper<WfForm>()
                .set(StrUtil.isNotBlank(bo.getFormName()), WfForm::getFormName, bo.getFormName())
                .set(StrUtil.isNotBlank(bo.getContent()), WfForm::getContent, bo.getContent())
                .set(StrUtil.isNotBlank(bo.getRemark()), WfForm::getRemark, bo.getRemark())
                .set(WfForm::getUpdateBy, username)
                .set(WfForm::getUpdateTime, now)
                .eq(WfForm::getFormId, bo.getFormId()));
    }

    /**
     * 批量删除流程表单
     *
     * @param ids 需要删除的流程表单ID
     * @return 结果
     */
    @Override
    public Boolean deleteWithValidByIds(Collection<Long> ids) {
        return baseMapper.deleteBatchIds(ids) > 0;
    }

    private LambdaQueryWrapper<WfForm> buildQueryWrapper(WfFormBo bo) {
        Map<String, Object> params = bo.getParams();
        LambdaQueryWrapper<WfForm> lqw = Wrappers.lambdaQuery();
        lqw.like(StringUtils.isNotBlank(bo.getFormName()), WfForm::getFormName, bo.getFormName());
        return lqw;
    }
}
