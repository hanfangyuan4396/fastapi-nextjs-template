#!/bin/bash
#====================================================================
# fastapi-nextjs 服务部署管理脚本
# 功能：管理部署的服务（API、Web、Nginx等）
# 用法：./fastapi-nextjs-service.sh [操作]
# 操作：
#   start   - 启动服务
#   stop    - 停止服务
#   logs    - 查看服务日志
#   -h      - 显示帮助信息
#====================================================================

# 显示帮助信息函数
show_help() {
  echo "用法: ./fastapi-nextjs-service.sh [操作]"
  echo "操作:"
  echo "  start   - 启动服务"
  echo "  stop    - 停止服务"
  echo "  logs    - 查看服务日志"
  echo "  -h      - 显示此帮助信息"
  echo ""
  echo "示例:"
  echo "  ./fastapi-nextjs-service.sh start  # 启动服务"
  echo "  ./fastapi-nextjs-service.sh stop   # 停止服务"
  echo "  ./fastapi-nextjs-service.sh logs   # 查看服务日志"
}

# 如果没有提供操作参数或请求帮助，显示帮助信息
if [ -z "$1" ] || [ "$1" = "-h" ]; then
  show_help
  exit 0
fi

# 设置操作
OPERATION=$1
PROJECT_NAME="fastapi-nextjs"
COMPOSE_FILE="docker-compose.yaml"

# 执行相应的操作
case $OPERATION in
  start)
    echo "启动服务..."
    docker compose -p $PROJECT_NAME -f $COMPOSE_FILE up -d
    ;;
  stop)
    echo "停止服务..."
    docker compose -p $PROJECT_NAME -f $COMPOSE_FILE down
    ;;
  logs)
    echo "查看服务日志..."
    docker compose -p $PROJECT_NAME -f $COMPOSE_FILE logs -f --tail 200
    ;;
  *)
    echo "错误: 未知操作 '$OPERATION'"
    show_help
    exit 1
    ;;
esac
