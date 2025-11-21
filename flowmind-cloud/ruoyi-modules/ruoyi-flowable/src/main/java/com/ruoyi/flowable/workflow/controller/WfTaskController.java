package com.ruoyi.flowable.workflow.controller;

import cn.hutool.core.util.ObjectUtil;
import com.ruoyi.common.core.domain.R;
import com.ruoyi.flowable.workflow.domain.bo.WfTaskBo;
import com.ruoyi.flowable.workflow.service.IWfTaskService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import javax.imageio.ImageIO;
import jakarta.servlet.http.HttpServletResponse;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

/**
 * 工作流任务管理
 *
 * @author KonBAI
 * @createTime 2022/3/10 00:12
 */
@Slf4j
@RequiredArgsConstructor
@RestController
@RequestMapping("/task")
public class WfTaskController {

    private final IWfTaskService flowTaskService;

    /**
     * 取消流程
     */
    @PostMapping(value = "/stopProcess")
    public R stopProcess(@RequestBody WfTaskBo bo) {
        flowTaskService.stopProcess(bo);
         return R.ok(null,"操作成功");
    }

    /**
     * 撤回流程
     */
    @PostMapping(value = "/revokeProcess")
    public R revokeProcess(@RequestBody WfTaskBo bo) {
        flowTaskService.revokeProcess(bo);
         return R.ok(null,"操作成功");
    }

    /**
     * 获取流程变量
     * @param taskId 流程任务Id
     */
    @GetMapping(value = "/processVariables/{taskId}")
    public R processVariables(@PathVariable(value = "taskId") String taskId) {
        return R.ok(flowTaskService.getProcessVariables(taskId));
    }

    /**
     * 审批任务
     */
    @PostMapping(value = "/complete")
    public R complete(@RequestBody WfTaskBo bo) {
        flowTaskService.complete(bo);
         return R.ok(null,"操作成功");
    }

    /**
     * 拒绝任务
     */
    @PostMapping(value = "/reject")
    public R taskReject(@RequestBody WfTaskBo taskBo) {
        flowTaskService.taskReject(taskBo);
         return R.ok(null,"操作成功");
    }

    /**
     * 退回任务
     */
    @PostMapping(value = "/return")
    public R taskReturn(@RequestBody WfTaskBo bo) {
        flowTaskService.taskReturn(bo);
         return R.ok(null,"操作成功");
    }

    /**
     * 获取所有可回退的节点
     */
    @PostMapping(value = "/returnList")
    public R findReturnTaskList(@RequestBody WfTaskBo bo) {
        return R.ok(flowTaskService.findReturnTaskList(bo));
    }

    /**
     * 删除任务
     */
    @DeleteMapping(value = "/delete")
    public R delete(@RequestBody WfTaskBo bo) {
        flowTaskService.deleteTask(bo);
         return R.ok(null,"操作成功");
    }

    /**
     * 认领/签收任务
     */
    @PostMapping(value = "/claim")
    public R claim(@RequestBody WfTaskBo bo) {
        flowTaskService.claim(bo);
         return R.ok(null,"操作成功");
    }

    /**
     * 取消认领/签收任务
     */
    @PostMapping(value = "/unClaim")
    public R unClaim(@RequestBody WfTaskBo bo) {
        flowTaskService.unClaim(bo);
         return R.ok(null,"操作成功");
    }

    /**
     * 委派任务
     */
    @PostMapping(value = "/delegate")
    public R delegate(@RequestBody WfTaskBo bo) {
        if (ObjectUtil.hasNull(bo.getTaskId(), bo.getUserId())) {
            return R.fail("参数错误！");
        }
        flowTaskService.delegateTask(bo);
         return R.ok(null,"操作成功");
    }

    /**
     * 转办任务
     */
    @PostMapping(value = "/transfer")
    public R transfer(@RequestBody WfTaskBo bo) {
        if (ObjectUtil.hasNull(bo.getTaskId(), bo.getUserId())) {
            return R.fail("参数错误！");
        }
        flowTaskService.transferTask(bo);
         return R.ok(null,"操作成功");
    }

    /**
     * 生成流程图
     *
     * @param processId 任务ID
     */
    @RequestMapping("/diagram/{processId}")
    public void genProcessDiagram(HttpServletResponse response,
                                  @PathVariable("processId") String processId) {
        InputStream inputStream = flowTaskService.diagram(processId);
        OutputStream os = null;
        BufferedImage image = null;
        try {
            image = ImageIO.read(inputStream);
            response.setContentType("image/png");
            os = response.getOutputStream();
            if (image != null) {
                ImageIO.write(image, "png", os);
            }
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            try {
                if (os != null) {
                    os.flush();
                    os.close();
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }
}
