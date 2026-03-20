<script setup lang="ts">
// 首页逻辑目前非常简单，主要负责导航
</script>

<template>
  <div class="min-h-screen bg-slate-50 p-8 md:p-12">
    <header class="max-w-6xl mx-auto mb-16 animate-fade-in">
      <div class="flex items-center gap-4 mb-4">
        <div class="w-12 h-12 bg-blue-600 rounded-2xl flex items-center justify-center text-white shadow-lg">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>
        </div>
        <h1 class="text-3xl font-black text-slate-800 tracking-tight">智程开发平台</h1>
      </div>
      <p class="text-slate-500 text-lg font-medium">欢迎回来！请选择一个 AI 辅助模块开始工作。</p>
    </header>

    <main class="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
      <div
        @click="$router.push('/task')"
        class="group cursor-pointer p-8 bg-white border border-slate-200 rounded-[2.5rem] shadow-sm hover:shadow-2xl hover:border-blue-500 transition-all duration-500 relative overflow-hidden"
      >
        <div class="absolute -right-8 -top-8 w-32 h-32 bg-blue-50 rounded-full group-hover:scale-150 transition-transform duration-700"></div>

        <div class="relative z-10">
          <div class="w-16 h-16 bg-blue-600 text-white rounded-2xl flex items-center justify-center mb-8 shadow-xl shadow-blue-100 group-hover:rotate-12 transition-transform">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m18 16 4-4-4-4"/><path d="m6 8-4 4 4 4"/><path d="m14.5 4-5 16"/></svg>
          </div>
          <h2 class="text-2xl font-bold text-slate-800 mb-3">AI 编程教练</h2>
          <p class="text-slate-500 leading-relaxed mb-6">
            根据您的技术栈自动生成挑战任务，提供实时代码批改与毒舌建议。
          </p>
          <div class="flex items-center text-blue-600 font-bold gap-2 group-hover:translate-x-2 transition-transform">
            立即进入 <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
          </div>
        </div>
      </div>

      <div class="p-8 bg-slate-100/50 border-2 border-dashed border-slate-200 rounded-[2.5rem] flex flex-col items-center justify-center text-slate-400 min-h-[320px]">
        <div class="w-12 h-12 rounded-full border-2 border-slate-200 flex items-center justify-center mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14"/><path d="M5 12h14"/></svg>
        </div>
        <p class="font-bold uppercase tracking-widest text-xs">更多功能开发中...</p>
      </div>
    </main>
  </div>
</template>

<style scoped>
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in {
  animation: fadeIn 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
</style>
