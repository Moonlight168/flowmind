package com.ruoyi.flowable.workflow.controller;

import cn.hutool.core.bean.BeanUtil;
import com.ruoyi.common.core.domain.R;
import com.ruoyi.common.core.utils.poi.ExcelUtil;
import com.ruoyi.common.core.web.controller.BaseController;
import com.ruoyi.common.core.web.domain.AjaxResult;
import com.ruoyi.flowable.common.validate.AddGroup;
import com.ruoyi.flowable.common.validate.EditGroup;
import com.ruoyi.flowable.core.domain.model.PageQuery;
import com.ruoyi.flowable.core.page.TableDataInfo;
import com.ruoyi.flowable.workflow.domain.WfCategory;
import com.ruoyi.flowable.workflow.domain.bo.WfModelBo;
import com.ruoyi.flowable.workflow.domain.vo.WfCategoryVo;
import com.ruoyi.flowable.workflow.domain.vo.WfModelExportVo;
import com.ruoyi.flowable.workflow.domain.vo.WfModelVo;
import com.ruoyi.flowable.workflow.service.IWfCategoryService;
import com.ruoyi.flowable.workflow.service.IWfModelService;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 工作流流程模型管理
 *
 * @author KonBAI
 * @createTime 2022/6/21 9:09
 */
@Slf4j
@RequiredArgsConstructor
@RestController
@RequestMapping("/model")
public class WfModelController extends BaseController {

    private final IWfModelService modelService;
    private final IWfCategoryService categoryService;

    /**
     * 查询流程模型列表
     *
     * @param modelBo 流程模型对象
     * @param pageQuery 分页参数
     */
    @GetMapping("/list")
    public TableDataInfo<WfModelVo> list(WfModelBo modelBo, PageQuery pageQuery) {
        return modelService.list(modelBo, pageQuery);
    }

    /**
     * 查询流程模型列表
     *
     * @param modelBo 流程模型对象
     * @param pageQuery 分页参数
     */
    @GetMapping("/historyList")
    public TableDataInfo<WfModelVo> historyList(WfModelBo modelBo, PageQuery pageQuery) {
        return modelService.historyList(modelBo, pageQuery);
    }

    /**
     * 获取流程模型详细信息
     *
     * @param modelId 模型主键
     */
    @GetMapping(value = "/{modelId}")
    public R<WfModelVo> getInfo(@NotNull(message = "主键不能为空") @PathVariable("modelId") String modelId) {
        return R.ok(modelService.getModel(modelId));
    }

    /**
     * 获取流程表单详细信息
     *
     * @param modelId 模型主键
     */
    @GetMapping(value = "/bpmnXml/{modelId}")
    public R<String> getBpmnXml(@NotNull(message = "主键不能为空") @PathVariable("modelId") String modelId) {
        return R.ok(modelService.queryBpmnXmlById(modelId),"操作成功");
    }

    /**
     * 新增流程模型
     */
    @PostMapping
    public R<Void> add(@Validated(AddGroup.class) @RequestBody WfModelBo modelBo) {
        modelService.insertModel(modelBo);
        return R.ok(null,"操作成功");
    }

    /**
     * 修改流程模型
     */
    @PutMapping
    public R<Void> edit(@Validated(EditGroup.class) @RequestBody WfModelBo modelBo) {
        modelService.updateModel(modelBo);
         return R.ok(null,"操作成功");
    }

    /**
     * 保存流程模型
     */
    @PostMapping("/save")
    public R<String> save(@RequestBody WfModelBo modelBo) {
        modelService.saveModel(modelBo);
         return R.ok(null,"操作成功");
    }

    /**
     * 设为最新流程模型
     * @param modelId
     * @return
     */
    @PostMapping("/latest")
    public R<?> latest(@RequestParam String modelId) {
        modelService.latestModel(modelId);
         return R.ok(null,"操作成功");
    }

    /**
     * 删除流程模型
     *
     * @param modelIds 流程模型主键串
     */
    @DeleteMapping("/{modelIds}")
    public R<String> remove(@NotEmpty(message = "主键不能为空") @PathVariable String[] modelIds) {
        modelService.deleteByIds(Arrays.asList(modelIds));
         return R.ok(null,"操作成功");
    }

    /**
     * 部署流程模型
     *
     * @param modelId 流程模型主键
     */
    @PostMapping("/deploy")
    public AjaxResult deployModel(@RequestParam String modelId) {
        return toAjax(modelService.deployModel(modelId));
    }

    /**
     * 导出流程模型数据
     */
    @PostMapping("/export")
    public void export(WfModelBo modelBo, HttpServletResponse response) {
        List<WfModelVo> list =  modelService.list(modelBo);
        List<WfModelExportVo> listVo = BeanUtil.copyToList(list, WfModelExportVo.class);
        List<WfCategoryVo> categoryVos = categoryService.queryList(new WfCategory());
        Map<String, String> categoryMap = categoryVos.stream()
            .collect(Collectors.toMap(WfCategoryVo::getCode, WfCategoryVo::getCategoryName));
        for (WfModelExportVo exportVo : listVo) {
            exportVo.setCategoryName(categoryMap.get(exportVo.getCategory()));
        }
        ExcelUtil<WfModelExportVo> util = new ExcelUtil<WfModelExportVo>(WfModelExportVo.class);
        // 确保列表不为null，避免Excel导出时出现"Invalid cell range"错误
        if (listVo == null) {
            listVo = new ArrayList<>();
        }
        util.exportExcel(response, listVo, "流程模型数据","流程模型数据");
    }
}
