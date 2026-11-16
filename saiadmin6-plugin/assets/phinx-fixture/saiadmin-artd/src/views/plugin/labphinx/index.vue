<template><div class="p-6"><h1>Phinx 插件验证</h1><p>版本 {{ version }}</p><p v-if="error">{{error}}</p><ul><li v-for="item in items" :key="item.id">{{item.id}}: {{item.label}}</li></ul></div></template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/utils/http'
const version = '1.0.1'
const items = ref<{id:number,label:string}[]>([])
const error=ref('')
onMounted(async()=>{try {items.value=await request.get({url:'/labphinx/items'})}catch(e){error.value=String(e)}})
</script>
