<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { reactive, ref, watch } from 'vue'

import { resetUserPassword } from '@/api/user'
import type { UserInfo } from '@/types'

const visible = defineModel<boolean>({ required: true })

const props = defineProps<{
  user?: UserInfo | null
}>()

const emit = defineEmits<{ success: [] }>()

const formRef = ref<FormInstance>()
const submitting = ref(false)
const form = reactive({ new_password: '', confirm_password: '' })

const rules: FormRules = {
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 72, message: '密码长度 6-72 位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== form.new_password) {
          callback(new Error('两次输入的密码不一致'))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
}

watch(visible, (opened) => {
  if (!opened) return
  form.new_password = ''
  form.confirm_password = ''
  formRef.value?.clearValidate()
})

async function submit() {
  if (!formRef.value || !props.user) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    await resetUserPassword(props.user.id, form.new_password)
    ElMessage.success('密码已重置')
    visible.value = false
    emit('success')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <el-dialog v-model="visible" title="重置密码" width="420px">
    <el-alert
      :title="`正在重置账号「${props.user?.username ?? ''}」的密码`"
      type="warning"
      :closable="false"
      show-icon
      style="margin-bottom: 16px"
    />
    <el-form ref="formRef" :model="form" :rules="rules" label-width="88px">
      <el-form-item label="新密码" prop="new_password">
        <el-input v-model="form.new_password" type="password" show-password maxlength="72" />
      </el-form-item>
      <el-form-item label="确认密码" prop="confirm_password">
        <el-input v-model="form.confirm_password" type="password" show-password maxlength="72" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">确定重置</el-button>
    </template>
  </el-dialog>
</template>
