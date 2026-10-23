"""不依赖日志或响应模型的异常分组，供基础设施启动阶段使用。"""

CONFIGURATION_ERRORS = (NameError, TypeError, ValueError)
