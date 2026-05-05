<template>
  <div class="app-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header flex justify-between items-center">
          <span class="text-lg font-semibold">AI 模型配置</span>
          <el-tag :type="healthStatus ? 'success' : 'danger'">
            {{ healthStatus ? '服务正常' : '服务异常' }}
          </el-tag>
        </div>
      </template>

      <el-form :model="form" :rules="rules" ref="configFormRef" label-width="140px">
        <!-- 阿里云配置 -->
        <el-divider content-position="left">
          <el-icon><Cloudy /></el-icon>
          阿里云（通义千问）
        </el-divider>

        <el-form-item label="启用" prop="aliyunEnabled">
          <el-switch v-model="form.aliyunEnabled" active-text="启用" inactive-text="禁用" />
        </el-form-item>

        <el-form-item label="API Key" prop="aliyunApiKey">
          <el-input
            v-model="form.aliyunApiKey"
            type="password"
            show-password
            placeholder="请输入阿里云 API Key（如：sk-xxxxx）"
            clearable
          />
          <div class="form-tip">在阿里云百炼平台获取：https://bailian.console.aliyun.com/</div>
        </el-form-item>

        <el-form-item label="模型名称" prop="aliyunModel">
          <el-input
            v-model="form.aliyunModel"
            placeholder="如：qwen-plus, qwen-max, qwen-turbo"
            clearable
          />
          <div class="form-tip">
            支持结构化输出的模型
          </div>
        </el-form-item>

        <el-form-item label="Base URL" prop="aliyunBaseUrl">
          <el-input v-model="form.aliyunBaseUrl" placeholder="https://dashscope.aliyuncs.com/compatible-mode/v1" clearable />
          <div class="form-tip">阿里云百炼 API 地址</div>
        </el-form-item>

        <el-form-item>
          <el-button @click="testModel('aliyun')" :loading="testingAliyun">
            <el-icon><Connection /></el-icon>
            测试阿里云模型
          </el-button>
        </el-form-item>

        <!-- 火山引擎配置 -->
        <el-divider content-position="left">
          <el-icon><Lightning /></el-icon>
          火山引擎（豆包）
        </el-divider>

        <el-form-item label="启用" prop="volcengineEnabled">
          <el-switch v-model="form.volcengineEnabled" active-text="启用" inactive-text="禁用" />
        </el-form-item>

        <el-form-item label="API Key" prop="volcengineApiKey">
          <el-input
            v-model="form.volcengineApiKey"
            type="password"
            show-password
            placeholder="请输入火山引擎 API Key"
            clearable
          />
          <div class="form-tip">在火山引擎控制台获取：https://console.volcengine.com/</div>
        </el-form-item>

        <el-form-item label="模型名称" prop="volcengineModel">
          <el-input
            v-model="form.volcengineModel"
            placeholder="如：doubao-pro-4k, doubao-lite-4k"
            clearable
          />
          <div class="form-tip">
            支持结构化输出的模型
          </div>
        </el-form-item>

        <el-form-item label="Base URL" prop="volcengineBaseUrl">
          <el-input v-model="form.volcengineBaseUrl" placeholder="https://ark.cn-beijing.volces.com/api/v3" clearable />
          <div class="form-tip">火山引擎方舟 API 地址</div>
        </el-form-item>

        <el-form-item>
          <el-button @click="testModel('volcengine')" :loading="testingVolcengine">
            <el-icon><Connection /></el-icon>
            测试火山引擎模型
          </el-button>
        </el-form-item>

        <!-- 默认模型 -->
        <el-divider content-position="left">
          <el-icon><Star /></el-icon>
          默认配置
        </el-divider>

        <el-form-item label="默认服务商" prop="defaultProvider">
          <el-radio-group v-model="form.defaultProvider">
            <el-radio label="aliyun">阿里云</el-radio>
            <el-radio label="volcengine">火山引擎</el-radio>
          </el-radio-group>
          <div class="form-tip">优先使用的模型服务商</div>
        </el-form-item>

        <el-form-item label="模型降级" prop="fallbackEnabled">
          <el-switch v-model="form.fallbackEnabled" active-text="启用" inactive-text="禁用" />
          <div class="form-tip">启用后，主模型失败时自动切换到备用服务商</div>
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item>
          <el-button type="primary" @click="submitForm" :loading="saving">保存配置</el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup name="AiConfig" lang="js">
