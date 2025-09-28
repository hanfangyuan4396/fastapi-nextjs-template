"use client";



export default function HomePage() {


  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-4 py-16 sm:px-6 sm:py-20">
      <h1 className="text-3xl font-semibold sm:text-4xl">学生管理系统模板</h1>
      <p className="text-lg text-muted-foreground">Next.js + FastAPI 前后端分离示例，适合作为教学与项目起点。</p>
      <p className="text-base leading-7 text-muted-foreground">通过导航栏进入学生管理页面，体验查询、分页与新增表单的基础能力。</p>
    </div>
  );
}
