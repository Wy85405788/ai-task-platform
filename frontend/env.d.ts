/// <reference types="vite/client" />
// 告诉 TypeScript：所有以 .vue 结尾的文件都是一个 Vue 组件
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}
