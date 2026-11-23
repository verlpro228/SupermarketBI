<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { computed, reactive, ref, watch } from 'vue'

import { createUser, updateUser } from '@/api/user'
import type { UserInfo, UserRole } from '@/types'

const visible = defineModel<boolean>({ required: true })

const props = defineProps<{
  user?: UserInfo | null
}>()

const emit = defineEmits<{ success: [] }>()

const isEdit = computed(() => Boolean(props.user?.id))
const formRef = ref<FormInstance>()
const submitting = ref(false)

const form = reactive({
  username: '',
  password: '',
  real_name: '',
  role: 'keeper' as UserRole,
})

const rules = computed<FormRules>(() => ({
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { min: 3, max: 50, message: '长度 3-50 个字符', trigger: 'blur' },
    {
      pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/,
      message: '字母开头，只能包含字母、数字和下划线',
      trigger: 'blur',
    },
  ],
  ...(isEdit.value
    ? {}
    : {
        password: [
          { required: true, message: '请输入初始密码', trigger: 'blur' },
          { min: 6, max: 72, message: '密码长度 6-72 位', trigger: 'blur' },
        ],
      }),
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}))

watch(visible, (opened) => {
  if (!opened) return
  form.username = props.user?.username ?? ''
  form.real_name = props.user?.real_name ?? ''
  form.role = props.user?.role ?? 'keeper'
  form.password = ''
  formRef.value?.clearValidate()
})

async function submit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (isEdit.value && props.user) {
      await updateUser(props.user.id, {
        real_name: form.real_name || null,
        role: form.role,
      })
      ElMessage.success('保存成功')
    } else {
      await createUser({
        username: form.username,
        password: form.password,
        real_name: form.real_name || null,
        role: form.role,
      })
      ElMessage.success('新增成功')
    }
    visible.value = false
    emit('success')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <el-dialog v-model="visible" :title="isEdit ? '编辑用户' : '新增用户'" width="460px">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
      <el-form-item label="账号" prop="username">
        <el-input
          v-model="form.username"
          :disabled="isEdit"
          placeholder="字母开头，可含数字和下划线"
          maxlength="50"
        />
      </el-form-item>

      <el-form-item v-if="!isEdit" label="初始密码" prop="password">
        <el-input v-model="form.password" type="password" show-password maxlength="72" />
      </el-form-item>

      <el-form-item label="姓名" prop="real_name">
        <el-input v-model="form.real_name" placeholder="选填" maxlength="50" />
      </el-form-item>

      <el-form-item label="角色" prop="role">
        <el-radio-group v-model="form.role">
          <el-radio value="keeper">库管员</el-radio>
          <el-radio value="admin">管理员</el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">确定</el-button>
    </template>
  </el-dialog>
</template>
