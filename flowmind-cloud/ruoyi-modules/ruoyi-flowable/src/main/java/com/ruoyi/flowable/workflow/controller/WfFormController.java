package com.ruoyi.flowable.workflow.controller;

import com.ruoyi.common.core.utils.poi.ExcelUtil;
import com.ruoyi.common.core.web.controller.BaseController;
import com.ruoyi.common.core.web.domain.AjaxResult;
import com.ruoyi.flowable.common.validate.QueryGroup;
import com.ruoyi.flowable.core.domain.model.PageQuery;
import com.ruoyi.flowable.core.page.TableDataInfo;
import com.ruoyi.flowable.workflow.domain.WfDeployForm;
import com.ruoyi.flowable.workflow.domain.bo.WfFormBo;
import com.ruoyi.flowable.workflow.domain.vo.WfFormVo;
import com.ruoyi.flowable.workflow.service.IWfDeployFormService;
import com.ruoyi.flowable.workflow.service.IWfFormService;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import java.util.Arrays;
import java.util.List;

/**
 * 流程表单Controller
 *
 * @author KonBAI
 * @createTime 2022/3/7 22:07
 */
@RequiredArgsConstructor
@RestController
@RequestMapping("/form")
public class WfFormController extends BaseController {

    private final IWfFormService formService;

    private final IWfDeployFormService deployFormService;

    /**
     * 查询流程表单列表
     */
    @GetMapping("/list")
    public TableDataInfo<WfFormVo> list(@Validated(QueryGroup.class) WfFormBo bo, PageQuery pageQuery) {
        return formService.queryPageList(bo, pageQuery);
    }

    /**
     * 导出流程表单列表
     */
    @PostMapping("/export")
    public void export(@Validated WfFormBo bo, HttpServletResponse response) {
        List<WfFormVo> list = formService.queryList(bo);
        ExcelUtil<WfFormVo> util = new ExcelUtil<WfFormVo>(WfFormVo.class);
        util.exportExcel(response, list, "流程表单","流程表单");
    }

    /**
     * 获取流程表单详细信息
     * @param formId 主键
     */
    @GetMapping(value = "/{formId}")
    public AjaxResult getInfo(@NotNull(message = "主键不能为空") @PathVariable("formId") Long formId) {
        return AjaxResult.success(formService.queryById(formId));
    }

    /**
     * 新增流程表单
     */
    @PostMapping
    public AjaxResult add(@RequestBody WfFormBo bo) {
        return toAjax(formService.insertForm(bo));
    }

    /**
     * 修改流程表单
     */
    @PutMapping
    public AjaxResult edit(@RequestBody WfFormBo bo) {
        return toAjax(formService.updateForm(bo));
    }

    /**
     * 删除流程表单
     * @param formIds 主键串
     */
    @DeleteMapping("/{formIds}")
    public AjaxResult remove(@NotEmpty(message = "主键不能为空") @PathVariable Long[] formIds) {
        return toAjax(formService.deleteWithValidByIds(Arrays.asList(formIds)) ? 1 : 0);
    }


    /**
     * 挂载流程表单
     */
    @PostMapping("/addDeployForm")
    public AjaxResult addDeployForm(@RequestBody WfDeployForm deployForm) {
        return toAjax(deployFormService.insertWfDeployForm(deployForm));
    }
}