import { Cloudy, Lightning, Connection, Star } from '@element-plus/icons-vue'
import { checkAiHealth, aiFormChat } from '@/api/workflow/ai'
import { ElMessage } from 'element-plus'

const { proxy } = getCurrentInstance()

// 表单数据
const form = reactive({
  // 阿里云
  aliyunEnabled: true,
  aliyunApiKey: '',
  aliyunModel: 'qwen-plus',
  aliyunBaseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  // 火山引擎
  volcengineEnabled: false,
  volcengineApiKey: '',
  volcengineModel: 'doubao-pro-4k',
  volcengineBaseUrl: 'https://ark.cn-beijing.volces.com/api/v3',
  // 默认配置
  defaultProvider: 'aliyun',
  fallbackEnabled: true
})

// 表单验证规则
const rules = {
  aliyunApiKey: [{ required: true, message: '请输入阿里云 API Key', trigger: 'blur' }],
  aliyunModel: [{ required: true, message: '请输入阿里云模型名称', trigger: 'blur' }],
  aliyunBaseUrl: [{ required: true, message: '请输入阿里云 Base URL', trigger: 'blur' }],
  volcengineApiKey: [{ required: true, message: '请输入火山引擎 API Key', trigger: 'blur' }],
  volcengineModel: [{ required: true, message: '请输入火山引擎模型名称', trigger: 'blur' }],
  volcengineBaseUrl: [{ required: true, message: '请输入火山引擎 Base URL', trigger: 'blur' }],
  defaultProvider: [{ required: true, message: '请选择默认服务商', trigger: 'change' }]
}

const configFormRef = ref(null)
const healthStatus = ref(null)
const testingAliyun = ref(false)
const testingVolcengine = ref(false)
const saving = ref(false)

// 测试服务健康状态
const testHealth = async () => {
  try {
    const res = await checkAiHealth()
    healthStatus.value = res.status === 'ok'
  } catch (error) {
    healthStatus.value = false
  }
}

// 测试模型
const testModel = async (provider) => {
  const isAliyun = provider === 'aliyun'
  const testing = isAliyun ? testingAliyun : testingVolcengine
  testing.value = true

  try {
    const model = isAliyun ? form.aliyunModel : form.volcengineModel
    const res = await aiFormChat({
      user_input: '你好，请用一句话介绍你自己',
      thread_id: null,
      selected_model: model,
      fallback_enabled: false
    })

    if (res.message) {
      ElMessage.success(`${isAliyun ? '阿里云' : '火山引擎'} 模型响应正常：${res.message}`)
    } else {
      ElMessage.warning('模型未返回预期消息')
    }
  } catch (error) {
    ElMessage.error(`${isAliyun ? '阿里云' : '火山引擎'} 模型测试失败：${error.message || '请稍后重试'}`)
  } finally {
    testing.value = false
  }
}

// 保存配置
const submitForm = async () => {
  if (!configFormRef.value) return

  await configFormRef.value.validate(async (valid) => {
    if (valid) {
      saving.value = true
      try {
        // TODO: 调用后端保存配置 API
        // await saveAiConfig(form)

        // 临时处理：保存到 localStorage
        localStorage.setItem('ai_config', JSON.stringify(form))

        ElMessage.success('配置已保存')
      } catch (error) {
        ElMessage.error('保存失败：' + (error.message || '请稍后重试'))
      } finally {
        saving.value = false
      }
    }
  })
}

// 重置表单
const resetForm = () => {
  if (configFormRef.value) {
    configFormRef.value.resetFields()
  }
  // 从 localStorage 加载配置
  const savedConfig = localStorage.getItem('ai_config')
  if (savedConfig) {
    Object.assign(form, JSON.parse(savedConfig))
  }
}

// 加载配置
const loadConfig = () => {
  const savedConfig = localStorage.getItem('ai_config')
  if (savedConfig) {
    Object.assign(form, JSON.parse(savedConfig))
  }
}

onMounted(() => {
  loadConfig()
  testHealth()
})
</script>

<style lang="scss" scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

:deep(.el-divider__text) {
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>