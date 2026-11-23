<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string
    description?: string
  }>(),
  {
    description: '该模块正在开发中，将在后续里程碑交付。',
  },
)
</script>

<template>
  <el-card shadow="never">
    <el-result icon="info" :title="title" :sub-title="description">
      <template #extra>
        <el-tag type="info">待开发</el-tag>
      </template>
    </el-result>
  </el-card>
</template>
