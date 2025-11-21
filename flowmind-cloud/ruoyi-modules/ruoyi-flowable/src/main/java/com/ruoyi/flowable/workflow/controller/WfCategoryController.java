package com.ruoyi.flowable.workflow.controller;

import com.ruoyi.common.core.domain.R;
import com.ruoyi.common.core.utils.poi.ExcelUtil;
import com.ruoyi.common.core.web.controller.BaseController;
import com.ruoyi.common.core.web.domain.AjaxResult;
import com.ruoyi.common.core.web.page.TableDataInfo;
import com.ruoyi.flowable.workflow.domain.WfCategory;
import com.ruoyi.flowable.workflow.domain.vo.WfCategoryVo;
import com.ruoyi.flowable.workflow.service.IWfCategoryService;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.Arrays;
import java.util.List;

/**
 * 流程分类Controller
 *
 * @author KonBAI
 * @createTime 2022/3/10 00:12
 */
@Validated
@RequiredArgsConstructor
@RestController
@RequestMapping("/category")
public class WfCategoryController extends BaseController {

    private final IWfCategoryService categoryService;

    /**
     * 查询流程分类列表
     */
    @GetMapping("/list")
    public TableDataInfo list(WfCategory category) {
        List<WfCategoryVo> list = categoryService.queryList(category);
        return getDataTable(list);
    }

    /**
     * 查询全部的流程分类列表
     */
    @GetMapping("/listAll")
    public R<List<WfCategoryVo>> listAll(WfCategory category) {
        return R.ok(categoryService.queryList(category));
    }

    /**
     * 导出流程分类列表
     */
    @PostMapping("/export")
    public void export(@Validated WfCategory category, HttpServletResponse response) {
        List<WfCategoryVo> list = categoryService.queryList(category);
        ExcelUtil<WfCategoryVo> util = new ExcelUtil<WfCategoryVo>(WfCategoryVo.class);
        util.exportExcel(response, list, "流程分类","流程分类");
    }

    /**
     * 获取流程分类详细信息
     * @param categoryId 分类主键
     */
    @GetMapping("/{categoryId}")
    public R<WfCategoryVo> getInfo(@NotNull(message = "主键不能为空") @PathVariable("categoryId") Long categoryId) {
        return R.ok(categoryService.queryById(categoryId));
    }

    /**
     * 新增流程分类
     */
    @PostMapping
    public AjaxResult add(@Validated @RequestBody WfCategory category) {
        if (!categoryService.checkCategoryCodeUnique(category)) {
            return AjaxResult.error("新增流程分类'" + category.getCategoryName() + "'失败，流程编码已存在");
        }
        return toAjax(categoryService.insertCategory(category));
    }

    /**
     * 修改流程分类
     */
    @PutMapping()
    public AjaxResult edit(@Validated @RequestBody WfCategory category) {
        if (!categoryService.checkCategoryCodeUnique(category)) {
            return AjaxResult.error("修改流程分类'" + category.getCategoryName() + "'失败，流程编码已存在");
        }
        return toAjax(categoryService.updateCategory(category));
    }

    /**
     * 删除流程分类
     * @param categoryIds 分类主键串
     */
    @DeleteMapping("/{categoryIds}")
    public AjaxResult remove(@NotEmpty(message = "主键不能为空") @PathVariable Long[] categoryIds) {
        return toAjax(categoryService.deleteWithValidByIds(Arrays.asList(categoryIds), true));
    }
}
