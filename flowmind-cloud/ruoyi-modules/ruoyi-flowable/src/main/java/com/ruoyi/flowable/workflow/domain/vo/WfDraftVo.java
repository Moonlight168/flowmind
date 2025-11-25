package com.ruoyi.flowable.workflow.domain.vo;

import com.alibaba.excel.annotation.ExcelIgnoreUnannotated;
import com.alibaba.excel.annotation.ExcelProperty;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.util.Date;

/**
 * 流程草稿视图对象
 *
 * @author ruoyi
 * @createTime 2025/01/01 00:00
 */
@Data
@ExcelIgnoreUnannotated
public class WfDraftVo {

    private static final long serialVersionUID = 1L;

    /**
     * 草稿主键
     */
    @ExcelProperty(value = "草稿ID")
    private Long draftId;

    /**
     * 用户ID
     */
    @ExcelProperty(value = "用户ID")
    private Long userId;

    /**
     * 流程定义ID
     */
    @ExcelProperty(value = "流程定义ID")
    private String definitionId;

    /**
     * 部署ID
     */
    @ExcelProperty(value = "部署ID")
    private String deployId;

    /**
     * 流程名称
     */
    @ExcelProperty(value = "流程名称")
    private String processName;

    /**
     * 表单数据(JSON格式)
     */
    @ExcelProperty(value = "表单数据")
    private String formData;

    /**
     * 表单模型(JSON格式)
     */
    @ExcelProperty(value = "表单模型")
    private String formModel;

    /**
     * 创建时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @ExcelProperty(value = "创建时间")
    private Date createTime;

    /**
     * 更新时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @ExcelProperty(value = "更新时间")
    private Date updateTime;

    /**
     * 删除标志(0代表存在 2代表删除)
     */
    @ExcelProperty(value = "删除标志")
    private String delFlag;
}