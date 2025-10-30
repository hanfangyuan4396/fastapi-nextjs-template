# 构建阶段
# FROM registry.cn-hangzhou.aliyuncs.com/hanfangyuan/node:22-alpine AS builder
FROM node:22-alpine AS builder

WORKDIR /web

# 复制依赖文件
COPY package.json package-lock.json ./

RUN npm ci

# 复制所有文件
COPY . .

# 设置环境变量
# TODO 除了放到Dockerfile还有其他更好的方式吗
ENV NEXT_PUBLIC_API_BASE_URL=/api

# 构建应用
RUN npm run build

# 运行阶段
# FROM registry.cn-hangzhou.aliyuncs.com/hanfangyuan/node:22-alpine AS runner
FROM node:22-alpine AS runner

WORKDIR /web

# 复制构建结果
COPY --from=builder /web/public ./public
COPY --from=builder /web/.next/standalone ./
COPY --from=builder /web/.next/static ./.next/static

# 暴露端口
EXPOSE 3000

# 启动应用
ENTRYPOINT ["node", "server.js"]
