package com.ruoyi.flowable.workflow.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.ruoyi.common.core.utils.poi.ExcelUtil;
import com.ruoyi.common.core.web.controller.BaseController;
import com.ruoyi.common.core.web.domain.AjaxResult;
import com.ruoyi.common.core.web.page.TableDataInfo;
import com.ruoyi.common.log.annotation.Log;
import com.ruoyi.common.log.enums.BusinessType;
import com.ruoyi.common.security.annotation.RequiresPermissions;
import com.ruoyi.common.security.utils.SecurityUtils;
import com.ruoyi.flowable.common.validate.QueryGroup;
import com.ruoyi.flowable.core.domain.model.PageQuery;
import com.ruoyi.flowable.workflow.domain.bo.WfDraftBo;
import com.ruoyi.flowable.workflow.domain.vo.WfDraftVo;
import com.ruoyi.flowable.workflow.service.IWfDraftService;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import java.util.Arrays;
import java.util.List;

/**
 * 流程草稿Controller
 *
 * @author ruoyi
 * @createTime 2025/01/01 00:00
 */
@RequiredArgsConstructor
@RestController
@RequestMapping("/draft")
public class WfDraftController extends BaseController {

    private final IWfDraftService draftService;

    /**
     * 查询流程草稿列表
     */
    @GetMapping("/list")
    public TableDataInfo list( PageQuery pageQuery) {
        // 设置当前用户ID，只查询当前用户的草稿
        WfDraftBo bo = new WfDraftBo();
        bo.setUserId(SecurityUtils.getUserId());
        Page<WfDraftVo> wfDraftVoPage = draftService.queryPageList(bo, pageQuery);
        return new TableDataInfo(wfDraftVoPage.getRecords(), wfDraftVoPage.getTotal());
    }

    /**
     * 导出流程草稿列表
     */
    @PostMapping("/export")
    public void export(@Validated WfDraftBo bo, HttpServletResponse response) {
        // 设置当前用户ID，只导出当前用户的草稿
        bo.setUserId(SecurityUtils.getUserId());
        List<WfDraftVo> list = draftService.queryList(bo);
        ExcelUtil<WfDraftVo> util = new ExcelUtil<WfDraftVo>(WfDraftVo.class);
        util.exportExcel(response, list, "流程草稿", "流程草稿");
    }

    /**
     * 获取流程草稿详细信息
     *
     * @param draftId 主键
     */
    @GetMapping(value = "/{draftId}")
    public AjaxResult getInfo(@NotNull(message = "主键不能为空") @PathVariable("draftId") Long draftId) {
        return AjaxResult.success(draftService.queryById(draftId));
    }

    /**
     * 根据流程定义ID获取草稿
     *
     * @param definitionId 流程定义ID
     */
    @GetMapping(value = "/definition/{definitionId}")
    public AjaxResult getByDefinitionId(@NotNull(message = "流程定义ID不能为空") @PathVariable("definitionId") String definitionId) {
        WfDraftVo draft = draftService.queryByUserIdAndDefId(SecurityUtils.getUserId(), definitionId);
        return AjaxResult.success(draft);
    }

    /**
     * 新增流程草稿
     */
    @Log(title = "流程草稿", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody WfDraftBo bo) {
        // 设置当前用户ID
        bo.setUserId(SecurityUtils.getUserId());
        return toAjax(draftService.insertDraft(bo));
    }

    /**
     * 保存草稿（确保同一流程只能存在一个草稿）
     */
    @Log(title = "流程草稿", businessType = BusinessType.INSERT)
    @PostMapping("/saveDraft")
    public AjaxResult saveDraft( @RequestBody WfDraftBo bo) {
        // 设置当前用户ID
        bo.setUserId(SecurityUtils.getUserId());
        int result = draftService.saveOrUpdateDraft(bo);
        
        // 如果是新建草稿，返回草稿ID
        if (result > 0 && bo.getDraftId() != null) {
            return AjaxResult.success("保存成功", bo.getDraftId());
        }
        
        return toAjax(result);
    }

    /**
     * 修改流程草稿
     */
    @Log(title = "流程草稿", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody WfDraftBo bo) {
        return toAjax(draftService.updateDraft(bo));
    }

    /**
     * 删除流程草稿
     *
     * @param draftIds 主键串
     */
    @Log(title = "流程草稿", businessType = BusinessType.DELETE)
    @DeleteMapping("/{draftIds}")
    public AjaxResult remove(@NotEmpty(message = "主键不能为空") @PathVariable Long[] draftIds) {
        return toAjax(draftService.deleteWithValidByIds(Arrays.asList(draftIds)) ? 1 : 0);
    }
}